# Quick Start Guide

Get your arXiv papers website up and running in 5 minutes!

## Option 1: GitHub Pages (Automatic Updates)

### Step 1: Initialize Repository

```bash
cd /Users/dhei/Downloads/thinking
./init-repo.sh
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Name your repository (e.g., `arxiv-papers`)
3. **DO NOT** initialize with README, .gitignore, or license
4. Click **Create repository**

### Step 3: Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Step 4: Enable GitHub Pages

1. Go to repository **Settings**
2. Click **Pages** in the left sidebar
3. Under **Source**, select **GitHub Actions**
4. Click **Save**

### Step 5: Enable Workflow Permissions

1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

### Step 6: Trigger First Build

1. Go to **Actions** tab
2. Click **Update arXiv Papers**
3. Click **Run workflow** → Select `main` → **Run workflow**

### Done! 🎉

Your site will be live in 2-3 minutes at:
```
https://YOUR_USERNAME.github.io/YOUR_REPO/
```

It will automatically update every day at 8 AM UTC!

---

## Option 2: Local Development Only

### Setup

```bash
cd /Users/dhei/Downloads/thinking

# Initialize environment
uvinit
source .venv/bin/activate
uv pip install requests arxiv

# Fetch papers
python fetch_papers.py
```

### Run Local Server

```bash
./test-local.sh
# Visit http://localhost:8000
```

### Update Papers

```bash
./update_papers.sh
```

---

## Quick Commands

| Task | Command |
|------|---------|
| Update papers locally | `./update_papers.sh` |
| Test website locally | `./test-local.sh` |
| Initialize repo | `./init-repo.sh` |
| Fetch papers manually | `python fetch_papers.py` |
| Open in browser | `open index.html` |

---

## Customization

### Change Update Time

Edit `.github/workflows/update-papers.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'  # Change this line
```

Examples:
- `'0 0 * * *'` - Midnight UTC
- `'0 */6 * * *'` - Every 6 hours
- `'0 8,20 * * *'` - 8 AM and 8 PM UTC

### Change Number of Papers

Edit `fetch_papers.py`:

```python
# Line 191: Papers per author
papers = get_all_recent_papers(authors, max_per_author=3)  # Change 3

# Line 194: Total papers
papers = papers[:100]  # Change 100

# Line 156: Initially visible
initial_papers = papers[:20]  # Change 20
```

### Use Different Author List

Edit `fetch_papers.py`, line 15:

```python
CONSTANTS_URL = 'https://your-url-here.com/constants.py'
```

---

## Troubleshooting

### "Permission denied" when running scripts

```bash
chmod +x init-repo.sh update_papers.sh test-local.sh
```

### Workflow fails on GitHub

1. Check you enabled "Read and write permissions" (Step 5)
2. View error in **Actions** tab
3. Make sure all files are committed

### Site not updating

1. Check **Actions** tab for errors
2. Manually trigger: **Actions** → **Update arXiv Papers** → **Run workflow**
3. Wait 2-3 minutes after workflow completes

### Infinite scroll not working

1. Make sure `papers.json` exists
2. Test locally with `./test-local.sh`
3. Check browser console for errors

---

## Next Steps

- **Customize**: Edit the HTML, CSS, or add your own features
- **Monitor**: Check the **Actions** tab to see daily updates
- **Share**: Give others the GitHub Pages URL
- **Extend**: Add filters, search, or RSS feeds

For detailed documentation, see:
- [README.md](README.md) - Full feature documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide

