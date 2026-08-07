(() => {
  const menuButton = document.querySelector('[data-menu-toggle]');
  const mobileNav = document.querySelector('[data-mobile-nav]');
  const year = document.querySelector('[data-current-year]');

  menuButton?.addEventListener('click', () => {
    const isOpen = mobileNav?.classList.toggle('is-open') ?? false;
    menuButton.setAttribute('aria-expanded', String(isOpen));
  });

  mobileNav?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mobileNav.classList.remove('is-open');
      menuButton?.setAttribute('aria-expanded', 'false');
    });
  });

  if (year) year.textContent = String(new Date().getFullYear());
})();
