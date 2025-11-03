// Infinite scroll functionality for arXiv papers
(function() {
    let allPapers = [];
    let currentIndex = 20; // First 20 papers are already loaded
    const papersPerLoad = 10;
    let isLoading = false;
    let hasMorePapers = true;

    // Load all papers from JSON
    async function loadPapersData() {
        try {
            // Try both relative and absolute paths for local file support
            let response = await fetch('papers.json');
            if (!response.ok) {
                response = await fetch('/papers.json');
            }
            if (!response.ok) {
                console.error('Failed to load papers.json');
                return;
            }
            allPapers = await response.json();
            hasMorePapers = currentIndex < allPapers.length;
            console.log(`Loaded ${allPapers.length} papers for infinite scroll`);
        } catch (error) {
            console.error('Error loading papers:', error);
        }
    }

    // Generate HTML for a single paper
    function generatePaperHTML(paper) {
        // Format authors - show up to 50, then et al.
        const matchingAuthors = new Set(paper.matching_authors || []);
        const authorParts = [];
        
        for (let i = 0; i < paper.authors.length && i < 50; i++) {
            const author = paper.authors[i];
            // Underline if this author is in the matching list
            if (matchingAuthors.has(author)) {
                authorParts.push(`<u>${author}</u>`);
            } else {
                authorParts.push(author);
            }
        }
        
        if (paper.authors.length > 50) {
            authorParts.push('et al.');
        }
        
        const authorsDisplay = authorParts.join(', ');

        return `
          <li> <a class="post-item-link" href="${paper.arxiv_url}" target="_blank"> <time
                class="desktop-time">${paper.published}</time>
              <div class="post-info">
                <div class="post-title">${paper.title}</div>
                <div class="author-date"> ${authorsDisplay}<span class="mobile-date-separator"> <span
                      class="separator">·</span> ${paper.published}</span> </div>
              </div>
            </a> </li>`;
    }

    // Load more papers
    function loadMorePapers() {
        if (isLoading || !hasMorePapers) return;

        isLoading = true;

        const postList = document.querySelector('.post-group ul');
        if (!postList) {
            console.error('Post list not found');
            isLoading = false;
            return;
        }

        // Get next batch of papers
        const endIndex = Math.min(currentIndex + papersPerLoad, allPapers.length);
        const papersToAdd = allPapers.slice(currentIndex, endIndex);

        // Add papers to the list
        papersToAdd.forEach(paper => {
            const li = document.createElement('li');
            li.innerHTML = generatePaperHTML(paper).trim();
            postList.appendChild(li.firstChild);
        });

        currentIndex = endIndex;
        hasMorePapers = currentIndex < allPapers.length;
        isLoading = false;

        if (!hasMorePapers) {
            console.log('All papers loaded');
        }
    }

    // Check if user has scrolled near bottom
    function checkScroll() {
        if (isLoading || !hasMorePapers) return;

        const scrollPosition = window.innerHeight + window.scrollY;
        const threshold = document.documentElement.scrollHeight - 800;

        if (scrollPosition >= threshold) {
            loadMorePapers();
        }
    }

    // Initialize
    async function init() {
        await loadPapersData();
        
        // Add scroll listener with throttle
        let ticking = false;
        window.addEventListener('scroll', function() {
            if (!ticking) {
                window.requestAnimationFrame(function() {
                    checkScroll();
                    ticking = false;
                });
                ticking = true;
            }
        });

        // Initial check in case content doesn't fill the page
        setTimeout(checkScroll, 100);
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

