(() => {
  const tabs = [...document.querySelectorAll('[data-tab]')];
  const search = document.querySelector('#search');
  const searchStatus = document.querySelector('#search-status');
  function filterRows() {
    const query = search.value.toLocaleLowerCase().trim();
    let matches = 0;
    document.querySelectorAll('[data-search-row]').forEach(row => {
      row.hidden = Boolean(query) && !row.textContent.toLocaleLowerCase().includes(query);
      if (!row.hidden && !row.closest('[role="tabpanel"]').hidden) matches += 1;
    });
    searchStatus.textContent = query ? `${matches} matching table rows in this section` : '';
  }
  function activate(tab) {
    tabs.forEach(button => button.setAttribute('aria-selected', String(button === tab)));
    document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
      panel.hidden = panel.id !== tab.dataset.tab;
    });
    filterRows();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activate(tab));
    tab.addEventListener('keydown', event => {
      if (!['ArrowDown', 'ArrowUp', 'ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 :
        (index + (['ArrowDown', 'ArrowRight'].includes(event.key) ? 1 : -1) + tabs.length) % tabs.length;
      tabs[next].focus();
      activate(tabs[next]);
    });
  });
  search.addEventListener('input', filterRows);
})();
