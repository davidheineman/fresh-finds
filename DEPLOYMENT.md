# Deployment Guide

This guide explains how to deploy the arXiv Papers website to GitHub Pages with automatic daily updates.

## GitHub Pages Setup

### 1. Create a GitHub Repository

```bash
cd /Users/dhei/Downloads/thinking
git init
git add .
git commit -m "Initial commit: arXiv papers aggregator"
```

Create a new repository on GitHub, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 2. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages** (in the left sidebar)
3. Under **Source**, select **GitHub Actions**
4. Save the settings

### 3. Configure Repository Settings

The workflow needs write permissions:

1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

### 4. Trigger the First Build

The workflow will run:
- **Daily at 8 AM UTC** (automatic)
- **On push to main branch**
- **Manually via workflow dispatch**

To trigger manually:
1. Go to **Actions** tab
2. Click **Update arXiv Papers** workflow
3. Click **Run workflow**
4. Select `main` branch
5. Click **Run workflow**

### 5. Access Your Website

After the workflow completes (usually 2-3 minutes), your site will be available at:

```
https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/
```

## Local Testing

### First Time Setup

```bash
# Initialize UV environment
uvinit

# Activate environment
source .venv/bin/activate

# Install dependencies
uv pip install requests arxiv
```

### Update Papers Locally

```bash
# Run the update script
./update_papers.sh

# Or manually
source .venv/bin/activate
python fetch_papers.py
```

### Test Locally

```bash
# Open in browser
open index.html

# Or use a local server (better for testing)
python -m http.server 8000
# Then visit: http://localhost:8000
```

## How It Works

### Automatic Updates

The GitHub Actions workflow (`.github/workflows/update-papers.yml`):

1. **Runs at 8 AM UTC daily** using a cron schedule
2. Checks out the repository
3. Sets up Python 3.12 and UV
4. Installs dependencies (requests, arxiv)
5. Runs `fetch_papers.py` to get latest papers
6. Commits changes if papers were updated
7. Deploys to GitHub Pages

### Manual Updates

You can trigger updates anytime:

1. **Via GitHub Actions UI** (see step 4 above)
2. **By pushing to main branch**
3. **Locally and push** (see Local Testing)

## Customization

### Change Update Schedule

Edit `.github/workflows/update-papers.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'  # Daily at 8 AM UTC
```

Cron examples:
- `'0 */6 * * *'` - Every 6 hours
- `'0 0 * * *'` - Daily at midnight UTC
- `'0 8 * * 1'` - Every Monday at 8 AM UTC
- `'0 8,20 * * *'` - Daily at 8 AM and 8 PM UTC

[Use crontab.guru to create schedules](https://crontab.guru/)

### Change Number of Papers

Edit `fetch_papers.py`:

```python
# Line 191: Papers per author
papers = get_all_recent_papers(authors, max_per_author=3)

# Line 194: Total papers to save
papers = papers[:100]

# Line 156: Initial papers visible
initial_papers = papers[:20]
```

### Change Researchers List

The workflow automatically fetches from the GitHub repository:
https://github.com/davidheineman/conference-papers/blob/main/constants.py

To use a different list, edit `CONSTANTS_URL` in `fetch_papers.py`.

## Troubleshooting

### Workflow Fails

1. Check **Actions** tab for error messages
2. Verify workflow permissions (see step 3 above)
3. Check if the constants.py URL is accessible

### Papers Not Updating

1. Check if workflow ran successfully in **Actions** tab
2. View workflow logs for errors
3. Verify arXiv API is accessible (sometimes rate-limited)

### Site Not Loading

1. Verify GitHub Pages is enabled (step 2)
2. Check repository name matches the URL
3. Wait 2-3 minutes after workflow completes
4. Check browser console for errors

### Infinite Scroll Not Working

1. Check browser console for errors
2. Verify `papers.json` exists and is accessible
3. Clear browser cache and reload

## Files Structure

```
.
├── .github/
│   └── workflows/
│       └── update-papers.yml    # GitHub Actions workflow
├── css/                          # Stylesheets
├── fonts/                        # Custom fonts
├── js/
│   ├── infinite-scroll.js       # Infinite scroll functionality
│   └── script.min.*.js          # Original site scripts
├── fetch_papers.py              # Main paper fetching script
├── update_papers.sh             # Local update convenience script
├── index.html                   # Website homepage
├── papers.json                  # Fetched papers data (auto-generated)
├── README.md                    # Main documentation
├── DEPLOYMENT.md                # This file
└── .gitignore                   # Git ignore patterns
```

## Cost

GitHub Pages and GitHub Actions are **free** for public repositories with generous limits:
- 2,000 Action minutes/month
- Unlimited GitHub Pages bandwidth
- The workflow uses ~2-3 minutes per run

With daily updates: 30 runs × 3 minutes = 90 minutes/month (well within limits)

## Security

The workflow:
- Uses official GitHub Actions (`actions/*`, `astral-sh/setup-uv`)
- Only reads from public URLs (arXiv, GitHub)
- Only writes to the repository (papers data)
- No secrets or API keys needed

## Support

For issues or questions:
1. Check the GitHub Actions logs
2. Review this documentation
3. Check arXiv API status: https://info.arxiv.org/help/api/index.html

