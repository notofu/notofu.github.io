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
