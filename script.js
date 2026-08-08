(() => {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const scrollBehavior = reducedMotion ? 'auto' : 'smooth';

  const menuButton = document.querySelector('[data-menu-toggle]');
  const mobileNav = document.querySelector('[data-mobile-nav]');
  const year = document.querySelector('[data-current-year]');

  menuButton?.addEventListener('click', () => {
    const open = mobileNav?.classList.toggle('is-open') ?? false;
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
  });
  mobileNav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
    mobileNav.classList.remove('is-open');
    menuButton?.setAttribute('aria-expanded', 'false');
  }));
  if (year) year.textContent = String(new Date().getFullYear());

  const setupSlider = (slider, prev, next, cardSelector) => {
    if (!slider) return;
    const step = () => {
      const card = slider.querySelector(cardSelector);
      if (!card) return slider.clientWidth;
      const gap = parseFloat(getComputedStyle(slider).columnGap || getComputedStyle(slider).gap) || 0;
      return card.getBoundingClientRect().width + gap;
    };
    const update = () => {
      const max = Math.max(0, slider.scrollWidth - slider.clientWidth - 2);
      if (prev) prev.disabled = slider.scrollLeft <= 2;
      if (next) next.disabled = slider.scrollLeft >= max;
    };
    const move = (direction) => slider.scrollBy({ left: direction * step(), behavior: scrollBehavior });
    prev?.addEventListener('click', () => move(-1));
    next?.addEventListener('click', () => move(1));
    slider.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') { event.preventDefault(); move(-1); }
      if (event.key === 'ArrowRight') { event.preventDefault(); move(1); }
    });
    slider.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    requestAnimationFrame(update);
  };

  setupSlider(
    document.querySelector('[data-research-slider]'),
    document.querySelector('[data-research-prev]'),
    document.querySelector('[data-research-next]'),
    '.research-card'
  );

  document.querySelectorAll('[data-content-row]').forEach((row) => {
    setupSlider(
      row.querySelector('[data-content-slider]'),
      row.querySelector('[data-content-prev]'),
      row.querySelector('[data-content-next]'),
      '.content-card'
    );
  });

  // Article image lightbox. The large source is loaded only after the user opens it.
  const zoomableImages = document.querySelectorAll('[data-lightbox-src]');
  if (zoomableImages.length) {
    const overlay = document.createElement('div');
    overlay.className = 'image-lightbox';
    overlay.hidden = true;
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', '画像の拡大表示');
    overlay.innerHTML = `
      <div class="image-lightbox__backdrop" data-lightbox-close></div>
      <div class="image-lightbox__panel">
        <button class="image-lightbox__close" type="button" data-lightbox-close aria-label="拡大表示を閉じる">×</button>
        <img class="image-lightbox__image" alt="">
        <p class="image-lightbox__caption" hidden></p>
      </div>
    `;
    document.body.appendChild(overlay);

    const lightboxImage = overlay.querySelector('.image-lightbox__image');
    const caption = overlay.querySelector('.image-lightbox__caption');
    const closeButton = overlay.querySelector('.image-lightbox__close');
    let previouslyFocused = null;

    const closeLightbox = () => {
      if (overlay.hidden) return;
      overlay.hidden = true;
      document.body.classList.remove('lightbox-open');
      lightboxImage.removeAttribute('src');
      lightboxImage.alt = '';
      if (caption) {
        caption.textContent = '';
        caption.hidden = true;
      }
      previouslyFocused?.focus?.();
    };

    const openLightbox = (trigger) => {
      const src = trigger.dataset.lightboxSrc;
      if (!src) return;
      const alt = trigger.dataset.lightboxAlt || trigger.getAttribute('alt') || '';
      previouslyFocused = trigger;
      lightboxImage.src = src;
      lightboxImage.alt = alt;
      if (caption) {
        caption.textContent = alt;
        caption.hidden = !alt;
      }
      overlay.hidden = false;
      document.body.classList.add('lightbox-open');
      closeButton?.focus();
    };

    zoomableImages.forEach((image) => {
      image.addEventListener('click', () => openLightbox(image));
      image.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openLightbox(image);
        }
      });
    });

    overlay.querySelectorAll('[data-lightbox-close]').forEach((element) => {
      element.addEventListener('click', closeLightbox);
    });

    document.addEventListener('keydown', (event) => {
      if (!overlay.hidden && event.key === 'Escape') closeLightbox();
    });
  }

  // Compact home profile disclosure: clicking the portrait reveals details and career.
  const profileToggle = document.querySelector('[data-profile-toggle]');
  const profileDetails = document.querySelector('[data-profile-details]');
  const profileToggleMark = document.querySelector('[data-profile-toggle-mark]');
  profileToggle?.addEventListener('click', () => {
    if (!profileDetails) return;
    const open = profileToggle.getAttribute('aria-expanded') === 'true';
    profileToggle.setAttribute('aria-expanded', String(!open));
    profileToggle.setAttribute('aria-label', open ? 'プロフィール詳細と経歴を表示' : 'プロフィール詳細と経歴を閉じる');
    profileDetails.hidden = open;
    if (profileToggleMark) profileToggleMark.textContent = open ? '＋' : '−';
  });

  const contactForm = document.querySelector('[data-contact-form]');
  contactForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    if (!contactForm.reportValidity()) return;
    const data = new FormData(contactForm);
    const to = `${contactForm.dataset.emailUser || ''}@${contactForm.dataset.emailDomain || ''}`;
    const name = String(data.get('name') || '').trim();
    const from = String(data.get('email') || '').trim();
    const subject = String(data.get('subject') || '').trim();
    const message = String(data.get('message') || '').trim();
    const body = [`お名前: ${name}`, `返信先: ${from}`, '', message].join('\n');
    window.location.href = `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  });
})();
