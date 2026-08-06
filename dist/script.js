(() => {
  const root = document.documentElement;
  const themeButton = document.querySelector('[data-theme-toggle]');
  const menuButton = document.querySelector('[data-menu-toggle]');
  const mobileNav = document.querySelector('[data-mobile-nav]');
  const year = document.querySelector('[data-current-year]');

  const savedTheme = localStorage.getItem('site-theme');
  if (savedTheme === 'dark' || savedTheme === 'light') {
    root.dataset.theme = savedTheme;
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    root.dataset.theme = 'dark';
  }

  themeButton?.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    localStorage.setItem('site-theme', next);
    themeButton.setAttribute('aria-label', next === 'dark' ? 'ライトモードに切り替える' : 'ダークモードに切り替える');
  });

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
