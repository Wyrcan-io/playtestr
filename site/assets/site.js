(() => {
  const navToggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('#site-nav');
  if (navToggle && nav) {
    navToggle.addEventListener('click', () => {
      const open = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('open', !open);
    });
  }

  const currentPath = window.location.pathname.replace(/index\.html$/, '');
  document.querySelectorAll('.docs-nav a').forEach((link) => {
    const linkPath = new URL(link.href).pathname.replace(/index\.html$/, '');
    if (linkPath === currentPath) link.setAttribute('aria-current', 'page');
  });

  document.querySelectorAll('.prose pre').forEach((pre) => {
    const code = pre.querySelector('code');
    if (!code) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy-button';
    button.textContent = 'Copy';
    button.setAttribute('aria-label', 'Copy code');
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = 'Copied';
      } catch (_) {
        button.textContent = 'Select text';
      }
      window.setTimeout(() => { button.textContent = 'Copy'; }, 1600);
    });
    pre.appendChild(button);
  });

  const article = document.querySelector('.interior-layout .prose');
  if (article) {
    const headings = [...article.querySelectorAll('h2[id]')];
    if (headings.length >= 3) {
      const contents = document.createElement('details'); contents.className = 'page-toc';
      const summary = document.createElement('summary'); summary.textContent = 'On this page';
      const links = document.createElement('nav'); links.setAttribute('aria-label', 'On this page');
      headings.forEach((heading) => { const link = document.createElement('a'); link.href = `#${heading.id}`; link.textContent = heading.textContent.replace(/#$/, ''); links.appendChild(link); });
      contents.append(summary, links);
      const firstHeading = article.querySelector('h1'); firstHeading.insertAdjacentElement('afterend', contents);
    }
  }

  const form = document.querySelector('[data-search-form]');
  if (!form) return;
  const input = form.querySelector('input');
  const results = document.querySelector('[data-search-results]');
  const status = document.querySelector('[data-search-status]');
  let indexPromise;

  const escapeHTML = (value) => value.replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const loadIndex = () => {
    if (!indexPromise) indexPromise = fetch(form.dataset.index).then((response) => {
      if (!response.ok) throw new Error('Search index unavailable');
      return response.json();
    });
    return indexPromise;
  };
  const excerpt = (text, term) => {
    const normalized = text.replace(/\s+/g, ' ').trim();
    const at = normalized.toLowerCase().indexOf(term);
    const start = Math.max(0, at - 65);
    const end = Math.min(normalized.length, start + 180);
    return `${start ? '…' : ''}${normalized.slice(start, end)}${end < normalized.length ? '…' : ''}`;
  };
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const term = input.value.trim().toLowerCase();
    results.replaceChildren();
    if (term.length < 2) { status.textContent = 'Enter at least two characters.'; return; }
    status.textContent = 'Searching documentation…';
    try {
      const pages = await loadIndex();
      const matches = pages.filter((page) => `${page.title} ${page.text}`.toLowerCase().includes(term)).slice(0, 8);
      status.textContent = matches.length ? `${matches.length} result${matches.length === 1 ? '' : 's'}.` : `No documentation found for “${input.value.trim()}”.`;
      matches.forEach((page) => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.href = page.url;
        link.textContent = page.title;
        const summary = document.createElement('p');
        summary.textContent = excerpt(page.text, term);
        item.append(link, summary);
        results.appendChild(item);
      });
    } catch (_) {
      status.textContent = 'Search is unavailable. Use the documentation navigation below.';
    }
  });
  form.querySelector('[data-search-clear]').addEventListener('click', () => {
    input.value = '';
    results.replaceChildren();
    status.textContent = 'Search page titles and documentation text.';
    input.focus();
  });
})();
