/**
 * Portfolio JavaScript
 * Handles animations, navigation, and interactions
 */

(function() {
    'use strict';

    // ===================================
    // Configuration
    // ===================================
    const CONFIG = {
        typingStrings: [
            'Data Analyst',
            'Full Stack Developer',
            'Computer Scientist',
            'Problem Solver'
        ],
        typingSpeed: 80,
        deletingSpeed: 50,
        pauseDuration: 2000
    };

    // ===================================
    // DOM Elements
    // ===================================
    const elements = {
        navbar: document.getElementById('navbar'),
        navToggle: document.getElementById('nav-toggle'),
        navMenu: document.getElementById('nav-menu'),
        navLinks: document.querySelectorAll('.nav-link'),
        typingText: document.querySelector('.typing-text'),
        contactForm: document.getElementById('contact-form'),
        currentYear: document.getElementById('current-year'),
        sections: document.querySelectorAll('.section')
    };

    // ===================================
    // Navigation
    // ===================================
    function initNavigation() {
        // Toggle mobile menu
        if (elements.navToggle) {
            elements.navToggle.addEventListener('click', () => {
                elements.navToggle.classList.toggle('active');
                elements.navMenu.classList.toggle('active');
            });
        }

        // Close mobile menu on link click
        elements.navLinks.forEach(link => {
            link.addEventListener('click', () => {
                elements.navToggle.classList.remove('active');
                elements.navMenu.classList.remove('active');
            });
        });

        // Navbar scroll effect
        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;

            // Add scrolled class
            if (currentScroll > 50) {
                elements.navbar.classList.add('scrolled');
            } else {
                elements.navbar.classList.remove('scrolled');
            }

            lastScroll = currentScroll;
        });

        // Active nav link on scroll
        window.addEventListener('scroll', debounce(updateActiveNavLink, 100));
    }

    function updateActiveNavLink() {
        const scrollPos = window.scrollY + 100;

        elements.sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');

            if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                elements.navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }

    // ===================================
    // Typing Animation
    // ===================================
    function initTypingAnimation() {
        if (!elements.typingText) return;

        let stringIndex = 0;
        let charIndex = 0;
        let isDeleting = false;

        function type() {
            const currentString = CONFIG.typingStrings[stringIndex];

            if (isDeleting) {
                elements.typingText.textContent = currentString.substring(0, charIndex - 1);
                charIndex--;
            } else {
                elements.typingText.textContent = currentString.substring(0, charIndex + 1);
                charIndex++;
            }

            let typeSpeed = isDeleting ? CONFIG.deletingSpeed : CONFIG.typingSpeed;

            if (!isDeleting && charIndex === currentString.length) {
                typeSpeed = CONFIG.pauseDuration;
                isDeleting = true;
            } else if (isDeleting && charIndex === 0) {
                isDeleting = false;
                stringIndex = (stringIndex + 1) % CONFIG.typingStrings.length;
                typeSpeed = 500;
            }

            setTimeout(type, typeSpeed);
        }

        // Start typing animation after a short delay
        setTimeout(type, 1000);
    }

    // ===================================
    // Scroll Reveal Animation
    // ===================================
    function initScrollReveal() {
        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                }
            });
        }, observerOptions);

        // Add animation class and observe
        document.querySelectorAll('.skill-category, .project-card, .timeline-item').forEach(el => {
            el.classList.add('fade-in-section');
            observer.observe(el);
        });
    }

    // ===================================
    // Contact Form
    // ===================================
    function initContactForm() {
        if (!elements.contactForm) return;

        elements.contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(elements.contactForm);
            const data = Object.fromEntries(formData);

            // Get submit button
            const submitBtn = elements.contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;

            // Show loading state
            submitBtn.innerHTML = '<span>Sending...</span>';
            submitBtn.disabled = true;

            // Simulate form submission (replace with actual endpoint)
            try {
                // For now, we'll just simulate a delay
                // In production, you'd send to your backend or a service like Formspree
                await new Promise(resolve => setTimeout(resolve, 1500));

                // Show success message
                submitBtn.innerHTML = '<span>Message Sent!</span>';
                submitBtn.style.background = 'var(--success)';

                // Reset form
                elements.contactForm.reset();

                // Reset button after delay
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.style.background = '';
                    submitBtn.disabled = false;
                }, 3000);

                // Log form data (for testing)
                console.log('Form submitted:', data);

            } catch (error) {
                submitBtn.innerHTML = '<span>Error - Try Again</span>';
                submitBtn.style.background = 'var(--error)';
                submitBtn.disabled = false;

                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.style.background = '';
                }, 3000);
            }
        });
    }

    // ===================================
    // Utilities
    // ===================================
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function setCurrentYear() {
        if (elements.currentYear) {
            elements.currentYear.textContent = new Date().getFullYear();
        }
    }

    // ===================================
    // Smooth scroll for anchor links
    // ===================================
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);

                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // ===================================
    // Initialize
    // ===================================
    function init() {
        initNavigation();
        initTypingAnimation();
        initScrollReveal();
        initContactForm();
        initSmoothScroll();
        setCurrentYear();
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
