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

  // Works page: load Researchmap public data for projects, IP rights, and academic contributions.
  // These sections refresh on every page view, so a Researchmap update does not require a GitHub commit.
  const rmapRoots = document.querySelectorAll('[data-rmap-achievements]');

  const extractResearchmapItems = (data) => {
    if (Array.isArray(data?.items)) return data.items;
    if (Array.isArray(data?.['@graph'])) return data['@graph'];
    if (Array.isArray(data)) return data;
    return [];
  };

  const firstArrayValue = (value) => {
    if (Array.isArray(value)) return value[0] ?? '';
    return value ?? '';
  };

  const joinNonEmpty = (values, separator = ' / ') => values.filter(Boolean).join(separator);

  const researchmapWebUrl = (permalink, type, item) => {
    const id = item?.['rm:id'];
    return id ? `https://researchmap.jp/${encodeURIComponent(permalink)}/${type}/${encodeURIComponent(id)}` : `https://researchmap.jp/${encodeURIComponent(permalink)}/${type}`;
  };

  const makeRmapRow = ({ period, badge, kind, title, meta, description, url }) => {
    const article = document.createElement('article');
    article.className = 'rmap-achievement-row';
    article.dataset.kind = kind;

    const date = document.createElement('div');
    date.className = 'rmap-achievement-period';
    date.textContent = period || '—';

    const badgeEl = document.createElement('div');
    badgeEl.className = 'rmap-achievement-badge';
    badgeEl.textContent = badge;

    const body = document.createElement('div');
    body.className = 'rmap-achievement-body';

    const heading = document.createElement('h3');
    if (url) {
      const link = document.createElement('a');
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = title || 'タイトル未登録';
      heading.appendChild(link);
    } else {
      heading.textContent = title || 'タイトル未登録';
    }
    body.appendChild(heading);

    if (meta) {
      const metaEl = document.createElement('p');
      metaEl.className = 'rmap-achievement-meta';
      metaEl.textContent = meta;
      body.appendChild(metaEl);
    }

    if (description) {
      const desc = document.createElement('p');
      desc.className = 'rmap-achievement-description';
      desc.textContent = description;
      body.appendChild(desc);
    }

    const arrow = document.createElement('div');
    arrow.className = 'rmap-achievement-arrow';
    arrow.setAttribute('aria-hidden', 'true');
    arrow.textContent = '↗';

    article.append(date, badgeEl, body, arrow);
    return article;
  };

  const projectRoleLabel = (value) => ({
    principal_investigator: '研究代表',
    coinvestigator: '研究分担',
    coinvestigator_not_use_grants: '連携研究者',
    others: 'その他',
  }[value] || '研究課題');

  const propertyTypeLabel = (value) => ({
    patent_right: '特許',
    utility_model_right: '実用新案',
    design_right: '意匠',
    trademark: '商標',
  }[value] || '産業財産権');

  const academicRoleLabel = (roles) => {
    const labels = {
      planning_etc: '企画・運営',
      panel_chair_etc: '座長等',
      supervision: '監修',
      review: '審査・評価',
      academic_research_planning: '学術調査',
      peer_review: '査読',
      save_or_restore: '保存・修復',
      others: 'その他',
    };
    const list = Array.isArray(roles) ? roles : (roles ? [roles] : []);
    return list.map((role) => labels[role] || role).filter(Boolean).join('・') || '学術貢献';
  };

  const periodFromTo = (from, to) => {
    const f = formatResearchmapDate(from);
    const t = formatResearchmapDate(to);
    if (f && t) return f === t ? f : `${f} – ${t}`;
    if (f) return f;
    if (t) return t;
    return '';
  };

  const renderResearchProject = (item, permalink) => {
    const grantNumber = firstArrayValue(item?.identifiers?.grant_number);
    const meta = joinNonEmpty([
      localizedText(item.offer_organization),
      localizedText(item.system_name),
      localizedText(item.category),
      grantNumber ? `課題番号 ${grantNumber}` : '',
    ]);
    return makeRmapRow({
      period: periodFromTo(item.from_date, item.to_date),
      badge: projectRoleLabel(item.research_project_owner_role),
      kind: 'project',
      title: localizedText(item.research_project_title),
      meta,
      description: localizedText(item.description),
      url: researchmapWebUrl(permalink, 'research_projects', item),
    });
  };

  const renderIndustrialProperty = (item, permalink) => {
    const number = item.patent_number || item.patent_announcement_number || item.application_number || item.patent_publication_number || '';
    const date = item.registration_date || item.patent_announcement_date || item.application_date || item.patent_publication_date || '';
    const meta = joinNonEmpty([
      number,
      localizedText(item.right_holder),
      item.application_number && item.application_number !== number ? `出願 ${item.application_number}` : '',
    ]);
    return makeRmapRow({
      period: formatResearchmapDate(date),
      badge: propertyTypeLabel(item.industrial_property_right_type),
      kind: 'property',
      title: localizedText(item.industrial_property_right_title),
      meta,
      description: localizedText(item.description),
      url: researchmapWebUrl(permalink, 'industrial_property_rights', item),
    });
  };

  const renderAcademicContribution = (item, permalink) => {
    const meta = joinNonEmpty([
      localizedText(item.promoter),
      localizedText(item.location),
    ]);
    return makeRmapRow({
      period: periodFromTo(item.from_event_date, item.to_event_date),
      badge: academicRoleLabel(item.academic_contribution_roles),
      kind: 'academic',
      title: localizedText(item.academic_contribution_title),
      meta,
      description: localizedText(item.description),
      url: researchmapWebUrl(permalink, 'academic_contribution', item),
    });
  };

  const rendererByType = {
    research_projects: renderResearchProject,
    industrial_property_rights: renderIndustrialProperty,
    academic_contribution: renderAcademicContribution,
  };

  rmapRoots.forEach((root) => {
    const type = root.dataset.rmapAchievements;
    const permalink = root.dataset.permalink || 'notokaede';
    const status = document.querySelector(`[data-rmap-achievement-status="${type}"]`);
    const renderer = rendererByType[type];
    if (!renderer) return;

    const apiUrl = `https://api.researchmap.jp/${encodeURIComponent(permalink)}/${type}?limit=100&sort=-modified`;
    fetch(apiUrl, { cache: 'no-store', headers: { Accept: 'application/json' } })
      .then((response) => {
        if (!response.ok) throw new Error(`Researchmap API: ${response.status}`);
        return response.json();
      })
      .then((data) => {
        const items = extractResearchmapItems(data).filter((item) => item && item.display !== 'hidden');
        root.replaceChildren();
        if (!items.length) {
          const empty = document.createElement('p');
          empty.className = 'rmap-empty';
          empty.textContent = '現在、Researchmapで公開されている登録はありません。';
          root.appendChild(empty);
          if (status) status.textContent = 'Researchmap公開情報：0件';
          return;
        }
        items.forEach((item) => root.appendChild(renderer(item, permalink)));
        if (status) status.textContent = `Researchmapから${items.length}件を自動表示`;
      })
      .catch((error) => {
        console.warn(error);
        root.replaceChildren();
        const errorBox = document.createElement('p');
        errorBox.className = 'rmap-error';
        const link = document.createElement('a');
        link.href = `https://researchmap.jp/${encodeURIComponent(permalink)}/${type}`;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = 'Researchmapで確認する ↗';
        errorBox.append('Researchmapの自動取得に失敗しました。 ', link);
        root.appendChild(errorBox);
        if (status) status.textContent = 'Researchmapを取得できませんでした';
      });
  });

  // Works page category coloring without adding maintenance fields to the HTML.
  document.querySelectorAll('.output-row').forEach((row) => {
    const text = row.querySelector('.output-type')?.textContent ?? '';
    let kind = 'conference';
    if (/査読論文|論文|テクニカル/.test(text) && !/国際会議/.test(text)) kind = 'journal';
    else if (/研究会|学会発表|全国大会|発表/.test(text) && !/国際会議論文/.test(text)) kind = 'presentation';
    else if (/紀要|研究報告/.test(text)) kind = 'report';
    row.dataset.kind = kind;
  });


  // Research hub: independent horizontal sliders for Research / Graduation / Blog.
  document.querySelectorAll('[data-content-row]').forEach((row) => {
    const slider = row.querySelector('[data-content-slider]');
    const prev = row.querySelector('[data-content-prev]');
    const next = row.querySelector('[data-content-next]');
    if (!slider || !prev || !next) return;

    const step = () => {
      const card = slider.querySelector('.content-card');
      if (!card) return slider.clientWidth;
      const gap = parseFloat(getComputedStyle(slider).gap) || 0;
      return card.getBoundingClientRect().width + gap;
    };

    const update = () => {
      const max = Math.max(0, slider.scrollWidth - slider.clientWidth - 2);
      prev.disabled = slider.scrollLeft <= 2;
      next.disabled = slider.scrollLeft >= max;
    };

    prev.addEventListener('click', () => slider.scrollBy({ left: -step(), behavior: 'smooth' }));
    next.addEventListener('click', () => slider.scrollBy({ left: step(), behavior: 'smooth' }));
    slider.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    requestAnimationFrame(update);
  });
})();
