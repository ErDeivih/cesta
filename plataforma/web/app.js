/* Cesta. El cliente.
 *
 * Solo guarda una cosa en el movil: la lista de la compra abierta. Son unos
 * pocos KB y es lo unico que hace falta mientras andas por los pasillos con el
 * PC de casa apagado. Todo lo demas se pide y se olvida.
 *
 * Lo que se hace sin cobertura se apunta en una cola y se sube al volver. Los
 * identificadores de linea los genera este fichero, no el servidor, para que un
 * producto anadido sin red conserve su identidad al subirlo.
 */
'use strict';

const API = '/api';
const CADENAS = ['alcampo', 'aldi', 'carrefour', 'dia', 'mercadona'];
const NOMBRE = {alcampo:'Alcampo', aldi:'Aldi', carrefour:'Carrefour', dia:'DIA', mercadona:'Mercadona'};

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const eur = c => (c/100).toLocaleString('es-ES',{minimumFractionDigits:2,maximumFractionDigits:2}) + ' €';
/* "1 cadenas · 1 productos" es lo que ve alguien que abre la app por primera
   vez, y le dice que esto esta a medias. */
const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
const esc = s => String(s ?? '').replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));

/* ---------------------------------------------------------------- estado -- */
const estado = {
  yo: null, vista: 'buscar', listaId: null, listaNombre: '', papel: 'escribe',
  lineas: [], cadenas: new Set(CADENAS), fechaDatos: null, enLinea: true,
  estimacion: null, personas: [], novedades: [], enCesta: new Set(),
  sellos: new Set(), conservacion: null, marcaPropia: false, ofertas: false,
  sinAlcohol: false,
  seccion: null,        // el pasillo que se esta mirando, si hay alguno
  panel: 'resumen',     // resumen | bajadas | dudosas
};

/* --------------------------------------------------------- guardar local -- */
/* Envuelto en try: en una ventana privada o con el almacenamiento bloqueado,
   acceder a localStorage lanza. La app tiene que funcionar igual. */
const local = {
  lee(clave, siFalla = null) {
    try { const v = localStorage.getItem('cesta.' + clave); return v ? JSON.parse(v) : siFalla; }
    catch { return siFalla; }
  },
  guarda(clave, valor) {
    try { localStorage.setItem('cesta.' + clave, JSON.stringify(valor)); } catch {}
  },
};

/* ------------------------------------------------------------------- red -- */
async function pide(ruta, opciones = {}) {
  const r = await fetch(API + ruta, {
    credentials: 'include',
    headers: opciones.cuerpo ? {'Content-Type': 'application/json'} : {},
    method: opciones.metodo || 'GET',
    body: opciones.cuerpo ? JSON.stringify(opciones.cuerpo) : undefined,
  });
  if (r.status === 401) { estado.yo = null; pintaEntrar(); throw new Error('sin sesion'); }
  if (!r.ok) throw new Error(await r.text().catch(() => r.statusText));
  estado.enLinea = true;
  return r.json();
}

/* La cola de lo que se hizo sin cobertura. */
const cola = {
  todo: () => local.lee('cola', []),
  anade(cambio) {
    const c = cola.todo(); c.push(cambio); local.guarda('cola', c);
  },
  async sube() {
    const pendientes = cola.todo();
    if (!pendientes.length || !estado.listaId) return 0;
    try {
      const r = await pide(`/listas/${estado.listaId}/sincronizar`, {metodo:'POST', cuerpo: pendientes});
      local.guarda('cola', []);
      estado.lineas = r.lineas;
      local.guarda('lineas.' + estado.listaId, r.lineas);
      return r.aplicados;
    } catch { return 0; }
  },
};

function flota(texto, ms = 2600) {
  $$('.aviso-flota').forEach(n => n.remove());
  const d = document.createElement('div');
  d.className = 'aviso-flota'; d.textContent = texto; d.setAttribute('role','status');
  document.body.appendChild(d);
  setTimeout(() => d.remove(), ms);
}

/* ---------------------------------------------------------------- entrar -- */
function pintaEntrar() {
  $('#v-entrar').hidden = false;
  $('#app').hidden = true;
}

/* El porqué de la queja, tal y como lo ha escrito la API.
 *
 * `pide` lanza el cuerpo crudo de la respuesta, que en FastAPI es
 * {"detail":"..."}. Esa frase está escrita para leerla una persona -- "ese
 * usuario ya está cogido", "la contraseña necesita al menos ocho caracteres" --
 * y tirarla para poner en su lugar un "ha habido un error" genérico es perder
 * justo lo que hace falta para arreglarlo. */
function motivo(err, siFalla) {
  try {
    const d = JSON.parse(err.message)?.detail;
    if (typeof d === 'string' && d.trim()) return d;
  } catch {}
  return siFalla;
}

/* Entrar y crear cuenta son la misma pantalla con dos formularios. Quien llega
   con un enlace de invitación casi nunca tiene cuenta, así que el camino de
   crearla tiene que estar a un toque y no escondido. */
function modoEntrar(registrando) {
  $('#f-entrar').hidden = registrando;
  $('#f-registro').hidden = !registrando;
  $('#e-entrar').hidden = true;
  $('#e-registro').hidden = true;
  $('#entrar-sub').textContent = registrando
    ? 'Crea tu cuenta. Los datos se quedan en este ordenador.'
    : 'Los precios de cinco supermercados, en casa.';
  (registrando ? $('#r-nombre') : $('#i-usuario')).focus();
}

$('#b-a-registro').addEventListener('click', () => modoEntrar(true));
$('#b-a-entrar').addEventListener('click', () => modoEntrar(false));

$('#f-registro').addEventListener('submit', async ev => {
  ev.preventDefault();
  const err = $('#e-registro');
  const boton = ev.target.querySelector('button[type=submit]');
  err.hidden = true;
  boton.disabled = true;
  try {
    const r = await pide('/registrarse', {metodo:'POST', cuerpo:{
      usuario: $('#r-usuario').value, nombre: $('#r-nombre').value,
      clave: $('#r-clave').value,
      dispositivo: navigator.userAgent.slice(0, 80),
    }});
    estado.yo = r.usuario;
    $('#r-clave').value = '';
    /* Se registra y entra en el mismo paso: el que llega aquí casi siempre
       viene de un enlace de lista, y la invitación sólo se aplica con sesión. */
    await aplicaInvitacion();
    arranca();
  } catch (e) {
    err.textContent = motivo(e, 'No se pudo crear la cuenta. Inténtalo otra vez.');
    err.hidden = false;
  } finally {
    boton.disabled = false;
  }
});

$('#f-entrar').addEventListener('submit', async ev => {
  ev.preventDefault();
  const err = $('#e-entrar');
  err.hidden = true;
  try {
    const r = await pide('/entrar', {metodo:'POST', cuerpo:{
      usuario: $('#i-usuario').value, clave: $('#i-clave').value,
      dispositivo: navigator.userAgent.slice(0, 80),
    }});
    estado.yo = r.usuario;
    $('#i-clave').value = '';
    await aplicaInvitacion();
    arranca();
  } catch (e) {
    err.textContent = motivo(e, 'Usuario o contraseña incorrectos.');
    err.hidden = false;
  }
});

/* ---------------------------------------------------------------- buscar -- */
let temporizador;
document.addEventListener('keydown', ev => {
  if (ev.key !== 'Enter' && ev.key !== ' ') return;
  const f = ev.target.closest?.('[data-ficha]');
  if (f) { ev.preventDefault(); abreFicha(f.dataset.ficha); }
});

$('#q').addEventListener('input', () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(busca, 220);
});

function pintaChips() {
  $('#chips-cadenas').innerHTML = CADENAS.map(c =>
    `<button class="chip cad ${c}" data-cadena="${c}" aria-pressed="${estado.cadenas.has(c)}">${NOMBRE[c]}</button>`
  ).join('');
  pintaFiltros();
}

/* Los sellos que se pueden filtrar, con el nombre que usa la gente y no el que
   usa la base de datos. El orden es el de cuánta gente los busca, no el
   alfabético: quien filtra por dieta suele hacerlo por gluten o lactosa. */
const SELLOS = [
  ['sin-gluten', 'Sin gluten'], ['sin-lactosa', 'Sin lactosa'],
  ['vegano', 'Vegano'], ['vegetariano', 'Vegetariano'],
  ['ecologico', 'Ecológico'], ['sin-azucar', 'Sin azúcar'],
  ['sin-sal', 'Sin sal'], ['sin-aceite-palma', 'Sin aceite de palma'],
];
const CONSERVACIONES = [
  ['refrigerado', 'Refrigerado'], ['congelado', 'Congelado'], ['ambiente', 'De despensa'],
];

function pintaFiltros() {
  $('#chips-sellos').innerHTML = SELLOS.map(([id, txt]) =>
    `<button class="chip" data-sello="${id}" aria-pressed="${estado.sellos.has(id)}">${txt}</button>`
  ).join('');
  $('#chips-otros').innerHTML = [
    ...CONSERVACIONES.map(([id, txt]) =>
      `<button class="chip" data-conserv="${id}" aria-pressed="${estado.conservacion === id}">${txt}</button>`),
    `<button class="chip" data-otro="marcaPropia" aria-pressed="${estado.marcaPropia}">Marca blanca</button>`,
    `<button class="chip" data-otro="ofertas" aria-pressed="${estado.ofertas}">En oferta</button>`,
    `<button class="chip" data-otro="sinAlcohol" aria-pressed="${estado.sinAlcohol}">Sin alcohol</button>`,
  ].join('');
  /* El contador en el resumen es lo que evita el peor fallo de un filtro
     plegado: buscar, no encontrar nada y no entender por qué. */
  const n = estado.sellos.size + (estado.conservacion ? 1 : 0)
          + (estado.marcaPropia ? 1 : 0) + (estado.ofertas ? 1 : 0)
          + (estado.sinAlcohol ? 1 : 0);
  const cuenta = $('#filtros-cuenta');
  cuenta.textContent = n ? ` ${n}` : '';
  cuenta.hidden = !n;
}

/* Un clic en cualquier filtro: se apunta y se vuelve a buscar. */
document.addEventListener('click', ev => {
  if (ev.target.id === 'quita-filtros') {
    estado.sellos.clear();
    estado.conservacion = null;
    estado.marcaPropia = estado.ofertas = estado.sinAlcohol = false;
    pintaFiltros();
    busca();
    return;
  }
  const c = ev.target.closest('#chips-sellos .chip, #chips-otros .chip');
  if (!c) return;
  if (c.dataset.sello) {
    estado.sellos.has(c.dataset.sello)
      ? estado.sellos.delete(c.dataset.sello) : estado.sellos.add(c.dataset.sello);
  } else if (c.dataset.conserv) {
    estado.conservacion = estado.conservacion === c.dataset.conserv ? null : c.dataset.conserv;
  } else if (c.dataset.otro) {
    estado[c.dataset.otro] = !estado[c.dataset.otro];
  }
  pintaFiltros();
  busca();
});

/* Un buscador vacio no enseña que se puede buscar. Tres ejemplos pulsables sí,
   y de paso demuestran que el catálogo es de verdad. Es lo primero que ve
   alguien que abre la app por primera vez. */
