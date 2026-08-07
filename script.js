(() => {
  const menuButton = document.querySelector('[data-menu-toggle]');
  const mobileNav = document.querySelector('[data-mobile-nav]');
  const year = document.querySelector('[data-current-year]');

  menuButton?.addEventListener('click', () => {
    const open = mobileNav?.classList.toggle('is-open') ?? false;
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
  });

  mobileNav?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mobileNav.classList.remove('is-open');
      menuButton?.setAttribute('aria-expanded', 'false');
      menuButton?.setAttribute('aria-label', 'メニューを開く');
    });
  });

  if (year) year.textContent = String(new Date().getFullYear());

  // Research carousel: one click = one card. Touch/trackpad scrolling also works naturally.
  const researchSlider = document.querySelector('[data-research-slider]');
  const researchPrev = document.querySelector('[data-research-prev]');
  const researchNext = document.querySelector('[data-research-next]');

  const cardStep = () => {
    if (!researchSlider) return 0;
    const card = researchSlider.querySelector('.research-card');
    if (!card) return 0;
    const styles = getComputedStyle(researchSlider);
    const gap = parseFloat(styles.columnGap || styles.gap) || 20;
    return card.getBoundingClientRect().width + gap;
  };

  const updateSliderButtons = () => {
    if (!researchSlider) return;
    const max = Math.max(0, researchSlider.scrollWidth - researchSlider.clientWidth - 2);
    if (researchPrev) researchPrev.disabled = researchSlider.scrollLeft <= 2;
    if (researchNext) researchNext.disabled = researchSlider.scrollLeft >= max;
  };

  const moveResearch = (direction) => {
    if (!researchSlider) return;
    researchSlider.scrollBy({ left: direction * cardStep(), behavior: 'smooth' });
  };

  researchPrev?.addEventListener('click', () => moveResearch(-1));
  researchNext?.addEventListener('click', () => moveResearch(1));
  researchSlider?.addEventListener('scroll', updateSliderButtons, { passive: true });
  window.addEventListener('resize', updateSliderButtons);
  updateSliderButtons();

  // Works page category coloring without adding maintenance fields to the HTML.
  document.querySelectorAll('.output-row').forEach((row) => {
    const text = row.querySelector('.output-type')?.textContent ?? '';
    let kind = 'conference';
    if (/査読論文|論文|テクニカル/.test(text) && !/国際会議/.test(text)) kind = 'journal';
    else if (/研究会|学会発表|全国大会|発表/.test(text) && !/国際会議論文/.test(text)) kind = 'presentation';
    else if (/紀要|研究報告/.test(text)) kind = 'report';
    row.dataset.kind = kind;
  });
})();
