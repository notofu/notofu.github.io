(() => {
  const menuButton = document.querySelector('[data-menu-toggle]');
  const mobileNav = document.querySelector('[data-mobile-nav]');
  const year = document.querySelector('[data-current-year]');

  menuButton?.addEventListener('click', () => {
    const open = mobileNav?.classList.toggle('is-open') ?? false;
    menuButton.setAttribute('aria-expanded', String(open));
  });

  mobileNav?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mobileNav.classList.remove('is-open');
      menuButton?.setAttribute('aria-expanded', 'false');
    });
  });

  if (year) year.textContent = String(new Date().getFullYear());

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


const researchSlider = document.querySelector('.research-grid');
const researchPrev = document.querySelector('[data-research-prev]');
const researchNext = document.querySelector('[data-research-next]');

function scrollResearch(direction) {
  if (!researchSlider) return;

  const card = researchSlider.querySelector('.research-card');
  if (!card) return;

  const gap = 20;
  const amount = card.getBoundingClientRect().width + gap;

  researchSlider.scrollBy({
    left: direction * amount,
    behavior: 'smooth'
  });
}

researchPrev?.addEventListener('click', () => {
  scrollResearch(-1);
});

researchNext?.addEventListener('click', () => {
  scrollResearch(1);
});