const EJEMPLOS = ['leche entera', 'papel de cocina', 'atún en aceite'];

/* ------------------------------------------------------ explorar pasillos --
   La pantalla de buscar estaba vacía hasta que escribías algo, y para escribir
   algo hay que saber ya lo que quieres. Los pasillos son la otra forma de
   entrar: la de quien no busca nada concreto y quiere ver qué hay.

   Van en el orden del recorrido de la tienda, no en alfabético, que es como se
   recorre un supermercado de verdad. */
let pasillos = null;          // se pide una vez y se guarda

async function cargaPasillos() {
  if (pasillos) return pasillos;
  try {
    const r = await pide(`/secciones?cadenas=${[...estado.cadenas].join(',')}`);
    pasillos = r.secciones || [];
  } catch { pasillos = []; }
  return pasillos;
}

function pintaPasillos(lista) {
  if (!lista.length) return '';
  return `<div class="pasillos">${lista.map(s => `
    <button class="pasillo" data-seccion="${esc(s.seccion)}">
      <span class="pn">${esc(s.nombre)}</span>
      <span class="pc"><span class="num">${s.productos.toLocaleString('es-ES')}</span> productos</span>
      ${s.comparable ? '' : '<span class="pu">una sola cadena</span>'}
    </button>`).join('')}</div>`;
}

async function pintaEjemplos() {
  const caja = $('#resultados');
  caja.innerHTML = `<div class="vacio" style="text-align:left">
    <p style="margin:0 0 12px">Busca lo que compras. Por ejemplo:</p>
    <div class="chips">${EJEMPLOS.map(e =>
      `<button class="chip" data-ejemplo="${esc(e)}">${esc(e)}</button>`).join('')}</div>
  </div>`;
  const lista = await cargaPasillos();
  if (!lista.length || $('#q').value.trim().length >= 2) return;
  caja.insertAdjacentHTML('beforeend', `
    <h2 class="titulillo">O mira pasillo por pasillo</h2>
    ${pintaPasillos(lista)}`);
}

async function busca() {
  const q = $('#q').value.trim();
  const caja = $('#resultados');
  /* Un pasillo es una búsqueda por sí mismo: "enséñame lo que hay en
     congelados" no necesita que escribas nada. */
  if (q.length < 2 && !estado.seccion) { pintaEjemplos(); return; }
  caja.innerHTML = '<div class="cargando">Buscando…</div>';
  try {
    const cadenas = [...estado.cadenas].join(',');
    const extra = [];
    if (estado.seccion) extra.push(`seccion=${encodeURIComponent(estado.seccion)}`);
    if (estado.sellos.size) extra.push(`sellos=${[...estado.sellos].join(',')}`);
    if (estado.conservacion) extra.push(`conservacion=${estado.conservacion}`);
    if (estado.marcaPropia) extra.push('marca_propia=true');
    if (estado.ofertas) extra.push('ofertas=true');
    if (estado.sinAlcohol) extra.push('sin_alcohol=true');
    const r = await pide(`/buscar?q=${encodeURIComponent(q)}&cadenas=${cadenas}&limite=40`
                         + (extra.length ? '&' + extra.join('&') : ''));
    estado.fechaDatos = r.fecha_datos;
    if (!r.resultados.length) {
      /* Si hay filtros puestos, casi siempre son ellos y no la palabra. Decirlo,
         y dar el botón para quitarlos: si no, el filtro plegado es una trampa. */
      const conFiltros = estado.sellos.size || estado.conservacion
                       || estado.marcaPropia || estado.ofertas || estado.sinAlcohol;
      /* Sin texto, el mensaje no puede hablar de la palabra buscada: decía
         literalmente «Nada con «».» al entrar en un pasillo vacío. */
      const que = q ? `«${esc(q)}»` : 'este pasillo';
      caja.innerHTML = cabeceraPasillo() + (conFiltros
        ? `<div class="vacio">Nada en ${que} con los filtros puestos.<br>
             <button class="chip" id="quita-filtros">Quitar los filtros</button></div>`
        : q
        ? `<div class="vacio">Nada con ${que}.<br>Prueba con una palabra más corta,
             o vuelve a activar alguna cadena.</div>`
        : `<div class="vacio">Este pasillo está vacío en las cadenas que miras.<br>
             Prueba a activar alguna más.</div>`);
      return;
    }
    caja.innerHTML = cabeceraPasillo() + r.resultados.map(tarjetaResultado).join('');
  } catch {
    caja.innerHTML = `<div class="vacio">No llego a casa ahora mismo.<br>
      Tu lista sigue disponible en la pestaña Lista.</div>`;
  }
}

function cabeceraPasillo() {
  if (!estado.seccion) return '';
  const s = (pasillos || []).find(p => p.seccion === estado.seccion);
  const nombre = s ? s.nombre : estado.seccion;
  return `<div class="enpasillo">
    <span>Pasillo: <b>${esc(nombre)}</b></span>
    <button class="chip" id="sal-pasillo">Salir del pasillo</button>
  </div>`;
}

function tarjetaResultado(x) {
  const trozos = [];
  if (x.comparable) trozos.push(plural(x.cadenas, 'cadena', 'cadenas'));
  /* Un ahorro de más de 30x no es una oferta, es un error nuestro: el azafrán
     que Alcampo etiqueta "400g" cuando son 400 mg, o un champán comparado por
     botella contra el mismo por unidad. Decirlo es mejor que gritar un ahorro
     falso; un «ahorra un 102.896 %» en pantalla se carga la confianza de golpe. */
  if (x.dudoso) trozos.push('precios que no cuadran entre cadenas');
  else if (x.comparable && x.ahorro_pct > 0) trozos.push(`hasta ${x.ahorro_pct} % de diferencia`);
  if (!x.comparable) trozos.push('solo en una cadena');
  if (x.con_oferta) trozos.push('con oferta');
  /* Una oferta de tarjeta no baja lo que pagas en caja: se acumula en un
     monedero. 200 de las 221 ofertas de DIA son de ese tipo, y llamarlas
     "oferta" a secas sería anunciar una rebaja que no está en el ticket. */
  else if (x.con_oferta_club) trozos.push('oferta solo con tarjeta');
  if (x.con_retirada) trozos.push('⚠ lote retirado');
  const puesto = x.grupo_id && estado.enCesta.has(String(x.grupo_id));
  /* La foto ayuda más que cualquier texto cuando buscas algo que conoces de
     verlo en la estantería. Se carga perezosa: en una búsqueda hay cuarenta. */
  const foto = x.imagen
    ? `<img class="mini" src="${esc(x.imagen)}" alt="" loading="lazy" decoding="async">`
    : '<span class="sinmini"></span>';
  return `<article class="tarjeta">
    <button class="cab" data-grupo="${x.grupo_id ?? ''}" aria-expanded="false">
      ${foto}
      <span>
        <span class="tit">${esc(x.nombre)}</span>
        <span class="meta">${trozos.join(' · ')}</span>
      </span>
      <span class="der">
        <span class="precio num">${eur(x.precio_cent)}</span>
        <span class="unit num">${eur(x.precio_unidad_cent)}/${x.unidad || 'ud'}</span>
      </span>
    </button>
    <div class="cuerpo" hidden></div>
  </article>`;
}

/* ------------------------------------------------------- ficha del grupo -- */
async function abreGrupo(boton, grupoId) {
  const cuerpo = boton.nextElementSibling;
  const abierto = boton.getAttribute('aria-expanded') === 'true';
  boton.setAttribute('aria-expanded', abierto ? 'false' : 'true');
  cuerpo.hidden = abierto;
  if (abierto || cuerpo.dataset.cargado) return;
  cuerpo.innerHTML = '<div class="cargando">Cargando…</div>';
  try {
    const g = await pide(`/grupo/${grupoId}`);
    g.productos.forEach(p => { fichas[p.producto_id] = p; });
    const mn = g.productos[0].precio_unidad_cent;
    const mx = g.productos[g.productos.length - 1].precio_unidad_cent;
    cuerpo.innerHTML = g.productos.map(p => filaProducto(p, mn, mx)).join('') + `
      <div class="acciones">
        <button class="bt principal" data-anadir="${g.grupo_id}"
                data-nombre="${esc(g.nombre)}" data-imagen="${esc(g.imagen || '')}"
                data-precio="${g.productos[0].precio_cent}">
          ${estado.enCesta.has(String(g.grupo_id)) ? 'Añadir otra vez' : 'Añadir a la lista'}</button>
        <button class="bt" data-favorito="${g.grupo_id}">Seguir</button>
        <button class="bt" data-avisar="${g.grupo_id}"
                data-precio-ud="${g.productos[0].precio_unidad_cent}"
                data-unidad="${esc(g.productos[0].unidad || 'ud')}">Avisarme</button>
      </div>
      <div class="avisos-de" hidden></div>`;
    cuerpo.dataset.cargado = '1';
  } catch {
    cuerpo.innerHTML = '<div class="cargando">No he podido cargarlo.</div>';
  }
}

function filaProducto(p, mn, mx) {
  const ancho = mx > mn ? Math.max(4, 100 * (p.precio_unidad_cent - mn) / (mx - mn)) : 100;
  const sellos = [];
  if (p.nutriscore) sellos.push(`<span class="sello ${p.nutriscore}" title="Nutri-Score">${p.nutriscore.toUpperCase()}</span>`);
  /* La letra solo se llama calidad si sale de leer una etiqueta. Si sale de
     ordenar por precio es gama, y se dice, porque mezclarlas hace creer que lo
     barato es peor. */
  if (p.calidad) sellos.push(`<span class="sello" title="Leída de los ingredientes">calidad ${p.calidad}</span>`);
  else if (p.gama) sellos.push(`<span class="sello suave" title="Sale de ordenar por precio, no de la etiqueta">gama ${p.gama}</span>`);
  if (!p.comparable) sellos.push(`<span class="sello suave" title="Su unidad no se compara entre cadenas">no comparable</span>`);
  if (p.promo) sellos.push(`<span class="sello oferta" title="${esc(p.promo)}">oferta</span>`);
  const mini = p.imagen
    ? `<img class="minip" src="${esc(p.imagen)}" alt="" loading="lazy" decoding="async">`
    : '<span class="minip"></span>';
  return `<div class="prod" data-ficha="${esc(p.producto_id)}" role="button" tabindex="0">
    <span class="cadena ${p.fuente}">${NOMBRE[p.fuente]}</span>
    ${mini}
    <span>
      <span class="n">${esc(p.nombre)}${sellos.join('')}</span>
      <span class="f">${p.marca ? esc(p.marca) + ' · ' : ''}${p.cantidad ?? ''} ${p.unidad ?? ''}</span>
    </span>
    <span class="p num"><b>${eur(p.precio_cent)}</b><span>${eur(p.precio_unidad_cent)}/${p.unidad || 'ud'}</span></span>
    <span class="barra"><i style="width:${ancho}%;background:var(--${p.fuente})"></i></span>
  </div>`;
}

