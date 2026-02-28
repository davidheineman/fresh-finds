import requests
import arxiv
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Set

RESEARCHERS = 'https://raw.githubusercontent.com/davidheineman/conference-papers/main/constants.py'
CATEGORIES = {'cs.LG', 'cs.AI', 'cs.CL', 'cs.HC', 'stat.ML'}

MAX_ABSTRACT_LEN = 1600
MAX_RESULTS = 4_000


@dataclass
class Paper:
    title: str
    authors: List[str]
    summary: str
    published: str
    published_raw: datetime
    pdf_url: str
    arxiv_url: str
    queried_author: str
    matching_authors: List[str] = field(default_factory=list)

    def to_json_dict(self) -> Dict:
        d = asdict(self)
        del d['published_raw']
        return d


def fetch_authors_from_github() -> List[str]:
    """Fetch the authors list from the GitHub repository."""
    response = requests.get(RESEARCHERS)
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


def get_all_recent_papers(authors: List[str], max_results: int = MAX_RESULTS) -> List[Paper]:
    """Fetch recent papers for all authors in a single batched arXiv query."""
    query = " OR ".join(f'au:"{author}"' for author in authors)

    print(f"Querying arXiv for {len(authors)} authors in one request (max {max_results} results)...")
    client = arxiv.Client(page_size=100, delay_seconds=3, num_retries=5)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    for result in client.results(search):
        paper_categories = set(result.categories)
        if not paper_categories.intersection(CATEGORIES):
            continue

        authors_list = [a.name for a in result.authors]
        matching = _find_matching_authors(authors_list, authors)
        if not matching:
            continue

        truncated_summary = result.summary[:MAX_ABSTRACT_LEN] + '...' if len(result.summary) > MAX_ABSTRACT_LEN else result.summary

        papers.append(Paper(
            title=result.title,
            authors=authors_list,
            summary=truncated_summary,
            published=result.published.strftime("%b %d"),
            published_raw=result.published,
            pdf_url=result.pdf_url,
            arxiv_url=result.entry_id,
            queried_author=matching[0],
            matching_authors=matching,
        ))

    papers.sort(key=lambda x: x.published_raw, reverse=True)
    print(f"Fetched {len(papers)} papers matching tracked authors")
    return papers


def main():
    print(f"Fetching authors from {RESEARCHERS}...")
    authors = fetch_authors_from_github()

    print(f"Found {len(authors)} authors")
    
    print("\nFetching recent papers (this may take a few minutes)...")
    papers = get_all_recent_papers(authors)
    
    # Keep top 500 papers for infinite scrolling
    papers = papers[:500]
    
    print(f"\nFound {len(papers)} unique recent papers")
    
    # Save papers to JSON
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'papers.json')
    
    with open(json_path, 'w') as f:
        papers_for_json = [p.to_json_dict() for p in papers]
        json.dump(papers_for_json, f, indent=2)
        print(f"\nDone! Saved {len(papers)} papers to papers.json")

if __name__ == '__main__':
    main()
