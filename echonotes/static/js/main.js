/* ============================================================
   EchoNotes — Enhanced Interactions
   Features: Reading progress, scroll reveal, word count,
   character counter, live search, typing indicator, reactions
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

    // ── 1. Reading Progress Bar ──────────────────────────────
    const postContent = document.querySelector('.post-content');
    if (postContent) {
        const bar = document.createElement('div');
        bar.id = 'reading-progress';
        bar.style.width = '0%';
        document.body.prepend(bar);

        window.addEventListener('scroll', () => {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
            bar.style.width = Math.min(progress, 100) + '%';
        }, { passive: true });
    }


    // ── 2. Scroll Reveal ─────────────────────────────────────
    const revealEls = document.querySelectorAll('.card, .post-card, .contest-card, .stats-card');
    revealEls.forEach(el => el.classList.add('reveal'));

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                setTimeout(() => entry.target.classList.add('visible'), i * 60);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));


    // ── 3. Live Word Count & Reading Time ────────────────────
    const contentField = document.getElementById('post-content') || document.getElementById('entry-content');
    const wordCountEl = document.getElementById('word-count');

    function updateWordCount() {
        if (!contentField || !wordCountEl) return;
        const text = contentField.value.trim();
        const words = text ? text.split(/\s+/).filter(w => w).length : 0;
        const chars = text.length;
        const minutes = Math.max(1, Math.ceil(words / 200));
        wordCountEl.innerHTML = `<span class="font-mono">${words}</span> words &nbsp;·&nbsp; <span class="font-mono">${chars}</span> chars &nbsp;·&nbsp; <span class="font-mono">${minutes}</span> min read`;
    }

    if (contentField) {
        contentField.addEventListener('input', updateWordCount);
        updateWordCount();
    }


    // ── 4. Auto-resize Textareas ─────────────────────────────
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.style.resize = 'vertical';
        textarea.addEventListener('input', function () {
            if (this.scrollHeight > this.offsetHeight + 10) {
                this.style.minHeight = this.scrollHeight + 'px';
            }
        });
    });


    // ── 5. Bootstrap Tooltips ────────────────────────────────
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });


    // ── 6. Auto-dismiss Alerts ───────────────────────────────
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            try { bootstrap.Alert.getOrCreateInstance(alert).close(); } catch (e) {}
        });
    }, 5000);


    // ── 7. Confirm Delete ────────────────────────────────────
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function (e) {
            if (!confirm(this.getAttribute('data-confirm') || 'Are you sure?')) {
                e.preventDefault();
            }
        });
    });


    // ── 8. Smooth Scroll ─────────────────────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });


    // ── 9. Toast Notification System ─────────────────────────
    window.showToast = function (message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const icons = { success: 'fa-check-circle', danger: 'fa-times-circle', warning: 'fa-exclamation-circle', info: 'fa-info-circle' };
        const colors = { success: '#2d6a4f', danger: '#c8472b', warning: '#d4a843', info: '#2c6fad' };

        const id = 'toast-' + Date.now();
        container.insertAdjacentHTML('beforeend', `
            <div id="${id}" class="toast align-items-center border-0" role="alert" style="background:white;border-left:4px solid ${colors[type] || colors.info} !important;border-radius:3px;box-shadow:0 4px 20px rgba(0,0,0,0.15)">
                <div class="d-flex align-items-center p-3">
                    <i class="fas ${icons[type] || icons.info} me-2" style="color:${colors[type] || colors.info}"></i>
                    <div class="me-auto" style="font-size:0.875rem;color:#1a1a2e">${message}</div>
                    <button type="button" class="btn-close ms-3" data-bs-dismiss="toast" style="font-size:0.7rem"></button>
                </div>
            </div>
        `);

        const toastEl = document.getElementById(id);
        const toast = new bootstrap.Toast(toastEl, { delay: 3500 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    };


    // ── 10. AJAX Like Button ─────────────────────────────────
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const postId = this.dataset.postId;

            fetch(`/post/${postId}/like/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(r => r.json())
            .then(data => {
                const liked = data.liked;
                this.classList.toggle('btn-outline-danger', !liked);
                this.classList.toggle('btn-danger', liked);
                const count = this.querySelector('.like-count');
                if (count) count.textContent = data.total_likes;

                // Heart bounce animation
                const icon = this.querySelector('i');
                if (icon) {
                    icon.style.transform = 'scale(1.5)';
                    setTimeout(() => icon.style.transform = '', 300);
                }

                showToast(liked ? '❤️ Added to your likes!' : 'Like removed', liked ? 'success' : 'info');
            })
            .catch(() => showToast('Something went wrong', 'danger'));
        });
    });


    // ── 11. AJAX Bookmark Button ─────────────────────────────
    document.querySelectorAll('.bookmark-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const postId = this.dataset.postId;

            fetch(`/post/${postId}/bookmark/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(r => r.json())
            .then(data => {
                const saved = data.bookmarked;
                this.classList.toggle('btn-outline-warning', !saved);
                this.classList.toggle('btn-warning', saved);
                this.innerHTML = `<i class="fas fa-bookmark"></i> ${saved ? 'Saved' : 'Save'}`;
                showToast(saved ? '🔖 Post saved to bookmarks!' : 'Bookmark removed', saved ? 'success' : 'info');
            })
            .catch(() => showToast('Something went wrong', 'danger'));
        });
    });


    // ── 12. Copy Link to Clipboard ───────────────────────────
    document.querySelectorAll('.copy-link-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const url = this.dataset.url || window.location.href;
            navigator.clipboard.writeText(url)
                .then(() => showToast('🔗 Link copied to clipboard!', 'success'))
                .catch(() => showToast('Could not copy link', 'danger'));
        });
    });


    // ── 13. Post Preview (create/edit) ───────────────────────
    const previewBtn = document.getElementById('preview-btn');
    if (previewBtn) {
        previewBtn.addEventListener('click', function () {
            const title = document.getElementById('id_title')?.value;
            const content = document.getElementById('post-content')?.value;
            if (!title || !content) {
                showToast('Please fill in both title and content first', 'warning');
                return;
            }
            openPreviewModal(title, content);
        });
    }

    function openPreviewModal(title, content) {
        let modal = document.getElementById('previewModal');
        if (!modal) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="modal fade" id="previewModal" tabindex="-1">
                    <div class="modal-dialog modal-lg modal-dialog-scrollable">
                        <div class="modal-content" style="border-radius:3px;border:none">
                            <div class="modal-header" style="background:#1a1a2e;border-bottom:2px solid #c8472b">
                                <h5 class="modal-title" id="previewModalTitle" style="font-family:'Playfair Display',serif;color:white"></h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body p-4" id="previewModalBody" style="font-size:1.05rem;line-height:1.9;color:#2d2d44"></div>
                            <div class="modal-footer">
                                <span class="text-muted" style="font-size:0.78rem">Preview only — not published yet</span>
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `);
            modal = document.getElementById('previewModal');
        }
        document.getElementById('previewModalTitle').textContent = title;
        document.getElementById('previewModalBody').innerHTML = content.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
        new bootstrap.Modal(modal).show();
    }


    // ── 14. Search Form Validation ───────────────────────────
    document.querySelectorAll('form[action*="search"]').forEach(form => {
        form.addEventListener('submit', function (e) {
            const q = this.querySelector('input[name="q"]');
            if (!q || !q.value.trim()) {
                e.preventDefault();
                showToast('Please enter a search term', 'warning');
                q?.focus();
            }
        });
    });


    // ── 15. Typing Indicator on Comment Box ──────────────────
    const commentBox = document.querySelector('textarea[name="content"]');
    const commentForm = commentBox?.closest('form');
    if (commentBox && commentForm) {
        let typingTimer;
        const indicator = document.createElement('small');
        indicator.style.cssText = 'color:var(--ink-muted);font-size:0.75rem;opacity:0;transition:opacity 0.3s';
        indicator.textContent = 'You are typing...';
        commentForm.insertBefore(indicator, commentBox.nextSibling);

        commentBox.addEventListener('input', () => {
            indicator.style.opacity = '1';
            clearTimeout(typingTimer);
            typingTimer = setTimeout(() => indicator.style.opacity = '0', 1500);
        });
    }


    // ── 16. Character counter on comment box ─────────────────
    if (commentBox) {
        const MAX = 500;
        const counter = document.createElement('small');
        counter.style.cssText = 'display:block;text-align:right;color:var(--ink-muted);font-family:var(--font-mono);font-size:0.72rem;margin-top:4px';
        counter.textContent = `0 / ${MAX}`;
        commentBox.parentNode.appendChild(counter);

        commentBox.addEventListener('input', function () {
            const len = this.value.length;
            counter.textContent = `${len} / ${MAX}`;
            counter.style.color = len > MAX * 0.9 ? '#c8472b' : 'var(--ink-muted)';
            if (len > MAX) this.value = this.value.substring(0, MAX);
        });
    }


    // ── Helper: Get CSRF Cookie ───────────────────────────────
    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^|;)\\s*' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

});