/* ----------------------------------------------------------------- lista -- */
async function cargaListas() {
  try {
    const r = await pide('/listas');
    let casa = r.listas.find(l => l.es_de_casa) || r.listas[0];
    if (!casa) casa = await pide('/listas', {metodo:'POST', cuerpo:{nombre:'Casa', es_de_casa:true}});
    estado.listaId = casa.id;
    estado.listaNombre = casa.nombre;
    local.guarda('listaId', casa.id);
    await cargaLineas();
  } catch {
    /* Sin conexion: se tira de lo ultimo que se vio. Es justo el caso del
       supermercado con el PC de casa apagado. */
    estado.listaId = local.lee('listaId');
    estado.lineas = local.lee('lineas.' + estado.listaId, []);
    estado.enLinea = false;
    pintaLista();
  }
}

async function cargaLineas() {
  await cola.sube();
  try {
    const r = await pide(`/listas/${estado.listaId}`);
    estado.lineas = r.lineas;
    estado.papel = r.papel;
    estado.estimacion = r.estimacion;
    estado.personas = r.personas || [];
    estado.novedades = r.novedades || [];
    estado.fechaDatos = r.fecha_datos;
    local.guarda('lineas.' + estado.listaId, r.lineas);
    local.guarda('estimacion.' + estado.listaId, r.estimacion);
    estado.enLinea = true;
  } catch {
    estado.lineas = local.lee('lineas.' + estado.listaId, []);
    estado.estimacion = local.lee('estimacion.' + estado.listaId, null);
    estado.enLinea = false;
  }
  refrescaCesta();
  pintaLista();
}

/* Qué grupos están ya en la lista, para marcarlos en la búsqueda: añadir dos
   veces lo mismo es el error más fácil de cometer en el pasillo. */
function refrescaCesta() {
  estado.enCesta = new Set(estado.lineas
    .filter(l => !l.borrado_en && l.grupo_id != null)
    .map(l => String(l.grupo_id)));
}

function enCarro(l) { return !!(l.en_carrito || l.tachado_en); }

function pintaLista() {
  const vivas = estado.lineas.filter(l => !l.borrado_en);
  const carro = vivas.filter(enCarro);
  const faltan = vivas.filter(l => !enCarro(l));

  $('#lista-nombre').textContent = estado.listaNombre || 'Lista';
  $('#lista-meta').textContent = vivas.length
    ? `${faltan.length} por coger · ${carro.length} en el carro` : '';
  const pin = $('#pin-lista');
  pin.hidden = faltan.length === 0;
  pin.textContent = faltan.length;

  /* Avisos: primero lo que impide fiarse de lo que se ve. */
  const avisos = [];
  if (!estado.enLinea) avisos.push(
    `<div class="tira rojo">No llego al ordenador donde viven los datos.
     Esto es lo último que vi; lo que cambies se guardará y se subirá cuando
     vuelva.</div>`);
  const pendientes = cola.todo().length;
  if (pendientes) avisos.push(
    `<div class="tira">${plural(pendientes, 'cambio', 'cambios')} por subir.</div>`);
  if (estado.novedades.length) avisos.push(`<div class="tira">
    ${estado.novedades.slice(0, 3).map(n => n.tachado_por && n.en_carrito
      ? `<b>${esc(n.tachado_por)}</b> cogió ${esc(n.nombre_visto)}`
      : `<b>${esc(n.anadido_por)}</b> puso ${esc(n.nombre_visto)}`).join(' · ')}
    ${estado.novedades.length > 3
      ? ` y ${plural(estado.novedades.length - 3, 'cosa más', 'cosas más')}` : ''}</div>`);
  $('#lista-avisos').innerHTML = avisos.join('');

  pintaMarcador(vivas, carro);

  if (!vivas.length) {
    $('#lista-lineas').innerHTML = `<div class="vacio">La lista está vacía.<br>
      Busca algo y pulsa el <b>+</b> para ponerlo aquí.</div>`;
    return;
  }
  let html = '';
  if (faltan.length) {
    html += `<div class="seccion"><h2>Por coger</h2>
      <span class="cuenta2">${faltan.length}</span></div>` + faltan.map(lineaHTML).join('');
  }
  if (carro.length) {
    html += `<div class="seccion"><h2>En el carro</h2>
      <span class="cuenta2">${carro.length}</span></div>` + carro.map(lineaHTML).join('');
  }
  $('#lista-lineas').innerHTML = html;
}

/* El número que se mira mientras se añaden cosas. No es "dónde la compro":
   ese cálculo pide elegir tienda. Esto es lo que cuesta cogiendo cada cosa
   donde esté más barata, y tiene que salir siempre y rápido. */
function pintaMarcador(vivas, carro) {
  const e = estado.estimacion;
  if (!vivas.length || !e) { $('#marcador').innerHTML = ''; return; }
  const pct = e.total_cent ? Math.round(100 * e.en_carrito_cent / e.total_cent) : 0;
  $('#marcador').innerHTML = `<div class="marcador" role="status" aria-live="polite">
    <span class="izq">
      <span class="q">Va a costar</span>
      <span class="v num">${eur(e.total_cent)}</span>
      <span class="aprox">aproximado, cogiendo cada cosa donde esté más barata</span>
    </span>
    <span class="der2">
      <b class="num">${eur(e.en_carrito_cent)}</b> en el carro<br>
      <span class="num">${eur(e.por_recoger_cent)}</span> por coger
      ${e.sin_precio ? `<br><span style="color:var(--ambar)">${e.sin_precio} sin precio</span>` : ''}
    </span>
    <span class="progreso"><i style="width:${pct}%"></i></span>
    <span class="letra-chica">Precios orientativos${estado.fechaDatos
      ? ' del ' + estado.fechaDatos.split('-').reverse().slice(0,2).join('/') : ''}.
      Pueden variar en tienda.</span>
  </div>`;
}

function lineaHTML(l) {
  const dentro = enCarro(l);
  const quien = [];
  if (dentro && l.tachado_por) quien.push(`lo cogió ${esc(l.tachado_por)}`);
  else if (l.anadido_por) quien.push(`lo puso ${esc(l.anadido_por)}`);
  if (l.nota) quien.push(esc(l.nota));
  const foto = l.imagen
    ? `<img class="foto" src="${esc(l.imagen)}" alt="" loading="lazy" decoding="async">`
    : '<span class="sinfoto"></span>';
  const precio = l.precio_cent
    ? `<span class="precio-l num">${eur(l.precio_cent * l.cantidad)}
         <small>${eur(l.precio_cent)} c/u</small></span>` : '';
  return `<div class="linea ${dentro ? 'en-carro' : ''}" data-linea="${l.id}">
    <button class="marca-check" data-carro="${l.id}"
            aria-label="${dentro ? 'Sacar del carro' : 'Meter en el carro'}: ${esc(l.nombre_visto)}"
            aria-pressed="${dentro}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#fff"
           stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
           style="opacity:${dentro ? 1 : 0}"><path d="m5 13 4 4L19 7"/></svg>
    </button>
    ${foto}
    <span>
      <span class="lt">${esc(l.nombre_visto)}</span>
      <span class="lm">${quien.join(' · ')}</span>
      <span class="cant" style="margin-top:5px">
        <button data-cantidad="${l.id}" data-delta="-1" aria-label="Menos">−</button>
        <span class="num">${l.cantidad}</span>
        <button data-cantidad="${l.id}" data-delta="1" aria-label="Más">+</button>
      </span>
    </span>
    ${precio}
  </div>`;
}

function uuid() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

async function anade(grupoId, nombre, extra = {}) {
  const linea = {id: uuid(), nombre, grupo_id: Number(grupoId), cantidad: 1};
  /* Se pinta ya, sin esperar al servidor: en el pasillo, un botón que tarda
     dos segundos se pulsa tres veces. La foto y el precio se guardan con la
     línea para que la lista siga siendo legible sin conexión. */
  estado.lineas.push({...linea, nombre_visto: nombre, anadido_por: estado.yo?.nombre,
                      tachado_en: null, borrado_en: null, en_carrito: false,
                      imagen: extra.imagen || null, precio_cent: extra.precio_cent || null});
  refrescaCesta();
  recalculaLocal();
  local.guarda('lineas.' + estado.listaId, estado.lineas);
  pintaLista();
  flota(`Añadido: ${nombre}`);
  try {
    await pide(`/listas/${estado.listaId}/lineas`, {metodo:'POST', cuerpo: linea});
  } catch {
    cola.anade({tipo:'anadir', ...linea});
    estado.enLinea = false;
    pintaLista();
  }
}

async function cambia(lineaId, cambio) {
  const l = estado.lineas.find(x => x.id === lineaId);
  if (!l) return;
  const momento = new Date().toISOString();
  if (cambio.en_carrito !== undefined) {
    l.en_carrito = cambio.en_carrito;
    l.tachado_en = cambio.en_carrito ? momento : null;
    l.tachado_por = cambio.en_carrito ? estado.yo?.nombre : null;
  }
  if (cambio.tachado !== undefined) {
    l.tachado_en = cambio.tachado ? momento : null;
    l.en_carrito = cambio.tachado;
    l.tachado_por = cambio.tachado ? estado.yo?.nombre : null;
  }
  if (cambio.cantidad !== undefined) l.cantidad = cambio.cantidad;
  local.guarda('lineas.' + estado.listaId, estado.lineas);
  recalculaLocal();
  pintaLista();
  try {
    await pide(`/listas/${estado.listaId}/lineas/${lineaId}`, {
      metodo:'PATCH', cuerpo: {...cambio, momento}});
  } catch {
    cola.anade({tipo:'cambio', id: lineaId, ...cambio, momento});
    estado.enLinea = false;
    pintaLista();
  }
}

/* El total se recalcula aquí mismo al tocar algo: esperar al servidor para ver
   cambiar un número hace que la app parezca rota en una red mala. El servidor
   lo corrige en la siguiente carga si hiciera falta. */
function recalculaLocal() {
  const vivas = estado.lineas.filter(l => !l.borrado_en);
  let total = 0, carro = 0, sin = 0;
  for (const l of vivas) {
    if (!l.precio_cent) { sin++; continue; }
    const c = l.precio_cent * l.cantidad;
    total += c;
    if (enCarro(l)) carro += c;
  }
  estado.estimacion = {total_cent: total, en_carrito_cent: carro,
                       por_recoger_cent: total - carro, lineas: vivas.length,
                       sin_precio: sin};
  local.guarda('estimacion.' + estado.listaId, estado.estimacion);
}

/* ---------------------------------------------------------- donde comprar -- */
$('#b-donde').addEventListener('click', async () => {
  const caja = $('#donde');
  caja.innerHTML = '<div class="cargando">Calculando…</div>';
  try {
    const max = local.lee('reparto', true) ? 2 : 1;
    const r = await pide(`/listas/${estado.listaId}/donde?max_tiendas=${max}`);
    caja.innerHTML = pintaDonde(r);
  } catch {
    caja.innerHTML = `<div class="vacio">Esto necesita llegar al ordenador donde
      viven los datos, y ahora mismo no llego.</div>`;
  }
});

