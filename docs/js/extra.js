// Custom JavaScript for Smart Pandoc Debugger documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add any custom JavaScript here
    console.log('Smart Pandoc Debugger documentation loaded');
    
    // Example: Add copy buttons to code blocks
    document.querySelectorAll('pre > code').forEach(function(codeBlock) {
        // Only add button if not already present
        if (!codeBlock.parentNode.querySelector('.copy-button')) {
            const button = document.createElement('button');
            button.className = 'copy-button';
            button.type = 'button';
            button.innerText = 'Copy';
            button.title = 'Copy to clipboard';
            
            button.addEventListener('click', function() {
                navigator.clipboard.writeText(codeBlock.textContent).then(
                    function() {
                        button.innerText = 'Copied!';
                        setTimeout(function() {
                            button.innerText = 'Copy';
                        }, 2000);
                    },
                    function() {
                        button.innerText = 'Failed';
                    }
                );
            });
            
            const div = document.createElement('div');
            div.className = 'code-block-header';
            div.appendChild(button);
            codeBlock.parentNode.insertBefore(div, codeBlock);
        }
    });
});
