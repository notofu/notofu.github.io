(() => {
  const menuButton = document.querySelector('[data-menu-toggle]');
  const mobileNav = document.querySelector('[data-mobile-nav]');
  const year = document.querySelector('[data-current-year]');

  menuButton?.addEventListener('click', () => {
    const isOpen = mobileNav?.classList.toggle('is-open') ?? false;
    menuButton.setAttribute('aria-expanded', String(isOpen));
  });
  mobileNav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
    mobileNav.classList.remove('is-open');
    menuButton?.setAttribute('aria-expanded', 'false');
  }));
  if (year) year.textContent = String(new Date().getFullYear());

  const classify = (text) => {
    if (/国際|conference|ICEC|CHIRA|SMC|CMMR/i.test(text)) return 'type-international';
    if (/査読|論文|technical|テクニカル/i.test(text)) return 'type-journal';
    if (/研究会|学会発表|全国大会|発表/i.test(text)) return 'type-presentation';
    if (/紀要|研究報告|MISC/i.test(text)) return 'type-report';
    return 'type-other';
  };
  document.querySelectorAll('.output-type').forEach((el) => {
    el.classList.add(classify(el.textContent.trim()));
  });
})();
