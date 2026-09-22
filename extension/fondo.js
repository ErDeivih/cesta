/* El que habla con Cesta.
 *
 * La petición va aquí y no en el content script a propósito: desde un content
 * script, `fetch` sale con el origen de la página del supermercado y se lo come
 * CORS. Desde el service worker, con `host_permissions`, no hay CORS que valga.
 *
 * Y hay una razón más importante: así **carrefour.es nunca ve una petición a tu
 * Cesta**. La página no se entera de que la extensión existe. */

const POR_DEFECTO = 'http://localhost:8080';

async function base() {
  const {api} = await chrome.storage.sync.get('api');
  return (api || POR_DEFECTO).replace(/\/+$/, '');
}

chrome.runtime.onMessage.addListener((msg, _emisor, responde) => {
  if (msg?.tipo !== 'producto') return false;
  base().then(async raiz => {
    try {
      const r = await fetch(
        `${raiz}/api/producto/${encodeURIComponent(msg.cadena)}/${encodeURIComponent(msg.id)}`,
        {credentials: 'include'});
      if (r.status === 404) return responde({estado: 'no esta'});
      if (!r.ok) return responde({estado: 'error', codigo: r.status});
      responde({estado: 'ok', datos: await r.json()});
    } catch {
      /* Cesta corre en el ordenador de casa. Fuera de casa no se llega, y eso
         no es un fallo: es que no estás en casa. */
      responde({estado: 'sin cesta'});
    }
  });
  return true;           // la respuesta es asíncrona
});
