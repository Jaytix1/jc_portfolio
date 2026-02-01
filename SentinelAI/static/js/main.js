// Configure marked for markdown rendering
marked.setOptions({
    highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
    },
    breaks: true
});

async function submitReview() {
    const codeInput = document.getElementById('code-input');
    const languageSelect = document.getElementById('language');
    const reviewOutput = document.getElementById('review-output');
    const reviewBtn = document.getElementById('review-btn');
    const btnText = reviewBtn.querySelector('.btn-text');
    const btnLoader = reviewBtn.querySelector('.btn-loader');

    const code = codeInput.value.trim();

    if (!code) {
        reviewOutput.innerHTML = '<p class="error-message">Please enter some code to review.</p>';
        return;
    }

    // Show loading state
    reviewBtn.disabled = true;
    btnText.textContent = 'Analyzing...';
    btnLoader.classList.remove('hidden');
    reviewOutput.innerHTML = '<p class="placeholder-text">Analyzing your code...</p>';

    try {
        const response = await fetch('/review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                language: languageSelect.value
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Render markdown response
            reviewOutput.innerHTML = marked.parse(data.review);
            // Apply syntax highlighting to code blocks
            reviewOutput.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        } else {
            reviewOutput.innerHTML = `<p class="error-message">${data.error || 'An error occurred'}</p>`;
        }
    } catch (error) {
        reviewOutput.innerHTML = `<p class="error-message">Failed to connect to the server. Please try again.</p>`;
        console.error('Error:', error);
    } finally {
        // Reset button state
        reviewBtn.disabled = false;
        btnText.textContent = 'Review Code';
        btnLoader.classList.add('hidden');
    }
}

// Allow Ctrl+Enter to submit
document.getElementById('code-input').addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        submitReview();
    }
});