function pintaDonde(r) {
  if (!r.una_tienda.length) return '<div class="vacio">Nada que calcular todavía.</div>';
  const completas = r.una_tienda.filter(t => !t.faltan.length);
  const mejorUna = completas[0]?.total_cent;
  let html = '<h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--tinta-3);margin:22px 0 10px">Todo en una tienda</h2>';
  html += r.una_tienda.map(t => {
    const ofertas = t.total_sin_ofertas_cent - t.total_cent;
    const esMejor = t.total_cent === mejorUna && !t.faltan.length;
    return `<div class="opcion ${esMejor ? 'mejor' : ''}">
      <div class="fila"><span class="cn">${NOMBRE[t.cadena]}</span>
        <span class="tot num">${eur(t.total_cent)}</span></div>
      ${t.faltan.length
        ? `<div class="det falta">no encuentro: ${t.faltan.map(esc).join(', ')}</div>`
        : `<div class="det">tiene ${plural(t.encontrados, 'el único producto',
                                            'los ' + t.encontrados)}</div>`}
      ${ofertas > 0 ? `<div class="ahorro">las ofertas te quitan ${eur(ofertas)}</div>` : ''}
    </div>`;
  }).join('');

  const rep = r.repartido;
  if (rep && rep.merece_la_pena) {
    html += '<h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--tinta-3);margin:22px 0 10px">Repartido</h2>';
    const detalle = Object.entries(rep.reparto)
      .map(([c, n]) => `${n} en ${NOMBRE[c]}`).join(', ');
    html += `<div class="opcion mejor">
      <div class="fila"><span class="cn">${rep.cadenas.map(c => NOMBRE[c]).join(' + ')}</span>
        <span class="tot num">${eur(rep.total_cent)}</span></div>
      <div class="det">${detalle}</div>
      <div class="ahorro">ahorras ${eur(rep.ahorro_cent)} yendo a dos sitios</div>
    </div>`;
  } else if (rep) {
    html += `<div class="tira">Repartir entre dos tiendas solo ahorra
      ${eur(Math.max(0, rep.ahorro_cent || 0))}. No compensa el viaje.</div>`;
  }
  return html;
}

/* ------------------------------------------------------------- favoritos -- */
async function cargaFavoritos() {
  const caja = $('#favoritos');
  caja.innerHTML = '<div class="cargando">Cargando…</div>';
  try {
    /* Los avisos que han saltado van arriba del todo: es lo único de esta
       pantalla que te estaba esperando a ti. */
    const [r, av] = await Promise.all([
      pide('/favoritos'),
      pide('/alertas').catch(() => ({alertas: [], saltan: []})),
    ]);
    const cabecera = pintaSaltan(av.saltan || []);
    caja.innerHTML = cabecera + (r.favoritos.length ? r.favoritos.map(f => `
      <article class="tarjeta"><button class="cab" data-grupo="${f.grupo_id ?? ''}" aria-expanded="false">
        <span><span class="tit">${esc(f.nombre)}</span>
          <span class="meta">más barato en ${NOMBRE[f.cadena] || f.cadena}</span></span>
        <span class="der"><span class="precio num">${eur(f.precio_unidad_cent)}</span>
          <span class="unit num">por ${f.unidad || 'ud'}</span></span>
      </button><div class="cuerpo" hidden></div></article>`).join('')
      : (cabecera ? '' : `<div class="vacio">Todavía no sigues nada.<br>
         Busca un producto, ábrelo y pulsa «Seguir».</div>`))
      + pintaMisAvisos(av.alertas || []);
  } catch {
    caja.innerHTML = `<div class="vacio">Esto necesita llegar al ordenador donde
      viven los datos, y ahora mismo no llego.</div>`;
  }
}

/* ----------------------------------------------------------------- panel -- */
const SUBPANELES = [
  ['resumen',  'Resumen'],
  ['indice',   'Índice'],
  ['posicion', 'Posición'],
  ['movs',     'Movimientos'],
  ['dudosas',  'Ofertas'],
];

function pestanasPanel() {
  return `<div class="subtabs" role="tablist">${SUBPANELES.map(([k, n]) =>
    `<button role="tab" class="subtab${estado.panel === k ? ' activa' : ''}"
             data-panel="${k}" aria-selected="${estado.panel === k}">${n}</button>`
  ).join('')}</div>`;
}

async function cargaPanel() {
  if (estado.panel === 'indice') return cargaIndice();
  if (estado.panel === 'posicion') return cargaPosicion();
  if (estado.panel === 'movs') return cargaMovimientos();
  if (estado.panel === 'dudosas') return cargaDudosas();
  return cargaResumen();
}

/* ------------------------------------------------------- índice de precios --
   La pantalla que sustituye a "Bajadas".

   La primera versión enseñaba el precio anterior tachado al lado del nuevo y un
   porcentaje en verde. Eso es el lenguaje de un folleto: está diseñado para que
   algo parezca una ganga. Aquí no se vende nada -- se mide. Lo que hace falta
   para decidir no es "este yogur ha bajado", es a qué ritmo se mueve el nivel
   de precios de cada cadena, sobre cuántos productos y desde cuándo. */

const COLOR = c => `var(--${c})`;

async function cargaIndice() {
  const caja = $('#panel');
  caja.innerHTML = pestanasPanel() + '<div class="cargando">Cargando…</div>';
  try {
    const r = await pide('/indice');
    $('#panel-meta').textContent =
      `Datos del ${r.fecha_datos.split('-').reverse().join('/')} · ${r.metodo}`;
    const series = r.series.filter(s => estado.cadenas.has(s.cadena));
    if (!series.length) { caja.innerHTML = pestanasPanel() + vacio(); return; }
    caja.innerHTML = pestanasPanel() + `
      <figure>
        <h2>Índice de precios por cadena</h2>
        <p class="sub">Base 100 en la primera captura de cada cadena. Cada eslabón
           compara <b>el mismo producto consigo mismo</b> contra la captura
           anterior de esa cadena, así que el índice no se mueve porque cambie el
           surtido.</p>
        ${lineas(series)}
        ${leyenda(series)}
        <figcaption>${resumenIndice(series)}</figcaption>
      </figure>
      ${tablaIndice(series)}`;
  } catch { caja.innerHTML = pestanasPanel() + vacio(); }
}

function vacio() {
  return `<div class="vacio">No llego a los datos ahora mismo.</div>`;
}

function resumenIndice(series) {
  const orden = [...series].sort((a, b) => a.variacion_pct - b.variacion_pct);
  const baja = orden[0], sube = orden[orden.length - 1];
  if (baja.cadena === sube.cadena) return 'Una sola cadena en el gráfico.';
  return `En el periodo medido, ${NOMBRE[baja.cadena]} es quien más ha bajado
    (${num(baja.variacion_pct)} %) y ${NOMBRE[sube.cadena]} quien más ha subido
    (${num(sube.variacion_pct)} %). Son décimas: en quince días un catálogo
    entero no se mueve mucho, y el valor está en la tendencia, no en el día.`;
}

const num = v => (v > 0 ? '+' : '') + v.toFixed(2).replace('.', ',');
/* Un decimal cuando el dato viene con un decimal: dos serían precisión
   inventada, y en una herramienta de medida eso se nota. */
const num1 = v => (v > 0 ? '+' : '') + v.toFixed(1).replace('.', ',');

/* Gráfico de líneas en SVG. Sin librería: son cinco series y catorce puntos. */
function lineas(series) {
  const W = 640, H = 260, M = {t: 14, r: 58, b: 26, l: 40};
  const fechas = [...new Set(series.flatMap(s => s.puntos.map(p => p.fecha)))].sort();
  const vals = series.flatMap(s => s.puntos.map(p => p.indice));
  let lo = Math.min(100, ...vals), hi = Math.max(100, ...vals);
  const pad = Math.max(0.25, (hi - lo) * 0.18);
  lo -= pad; hi += pad;
  const x = f => M.l + (fechas.indexOf(f) / Math.max(1, fechas.length - 1)) * (W - M.l - M.r);
  const y = v => M.t + (1 - (v - lo) / (hi - lo)) * (H - M.t - M.b);

  const ticks = [];
  for (let k = 0; k <= 4; k++) {
    const v = lo + (hi - lo) * k / 4;
    ticks.push(`<line x1="${M.l}" x2="${W - M.r}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}"
      class="rej"/><text x="${M.l - 7}" y="${(y(v) + 3.5).toFixed(1)}" class="ejeY">${v.toFixed(1).replace('.', ',')}</text>`);
  }
  /* El 100 es la referencia, no una serie: va en gris y con guiones. */
  const cien = (lo < 100 && hi > 100)
    ? `<line x1="${M.l}" x2="${W - M.r}" y1="${y(100).toFixed(1)}" y2="${y(100).toFixed(1)}" class="base"/>` : '';

  const cada = Math.ceil(fechas.length / 5);
  const ejeX = fechas.map((f, i) => (i % cada === 0 || i === fechas.length - 1)
    ? `<text x="${x(f).toFixed(1)}" y="${H - 8}" class="ejeX">${f.slice(8)}/${f.slice(5, 7)}</text>` : '').join('');

  /* Las etiquetas del final se pisan: con cinco cadenas en dos décimas, tres
     caen en el mismo píxel. Se separan lo justo manteniendo el orden, que es
     como se lee cuál es cuál sin mirar el color. */
  const finales = series.map(s => {
    const u = s.puntos[s.puntos.length - 1];
    return {cadena: s.cadena, fecha: u.fecha, v: u.indice, y: y(u.indice), ey: y(u.indice)};
  }).sort((a, b) => a.ey - b.ey);
  const HUECO = 11;
  for (let i = 1; i < finales.length; i++) {
    if (finales[i].ey - finales[i - 1].ey < HUECO)
      finales[i].ey = finales[i - 1].ey + HUECO;
  }
  const exceso = finales.length ? finales[finales.length - 1].ey - (H - M.b) : 0;
  if (exceso > 0) finales.forEach(f => { f.ey -= exceso; });

  const trazos = series.map(s => {
    const d = s.puntos.map((p, i) => `${i ? 'L' : 'M'}${x(p.fecha).toFixed(1)},${y(p.indice).toFixed(1)}`).join('');
    const f = finales.find(z => z.cadena === s.cadena);
    const px = x(f.fecha), guia = Math.abs(f.ey - f.y) > 2
      ? `<line x1="${(px + 5).toFixed(1)}" y1="${f.y.toFixed(1)}"
               x2="${(px + 9).toFixed(1)}" y2="${(f.ey - 3.5).toFixed(1)}"
               stroke="${COLOR(s.cadena)}" stroke-width="1" opacity=".55"/>` : '';
    return `<path d="${d}" fill="none" stroke="${COLOR(s.cadena)}" stroke-width="2"
              stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="${px.toFixed(1)}" cy="${f.y.toFixed(1)}" r="3.5"
              fill="${COLOR(s.cadena)}" stroke="var(--panel)" stroke-width="2"/>
      ${guia}
      <text x="${(px + 10).toFixed(1)}" y="${f.ey.toFixed(1)}"
            class="dir">${f.v.toFixed(1).replace('.', ',')}</text>`;
  }).join('');

  return `<svg class="gr" viewBox="0 0 ${W} ${H}" role="img"
            aria-label="Índice de precios por cadena, base 100">
    ${ticks.join('')}${cien}${ejeX}${trazos}</svg>`;
}

