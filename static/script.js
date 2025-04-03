document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for form submissions
    const uploadForm = document.getElementById('upload-form');
    const createFolderForm = document.getElementById('create-folder-form');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const fileInput = document.querySelector('input[name="files"]');
            if (fileInput.files.length === 0) {
                alert('Please select at least one file to upload.');
                return;
            }

            const progressContainer = uploadForm.querySelector('.upload-progress');
            const progressBarFill = uploadForm.querySelector('.progress-bar-fill');
            const progressText = uploadForm.querySelector('.progress-text');
            
            // Show progress bar
            progressContainer.style.display = 'block';
            
            // Create FormData object
            const formData = new FormData(uploadForm);
            
            // Create and configure XMLHttpRequest
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressBarFill.style.width = percentComplete + '%';
                    progressText.textContent = Math.round(percentComplete) + '%';
                }
            });
            
            xhr.addEventListener('load', function() {
                if (xhr.status === 200) {
                    // Reload the page to show new files
                    window.location.reload();
                } else {
                    alert('Upload failed: ' + xhr.statusText);
                    progressContainer.style.display = 'none';
                }
            });
            
            xhr.addEventListener('error', function() {
                alert('Upload failed. Please try again.');
                progressContainer.style.display = 'none';
            });
            
            // Send the request
            xhr.open('POST', uploadForm.action, true);
            xhr.send(formData);
        });
    }
    
    if (createFolderForm) {
        createFolderForm.addEventListener('submit', function(e) {
            const folderNameInput = document.querySelector('input[name="folder_name"]');
            if (!folderNameInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a folder name.');
            }
        });
    }
    
    // Add file size formatter for display
    const fileSizeCells = document.querySelectorAll('.file-size');
    fileSizeCells.forEach(cell => {
        const size = parseInt(cell.getAttribute('data-size'));
        if (!isNaN(size)) {
            cell.textContent = formatFileSize(size);
        }
    });

    // Get the theme toggle button
    const themeToggle = document.getElementById('theme-toggle');

    // Check for saved theme preference or system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }

    // Theme toggle handler
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // Watch for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem('theme')) {
                document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            }
        });
    }
});

// Format file size in human-readable format
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(1)) + ' ' + units[i];
} 