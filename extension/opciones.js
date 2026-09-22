const campo = document.getElementById('api');
chrome.storage.sync.get('api').then(({api}) => {
  campo.value = api || 'http://localhost:8080';
});
document.getElementById('guardar').addEventListener('click', async () => {
  await chrome.storage.sync.set({api: campo.value.trim()});
  document.getElementById('dicho').textContent = 'Guardado.';
});