function leyenda(series) {
  return `<div class="leyenda-gr">${series.map(s =>
    `<span><i style="background:${COLOR(s.cadena)}"></i>${NOMBRE[s.cadena]}</span>`).join('')}</div>`;
}

/* La tabla no es un extra: el gráfico usa color para distinguir cinco cadenas y
   tres de esos colores no llegan a 3:1 contra el fondo claro. Con la tabla, el
   dato nunca depende de ver bien un color. */
function tablaIndice(series) {
  return `<details class="tabla-gr"><summary>Ver los números</summary>
    <table><thead><tr><th>Cadena</th><th>Índice</th><th>Variación</th>
      <th>Capturas</th><th>Productos en el último eslabón</th></tr></thead>
    <tbody>${series.map(s => {
      const u = s.puntos[s.puntos.length - 1];
      return `<tr><td>${NOMBRE[s.cadena]}</td>
        <td class="num">${s.indice.toFixed(2).replace('.', ',')}</td>
        <td class="num">${num(s.variacion_pct)} %</td>
        <td class="num">${s.capturas}</td>
        <td class="num">${u.productos.toLocaleString('es-ES')}</td></tr>`;
    }).join('')}</tbody></table></details>`;
}

/* ------------------------------------------------------- posición por sección --
   "¿Quién es más barato?" es la pregunta fácil y la menos útil. La que decide es
   "¿en qué soy caro?", y sólo se puede contestar comparando lo emparejado. */
async function cargaPosicion() {
  const caja = $('#panel');
  caja.innerHTML = pestanasPanel() + '<div class="cargando">Cargando…</div>';
  try {
    const r = await pide('/posicion');
    $('#panel-meta').textContent =
      `Datos del ${r.fecha_datos.split('-').reverse().join('/')}`;
    if (!r.secciones.length) {
      caja.innerHTML = pestanasPanel() + `<div class="vacio">Esto se llena en la
        primera ejecución del scraper posterior al cambio de secciones.</div>`;
      return;
    }
    const tope = Math.max(...r.secciones.flatMap(s =>
      s.cadenas.map(c => Math.abs(c.desvio_pct))), 5);
    /* Primero las secciones donde más se separan las cadenas: ahí es donde
       elegir tienda cambia el ticket. Las que están empatadas no deciden nada
       y no tienen por qué abrir la pantalla. */
    const orden = [...r.secciones].sort((a, b) => horquilla(b) - horquilla(a));
    caja.innerHTML = pestanasPanel() + `
      <p class="sub" style="margin:0 0 6px">Cada cadena contra <b>las otras</b>
        dentro de cada grupo de productos equivalentes. No es el precio medio de
        la sección: eso mediría el surtido, no el precio.</p>
      <p class="sub" style="margin:0 0 14px">
        <i class="pt" style="background:var(--debajo)"></i>a la izquierda, por
        debajo de las demás &nbsp;·&nbsp;
        <i class="pt" style="background:var(--encima)"></i>a la derecha, por
        encima. Ordenado por cuánto se separan.</p>
      ${orden.map(s => bloquePosicion(s, tope)).join('')}`;
  } catch { caja.innerHTML = pestanasPanel() + vacio(); }
}

/* Cuánto separa a la cadena más barata de la más cara dentro de la sección.
   Es la medida de si esa sección decide algo. */
function horquilla(s) {
  const v = s.cadenas.map(c => c.desvio_pct);
  return v.length > 1 ? Math.max(...v) - Math.min(...v) : 0;
}

function bloquePosicion(s, tope) {
  const filas = s.cadenas.filter(c => estado.cadenas.has(c.cadena));
  if (!filas.length) return '';
  return `<figure class="pos">
    <h2>${esc(NOMBRE_SECCION[s.seccion] || s.seccion)}</h2>
    <p class="sub">${s.productos.toLocaleString('es-ES')} productos emparejados${
      horquilla(s) > 0 ? ` · ${horquilla(s).toFixed(1).replace('.', ',')} puntos
      entre la más barata y la más cara` : ''}</p>
    <div class="dv">${filas.map(c => {
      const w = 50 * Math.min(1, Math.abs(c.desvio_pct) / tope);
      const caro = c.desvio_pct > 0;
      return `<div class="dvr">
        <span class="dvn">${NOMBRE[c.cadena]}</span>
        <span class="dvb">
          <span class="dvcero"></span>
          <span class="dvf ${caro ? 'caro' : 'barato'}"
                style="${caro ? 'left:50%' : `right:50%`};width:${w}%"></span>
          <span class="dvv num" style="${caro ? 'left' : 'right'}:calc(50% + ${w}% + 6px)">
            ${num1(c.desvio_pct)} %</span>
        </span></div>`;
    }).join('')}</div>
  </figure>`;
}

const NOMBRE_SECCION = {
  'frutas-verduras': 'Frutas y verduras', carniceria: 'Carnicería',
  pescaderia: 'Pescadería', 'lacteos-huevos': 'Lácteos y huevos',
  panaderia: 'Panadería', despensa: 'Despensa',
  'desayuno-dulces': 'Desayuno y dulces', aperitivos: 'Aperitivos',
  congelados: 'Congelados', preparados: 'Platos preparados', bebidas: 'Bebidas',
  'droguería-limpieza': 'Droguería y limpieza', 'higiene-belleza': 'Higiene y belleza',
  parafarmacia: 'Parafarmacia', bebe: 'Bebé', mascotas: 'Mascotas',
  ecologico: 'Ecológico', hogar: 'Hogar', promociones: 'Promociones',
};

/* ---------------------------------------------------------- movimientos --
   Cuántos precios toca cada cadena y cuánto. Sin precios tachados: lo que
   importa aquí es la frecuencia y la amplitud, no el chollo del día. */
async function cargaMovimientos() {
  const caja = $('#panel');
  caja.innerHTML = pestanasPanel() + '<div class="cargando">Cargando…</div>';
  try {
    const r = await pide('/pulso');
    $('#panel-meta').textContent =
      `Datos del ${r.fecha_datos.split('-').reverse().join('/')}`;
    const filas = r.capturas.filter(c => estado.cadenas.has(c.cadena)).reverse();
    if (!filas.length) { caja.innerHTML = pestanasPanel() + vacio(); return; }
    const tope = Math.max(...filas.map(f => f.movidos_pct), 1);
    caja.innerHTML = pestanasPanel() + `
      <p class="sub" style="margin:0 0 12px">Qué parte del catálogo cambia de
        precio en cada captura. Se ignoran los movimientos por debajo del
        ${num(r.umbral_pct).replace('+', '')} %, que son redondeo.</p>
      <table class="tm"><thead><tr>
        <th>Captura</th><th>Cadena</th><th class="d">Del catálogo</th>
        <th class="d">Bajan / suben</th>
      </tr></thead><tbody>${filas.map(f => `<tr>
        <td class="nw">${f.fecha.slice(8)}/${f.fecha.slice(5, 7)}${
          f.dias_del_salto > 1 ? `<span class="salto" title="el eslabón cubre ${f.dias_del_salto} días">·${f.dias_del_salto}d</span>` : ''}</td>
        <td class="nw"><i class="pt" style="background:${COLOR(f.cadena)}"></i>${NOMBRE[f.cadena]}</td>
        <td class="d num nw"><span class="mini" style="width:${(100 * f.movidos_pct / tope).toFixed(0)}%"></span>
          ${f.movidos_pct.toFixed(2).replace('.', ',')} %</td>
        <td class="d nw">${f.movidos
          ? `<span class="num">${f.bajan}</span>↓ <span class="num">${f.suben}</span>↑${
              f.mediana_bajada_pct == null ? ''
              : `<span class="med num">mediana ${num1(f.mediana_bajada_pct)} %</span>`}`
          : '<span class="quieto">sin cambios</span>'}</td>
      </tr>`).join('')}</tbody></table>`;
  } catch { caja.innerHTML = pestanasPanel() + vacio(); }
}

/* ------------------------------------------------------------------ avisos --
   Los tres tipos vienen escritos en el CHECK de la tabla desde el primer día.
   `minimo_90d` es el bueno y el que casi nadie tiene: no hay que saber de
   antemano cuánto debería costar algo, que es justo lo que no sabe nadie hasta
   que ve la curva. */

function pintaAvisos(caja, grupoId, precioUd, unidad) {
  const sugerido = Math.max(1, Math.round(precioUd * 0.9));
  caja.hidden = false;
  caja.innerHTML = `
    <p class="sub" style="margin:0 0 8px">¿Cuándo quieres que te avise?</p>
    <div class="chips">
      <button class="chip" data-crear-aviso="minimo_90d" data-grupo="${grupoId}">
        Cuando esté más barato que nunca en 90 días</button>
      <button class="chip" data-crear-aviso="cualquier_bajada" data-grupo="${grupoId}">
        Cada vez que baje</button>
    </div>
    <div class="umbral">
      <label>O si baja de
        <input type="number" step="0.01" min="0.01" id="i-umbral"
               value="${(sugerido / 100).toFixed(2)}"> €/${esc(unidad)}</label>
      <button class="chip" data-crear-aviso="baja_de" data-grupo="${grupoId}">Avisarme</button>
    </div>`;
}

async function creaAviso(boton) {
  const cuerpo = {grupo_id: Number(boton.dataset.grupo), tipo: boton.dataset.crearAviso};
  if (cuerpo.tipo === 'baja_de') {
    const euros = Number($('#i-umbral')?.value);
    if (!euros || euros <= 0) return flota('Pon un precio primero');
    cuerpo.umbral_cent = Math.round(euros * 100);
  }
  try {
    await pide('/alertas', {metodo: 'POST', cuerpo});
    boton.closest('.avisos-de').hidden = true;
    flota('Te aviso cuando pase');
  } catch { flota('No he podido guardar el aviso'); }
}

const NOMBRE_TIPO = {
  baja_de: 'si baja del precio que pusiste',
  minimo_90d: 'cuando esté más barato que nunca en 90 días',
  cualquier_bajada: 'cada vez que baje',
};

function pintaSaltan(saltan) {
  if (!saltan.length) return '';
  return `<section class="saltan">
    <h2>${saltan.length === 1 ? 'Un aviso' : saltan.length + ' avisos'}</h2>
    ${saltan.map(a => `<article class="salta">
      <div class="txt">
        <h3>${esc(a.nombre)}</h3>
        <p class="porque">${esc(a.por_que)}</p>
      </div>
      <span class="num precio">${eur(a.precio_unidad_cent)}<span class="unit">/${esc(a.unidad)}</span></span>
    </article>`).join('')}
    <button class="bt" id="b-vistos" data-ids="${saltan.map(a => a.alerta_id).join(',')}">
      Entendido</button>
  </section>`;
}

function pintaMisAvisos(lista) {
  if (!lista.length) return '';
  return `<section class="misavisos">
    <h2>Avisos puestos</h2>
    ${lista.map(a => `<div class="tira">
      <span>${esc(NOMBRE_TIPO[a.tipo] || a.tipo)}${
        a.umbral_cent ? ` (${eur(a.umbral_cent)})` : ''}${
        a.vista_en ? ' · ya saltó' : ''}</span>
      <button class="chip" data-borrar-aviso="${a.id}">Quitar</button>
    </div>`).join('')}
  </section>`;
}

