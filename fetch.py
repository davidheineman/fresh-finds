import os
import re
import sys
import json
import time
import requests
import feedparser
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

RESEARCHERS = 'https://raw.githubusercontent.com/davidheineman/conference-papers/main/constants.py'
ARXIV_API = 'https://export.arxiv.org/api/query'

# arXiv asks API clients to identify themselves and to stay under ~1 request / 3s.
USER_AGENT = 'fresh-finds/1.0 (+https://github.com/davidheineman/fresh-finds)'
MIN_REQUEST_INTERVAL = 5.0

# arXiv rejects expensive queries with a 429 and then keeps throttling the caller
# for minutes, so query a handful of authors at a time and back off generously.
AUTHORS_PER_QUERY = 8
RESULTS_PER_QUERY = 100
MAX_ATTEMPTS = 5
INITIAL_BACKOFF = 60
MAX_BACKOFF = 480
REQUEST_TIMEOUT = 60

# Upper bound on the whole arXiv fetch. If throttling eats the budget we save
# whatever came back instead of letting the job grind on for hours.
TIME_BUDGET = 25 * 60

CATEGORIES = {'cs.LG', 'cs.AI', 'cs.CL', 'cs.HC', 'stat.ML'}

MAX_ABSTRACT_LEN = 1600
MAX_PAPERS = 500

_last_request_at = 0.0


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


def _arxiv_id(url: str) -> str:
    """Version-stripped arXiv id, used to dedupe across runs."""
    match = re.search(r'(\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})', url or '')
    return match.group(1) if match else (url or '')


def _request(params: Dict, deadline: float) -> Optional[feedparser.FeedParserDict]:
    """GET the arXiv API, honoring its rate limit. Returns None if it keeps refusing."""
    global _last_request_at

    backoff = INITIAL_BACKOFF
    for attempt in range(1, MAX_ATTEMPTS + 1):
        elapsed = time.monotonic() - _last_request_at
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
            print(f"    request failed ({e}); attempt {attempt}/{MAX_ATTEMPTS}")
            response = None
        finally:
            _last_request_at = time.monotonic()

        if response is not None and response.status_code == 200:
            return feedparser.parse(response.text)

        if attempt == MAX_ATTEMPTS:
            break

        wait = backoff
        if response is not None and response.status_code == 429:
            # arXiv rarely sends Retry-After, but use it when it does.
            try:
                wait = max(wait, int(response.headers.get('Retry-After', 0)))
            except ValueError:
                pass
            print(f"    rate limited; waiting {wait}s (attempt {attempt}/{MAX_ATTEMPTS})")
        else:
            status = f"HTTP {response.status_code}" if response is not None else "no response"
            print(f"    {status}; waiting {wait}s (attempt {attempt}/{MAX_ATTEMPTS})")

        if time.monotonic() + wait > deadline:
            break

        time.sleep(wait)
        backoff = min(backoff * 2, MAX_BACKOFF)

    return None


def _parse_entry(entry, tracked_authors: List[str]) -> Optional[Paper]:
    """Convert one Atom entry into a Paper, or None if it isn't a match."""
    categories = {t.get('term') for t in entry.get('tags', [])}
    if not categories.intersection(CATEGORIES):
        return None

    authors_list = [a.get('name', '') for a in entry.get('authors', [])]
    matching = _find_matching_authors(authors_list, tracked_authors)
    if not matching:
        return None

    summary = ' '.join(entry.get('summary', '').split())
    if len(summary) > MAX_ABSTRACT_LEN:
        summary = summary[:MAX_ABSTRACT_LEN] + '...'

    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

    arxiv_url = entry.get('id', '')
    pdf_url = next(
        (l.get('href') for l in entry.get('links', []) if l.get('title') == 'pdf'),
        arxiv_url.replace('/abs/', '/pdf/'),
    ).replace('http://', 'https://')

    return Paper(
        title=' '.join(entry.get('title', '').split()),
        authors=authors_list,
        summary=summary,
        published=published.strftime("%b %d"),
        published_iso=published.isoformat(),
        pdf_url=pdf_url,
        arxiv_url=arxiv_url,
        queried_author=matching[0],
        matching_authors=matching,
    )


def get_all_recent_papers(authors: List[str]) -> tuple[List[Paper], int]:
    """Fetch recent papers in small author batches. Returns (papers, failed_batch_count)."""
    batches = [
        authors[i:i + AUTHORS_PER_QUERY]
        for i in range(0, len(authors), AUTHORS_PER_QUERY)
    ]
    print(f"Querying arXiv for {len(authors)} authors in {len(batches)} batches...")

    papers: List[Paper] = []
    failed = 0
    deadline = time.monotonic() + TIME_BUDGET

    for i, batch in enumerate(batches, 1):
        if time.monotonic() > deadline:
            failed += len(batches) - i + 1
            print(f"  out of time after {i - 1}/{len(batches)} batches")
            break

        feed = _request({
            'search_query': " OR ".join(f'au:"{a}"' for a in batch),
            'start': 0,
            'max_results': RESULTS_PER_QUERY,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
        }, deadline)

        if feed is None:
            failed += 1
            print(f"  batch {i}/{len(batches)}: giving up after {MAX_ATTEMPTS} attempts")
            continue

        matched = [p for p in (_parse_entry(e, authors) for e in feed.entries) if p]
        papers.extend(matched)
        print(f"  batch {i}/{len(batches)}: {len(feed.entries)} results, {len(matched)} matched")

    return papers, failed


def _sort_key(paper: Dict) -> tuple:
    """Sort newest first. Entries predating published_iso keep their existing order."""
    return (0, '') if not paper.get('published_iso') else (1, paper['published_iso'])


def merge_papers(existing: List[Dict], fetched: List[Paper]) -> List[Dict]:
    """Merge freshly fetched papers into the stored set, newest first."""
    merged: Dict[str, Dict] = {_arxiv_id(p.get('arxiv_url', '')): p for p in existing}
    for paper in fetched:
        merged[_arxiv_id(paper.arxiv_url)] = paper.to_json_dict()

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
    print(f"Loaded {len(existing)} previously saved papers")

    print("\nFetching recent papers (this may take a few minutes)...")
    fetched, failed = get_all_recent_papers(authors)
    print(f"\nFetched {len(fetched)} papers matching tracked authors")

    if not fetched:
        # arXiv throttling is common and transient; keep serving what we already have
        # rather than failing the run (and blocking the Pages deploy) or truncating the feed.
        message = "arXiv returned no papers; keeping the existing papers.json"
        if not existing:
            print(f"::error::{message} - but there is nothing saved yet", file=sys.stderr)
            sys.exit(1)
        print(f"::warning::{message}")
        return

    if failed:
        print(f"::warning::{failed} author batch(es) failed; papers.json may be incomplete")

    papers = merge_papers(existing, fetched)[:MAX_PAPERS]
    new_count = len(papers) - len(existing)

    with open(json_path, 'w') as f:
        json.dump(papers, f, indent=2)

    print(f"\nDone! Saved {len(papers)} papers to papers.json ({new_count:+d} vs. previous run)")


if __name__ == '__main__':
    main()
