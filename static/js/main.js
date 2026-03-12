// Main JavaScript file for EchoNotes

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Character counter for textareas
    var textareas = document.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(function(textarea) {
        var maxLength = textarea.getAttribute('data-max-length');
        var counter = document.createElement('small');
        counter.className = 'form-text text-muted float-end';
        counter.innerHTML = '0/' + maxLength;
        
        textarea.parentNode.appendChild(counter);
        
        textarea.addEventListener('input', function() {
            var length = this.value.length;
            counter.innerHTML = length + '/' + maxLength;
            
            if (length > maxLength) {
                counter.classList.add('text-danger');
            } else {
                counter.classList.remove('text-danger');
            }
        });
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Confirm delete actions
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm') || 'Are you sure?')) {
                e.preventDefault();
            }
        });
    });
    
    // Like button functionality (AJAX)
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            var postId = this.dataset.postId;
            var url = this.dataset.url || '/post/' + postId + '/like/';
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.liked) {
                    this.classList.remove('btn-outline-danger');
                    this.classList.add('btn-danger');
                } else {
                    this.classList.remove('btn-danger');
                    this.classList.add('btn-outline-danger');
                }
                
                var likeCount = this.querySelector('.like-count');
                if (likeCount) {
                    likeCount.textContent = data.total_likes;
                }
                
                // Show toast notification
                showToast(data.message, data.liked ? 'success' : 'info');
            })
            .catch(error => console.error('Error:', error));
        });
    });
    
    // Search form validation
    var searchForm = document.querySelector('form[action*="search"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            var searchInput = this.querySelector('input[name="q"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                showToast('Please enter a search term', 'warning');
            }
        });
    }
    
    // Infinite scroll for posts (if implemented)
    var infiniteScroll = document.querySelector('[data-infinite-scroll]');
    if (infiniteScroll) {
        var page = 2;
        var loading = false;
        var endMessage = document.querySelector('[data-end-message]');
        
        window.addEventListener('scroll', function() {
            if (loading) return;
            
            var scrollPosition = window.innerHeight + window.scrollY;
            var documentHeight = document.documentElement.scrollHeight;
            
            if (scrollPosition >= documentHeight - 1000) {
                loadMorePosts();
            }
        });
        
        function loadMorePosts() {
            loading = true;
            
            fetch('/api/posts/?page=' + page)
                .then(response => response.json())
                .then(data => {
                    if (data.posts.length > 0) {
                        appendPosts(data.posts);
                        page++;
                        loading = false;
                    } else {
                        if (endMessage) {
                            endMessage.style.display = 'block';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    loading = false;
                });
        }
        
        function appendPosts(posts) {
            var container = document.querySelector('[data-posts-container]');
            posts.forEach(post => {
                // Create and append post HTML
                var postElement = createPostElement(post);
                container.appendChild(postElement);
            });
        }
    }
});

// Helper function to get CSRF token
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toast notification function
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    var toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    var toastId = 'toast-' + Date.now();
    var toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">EchoNotes</strong>
                <small>just now</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Initialize and show toast
    var toastElement = document.getElementById(toastId);
    var toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Form validation
function validateForm(formElement) {
    var inputs = formElement.querySelectorAll('input[required], textarea[required], select[required]');
    var isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
        
        // Email validation
        if (input.type === 'email' && input.value) {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value)) {
                input.classList.add('is-invalid');
                isValid = false;
            }
        }
        
        // Password confirmation
        if (input.id === 'password2') {
            var password1 = document.getElementById('password1');
            if (password1 && input.value !== password1.value) {
                input.classList.add('is-invalid');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

// Preview post before publishing
function previewPost(title, content) {
    var modal = document.getElementById('previewModal');
    if (!modal) {
        // Create modal if it doesn't exist
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'previewModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Post Preview</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <h4 id="previewTitle"></h4>
                        <hr>
                        <div id="previewContent"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    document.getElementById('previewTitle').textContent = title;
    document.getElementById('previewContent').innerHTML = content.replace(/\n/g, '<br>');
    
    var previewModal = new bootstrap.Modal(modal);
    previewModal.show();
}

// Share post on social media
function sharePost(title, url) {
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url
        }).catch(console.error);
    } else {
        // Fallback - copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
            showToast('Link copied to clipboard!', 'success');
        }).catch(() => {
            showToast('Failed to copy link', 'error');
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add preview button to post forms
    var postForm = document.querySelector('form[action*="create"]');
    if (postForm) {
        var previewBtn = document.createElement('button');
        previewBtn.type = 'button';
        previewBtn.className = 'btn btn-info me-2';
        previewBtn.innerHTML = '<i class="fas fa-eye"></i> Preview';
        previewBtn.onclick = function() {
            var title = document.getElementById('id_title').value;
            var content = document.getElementById('id_content').value;
            if (title && content) {
                previewPost(title, content);
            } else {
                showToast('Please fill in both title and content', 'warning');
            }
        };
        
        var submitBtn = postForm.querySelector('button[type="submit"]');
        submitBtn.parentNode.insertBefore(previewBtn, submitBtn);
    }
    
    // Add share buttons to posts
    document.querySelectorAll('.share-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            var title = this.dataset.title;
            var url = this.dataset.url;
            sharePost(title, url);
        });
    });
});