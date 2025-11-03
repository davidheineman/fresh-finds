#!/bin/bash
# Initialize the repository for GitHub Pages deployment

set -e

echo "🚀 Initializing arXiv Papers Repository"
echo "========================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
else
    echo "✓ Git repository already initialized"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
.venv/
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.bak
EOF
else
    echo "✓ .gitignore already exists"
fi

# Setup Python environment
echo ""
echo "🐍 Setting up Python environment..."
if [ ! -d ".venv" ]; then
    uvinit
    source .venv/bin/activate
    uv pip install requests arxiv
    echo "✓ Python environment created"
else
    echo "✓ Python environment already exists"
fi

# Add all files
echo ""
echo "📁 Adding files to git..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "✓ No changes to commit"
else
    echo "💾 Creating initial commit..."
    git commit -m "Initial commit: arXiv papers aggregator"
fi

echo ""
echo "✅ Repository initialized!"
echo ""
echo "Next steps:"
echo "1. Create a repository on GitHub"
echo "2. Run: git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo "3. Run: git branch -M main"
echo "4. Run: git push -u origin main"
echo "5. Enable GitHub Pages (Settings → Pages → GitHub Actions)"
echo "6. Enable workflow permissions (Settings → Actions → General)"
echo ""
echo "See DEPLOYMENT.md for detailed instructions!"

