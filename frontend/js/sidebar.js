/* sidebar.js — Inyecta sidebar y envuelve el contenido en main-content */
(function() {
  const currentPage = location.pathname.split('/').pop() || 'index.html';
  if (currentPage !== 'login.html' && !sessionStorage.getItem('cloudarch_auth')) {
    window.location.href = 'login.html';
    return;
  }

  const id = new URLSearchParams(location.search).get('id');

  const links = [
    { section: 'General' },
    { href: 'index.html', icon: 'home', label: 'Dashboard' },
    { href: 'ingesta.html', icon: 'plus', label: 'Nueva Ingesta' },
    { href: 'listado.html', icon: 'list', label: 'Listado' },
    { section: 'Flujo de Trabajo' },
    { href: 'paso1-validacion.html', icon: 'check', label: '1. Validación', needsId: true },
    { href: 'paso2-servicios.html', icon: 'cloud', label: '2. Servicios', needsId: true },
    { href: 'paso3-costos.html', icon: 'dollar', label: '3. Costos', needsId: true },
    { href: 'paso4-propuesta.html', icon: 'doc', label: '4. Propuesta', needsId: true },
  ];

  const icons = {
    home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12l9-9 9 9M5 10v9a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-9"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>',
    list: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
    cloud: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z"/></svg>',
    dollar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
    doc: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
  };

  let nav = '';
  links.forEach(l => {
    if (l.section) {
      nav += `<div class="sidebar-section">${l.section}</div>`;
    } else {
      const active = currentPage === l.href ? ' active' : '';
      let href = l.href;
      if (l.needsId && id) href += '?id=' + id;
      const disabled = (l.needsId && !id) ? ' style="opacity:.35;pointer-events:none"' : '';
      nav += `<a class="sidebar-link${active}" href="${href}"${disabled}>${icons[l.icon]}<span>${l.label}</span></a>`;
    }
  });

  const sidebarHTML = `<aside class="sidebar">
    <div class="sidebar-logo"><div class="sidebar-logo-dots"><span></span><span></span><span></span></div><div class="sidebar-logo-text">CloudArch<sub>AI</sub></div></div>
    <nav class="sidebar-nav">${nav}</nav>
    <div class="sidebar-footer">Portal interno v1.0</div>
  </aside>`;

  const body = document.body;
  body.classList.add('has-sidebar');

  const wrapper = document.createElement('div');
  wrapper.className = 'main-content';
  while (body.firstChild) wrapper.appendChild(body.firstChild);
  body.appendChild(wrapper);
  body.insertAdjacentHTML('afterbegin', sidebarHTML);
})();
