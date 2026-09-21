import os
import re
import sys
import json
import time
import requests
import feedparser
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
from zoneinfo import ZoneInfo

RESEARCHERS = 'https://raw.githubusercontent.com/davidheineman/conference-papers/main/constants.py'

# New submissions come from the RSS feeds: they cover a full day of announcements
# in one request per category and are not subject to the export API's throttling.
ARXIV_RSS = 'https://rss.arxiv.org/rss'
ANNOUNCE_TYPES = {'new', 'cross'}

# The export API is only used to backfill papers older than today's announcements.
# It rejects sustained querying with 429s that persist for a long time afterwards,
# so each run works through a small rotating slice of the author list.
ARXIV_API = 'https://export.arxiv.org/api/query'
AUTHORS_PER_QUERY = 8
RESULTS_PER_QUERY = 100
BACKFILL_BATCHES = 2
BACKFILL_ATTEMPTS = 3
BACKFILL_BUDGET = 8 * 60
INITIAL_BACKOFF = 60
MAX_BACKOFF = 240

# arXiv asks API clients to identify themselves and to stay under ~1 request / 3s.
USER_AGENT = 'fresh-finds/1.0 (+https://github.com/davidheineman/fresh-finds)'
MIN_REQUEST_INTERVAL = 5.0
REQUEST_TIMEOUT = 60

CATEGORIES = ['cs.LG', 'cs.AI', 'cs.CL', 'cs.HC', 'stat.ML']

# Papers are dated by when they first went live on arXiv. The RSS feeds report that
# directly; the API reports submission times, which are converted with the schedule below.
ARXIV_TZ = ZoneInfo('America/New_York')
SUBMISSION_CUTOFF_HOUR = 14

MAX_ABSTRACT_LEN = 1600
MAX_PAPERS = 500

_last_api_request_at = 0.0


@dataclass
class Paper:
    title: str
    authors: List[str]
    summary: str
    published: str
    published_iso: str
    pdf_url: str
    arxiv_url: str
    queried_author: str
    matching_authors: List[str] = field(default_factory=list)

    def to_json_dict(self) -> Dict:
        return asdict(self)