/* ---------------------------------------------------------- verificador --
   La pregunta no es cuánto cuesta, es si el descuento es real. La regla ya
   estaba calculada y no tenía pantalla. */
async function cargaDudosas() {
  const caja = $('#panel');
  caja.innerHTML = pestanasPanel() + '<div class="cargando">Cargando…</div>';
  try {
    const cadenas = [...estado.cadenas].join(',');
    const r = await pide(`/ofertas-dudosas?limite=60&cadenas=${cadenas}`);
    $('#panel-meta').textContent =
      `Datos del ${r.fecha_datos.split('-').reverse().join('/')}`;
    if (!r.resultados.length) {
      caja.innerHTML = pestanasPanel() + `<div class="vacio">
        Ninguna oferta sospechosa hoy en las cadenas que miras.</div>`;
      return;
    }
    caja.innerHTML = pestanasPanel()
      + `<p class="sub" style="margin:4px 0 12px">Ofertas anunciadas que el
         histórico no sostiene. No son mentiras necesariamente: son las que
         conviene mirar dos veces.</p>`
      + r.resultados.map(tarjetaDudosa).join('');
  } catch {
    caja.innerHTML = pestanasPanel() + `<div class="vacio">No llego a los datos
      ahora mismo.</div>`;
  }
}

function tarjetaDudosa(x) {
  /* Dónde cae el precio de hoy dentro de lo que ha costado en 90 días. Pegado
     a la derecha es que "la oferta" está entre lo más caro del trimestre. */
  const pos = x.posicion_90d == null ? null : Math.round(100 * x.posicion_90d);
  return `<article class="dudosa">
    ${x.imagen ? `<img src="${esc(x.imagen)}" alt="" loading="lazy">` : ''}
    <div class="txt">
      <h3>${esc(x.nombre)}</h3>
      <p class="meta">${x.marca ? esc(x.marca) + ' · ' : ''}${NOMBRE[x.cadena] || x.cadena}</p>
      ${x.promo_txt ? `<p class="promo">${esc(x.promo_txt)}</p>` : ''}
      <p class="porque">${esc(x.por_que)}</p>
      ${pos == null ? '' : `
      <p class="leyenda">Hoy, dentro de sus 90 días</p>
      <div class="regla">
        <span class="marca" style="left:${pos}%"></span>
        <span class="extremo izq num">${eur(x.min_90d_cent)}</span>
        <span class="extremo der num">${eur(x.max_90d_cent)}</span>
      </div>`}
      ${x.solo_con_tarjeta ? `<p class="aviso-tarjeta">Y además sólo con la
        tarjeta de la cadena</p>` : ''}
    </div>
  </article>`;
}

async function cargaResumen() {
  const caja = $('#panel');
  caja.innerHTML = pestanasPanel() + '<div class="cargando">Cargando…</div>';
  try {
    const [cad, hist, mar] = await Promise.all([
      pide('/panel/cadenas'), pide('/panel/historico'), pide('/panel/marcas')]);
    $('#panel-meta').textContent = `Datos del ${cad.fecha_datos.split('-').reverse().join('/')} · ${hist.dias} días de histórico`;
    const d = cad.dispersion;
    const maxB = Math.max(...cad.mas_barata.map(x => x.pct));
    const maxM = Math.max(...cad.movimiento.map(x => x.pct));
    const faltan = hist.pendientes.filter(p => p.faltan > 0);

    caja.innerHTML = pestanasPanel() + `
      <div class="tiles">
        <div class="tile"><span class="q">Grupos comparables</span>
          <span class="v num">${d.grupos.toLocaleString('es-ES')}</span>
          <span class="s">con dos cadenas o más</span></div>
        <div class="tile"><span class="q">Diferencia mediana</span>
          <span class="v num">${d.mediana_pct} %</span>
          <span class="s">entre la más cara y la más barata del mismo grupo</span></div>
        <div class="tile"><span class="q">Percentil 90</span>
          <span class="v num">${d.p90_pct} %</span>
          <span class="s">uno de cada diez grupos más que duplica</span></div>
      </div>

      <figure><h2>Veces que cada cadena es la más barata</h2>
        <p class="sub">Entre los grupos donde compite con al menos otra</p>
        <div class="bh">${cad.mas_barata.map(b => barra(b.cadena, b.pct, maxB,
          b.pct.toFixed(1).replace('.', ',') + ' %',
          b.compite_en.toLocaleString('es-ES') + ' grupos')).join('')}</div>
        <figcaption>Aldi gana casi siempre pero compite en pocos grupos.
          Carrefour es la más cara de forma consistente.</figcaption>
      </figure>

      <figure><h2>Productos que cambian de precio cada día</h2>
        <p class="sub">Al lado, cuánto se mueve cuando se mueve</p>
        <div class="bh">${cad.movimiento.sort((a,b) => b.pct - a.pct).map(m => barra(
          m.cadena, m.pct, maxM * 1.12, m.pct.toFixed(2).replace('.', ',') + ' %',
          eur(m.mediana_cent) + '/kg')).join('')}</div>
      </figure>

      <figure><h2>Marca propia contra marca</h2>
        <p class="sub">En los ${mar.grupos_con_ambas.toLocaleString('es-ES')} grupos donde compiten las dos</p>
        <div class="tiles" style="margin:0 0 12px">
          <div class="tile"><span class="q">Marca propia</span>
            <span class="v num">${eur(mar.media_propia_cent)}</span><span class="s">por unidad, media</span></div>
          <div class="tile"><span class="q">Marca</span>
            <span class="v num">${eur(mar.media_marca_cent)}</span><span class="s">por unidad, media</span></div>
          <div class="tile"><span class="q">Diferencia</span>
            <span class="v num">${mar.ahorro_pct} %</span><span class="s">más barata la propia</span></div>
        </div>
        <div class="tira">${esc(mar.aviso)}</div>
        <p style="font-size:13.5px;margin:12px 0 0">Cara a cara en los
          ${mar.duelo.grupos} grupos con calidad leída de la etiqueta:
          gana la propia <b>${mar.duelo.gana_propia}</b>,
          empatan <b>${mar.duelo.empatan}</b>,
          gana la marca <b>${mar.duelo.gana_marca}</b>.</p>
        <figcaption>La conclusión honesta es que la marca propia cuesta menos
          y, donde se pueden leer los ingredientes, no es peor.</figcaption>
      </figure>

      ${faltan.length ? `<figure><h2>Lo que todavía no se puede medir</h2>
        <p class="sub">Con ${hist.dias} días de histórico</p>
        ${faltan.map(p => `<div class="tira">
          <b style="font-family:'JetBrains Mono',monospace">${p.que}</b>
          — faltan ${p.faltan} días para ${p.para}.</div>`).join('')}
        <figcaption>No se arregla programando: se arregla esperando.
          Las gráficas aparecerán solas.</figcaption>
      </figure>` : ''}`;
  } catch {
    caja.innerHTML = pestanasPanel() + `<div class="vacio">Esto necesita llegar
      al ordenador donde viven los datos, y ahora mismo no llego.</div>`;
  }
}

function barra(cadena, valor, max, texto, sub) {
  const w = Math.max(6, 100 * valor / max);
  return `<div class="r"><span class="n">${NOMBRE[cadena] || cadena}</span>
    <span class="t"><span class="b num" style="width:${w}%;background:var(--${cadena})">${texto}</span>
    ${sub ? `<span class="s num" style="left:calc(${w}% + 8px)">${sub}</span>` : ''}</span></div>`;
}

/* ---------------------------------------------------- ficha del producto -- */
/* Lo que se mira de verdad en el pasillo, por este orden: qué lleva, si tiene
   algo que no puedo comer, y cuánto cuesta por kilo. El Nutri-Score va después
   porque se entiende de un vistazo y no hace falta leerlo. */
const fichas = {};

