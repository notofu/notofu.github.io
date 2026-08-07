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

  // Teaching page: load public Researchmap teaching_experience records.
  // A static fallback remains in the HTML if the API is unavailable.
  const teachingRoot = document.querySelector('[data-researchmap-teaching]');
  const teachingStatus = document.querySelector('[data-rmap-status]');

  const localizedText = (value) => {
    if (!value) return '';
    if (typeof value === 'string') return value;
    return value.ja || value.en || '';
  };

  const formatResearchmapDate = (value) => {
    if (!value) return '';
    const text = String(value).trim();
    if (!text) return '';
    const match = text.match(/^(\d{4})(?:-(\d{1,2}))?/);
    if (!match) return text;
    return match[2] ? `${match[1]}.${String(match[2]).padStart(2, '0')}` : match[1];
  };

  const teachingPeriod = (item) => {
    const from = formatResearchmapDate(item.from_date);
    const to = formatResearchmapDate(item.to_date);
    if (from && to) return `${from} – ${to}`;
    if (from) return `${from} – 現在`;
    if (to) return `– ${to}`;
    return '';
  };

  const makeTeachingCourse = (item) => {
    const article = document.createElement('article');
    article.className = 'teaching-course';

    const period = document.createElement('div');
    period.className = 'teaching-course-period';
    period.textContent = teachingPeriod(item) || '期間未登録';

    const main = document.createElement('div');
    main.className = 'teaching-course-main';

    const title = document.createElement('h2');
    title.textContent = localizedText(item.subject_name) || '科目名未登録';
    main.appendChild(title);

    const institution = localizedText(item.institution_name);
    if (institution) {
      const inst = document.createElement('p');
      inst.className = 'teaching-course-institution';
      inst.textContent = institution;
      main.appendChild(inst);
    }

    const description = localizedText(item.description);
    if (description) {
      const desc = document.createElement('p');
      desc.className = 'teaching-course-description';
      desc.textContent = description;
      main.appendChild(desc);
    }

    article.append(period, main);
    return article;
  };

  if (teachingRoot) {
    const permalink = teachingRoot.dataset.permalink || 'notokaede';
    const apiUrl = `https://api.researchmap.jp/${encodeURIComponent(permalink)}/teaching_experience?limit=100`;

    fetch(apiUrl, { headers: { Accept: 'application/json' } })
      .then((response) => {
        if (!response.ok) throw new Error(`Researchmap API: ${response.status}`);
        return response.json();
      })
      .then((data) => {
        const items = Array.isArray(data.items) ? data.items : [];
        if (!items.length) throw new Error('Researchmapに公開中の担当科目がありません');

        teachingRoot.replaceChildren();
        items.forEach((item) => teachingRoot.appendChild(makeTeachingCourse(item)));
        if (teachingStatus) teachingStatus.textContent = `Researchmapから${items.length}件を表示中`;
      })
      .catch((error) => {
        console.warn(error);
        if (teachingStatus) teachingStatus.textContent = 'Researchmapを取得できないため、サイト登録情報を表示中';
      });
  }

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