def fetch_authors_from_github() -> List[str]:
    """Fetch the authors list from the GitHub repository."""
    response = requests.get(RESEARCHERS, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch constants.py: {response.status_code}")

    # Execute the Python code to get the variables
    namespace = {}
    exec(response.text, namespace)

    # Get the ARXIV_RESEARCHERS list
    if 'ARXIV_RESEARCHERS' not in namespace:
        raise RuntimeError("ARXIV_RESEARCHERS not found in constants.py")

    authors = namespace['ARXIV_RESEARCHERS']

    if not authors:
        raise RuntimeError("No authors found.")

    return authors


def _normalize_name(name: str) -> Set[str]:
    """Normalize an author name into a set of lowercase tokens (ignoring periods/commas)."""
    return set(name.lower().replace(".", "").replace(",", "").split())


def _find_matching_authors(paper_authors: List[str], tracked_authors: List[str]) -> List[str]:
    """Find which tracked authors appear in a paper's author list."""
    normalized_paper = [_normalize_name(a) for a in paper_authors]

    matches = []
    for tracked in tracked_authors:
        tracked_parts = _normalize_name(tracked)
        for paper_parts in normalized_paper:
            if tracked_parts == paper_parts:
                matches.append(tracked)
                break
    return matches


def _arxiv_id(value: str) -> str:
    """Version-stripped arXiv id, used to dedupe across feeds and across runs."""
    match = re.search(r'(\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})', value or '')
    return match.group(1) if match else (value or '')


def _build_paper(title, authors_list, summary, published, abs_url, pdf_url, matching) -> Paper:
    summary = ' '.join(summary.split())
    if len(summary) > MAX_ABSTRACT_LEN:
        summary = summary[:MAX_ABSTRACT_LEN] + '...'

    return Paper(
        title=' '.join(title.split()),
        authors=authors_list,
        summary=summary,
        published=published.strftime("%b %d"),
        published_iso=published.isoformat(),
        pdf_url=pdf_url,
        arxiv_url=abs_url,
        queried_author=matching[0],
        matching_authors=matching,
    )


def _published(entry) -> Optional[datetime]:
    parsed = entry.get('published_parsed')
    return datetime(*parsed[:6], tzinfo=timezone.utc) if parsed else None


def announcement_date(submitted: datetime) -> datetime:
    """The date a submission first went live on arXiv.

    Submissions are batched at a 14:00 ET weekday cutoff, and the batch that closed
    at that cutoff is announced the following weekday. Applying this to the v1
    submission time gives a paper's first announcement, which never moves when a
    later version is posted."""
    day = submitted.astimezone(ARXIV_TZ)
    date = day.date()

    # A submission only makes a cutoff on a weekday; weekends roll into Monday's
    if day.hour >= SUBMISSION_CUTOFF_HOUR or date.weekday() >= 5:
        date += timedelta(days=1)
    while date.weekday() >= 5:
        date += timedelta(days=1)

    date += timedelta(days=1)
    while date.weekday() >= 5:
        date += timedelta(days=1)

    # Stored in UTC to match the RSS feeds, so timestamps stay directly comparable
    return datetime(date.year, date.month, date.day, tzinfo=ARXIV_TZ).astimezone(timezone.utc)


def fetch_from_rss(authors: List[str]) -> Tuple[List[Paper], int]:
    """Read today's announcements from the per-category RSS feeds."""
    print(f"Reading RSS feeds for {len(CATEGORIES)} categories...")

    papers: List[Paper] = []
    failed = 0

    for category in CATEGORIES:
        try:
            response = requests.get(
                f"{ARXIV_RSS}/{category}",
                headers={'User-Agent': USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            failed += 1
            print(f"  {category}: failed ({e})")
            continue

        feed = feedparser.parse(response.text)
        matched = []

        for entry in feed.entries:
            if entry.get('arxiv_announce_type') not in ANNOUNCE_TYPES:
                continue

            published = _published(entry)
            if published is None:
                continue

            # RSS gives the author list as a single comma-separated string
            authors_list = [n.strip() for n in (entry.get('author') or '').split(',') if n.strip()]
            matching = _find_matching_authors(authors_list, authors)
            if not matching:
                continue

            # Summaries are prefixed with "arXiv:ID Announce Type: new  Abstract: ..."
            summary = re.sub(r'^.*?Abstract:\s*', '', entry.get('summary', ''), flags=re.DOTALL)

            abs_url = entry.get('link') or f"https://arxiv.org/abs/{_arxiv_id(entry.get('id', ''))}"
            matched.append(_build_paper(
                title=entry.get('title', ''),
                authors_list=authors_list,
                summary=summary,
                published=published,
                abs_url=abs_url,
                pdf_url=abs_url.replace('/abs/', '/pdf/'),
                matching=matching,
            ))

        papers.extend(matched)
        print(f"  {category}: {len(feed.entries)} entries, {len(matched)} matched")

    return papers, failed


def _api_request(params: Dict, deadline: float) -> Optional[feedparser.FeedParserDict]:
    """GET the export API, honoring its rate limit. Returns None if it keeps refusing."""
    global _last_api_request_at

    backoff = INITIAL_BACKOFF
    for attempt in range(1, BACKFILL_ATTEMPTS + 1):
        elapsed = time.monotonic() - _last_api_request_at
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)

        try:
            response = requests.get(
                ARXIV_API,
                params=params,
                headers={'User-Agent': USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as e:
            print(f"    request failed ({e})")
            response = None
        finally:
            _last_api_request_at = time.monotonic()

        if response is not None and response.status_code == 200:
            return feedparser.parse(response.text)

        status = f"HTTP {response.status_code}" if response is not None else "no response"
        if attempt == BACKFILL_ATTEMPTS or time.monotonic() + backoff > deadline:
            print(f"    {status}; giving up after {attempt} attempt(s)")
            break

        print(f"    {status}; waiting {backoff}s (attempt {attempt}/{BACKFILL_ATTEMPTS})")
        time.sleep(backoff)
        backoff = min(backoff * 2, MAX_BACKOFF)

    return None


def _parse_api_entry(entry, authors: List[str]) -> Optional[Paper]:
    """Convert one export API Atom entry into a Paper, or None if it isn't a match."""
    categories = {t.get('term') for t in entry.get('tags', [])}
    if not categories.intersection(CATEGORIES):
        return None

    authors_list = [a.get('name', '') for a in entry.get('authors', [])]
    matching = _find_matching_authors(authors_list, authors)
    if not matching:
        return None

    submitted = _published(entry)
    if submitted is None:
        return None

    abs_url = entry.get('id', '')
    pdf_url = next(
        (l.get('href') for l in entry.get('links', []) if l.get('title') == 'pdf'),
        abs_url.replace('/abs/', '/pdf/'),
    )

    return _build_paper(
        title=entry.get('title', ''),
        authors_list=authors_list,
        summary=entry.get('summary', ''),
        published=announcement_date(submitted),
        abs_url=abs_url,
        pdf_url=pdf_url.replace('http://', 'https://'),
        matching=matching,
    )


def backfill_from_api(authors: List[str]) -> List[Paper]:
    """Best-effort top-up for a rotating slice of authors. Never fatal: the API
    throttles hard, and RSS already covers everything announced today."""
    batches = [
        authors[i:i + AUTHORS_PER_QUERY]
        for i in range(0, len(authors), AUTHORS_PER_QUERY)
    ]

    # Rotate through the author list across runs so the archive stays fresh
    # without ever asking the API for more than a couple of queries at a time.
    slot = int(time.time() // (8 * 3600))
    selected = [batches[(slot * BACKFILL_BATCHES + i) % len(batches)] for i in range(BACKFILL_BATCHES)]

    print(f"\nBackfilling {len(selected)} of {len(batches)} author batches from the export API...")

    papers: List[Paper] = []
    deadline = time.monotonic() + BACKFILL_BUDGET

    for i, batch in enumerate(selected, 1):
        feed = _api_request({
            'search_query': " OR ".join(f'au:"{a}"' for a in batch),
            'start': 0,
            'max_results': RESULTS_PER_QUERY,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
        }, deadline)

        if feed is None:
            # Once the API starts refusing it keeps refusing; stop rather than
            # hammering it, which only prolongs the throttling.
            print(f"  batch {i}/{len(selected)}: skipped, abandoning backfill")
            break

        matched = [p for p in (_parse_api_entry(e, authors) for e in feed.entries) if p]
        papers.extend(matched)
        print(f"  batch {i}/{len(selected)}: {len(feed.entries)} results, {len(matched)} matched")

    return papers


def _sort_key(paper: Dict) -> tuple:
    """Sort newest first. Anything still undated keeps its existing relative order."""
    return (0, '') if not paper.get('published_iso') else (1, paper['published_iso'])


def merge_papers(existing: List[Dict], fetched: List[Paper]) -> List[Dict]:
    """Merge freshly fetched papers into the stored set, newest first."""
    merged: Dict[str, Dict] = {_arxiv_id(p.get('arxiv_url', '')): p for p in existing}
    for paper in fetched:
        merged.setdefault(_arxiv_id(paper.arxiv_url), paper.to_json_dict())

    # sorted() is stable, so legacy entries without published_iso keep their relative order
    return sorted(merged.values(), key=_sort_key, reverse=True)


def load_existing(json_path: str) -> List[Dict]:
    if not os.path.exists(json_path):
        return []
    try:
        with open(json_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Could not read existing papers.json ({e}); starting fresh")
        return []


def main():
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'papers.json')

    print(f"Fetching authors from {RESEARCHERS}...")
    authors = fetch_authors_from_github()
    print(f"Found {len(authors)} authors")

    existing = load_existing(json_path)
    print(f"Loaded {len(existing)} previously saved papers\n")

    fetched, failed_feeds = fetch_from_rss(authors)
    print(f"\nMatched {len(fetched)} papers in today's announcements")

    fetched += backfill_from_api(authors)

    if failed_feeds == len(CATEGORIES):
        # Every feed failed, so this is an arXiv outage rather than a quiet day.
        message = "could not read any arXiv RSS feed; keeping the existing papers.json"
        if not existing:
            print(f"::error::{message} - but there is nothing saved yet", file=sys.stderr)
            sys.exit(1)
        print(f"::warning::{message}")
        return

    if failed_feeds:
        print(f"::warning::{failed_feeds} RSS feed(s) failed; papers.json may be incomplete")

    papers = merge_papers(existing, fetched)[:MAX_PAPERS]
    added = len({_arxiv_id(p['arxiv_url']) for p in papers} - {_arxiv_id(p.get('arxiv_url', '')) for p in existing})

    with open(json_path, 'w') as f:
        json.dump(papers, f, indent=2)

    print(f"\nDone! Saved {len(papers)} papers to papers.json ({added} new)")


if __name__ == '__main__':
    main()
