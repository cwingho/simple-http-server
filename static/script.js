document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for form submissions
    const uploadForm = document.getElementById('upload-form');
    const createFolderForm = document.getElementById('create-folder-form');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = document.querySelector('input[name="files"]');
            if (fileInput.files.length === 0) {
                e.preventDefault();
                alert('Please select at least one file to upload.');
            }
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
});

// Format file size in human-readable format
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(1)) + ' ' + units[i];
} 