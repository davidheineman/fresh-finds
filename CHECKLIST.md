# Deployment Checklist

Use this checklist to ensure everything is set up correctly.

## ✅ Pre-Deployment Checklist

### Local Setup
- [ ] Run `./init-repo.sh` to initialize the repository
- [ ] Test locally with `./test-local.sh` - verify site loads at http://localhost:8000
- [ ] Check that `papers.json` exists and has data
- [ ] Verify `index.html` shows papers with underlined author names
- [ ] Test infinite scroll by scrolling down the page

### GitHub Repository
- [ ] Create repository on GitHub
- [ ] Add remote: `git remote add origin https://github.com/USERNAME/REPO.git`
- [ ] Push to GitHub: `git push -u origin main`
- [ ] Update README.md badge URLs with your username/repo name

### GitHub Settings
- [ ] Enable GitHub Pages (Settings → Pages → GitHub Actions)
- [ ] Enable workflow permissions (Settings → Actions → General → Read and write permissions)
- [ ] Check "Allow GitHub Actions to create and approve pull requests"

### First Deploy
- [ ] Go to Actions tab
- [ ] Run "Update arXiv Papers" workflow manually
- [ ] Wait for workflow to complete (green checkmark)
- [ ] Visit your GitHub Pages URL: `https://USERNAME.github.io/REPO/`

## ✅ Post-Deployment Verification

### Website Checks
- [ ] Site loads without errors
- [ ] Papers are displayed
- [ ] Tracked authors are underlined
- [ ] Infinite scroll works (scroll down to load more)
- [ ] Links to arXiv papers work
- [ ] Mobile responsive (test on phone/narrow browser)

### Automation Checks
- [ ] Workflow shows in Actions tab
- [ ] Scheduled for daily runs at 8 AM UTC
- [ ] Manual trigger works (workflow_dispatch)
- [ ] Papers update after running workflow

## ✅ Maintenance Checklist (Weekly)

- [ ] Check Actions tab for failed workflows
- [ ] Verify papers are updating daily
- [ ] Review paper count (should have ~100 papers)
- [ ] Check for any GitHub notifications

## ✅ Customization Checklist (Optional)

### Change Update Schedule
- [ ] Edit `.github/workflows/update-papers.yml` line 6
- [ ] Test with manual workflow trigger
- [ ] Commit and push changes

### Change Paper Count
- [ ] Edit `fetch_papers.py` lines 191, 194, 156
- [ ] Test locally with `./update_papers.sh`
- [ ] Commit and push changes

### Change Author List
- [ ] Update `CONSTANTS_URL` in `fetch_papers.py`
- [ ] Test locally first
- [ ] Commit and push changes

## 🐛 Troubleshooting Checklist

### Site Not Loading
- [ ] Check GitHub Pages is enabled
- [ ] Verify workflow completed successfully
- [ ] Wait 2-3 minutes after deployment
- [ ] Check browser console for errors
- [ ] Try hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

### Workflow Failing
- [ ] Check Actions tab for error message
- [ ] Verify workflow permissions are enabled
- [ ] Check if arXiv API is accessible
- [ ] Review recent commits for syntax errors

### Papers Not Updating
- [ ] Check workflow ran (Actions tab)
- [ ] Verify workflow completed successfully
- [ ] Check if `papers.json` was updated (commit history)
- [ ] Manually trigger workflow to test

### Infinite Scroll Not Working
- [ ] Check browser console for JavaScript errors
- [ ] Verify `papers.json` exists and is accessible
- [ ] Test locally with `./test-local.sh`
- [ ] Clear browser cache

## 📊 Success Criteria

Your deployment is successful when:

✅ Website loads at GitHub Pages URL
✅ Papers are visible and formatted correctly
✅ Tracked authors are underlined
✅ Infinite scroll loads more papers
✅ Links to arXiv work
✅ Workflow runs daily at 8 AM UTC
✅ Papers update automatically
✅ No errors in Actions tab

## 🎉 You're Done!

If all checkboxes above are checked, your arXiv paper aggregator is fully deployed and will update automatically every day!

### Next Steps:
1. Share your GitHub Pages URL with others
2. Star the repository to track it
3. Watch the Actions tab to see daily updates
4. Customize as needed

### Getting Help:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions
- Review [QUICKSTART.md](QUICKSTART.md) for quick setup
- See [README.md](README.md) for full documentation
- Check GitHub Actions logs for error details