function abreFicha(productoId) {
  const p = fichas[productoId];
  if (!p) return;
  $('#hoja-titulo').textContent = p.nombre;
  $('#hoja-sub').textContent = [NOMBRE[p.fuente], p.marca,
    p.cantidad ? `${p.cantidad} ${p.unidad}` : null].filter(Boolean).join(' · ');

  const datos = [];
  /* Lo primero de todo, en rojo: un lote retirado de la venta no es un detalle
     de la ficha. Ninguna app de la competencia avisa de esto y nosotros sabemos
     exactamente qué hay en cada lista. */
  if (p.es_recall) datos.push(`<div class="aviso-grave"><b>Producto retirado</b><br>
    La cadena ha retirado este lote de la venta. Si lo tienes en casa, no lo consumas
    y consulta en su web o en la AESAN.</div>`);
  if (p.promo) {
    /* Cuándo se acaba importa tanto como cuánto baja: una oferta que termina
       mañana cambia si merece la pena ir hoy. */
    const hasta = p.promo_hasta ? `<br><span class="hasta">Hasta el ${diaCorto(p.promo_hasta)}</span>` : '';
    /* Con tarjeta: el dinero no se descuenta en caja, se acumula. Decirlo con
       esas palabras es la diferencia entre informar y hacer creer. */
    const club = p.promo_club
      ? `<br><span class="hasta">Solo con la tarjeta de la cadena — no baja lo que pagas en caja</span>` : '';
    datos.push(`<div class="oferta-caja ${p.promo_club ? 'club' : ''}">
      <b>${p.promo_club ? 'Oferta de tarjeta' : 'Oferta'}</b><br>${esc(p.promo)}${hasta}${club}</div>`);
  }
  /* Los sellos, arriba del todo: quien filtra por dieta vuelve a comprobarlo en
     la ficha, y es lo que mira primero. Con su procedencia al lado, porque un
     certificado auditado y una palabra en el nombre no valen lo mismo y dar a
     entender lo contrario es lo peor que puede hacer esta app. */
  if (p.sellos?.length) {
    const comoLoSabemos = {
      certificado: 'certificado del producto',
      etiqueta: 'lo etiqueta la cadena',
      nombre: 'solo lo dice el nombre del producto',
      mixto: 'la cadena y el nombre del producto',
    }[p.sellos_origen] || '';
    datos.push(`<div class="sellos-ficha">${p.sellos.map(x =>
      `<span class="sello suave">${esc(NOMBRE_SELLO[x] || x)}</span>`).join('')}
      ${comoLoSabemos ? `<span class="fuente-dato">${esc(comoLoSabemos)}</span>` : ''}</div>`);
  }
  datos.push(`<dl style="margin:0">`);
  datos.push(fila('Precio', `<b class="num">${eur(p.precio_cent)}</b>
    <span class="num" style="color:var(--tinta-3)"> · ${eur(p.precio_unidad_cent)}/${p.unidad || 'ud'}</span>`));
  if (p.alergenos) datos.push(fila('Alérgenos',
    `<span style="color:var(--mal);font-weight:600">${esc(p.alergenos)}</span>`));
  if (p.ingredientes) datos.push(fila('Ingredientes', esc(p.ingredientes)));
  if (p.nutriscore) datos.push(fila('Nutri-Score',
    `<span class="sello ${p.nutriscore}">${p.nutriscore.toUpperCase()}</span>`
    + (p.nova ? ` <span class="sello suave">NOVA ${p.nova}</span>` : '')));
  if (p.calidad) datos.push(fila('Composición',
    `Calidad ${p.calidad} <span style="color:var(--tinta-3)">— leída de los ingredientes</span>`));
  else if (p.gama) datos.push(fila('Gama',
    `${p.gama} <span style="color:var(--tinta-3)">— sale de ordenar por precio, no de la etiqueta</span>`));
  if (p.nutricion) datos.push(fila(`Por ${p.nutricion_por || '100 g'}`, tablaNutricion(p.nutricion)));
  if (p.descripcion) datos.push(fila('Descripción', esc(p.descripcion)));
  if (p.origen) datos.push(fila('Origen', esc(p.origen)));
  if (p.certificados?.length) datos.push(fila('Certificados',
    p.certificados.map(c => esc(NOMBRE_CERT[c] || c)).join(' · ')));
  if (p.conservacion) datos.push(fila('Conservación',
    {refrigerado: 'En la nevera', congelado: 'En el congelador',
     ambiente: 'En la despensa'}[p.conservacion] || p.conservacion));
  if (p.envase) datos.push(fila('Envase', esc(p.envase)));
  /* "6 × 125 g · 0,42 € cada uno". Mercadona publica cuántas piezas trae el
     envase en 1.087 productos; nosotros lo deducíamos dividiendo precios y nos
     equivocábamos en el 87 % de los casos, diciendo "1" para un pack de seis. */
  if (p.unidades_pack && p.cantidad) {
    const cadaUno = p.cantidad / p.unidades_pack;
    const tamano = p.unidad === 'kg' || p.unidad === 'l'
      ? `${Math.round(cadaUno * 1000)} ${p.unidad === 'kg' ? 'g' : 'ml'}`
      : `${(+cadaUno.toFixed(2))} ${p.unidad || ''}`;
    const suelto = p.precio_cent ? ` · ${eur(Math.round(p.precio_cent / p.unidades_pack))} cada una` : '';
    datos.push(fila('Vienen', `${p.unidades_pack} × ${tamano}${suelto}`));
  }
  if (p.peso_variacion_pct) datos.push(fila('Al peso',
    `Ronda los ${p.peso_neto_g} g, y puede variar un ${p.peso_variacion_pct} %.
     <span style="color:var(--tinta-3)">El precio por kilo es exacto; el total, una estimación.</span>`));
  if (p.distintivo) datos.push(fila('La cadena dice',
    {'mejor-valorado': 'De los mejor valorados en su web',
     'novedad': 'Novedad', 'precio-destacado': 'Precio destacado',
     'air-fryer': 'Apto para freidora de aire'}[p.distintivo] || p.distintivo));
  if (p.advertencias?.length) datos.push(fila('Atención',
    `<span style="color:var(--mal);font-weight:600">${p.advertencias.map(esc).join(' · ')}</span>`));
  if (p.grado_alcohol) datos.push(fila('Alcohol', `${p.grado_alcohol} %`));
  if (p.ean) datos.push(fila('Código', `<span class="num">${esc(p.ean)}</span>`));
  if (!p.comparable) datos.push(fila('Aviso',
    'Su unidad no se puede comparar entre cadenas, así que este producto no decide dónde comprar.'));
  datos.push('</dl>');

  $('#hoja-contenido').innerHTML =
    (p.imagen ? `<img class="retrato" src="${esc(p.imagen)}" alt="" decoding="async">` : '')
    + datos.join('')
    + (p.url ? `<a class="bt" style="display:block;text-align:center;margin-top:16px;text-decoration:none"
         href="${esc(p.url)}" target="_blank" rel="noopener">Verlo en ${NOMBRE[p.fuente]}</a>` : '');
  $('#hoja').hidden = false;
  document.body.style.overflow = 'hidden';
  $('#hoja-cerrar').focus();
}

function fila(etiqueta, valor) {
  return `<div class="dato"><dt>${etiqueta}</dt><dd>${valor}</dd></div>`;
}

function cierraFicha() {
  $('#hoja').hidden = true;
  document.body.style.overflow = '';
}

$('#hoja-cerrar').addEventListener('click', cierraFicha);
$('#hoja').addEventListener('click', ev => { if (ev.target.id === 'hoja') cierraFicha(); });
document.addEventListener('keydown', ev => { if (ev.key === 'Escape') cierraFicha(); });

/* -------------------------------------------------------------- compartir -- */
$('#b-compartir').addEventListener('click', async () => {
  $('#hoja-titulo').textContent = 'Compartir la lista';
  $('#hoja-sub').textContent = estado.listaNombre;
  $('#hoja-contenido').innerHTML = '<div class="cargando">Preparando el enlace…</div>';
  $('#hoja').hidden = false;
  document.body.style.overflow = 'hidden';

  const gente = estado.personas.map(q => `<div class="persona">
    <span>${esc(q.nombre)} <span style="color:var(--tinta-3)">@${esc(q.usuario)}</span></span>
    <span class="papel">${q.papel === 'dueno' ? 'creó la lista' : q.papel}</span></div>`).join('');

  if (estado.papel !== 'dueno') {
    $('#hoja-contenido').innerHTML = `<p style="font-size:14px;color:var(--tinta-2)">
      Esta lista la creó otra persona, así que solo quien la creó puede invitar.</p>${gente}`;
    return;
  }
  try {
    const inv = await pide(`/listas/${estado.listaId}/invitacion`,
                           {metodo:'POST', cuerpo:{papel:'escribe', usos:3, dias:7}});
    const url = location.origin + inv.ruta;
    $('#hoja-contenido').innerHTML = `
      <p style="font-size:14px;color:var(--tinta-2);margin-top:0">
        Mándale este enlace. Al abrirlo entra en la lista y puede escribir en ella.
        Caduca en 7 días y sirve para 3 personas.</p>
      <div class="enlace-caja">
        <input type="text" id="i-enlace" value="${esc(url)}" readonly aria-label="Enlace de invitación">
        <button class="bt principal" id="b-copiar" style="flex:0 0 auto">Copiar</button>
      </div>
      <h3 style="font-size:12px;letter-spacing:.09em;text-transform:uppercase;
                 color:var(--tinta-3);margin:22px 0 4px">Quién está dentro</h3>
      ${gente}
      <button class="bt" id="b-revocar" style="width:100%;margin-top:18px">
        Anular los enlaces que haya dado</button>`;
  } catch {
    $('#hoja-contenido').innerHTML = `<div class="vacio">Esto necesita llegar al
      ordenador donde viven los datos, y ahora mismo no llego.</div>`;
  }
});

/* --------------------------------------------------------------- ajustes -- */
function pintaAjustes() {
  $('#ajustes-quien').textContent = estado.yo ? `${estado.yo.nombre} · @${estado.yo.usuario}` : '';
  const cercanas = estado.cadenas;
  $('#ajustes').innerHTML = `
    <h3 style="font-size:12px;letter-spacing:.09em;text-transform:uppercase;
               color:var(--tinta-3);margin:6px 0 4px">Supermercados que tengo cerca</h3>
    <p style="font-size:13px;color:var(--tinta-3);margin:0 0 10px">
      Los que quites no salen en las búsquedas ni deciden dónde comprar.
      Si no tienes un Aldi al lado, no tiene sentido que te diga que es el más barato.</p>
    <div class="chips">${CADENAS.map(c =>
      `<button class="chip cad ${c}" data-cadena="${c}" aria-pressed="${cercanas.has(c)}">${NOMBRE[c]}</button>`
    ).join('')}</div>

    <h3 style="font-size:12px;letter-spacing:.09em;text-transform:uppercase;
               color:var(--tinta-3);margin:24px 0 2px">La app</h3>
    <div class="ajuste">
      <span><span class="et2">Repartir entre dos tiendas</span>
        <span class="ex">Si lo quitas, solo te digo dónde sale mejor yendo a una sola.</span></span>
      <button class="interruptor" id="s-reparto" role="switch"
              aria-checked="${local.lee('reparto', true)}"><i></i></button>
    </div>
    <div class="ajuste">
      <span><span class="et2">Cerrar sesión</span>
        <span class="ex">Tendrás que volver a entrar con tu usuario.</span></span>
      <button class="bt" id="b-salir" style="flex:0 0 auto;padding:8px 16px">Salir</button>
    </div>
    <div class="ajuste">
      <span><span class="et2">Darme de baja</span>
        <span class="ex">Se borran tus listas, tus favoritos y tu cuenta.
          Lo que añadiste a listas de otros se queda, sin tu nombre.</span></span>
      <button class="bt" id="b-baja" style="flex:0 0 auto;padding:8px 16px;
        border-color:var(--mal);color:var(--mal)">Baja</button>
    </div>

    <p style="font-size:12px;color:var(--tinta-3);margin-top:22px;line-height:1.6">
      Los datos viven en el ordenador de casa y no salen de ahí. Esta pantalla
      solo pide lo que estás mirando.<br>
      Información nutricional de Open Food Facts, bajo licencia ODbL.</p>`;
}

/* ----------------------------------------------------------------- rutas -- */
function ve(vista) {
  estado.vista = vista;
  ['buscar','lista','favoritos','panel','ajustes'].forEach(v => {
    $('#v-' + v).hidden = v !== vista;
  });
  $$('nav button').forEach(b => {
    if (b.dataset.vista === vista) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  });
  if (vista === 'lista') cargaLineas();
  if (vista === 'favoritos') cargaFavoritos();
  if (vista === 'panel') cargaPanel();
  if (vista === 'ajustes') pintaAjustes();
}

