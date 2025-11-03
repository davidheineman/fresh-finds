# arXiv Papers Aggregator

[![Update arXiv Papers](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/update-papers.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/update-papers.yml)

This website displays the most recent arXiv papers from researchers listed in the [ARXIV_RESEARCHERS list](https://github.com/davidheineman/conference-papers/blob/main/constants.py) in the conference-papers repository.

> **Live Demo**: Updates automatically every day at 8 AM UTC and deploys to GitHub Pages.

## Quick Links

- 🚀 **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in 5 minutes
- 📖 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detailed deployment guide
- 💻 **Local Testing**: Run `./test-local.sh`

## Features

- **Automatic Paper Fetching**: Queries arXiv for recent papers from 58 curated researchers
- **Infinite Scrolling**: Loads more papers automatically as you scroll down
- **Full Author Lists**: Shows all authors (up to 50) instead of truncating after 3
- **Highlighted Matches**: Matching authors from the researcher list are <u>underlined</u> so you can see who matched
- **Clean Design**: Beautiful, responsive layout matching the existing site design
- **Real-time Updates**: Easy one-command refresh to get the latest papers

## How it Works

The `fetch_papers.py` script:
1. Fetches the list of 58 researchers from the ARXIV_RESEARCHERS list in the GitHub repository
2. Queries arXiv for the most recent papers from each researcher (3 papers per author)
3. Identifies which author(s) from the list appear on each paper
4. Updates `index.html` with the 20 most recent papers initially visible
5. Shows all authors (up to 50) with matching researchers <u>underlined</u>
6. Saves all 100 papers to `papers.json` for infinite scrolling
7. JavaScript (`infinite-scroll.js`) loads more papers as you scroll with the same formatting

### Example

If a paper has authors: "John Smith, <u>Diyi Yang</u>, Jane Doe, <u>William Held</u>, Bob Jones"

The underlined names indicate that Diyi Yang and William Held are in the researcher list, so you can quickly identify which researchers you're tracking contributed to the paper.

## Setup

1. Initialize the uv virtual environment:
```bash
uvinit
```

2. Activate the environment and install dependencies:
```bash
source .venv/bin/activate
uv pip install requests arxiv
```

## Usage

To update the website with the latest papers:

```bash
source .venv/bin/activate
python fetch_papers.py
```

This will:
- Fetch the current list of 121 researchers from GitHub
- Query arXiv for their recent papers (3 papers per author)
- Display 20 papers initially, with 100 total papers available
- Enable infinite scrolling to load more papers as you scroll
- Save all data to `papers.json`

The process takes a few minutes since it queries arXiv for 120+ researchers.

## Files

- `fetch_papers.py` - Main script to fetch and update papers
- `update_papers.sh` - Convenient shell script to update everything
- `index.html` - Website homepage displaying the papers
- `papers.json` - JSON data of all fetched papers (100 papers)
- `js/infinite-scroll.js` - JavaScript for infinite scrolling functionality
- `js/script.min.*.js` - Original site JavaScript
- `css/` - Stylesheets for the website
- `fonts/` - Custom fonts used on the site

## Customization

You can modify the following in `fetch_papers.py`:

- `max_per_author` - Number of papers to fetch per author (currently 3)
- `papers[:100]` - Total number of papers to save (currently 100)
- `papers[:20]` - Number of papers initially visible (currently 20)
- Change the GitHub URL to fetch from a different author list

In `js/infinite-scroll.js`:
- `papersPerLoad` - Number of papers to load on each scroll (currently 10)
- `threshold` - Distance from bottom to trigger loading (currently 800px)

## Deployment to GitHub Pages

This website is configured to automatically deploy to GitHub Pages with daily updates at 8 AM UTC.

**Quick Setup:**

1. Create a GitHub repository and push this code
2. Enable GitHub Pages (Settings → Pages → Source: GitHub Actions)
3. Enable workflow permissions (Settings → Actions → General → Read and write permissions)
4. The site will update automatically every day!

**See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup instructions.**

Your site will be available at: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`

