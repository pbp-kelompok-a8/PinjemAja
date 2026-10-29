function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

async function handleAksiSubmit(form, container, submitter) {
    const formData = submitter ? new FormData(form, submitter) : new FormData(form);

            const csrfToken = formData.get('csrfmiddlewaretoken') || getCookie('csrftoken');
            const submitBtn = form.querySelector('button[type="submit"]')
            const originalText = submitBtn? submitBtn.innerHTML : '';

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'Memproses...';
            }

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                    }, body: formData,
                });

                const toastHeader = response.headers.get('X-Toast');
                if (toastHeader) {
                    try {
                        const toast = JSON.parse(toastHeader);
                        showToast(toast.title, toast.message, toast.type);
                    } catch (err) {
                        console.error('Invalid X-Toast header:', err);
                    }
                }

                if (!response.ok) {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                    return;
                }

                const html = await response.text();

                if (html.trim() && container) {
                    container.innerHTML = html;
                }

                const popoverEl = form.closest('[popover]');
                if (popoverEl && popoverEl.matches(':popover-open')) {
                    popoverEl.hidePopover();
                }

            } catch(error){
                console.error(error);
                showToast('Error', 'Terjadi kesalahan jaringan. Coba lagi.', 'error');

                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            }
        }

async function handleFilterClick(link, container, filterNav) {
    const status = link.dataset.status;

    try {
        const url = new URL(window.location.href);
        url.searchParams.set('status', status);
        const res = await fetch(url, {
            headers: {'X-Requested-With': 'XMLHttpRequest'},
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const html = await res.text();
        if (html.trim() && container) {
            container.innerHTML = html;
            container.dataset.statusFilter = status;
            window.history.replaceState({}, '', url);
            filterNav.querySelectorAll('a').forEach(a => a.classList.toggle('active', a.dataset.status === status));
        }
    } catch (err) {
        console.error(err);
        showToast('Error', 'Gagal memuat data.', 'error');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('transaksi-list');
    const filterNav = document.getElementById('filter-nav');

    if (container) {
        container.addEventListener('submit', function (e) {
            const form = e.target.closest('form.form-aksi');
            if (!form) return;
            e.preventDefault();
            handleAksiSubmit(form, container, e.submitter);
        });
    }

    if (filterNav && container) {
        filterNav.addEventListener('click', function (e) {
            const link = e.target.closest('a[data-status]');
            if (!link) return;
            e.preventDefault();
            handleFilterClick(link, container, filterNav);
        });
    }

    document.addEventListener('click', function (e) {
        const ratingButton = e.target.closest('.transaction-open-rating');
        if (ratingButton) {
            const dialog = document.getElementById(ratingButton.dataset.ratingDialog);
            if (dialog && !dialog.open) dialog.showModal();
        }

        const btn = e.target.closest('.btn-tolak');
        if (!btn) return;
        const formTolak = document.getElementById('formTolak');
        if (formTolak) {
            formTolak.action = btn.dataset.url;
        }
    });

    document.addEventListener('submit', async function (e) {
        const form = e.target.closest('form.rating-ajax-form');
        if (!form) return;
        e.preventDefault();

        const submitter = e.submitter;
        const formData = submitter ? new FormData(form, submitter) : new FormData(form);
        const button = submitter || form.querySelector('button[type="submit"]');
        if (button) button.disabled = true;

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken') || getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            });
            const toastHeader = response.headers.get('X-Toast');
            if (toastHeader) {
                const toast = JSON.parse(toastHeader);
                showToast(toast.title, toast.message, toast.type);
            }

            if (!response.ok) {
                if (button) button.disabled = false;
                return;
            }

            const newRating = response.headers.get('X-Owner-Rating');
            const ratingElement = document.getElementById('transaction-owner-rating');
            if (newRating && ratingElement) {
                const rating = Number(newRating).toFixed(1);
                ratingElement.textContent = `★ ${rating}`;
                ratingElement.setAttribute('aria-label', `Rating ${rating} dari 5`);
            }
            document.querySelector('.transaction-rating-dialog')?.remove();
        } catch (error) {
            console.error(error);
            showToast('Gagal', 'Rating belum terkirim. Coba lagi.', 'error');
            if (button) button.disabled = false;
        }
    });

    document.addEventListener('submit', async function (e) {
        const form = e.target.closest('form.tolak-bukti-form, form.form-aksi');
        if (!form || form.closest('#transaksi-list')) return;
        e.preventDefault();

        const submitter = e.submitter;
        const formData = submitter ? new FormData(form, submitter) : new FormData(form);
        const button = submitter || form.querySelector('button[type="submit"]');
        const originalText = button?.textContent;
        if (button) {
            button.disabled = true;
            button.textContent = 'Memproses…';
        }

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken') || getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            });
            const toastHeader = response.headers.get('X-Toast');
            if (toastHeader) {
                const toast = JSON.parse(toastHeader);
                showToast(toast.title, toast.message, toast.type);
            }

            if (!response.ok) {
                if (button) {
                    button.disabled = false;
                    button.textContent = originalText;
                }
                return;
            }

            const popover = form.closest('[popover]');
            if (popover?.matches(':popover-open')) popover.hidePopover();
            window.setTimeout(() => window.location.reload(), 3200);
        } catch (error) {
            console.error(error);
            showToast('Gagal', 'Aksi belum berhasil. Coba lagi.', 'error');
            if (button) {
                button.disabled = false;
                button.textContent = originalText;
            }
        }
    });
});
