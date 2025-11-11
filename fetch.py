import requests
import arxiv
import json
from typing import List, Dict
import re

RESEARCHERS_URL = 'https://raw.githubusercontent.com/davidheineman/conference-papers/main/constants.py'

def fetch_authors_from_github() -> List[str]:
    """Fetch the authors list from the GitHub repository."""
    response = requests.get(RESEARCHERS_URL)
    if response.status_code != 200:
        print(f"Failed to fetch constants.py: {response.status_code}")
        return []
    
    content = response.text
    
    # The file has an ARXIV_RESEARCHERS list with quoted author names
    authors = []
    
    # Look for ARXIV_RESEARCHERS = [ ... ]
    if 'ARXIV_RESEARCHERS' in content:
        # Find the start of the list
        start_idx = content.find('ARXIV_RESEARCHERS')
        if start_idx != -1:
            # Find the opening bracket
            bracket_idx = content.find('[', start_idx)
            if bracket_idx != -1:
                # Extract everything until the closing bracket
                # Count brackets to handle nested structures
                bracket_count = 1
                end_idx = bracket_idx + 1
                while end_idx < len(content) and bracket_count > 0:
                    if content[end_idx] == '[':
                        bracket_count += 1
                    elif content[end_idx] == ']':
                        bracket_count -= 1
                    end_idx += 1
                
                # Extract the list content
                list_content = content[bracket_idx:end_idx]
                
                # Find all quoted strings (author names)
                # Match both single and double quotes
                pattern = r'["\']([^"\']+)["\']'
                authors = re.findall(pattern, list_content)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_authors = []
    for author in authors:
        # Skip empty strings
        if author.strip() and author not in seen:
            seen.add(author)
            unique_authors.append(author.strip())
    
    return unique_authors

def get_recent_papers_for_author(author_name: str, max_results: int | None = None) -> List[Dict]:
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
            # Format the date without year
            pub_date = result.published.strftime("%b %d")
            
            # Get all authors
            authors_list = [author.name for author in result.authors]
            
            papers.append({
                'title': result.title,
                'authors': authors_list,
                'summary': result.summary[:300] + '...' if len(result.summary) > 300 else result.summary,
                'published': pub_date,
                'published_raw': result.published,
                'pdf_url': result.pdf_url,
                'arxiv_url': result.entry_id,
                'queried_author': author_name,
                'matching_authors': [author_name]  # Track which author(s) matched
            })
        
        return papers
    except Exception as e:
        raise RuntimeError(f"Error fetching papers for {author_name}: {e}")

def get_all_recent_papers(authors: List[str], max_per_author: int | None = None) -> List[Dict]:
    """Fetch recent papers for all authors."""
    all_papers = []
    
    for author in authors:
        papers = get_recent_papers_for_author(author, max_per_author)
        all_papers.extend(papers)
    
    # Sort by publication date (most recent first)
    all_papers.sort(key=lambda x: x['published_raw'], reverse=True)
    
    # Remove duplicates (same paper might appear for multiple authors)
    # But merge the matching_authors lists
    seen_titles = {}
    unique_papers = []
    for paper in all_papers:
        if paper['title'] not in seen_titles:
            seen_titles[paper['title']] = len(unique_papers)
            unique_papers.append(paper)
        else:
            # Paper already exists, add this queried author to matching_authors
            existing_idx = seen_titles[paper['title']]
            if paper['queried_author'] not in unique_papers[existing_idx]['matching_authors']:
                unique_papers[existing_idx]['matching_authors'].append(paper['queried_author'])
    
    return unique_papers


def main():
    print(f"Fetching authors from {RESEARCHERS_URL}...")
    authors = fetch_authors_from_github()
    
    if not authors:
        raise RuntimeError("No authors found.")

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
        # Remove published_raw for JSON serialization
        papers_for_json = []
        for p in papers:
            paper_copy = {k: v for k, v in p.items() if k != 'published_raw'}
            # Keep matching_authors for JavaScript to use
            papers_for_json.append(paper_copy)
        json.dump(papers_for_json, f, indent=2)
        print(f"\nDone! Saved {len(papers)} papers to papers.json")

if __name__ == '__main__':
    main()

