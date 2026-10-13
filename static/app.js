document.addEventListener('DOMContentLoaded', () => {
  const list = document.querySelector('#evidence-list');
  const add = document.querySelector('#add-evidence');
  if (!list || !add) return;
  add.addEventListener('click', () => {
    if (list.children.length >= 12) return;
    const row = list.firstElementChild.cloneNode(true);
    row.querySelector('input').value = '';
    list.appendChild(row);
  });
  list.addEventListener('click', (event) => {
    if (!event.target.classList.contains('remove')) return;
    if (list.children.length > 1) event.target.closest('.evidence-row').remove();
    else list.firstElementChild.querySelector('input').value = '';
  });
});
