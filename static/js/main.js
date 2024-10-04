document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadForm = document.getElementById('upload-form');
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    let searchTimeout;

    if (fileInput && fileNameDisplay) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                fileNameDisplay.textContent = e.target.files[0].name;
            } else {
                fileNameDisplay.textContent = 'No file chosen';
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('file');
            if (fileInput.files.length === 0) {
                e.preventDefault();
                alert('Please select a file to upload.');
            }
        });
    }

    if (searchInput && searchForm) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.trim() === '') {
                    window.location.href = '/dashboard';
                } else {
                    searchForm.submit();
                }
            }, 300);
        });
    }

    const deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this file?')) {
                e.preventDefault();
            }
        });
    });
});
