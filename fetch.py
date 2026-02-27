import requests
import arxiv
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict

RESEARCHERS = 'https://raw.githubusercontent.com/davidheineman/conference-papers/main/constants.py'
CATEGORIES = {'cs.LG', 'cs.AI', 'cs.CL', 'cs.HC', 'stat.ML'}


MAX_ABSTRACT_LEN = 1600


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


def get_recent_papers_for_author(author_name: str, max_results: int | None = None) -> List[Paper]:
    """Fetch recent papers for a given author from arXiv."""
    print(f"Fetching papers for {author_name}...")
    
    try:
        # import time
        # # Add a small delay to avoid rate limiting
        # time.sleep(0.5)
        
        client = arxiv.Client()
        search = arxiv.Search(
            query=f'au:"{author_name}"',
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order = arxiv.SortOrder.Descending
        )
        
        papers = []
        for result in client.results(search):
            # Filter by category - only include papers from allowed categories
            paper_categories = set(result.categories)
            if not paper_categories.intersection(CATEGORIES):
                continue  # Skip papers not in our allowed categories
            
            # Format the date without year
            pub_date = result.published.strftime("%b %d")
            
            # Get all authors
            authors_list = [author.name for author in result.authors]

            truncated_summary = result.summary[:MAX_ABSTRACT_LEN] + '...' if len(result.summary) > MAX_ABSTRACT_LEN else result.summary
            
            papers.append(Paper(
                title=result.title,
                authors=authors_list,
                summary=truncated_summary,
                published=pub_date,
                published_raw=result.published,
                pdf_url=result.pdf_url,
                arxiv_url=result.entry_id,
                queried_author=author_name,
                matching_authors=[author_name]
            ))
        
        return papers
    except Exception as e:
        raise RuntimeError(f"Error fetching papers for {author_name}: {e}")

def get_all_recent_papers(authors: List[str], max_per_author: int | None = None) -> List[Paper]:
    """Fetch recent papers for all authors."""
    all_papers = []
    
    for author in authors:
        papers = get_recent_papers_for_author(author, max_per_author)
        all_papers.extend(papers)
    
    # Sort by publication date (most recent first)
    all_papers.sort(key=lambda x: x.published_raw, reverse=True)
    
    # Remove duplicates (same paper might appear for multiple authors)
    # But merge the matching_authors lists
    seen_titles: Dict[str, int] = {}
    unique_papers: List[Paper] = []
    for paper in all_papers:
        if paper.title not in seen_titles:
            seen_titles[paper.title] = len(unique_papers)
            unique_papers.append(paper)
        else:
            # Paper already exists, add this queried author to matching_authors
            existing_idx = seen_titles[paper.title]
            if paper.queried_author not in unique_papers[existing_idx].matching_authors:
                unique_papers[existing_idx].matching_authors.append(paper.queried_author)
    
    return unique_papers


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

