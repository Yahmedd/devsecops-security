// Smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.product-card, .feature-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.6s ease';
    observer.observe(el);
});

// Add loading state only to buttons that opt-in via data-loading="true"
document.querySelectorAll('button[type="submit"][data-loading="true"]').forEach(btn => {
    btn.addEventListener('click', function() {
        if (this.form && this.form.checkValidity()) {
            const text = this.getAttribute('data-loading-text') || 'Processing...';
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + text;
            this.disabled = true;
        }
    });
});
