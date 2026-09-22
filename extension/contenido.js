/* La curva de precios, encima de la web del supermercado.
 *
 * La idea es de `supermarket-tracker`, y es la mejor que le hemos copiado a
 * nadie: **el histórico sólo sirve en el momento de decidir**, y ese momento no
 * ocurre en nuestra aplicación, ocurre delante del producto en la web de la
 * cadena. Una pestaña más es una pestaña que no se abre.
 *
 * Lo único que hace falta sacar de la página es su identificador, y cada cadena
 * lo pone en su URL. Nada de leer el DOM del supermercado: un selector CSS
 * ajeno se rompe cada dos semanas y además haría que la extensión dependiera de
 * cómo pintan ellos su página. La URL es el único contrato estable que tienen.
 */

const DE_LA_URL = [
  // carrefour.es/supermercado/<slug>/R-521028123/p
  //
  // Ojo con el identificador de Carrefour: **no siempre es un numero**. De los
  // 16.560 productos del 21 de septiembre de 2026, 10.835 llevan uno de la
  // forma `VC4AECOMM-647163`. Con `\d+` la extension se quedaba muda en dos de
  // cada tres paginas de Carrefour, que es justo el tipo de fallo que no se ve
  // probando un producto a mano.
  {cadena: 'carrefour', patron: /\/R-([\w-]+)\/p/},
  // dia.es/<rama>/<hoja>/p/49608
  {cadena: 'dia', patron: /dia\.es\/.*\/p\/(\d+)/},
  // aldi.es/p/<slug>-279705
  {cadena: 'aldi', patron: /aldi\.es\/p\/.*?-(\d+)\/?$/},
  // tienda.mercadona.es/product/13294/<slug>
  {cadena: 'mercadona', patron: /mercadona\.es\/product\/(\d+)/},
  // compraonline.alcampo.es/products/181786
  //
  // Los digitos van anclados al final del segmento a proposito. Sin eso, la URL
  // vieja con UUID (`products/72bccb32-...`) casaba y devolvia "72": un
  // identificador inventado que habria pedido a Cesta un producto que no es.
  {cadena: 'alcampo', patron: /alcampo\.es\/products\/(\d+)(?:[/?#]|$)/},
];

function queProducto(url) {
  for (const {cadena, patron} of DE_LA_URL) {
    const m = url.match(patron);
    if (m) return {cadena, id: m[1]};
  }
  return null;
}

const eur = c => (c / 100).toLocaleString('es-ES', {
  minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' €';

const esc = s => String(s ?? '').replace(/[&<>"]/g,
  m => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[m]));

/* La curva. Sin librería: son catorce puntos y una línea.
 *
 * El eje no empieza en cero a propósito: con precios entre 0,89 y 1,12 un eje
 * desde cero dibuja una raya plana y esconde justo lo que se viene a mirar. Va
 * escrito en el pie para que nadie lea una subida del doble donde hay un 5 %. */
function curva(puntos) {
  if (puntos.length < 2) return '';
  const W = 260, H = 64, M = 4;
  const vs = puntos.map(p => p.precio_unidad_cent);
  let lo = Math.min(...vs), hi = Math.max(...vs);
  if (hi === lo) { hi += 1; lo -= 1; }
  const x = i => M + (i / (puntos.length - 1)) * (W - 2 * M);
  const y = v => M + (1 - (v - lo) / (hi - lo)) * (H - 2 * M);
  const d = puntos.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.precio_unidad_cent).toFixed(1)}`).join('');
  const ult = puntos[puntos.length - 1];
  return `<svg class="cesta-curva" viewBox="0 0 ${W} ${H}" aria-hidden="true">
    <path d="${d}" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${x(puntos.length - 1).toFixed(1)}"
            cy="${y(ult.precio_unidad_cent).toFixed(1)}" r="3" fill="currentColor"/>
  </svg>`;
}

function panel(datos) {
  const p = datos.producto, g = datos.grupo;
  const serie = (g && g.curva) || [];
  const otros = ((g && g.productos) || []).filter(x => x.fuente !== p.fuente);
  const masBarato = otros.length ? otros[0] : null;
  const ahorro = (masBarato && p.precio_unidad_cent)
    ? Math.round(100 * (p.precio_unidad_cent - masBarato.precio_unidad_cent)
                 / p.precio_unidad_cent) : 0;

  const caja = document.createElement('aside');
  caja.className = 'cesta-panel';
  caja.innerHTML = `
    <header>
      <span class="cesta-marca">Cesta</span>
      <button class="cesta-cerrar" aria-label="Cerrar">&times;</button>
    </header>
    <p class="cesta-precio">
      <b>${p.precio_unidad_cent ? eur(p.precio_unidad_cent) : '—'}</b>
      <span>/${esc(p.unidad_canon || 'ud')} aquí</span>
    </p>
    ${serie.length > 1 ? `${curva(serie)}
      <p class="cesta-pie">${serie.length} días · de ${eur(Math.min(...serie.map(s => s.precio_unidad_cent)))}
         a ${eur(Math.max(...serie.map(s => s.precio_unidad_cent)))}
         <span title="el eje no empieza en cero">(escala recortada)</span></p>`
      : '<p class="cesta-pie">Todavía sin histórico suficiente para la curva.</p>'}
    ${masBarato && ahorro > 0 ? `<p class="cesta-otro">
        Más barato en <b>${esc(masBarato.fuente)}</b>:
        ${eur(masBarato.precio_unidad_cent)}/${esc(masBarato.unidad_canon || 'ud')}
        <span class="cesta-ahorro">−${ahorro} %</span></p>`
      : (otros.length ? '<p class="cesta-otro">Aquí es donde está más barato.</p>' : '')}
    <p class="cesta-fecha">Datos del ${datos.fecha_datos.split('-').reverse().join('/')}</p>`;
  caja.querySelector('.cesta-cerrar').addEventListener('click', () => caja.remove());
  return caja;
}

function aviso(texto) {
  const caja = document.createElement('aside');
  caja.className = 'cesta-panel cesta-flojo';
  caja.textContent = texto;
  setTimeout(() => caja.remove(), 6000);
  return caja;
}

let puesto = null;

function pinta(nodo) {
  if (puesto) puesto.remove();
  puesto = nodo;
  document.body.appendChild(nodo);
}

function mira() {
  const que = queProducto(location.href);
  if (!que) { if (puesto) { puesto.remove(); puesto = null; } return; }
  chrome.runtime.sendMessage({tipo: 'producto', ...que}, r => {
    if (!r) return;
    if (r.estado === 'ok') return pinta(panel(r.datos));
    if (r.estado === 'no esta') return;      // no lo tenemos; no se molesta a nadie
    if (r.estado === 'sin cesta') return pinta(aviso('Cesta no responde: sólo funciona en casa.'));
  });
}

/* Las cinco tiendas son aplicaciones de una sola página: cambiar de producto no
   recarga nada, así que no basta con mirar al cargar. */
let ultima = location.href;
new MutationObserver(() => {
  if (location.href !== ultima) { ultima = location.href; mira(); }
}).observe(document, {subtree: true, childList: true});

mira();
