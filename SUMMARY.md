# Project Summary

## What This Is

An automated arXiv paper aggregator that:
- Tracks 58 researchers from a curated list
- Fetches their latest papers from arXiv daily
- Displays them on a beautiful, responsive website
- Updates automatically via GitHub Actions
- Deploys to GitHub Pages

## Key Features

✅ **Automatic Updates** - Runs every day at 8 AM UTC
✅ **Infinite Scroll** - Loads papers as you scroll
✅ **Smart Highlighting** - Underlines tracked researchers
✅ **Full Author Lists** - Shows up to 50 authors per paper
✅ **Works Everywhere** - Local testing + GitHub Pages

## File Structure

```
📁 Project Root
├── 🤖 .github/workflows/update-papers.yml  # Daily automation
├── 🎨 css/                                 # Stylesheets
├── 🔤 fonts/                               # Custom fonts
├── 📜 js/
│   ├── infinite-scroll.js                  # Scroll functionality
│   └── script.min.js                       # Site scripts
├── 🐍 fetch_papers.py                      # Main fetcher
├── 🌐 index.html                           # Website
├── 📊 papers.json                          # Paper data (auto-gen)
├── 🚀 init-repo.sh                         # Setup script
├── 🧪 test-local.sh                        # Test server
├── 🔄 update_papers.sh                     # Manual update
├── 📖 README.md                            # Full docs
├── 📘 QUICKSTART.md                        # 5-min guide
├── 📗 DEPLOYMENT.md                        # Deploy guide
└── 🙈 .gitignore                           # Git ignore

```

## How It Works

### Daily Workflow (Automated)

```
8:00 AM UTC
    ↓
GitHub Actions Triggers
    ↓
Fetch 58 Researchers List
    ↓
Query arXiv (3 papers/author)
    ↓
Process & Format (100 papers)
    ↓
Update index.html & papers.json
    ↓
Commit Changes
    ↓
Deploy to GitHub Pages
    ↓
Website Updated! 🎉
```

### Local Development

```
./update_papers.sh
    ↓
Activate venv
    ↓
Run fetch_papers.py
    ↓
Update HTML & JSON
    ↓
Test with ./test-local.sh
```

## Quick Commands

```bash
# Setup
./init-repo.sh              # Initialize everything

# Development
./update_papers.sh          # Fetch latest papers
./test-local.sh             # Test locally (port 8000)
open index.html             # Quick preview

# Deployment
git add .
git commit -m "Update"
git push                    # Triggers deploy
```

## Configuration

### Update Schedule
`.github/workflows/update-papers.yml:6`
```yaml
cron: '0 8 * * *'  # Daily at 8 AM UTC
```

### Papers Count
`fetch_papers.py:191-194`
```python
max_per_author=3    # Papers per author
papers[:100]        # Total papers
papers[:20]         # Initially visible
```

### Author Source
`fetch_papers.py:15`
```python
CONSTANTS_URL = 'https://...'  # Author list URL
```

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python 3.12
- **Package Manager**: uv (fast Python package installer)
- **Dependencies**: requests, arxiv
- **Automation**: GitHub Actions
- **Hosting**: GitHub Pages
- **Cost**: FREE! 🎉

## Links

- **Setup Guide**: [QUICKSTART.md](QUICKSTART.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Main Docs**: [README.md](README.md)
- **Author List**: [GitHub](https://github.com/davidheineman/conference-papers/blob/main/constants.py)
- **arXiv API**: [Documentation](https://info.arxiv.org/help/api/index.html)

## Support & Maintenance

**Issue?** Check the docs above or GitHub Actions logs

**Want to customize?** All code is well-commented and modular

**Need help?** Create an issue on GitHub

---

Built with ❤️ for the research community
