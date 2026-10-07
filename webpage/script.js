document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  /* ============ 1. THEME TOGGLE ============ */
  const body = document.body;
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = themeToggle ? themeToggle.querySelector('i') : null;

  const applyTheme = (light) => {
    body.classList.toggle('light-theme', light);
    if (themeIcon) {
      themeIcon.className = light ? 'fas fa-moon' : 'fas fa-sun';
    }
    localStorage.setItem('theme', light ? 'light' : 'dark');
  };

  const savedTheme = localStorage.getItem('theme');
  const prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
  applyTheme(savedTheme ? savedTheme === 'light' : prefersLight);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      applyTheme(!body.classList.contains('light-theme'));
    });
  }

  /* ============ 2. SCROLL REVEAL ============ */
  const revealEls = document.querySelectorAll('[data-reveal], .reveal');
  revealEls.forEach((el, i) => {
    if (!el.style.transitionDelay) {
      el.style.transitionDelay = `${(i % 6) * 0.1}s`;
    }
  });

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  revealEls.forEach((el) => revealObserver.observe(el));

  /* ============ 3. PARALLAX ============ */
  const parallaxEls = document.querySelectorAll('[data-speed]');
  let mouseX = 0, mouseY = 0, scrollY = window.scrollY, ticking = false;

  const updateParallax = () => {
    parallaxEls.forEach((el) => {
      const speed = parseFloat(el.dataset.speed) || 0;
      const rect = el.parentElement ? el.parentElement.getBoundingClientRect() : null;
      const offset = rect ? Math.min(Math.max(-rect.top, -600), 600) : 0;
      const x = mouseX * speed * 20;
      const y = offset * speed + mouseY * speed * 20;
      el.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    });
    ticking = false;
  };

  const requestTick = () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(updateParallax);
    }
  };

  window.addEventListener('scroll', () => {
    scrollY = window.scrollY;
    requestTick();
  }, { passive: true });

  window.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    requestTick();
  }, { passive: true });

  requestTick();

  /* ============ 4. TYPING EFFECT ============ */
  const typeEl = document.getElementById('typing-text');
  if (typeEl) {
    const phrases = JSON.parse(typeEl.dataset.phrases || '[]') || [
      'Creative Developer',
      'UI/UX Designer',
      'Digital Craftsman'
    ];
    let phraseIndex = 0, charIndex = 0, deleting = false;

    const type = () => {
      const current = phrases[phraseIndex];
      charIndex += deleting ? -1 : 1;
      typeEl.textContent = current.slice(0, charIndex);

      let delay = deleting ? 50 : 100;
      if (!deleting && charIndex === current.length) {
        delay = 2000;
        deleting = true;
      } else if (deleting && charIndex === 0) {
        deleting = false;
        phraseIndex = (phraseIndex + 1) % phrases.length;
        delay = 500;
      }
      setTimeout(type, delay);
    };
    type();
  }

  /* ============ 5. STAT COUNTERS ============ */
  const counters = document.querySelectorAll('.stat-number, [data-count]');
  const animateCounter = (el) => {
    const target = parseInt(el.dataset.count || el.textContent.replace(/\D/g, ''), 10) || 0;
    const suffix = el.dataset.suffix || '+';
    const duration = 2000;
    const start = performance.now();
    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(eased * target) + (progress === 1 ? suffix : '');
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach((el) => counterObserver.observe(el));

  /* ============ 6. SKILL BARS ============ */
  const skillBars = document.querySelectorAll('.skill-progress, [data-percent]');
  const skillObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const bar = entry.target;
        const percent = bar.dataset.percent || '0';
        bar.style.width = `${percent}%`;
        skillObserver.unobserve(bar);
      }
    });
  }, { threshold: 0.4 });

  skillBars.forEach((bar) => skillObserver.observe(bar));

  /* ============ 7. NAVBAR ============ */
  const navbar = document.querySelector('.navbar');
  const navLinks = document.querySelectorAll('.nav-link');
  const hamburger = document.getElementById('hamburger');
  const navMenu = document.getElementById('nav-menu');

  const onScrollNav = () => {
    if (navbar) navbar.classList.toggle('scrolled', window.scrollY > 50);

    let current = '';
    document.querySelectorAll('section[id]').forEach((section) => {
      if (window.scrollY >= section.offsetTop - 120) current = section.id;
    });
    navLinks.forEach((link) => {
      link.classList.toggle('active', link.getAttribute('href') === `#${current}`);
    });
  };
  window.addEventListener('scroll', onScrollNav, { passive: true });
  onScrollNav();

  const closeMenu = () => {
    if (navMenu) navMenu.classList.remove('open');
    if (hamburger) hamburger.classList.remove('active');
  };

  if (hamburger) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('active');
      if (navMenu) navMenu.classList.toggle('open');
    });
  }

  /* ============ 8. TESTIMONIAL CAROUSEL ============ */n  const carousel = document.querySelector('.testimonial-carousel');
  if (carousel) {
    const slides = carousel.querySelectorAll('.testimonial-slide, .testimonial');
    const dotsContainer = carousel.querySelector('.carousel-dots');
    const prevBtn = carousel.querySelector('.carousel-prev');
    const nextBtn = carousel.querySelector('.carousel-next');
    let currentSlide = 0;
    let autoTimer;

    const showSlide = (index) => {
      currentSlide = (index + slides.length) % slides.length;
      slides.forEach((s, i) => s.classList.toggle('active', i === currentSlide));
      if (dotsContainer) {
        dotsContainer.querySelectorAll('.dot').forEach((d, i) => {
          d.classList.toggle('active', i === currentSlide);
        });
      }
    };

    const next = () => showSlide(currentSlide + 1);
    const prev = () => showSlide(currentSlide - 1);
    const resetAuto = () => {
      clearInterval(autoTimer);
      autoTimer = setInterval(next, 5000);
    };

    if (dotsContainer) {
      slides.forEach((_, i) => {
        const dot = document.createElement('button');
        dot.className = 'dot';
        dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
        dot.addEventListener('click', () => { showSlide(i); resetAuto(); });
        dotsContainer.appendChild(dot);
      });
    }

    if (nextBtn) nextBtn.addEventListener('click', () => { next(); resetAuto(); });
    if (prevBtn) prevBtn.addEventListener('click', () => { prev(); resetAuto(); });

    showSlide(0);
    resetAuto();
  }

  /* ============ 9. SMOOTH SCROLL & FORM ============ */
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const id = anchor.getAttribute('href');
      if (id.length > 1) {
        const target = document.querySelector(id);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          closeMenu();
        }
      }
    });
  });

  const form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const success = form.querySelector('.form-success');
      if (success) {
        success.classList.add('show');
        setTimeout(() => success.classList.remove('show'), 4000);
      } else {
        const msg = document.createElement('p');
        msg.className = 'form-success show';
        msg.textContent = 'Thank you! Your message has been sent successfully.';
        form.appendChild(msg);
        setTimeout(() => msg.remove(), 4000);
      }
      form.reset();
    });
  }
});