document.addEventListener('click', async ev => {
  const nav = ev.target.closest('nav button');
  if (nav) return ve(nav.dataset.vista);

  const ejemplo = ev.target.closest('[data-ejemplo]');
  if (ejemplo) {
    $('#q').value = ejemplo.dataset.ejemplo;
    estado.seccion = null;
    return busca();
  }

  const pasillo = ev.target.closest('[data-seccion]');
  if (pasillo) {
    estado.seccion = pasillo.dataset.seccion;
    $('#q').value = '';
    return busca();
  }

  if (ev.target.closest('#sal-pasillo')) {
    estado.seccion = null;
    $('#q').value = '';
    return busca();
  }

  const avisar = ev.target.closest('[data-avisar]');
  if (avisar) {
    const caja = avisar.closest('.acciones').nextElementSibling;
    if (!caja.hidden) { caja.hidden = true; return; }
    pintaAvisos(caja, avisar.dataset.avisar,
                Number(avisar.dataset.precioUd), avisar.dataset.unidad);
    return;
  }

  const crear = ev.target.closest('[data-crear-aviso]');
  if (crear) return creaAviso(crear);

  const borrar = ev.target.closest('[data-borrar-aviso]');
  if (borrar) {
    try {
      await pide(`/alertas/${borrar.dataset.borrarAviso}`, {metodo: 'DELETE'});
      cargaFavoritos();
    } catch { flota('No he podido quitarlo'); }
    return;
  }

  const vistos = ev.target.closest('#b-vistos');
  if (vistos) {
    /* Marcarlos como vistos es una acción aparte a propósito: abrir la pantalla
       en el autobús no es haberlos leído. */
    const ids = vistos.dataset.ids.split(',').filter(Boolean);
    try {
      await pide('/alertas/vistas', {metodo: 'POST', cuerpo: {ids}});
      cargaFavoritos();
    } catch { flota('No he podido marcarlos'); }
    return;
  }

  const sub = ev.target.closest('[data-panel]');
  if (sub) {
    estado.panel = sub.dataset.panel;
    return cargaPanel();
  }


  const chip = ev.target.closest('.chip.cad');
  if (chip) {
    const c = chip.dataset.cadena;
    estado.cadenas.has(c) ? estado.cadenas.delete(c) : estado.cadenas.add(c);
    if (!estado.cadenas.size) estado.cadenas.add(c);   // al menos una
    local.guarda('cadenas', [...estado.cadenas]);
    pide('/preferencias', {metodo:'PUT',
      cuerpo:{clave:'cadenas_cerca', valor:[...estado.cadenas]}}).catch(() => {});
    pintaChips();
    /* Los pasillos dependen de las cadenas que se miran: si se apaga Alcampo,
       el pasillo de ecológico se queda sin casi nada. Se vuelven a pedir. */
    pasillos = null;
    if (estado.vista === 'ajustes') pintaAjustes(); else busca();
    return;
  }

  const cab = ev.target.closest('.cab');
  if (cab && cab.dataset.grupo) return abreGrupo(cab, cab.dataset.grupo);

  const anadir = ev.target.closest('[data-anadir]');
  if (anadir) return anade(anadir.dataset.anadir, anadir.dataset.nombre, {
    imagen: anadir.dataset.imagen || null,
    precio_cent: Number(anadir.dataset.precio) || null,
  });

  const ficha = ev.target.closest('[data-ficha]');
  if (ficha) return abreFicha(ficha.dataset.ficha);

  const copiar = ev.target.closest('#b-copiar');
  if (copiar) {
    const campo = $('#i-enlace');
    campo.select();
    try {
      await navigator.clipboard.writeText(campo.value);
      copiar.textContent = 'Copiado';
    } catch {
      /* En un navegador que no deja copiar, el texto ya está seleccionado:
         se copia a mano y no se queda nadie sin el enlace. */
      copiar.textContent = 'Cópialo';
    }
    return;
  }

  const revocar = ev.target.closest('#b-revocar');
  if (revocar) {
    try {
      const r = await pide(`/listas/${estado.listaId}/invitacion`, {metodo:'DELETE'});
      revocar.textContent = r.revocadas ? `Anulados ${r.revocadas}` : 'No había ninguno';
      revocar.disabled = true;
    } catch { flota('No he podido anularlos'); }
    return;
  }

  const baja = ev.target.closest('#b-baja');
  if (baja) {
    /* Escribir el propio usuario, no un "¿seguro?": borrar la cuenta no se
       puede deshacer y un botón de confirmar se pulsa sin leer. */
    $('#hoja-titulo').textContent = 'Darte de baja';
    $('#hoja-sub').textContent = estado.yo?.nombre || '';
    $('#hoja-contenido').innerHTML = `
      <p style="font-size:14.5px;color:var(--tinta-2);margin-top:0">
        Se borran <b>tus listas, tus favoritos y tu cuenta</b>. Lo que añadiste a
        listas de otras personas se queda ahí, sin tu nombre, para no vaciarles
        la compra.</p>
      <p style="font-size:14.5px;color:var(--tinta-2)">Esto no se puede deshacer.
        Escribe <b>${esc(estado.yo?.usuario || '')}</b> para confirmarlo.</p>
      <input type="text" id="i-baja" autocomplete="off" aria-label="Tu usuario">
      <button class="bt" id="b-baja-ok" style="width:100%;margin-top:12px;
        border-color:var(--mal);color:var(--mal)">Darme de baja</button>`;
    $('#hoja').hidden = false;
    document.body.style.overflow = 'hidden';
    return;
  }

  const bajaOk = ev.target.closest('#b-baja-ok');
  if (bajaOk) {
    if ($('#i-baja').value.trim() !== estado.yo?.usuario) {
      flota('El usuario no coincide');
      return;
    }
    try {
      await pide('/yo', {metodo: 'DELETE'});
      location.reload();
    } catch { flota('No he podido darte de baja'); }
    return;
  }

  const salir = ev.target.closest('#b-salir');
  if (salir) {
    await pide('/salir', {metodo:'POST'}).catch(() => {});
    location.reload();
    return;
  }

  const interruptor = ev.target.closest('.interruptor');
  if (interruptor) {
    const puesto = interruptor.getAttribute('aria-checked') === 'true';
    interruptor.setAttribute('aria-checked', String(!puesto));
    if (interruptor.id === 's-reparto') local.guarda('reparto', !puesto);
    return;
  }

  const fav = ev.target.closest('[data-favorito]');
  if (fav) {
    try {
      await pide('/favoritos', {metodo:'POST', cuerpo:{grupo_id: Number(fav.dataset.favorito)}});
      fav.textContent = 'Siguiendo';
      fav.classList.add('activo');
    } catch { flota('No he podido guardarlo'); }
    return;
  }

  const carro = ev.target.closest('[data-carro]');
  if (carro) {
    const l = estado.lineas.find(x => x.id === carro.dataset.carro);
    return cambia(carro.dataset.carro, {en_carrito: !enCarro(l)});
  }

  const cant = ev.target.closest('[data-cantidad]');
  if (cant) {
    const l = estado.lineas.find(x => x.id === cant.dataset.cantidad);
    if (!l) return;
    const nueva = l.cantidad + Number(cant.dataset.delta);
    if (nueva < 1) return cambia(l.id, {borrado: true});
    return cambia(l.id, {cantidad: nueva});
  }
});

/* Al volver la red, se sube lo pendiente sin que nadie lo pida. */
window.addEventListener('online', async () => {
  const n = await cola.sube();
  if (n) flota(`Subidos ${n} cambios`);
  estado.enLinea = true;
  if (estado.vista === 'lista') pintaLista();
});

/* --------------------------------------------------------------- arranca -- */
async function arranca() {
  $('#v-entrar').hidden = true;
  $('#app').hidden = false;
  const guardadas = local.lee('cadenas');
  if (guardadas?.length) estado.cadenas = new Set(guardadas);
  pintaChips();
  await cargaListas();
  ve('buscar');
  pintaEjemplos();
  try {
    const e = await pide('/estado');
    const atrasadas = e.cadenas.filter(c => !c.al_dia);
    if (atrasadas.length) {
      $('#aviso-datos').innerHTML = `<div class="tira">
        ${atrasadas.map(c => NOMBRE[c.cadena]).join(', ')}
        ${atrasadas.length === 1 ? 'no se dejó capturar hoy' : 'no se dejaron capturar hoy'}:
        sus precios llevan su fecha y no deciden dónde comprar.</div>`;
    }
  } catch {}
}

/* Alguien ha abierto un enlace de invitación. Si no tiene sesión, primero
   entra y luego se le mete en la lista: el código sobrevive al login. */
function codigoInvitacion() {
  const m = location.pathname.match(/^\/unirme\/([\w-]+)/);
  if (m) { local.guarda('invitacion', m[1]); history.replaceState({}, '', '/'); }
  return local.lee('invitacion');
}

async function aplicaInvitacion() {
  const codigo = codigoInvitacion();
  if (!codigo) return;
  try {
    const r = await pide(`/invitacion/${codigo}`, {metodo:'POST'});
    local.guarda('invitacion', null);
    flota(r.ya_estabas ? `Ya estabas en «${r.nombre}»` : `Ya estás en «${r.nombre}»`);
  } catch {
    local.guarda('invitacion', null);
    flota('Ese enlace ya no vale');
  }
}

(async () => {
  codigoInvitacion();
  try {
    const r = await pide('/yo');
    if (r.usuario) {
      estado.yo = r.usuario;
      const prefs = r.preferencias || {};
      if (Array.isArray(prefs.cadenas_cerca) && prefs.cadenas_cerca.length) {
        estado.cadenas = new Set(prefs.cadenas_cerca);
      }
      await aplicaInvitacion();
      arranca();
    } else pintaEntrar();
  } catch { pintaEntrar(); }
})();


/* ---------------------------------------------------- nombres para la gente -- */
/* La base de datos dice "sin-aceite-palma"; una persona dice "Sin aceite de
   palma". Traducir aquí y no en el servidor deja el dato limpio para filtrar. */
const NOMBRE_SELLO = {
  'sin-gluten': 'Sin gluten', 'sin-lactosa': 'Sin lactosa', vegano: 'Vegano',
  vegetariano: 'Vegetariano', ecologico: 'Ecológico', 'sin-azucar': 'Sin azúcar',
  'sin-sal': 'Sin sal', 'sin-aceite-palma': 'Sin aceite de palma',
  halal: 'Halal', kosher: 'Kosher',
};
const NOMBRE_CERT = {
  'origen-espana': 'Origen España', dop: 'Denominación de Origen', igp: 'Indicación Geográfica',
  etg: 'Especialidad Tradicional', msc: 'Pesca sostenible (MSC)',
  asc: 'Acuicultura responsable (ASC)', 'comercio-justo': 'Comercio justo',
  'rainforest-alliance': 'Rainforest Alliance', 'bienestar-animal': 'Bienestar animal',
  eurohoja: 'Ecológico europeo', 'v-label': 'V-Label', adilac: 'Adilac (sin lactosa)',
  feacab: 'Sin gluten (FACE)', 'vegan-trademark': 'Vegan Trademark', natrue: 'Natrue',
  ecolabel: 'Ecolabel', fsc: 'FSC', pefc: 'PEFC', 'oeko-tex': 'Oeko-Tex',
  'algodon-organico': 'Algodón orgánico', ggn: 'GGN',
};

const NUTRIENTES = [
  ['energia_kcal', 'Calorías', 'kcal'], ['grasas', 'Grasas', 'g'],
  ['saturadas', 'de las cuales saturadas', 'g'], ['hidratos', 'Hidratos', 'g'],
  ['azucares', 'de los cuales azúcares', 'g'], ['fibra', 'Fibra', 'g'],
  ['proteinas', 'Proteínas', 'g'], ['sal', 'Sal', 'g'],
];

/* La tabla de la etiqueta, la misma que hay en el envase. No es el Nutri-Score:
   es el dato del que sale, y lo publica la cadena, no una base de datos ajena. */
function tablaNutricion(n) {
  const filas = NUTRIENTES
    .filter(([k]) => n[k] !== undefined && n[k] !== null)
    .map(([k, txt, uni]) => `<tr><td>${txt}</td><td class="num">${n[k]} ${uni}</td></tr>`);
  if (!filas.length) return '';
  return `<table class="nutricion">${filas.join('')}</table>`;
}

/* "2026-09-20" -> "20 de septiembre". Sin librerías: una función y doce nombres. */
const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
               'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
function diaCorto(iso) {
  const [a, m, d] = String(iso).split('-').map(Number);
  if (!a || !m || !d) return iso;
  return `${d} de ${MESES[m - 1]}`;
}
