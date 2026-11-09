"""Capturas de la interfaz para revisión externa (y medida objetiva de cada pantalla).

Para qué
--------
David revisa la app con otros ojos (Claude, GPT, Codex) y necesita un inventario de
pantallas: una captura por pantalla, la ruta exacta, y lo que se puede medir sin
discutir: si la pantalla se desborda en horizontal, cuántas imágenes no cargan,
cuántos botones son más pequeños que un dedo, cuántas letras bajan de 12 px y qué
errores de consola o peticiones fallidas hay.

Cómo se usa
-----------
Necesita la API y la interfaz levantadas y **con el catálogo real**, no el de ensayo:

    # 1. base desechable (no toca la de casa), puerto 55432
    .\\.venv\\Scripts\\python.exe -m plataforma.ensayo prepara

    # 2. API contra esa base, con el gold de verdad montado
    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:55432/cesta_ensayo_propio'
    $env:CESTA_GOLD='F:\\Proyectos\\cesta\\data\\gold'
    .\\.venv\\Scripts\\python.exe -m uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8099

    # 3. la interfaz, en modo desarrollo (hace proxy de /api)
    cd plataforma\\web\\app
    $env:CESTA_API='http://127.0.0.1:8099'; npm run dev

    # 4. las capturas
    .\\.venv\\Scripts\\python.exe scripts/capturar_pantallas.py

Escribe en `data/revision-ui-2026-11-09/` (fuera de git: se regenera): una imagen por
pantalla -- página completa y primera pantalla, en móvil y en escritorio -- y
`manifiesto.json` con la medida de cada una. El inventario que las explica está en
`docs/revision-interfaz.md`. La cuenta y la lista de la compra son de usar y
tirar (`revision-ui`, en la base desechable), así que se puede repetir las veces que
haga falta.
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from patchright.sync_api import Error as ErrorNavegador
from patchright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
#: Las capturas viven en `data/`, que está fuera de git: son un artefacto que se
#: regenera, no producto. El inventario que las explica sí va en `docs/`.
SALIDA = RAIZ / "data" / "revision-ui-2026-11-09"
API = os.environ.get("CESTA_CAPTURA_API", "http://127.0.0.1:8099")
UI = os.environ.get("CESTA_CAPTURA_UI", "http://127.0.0.1:5173")
USUARIO = "revision-ui"
CLAVE = "revision-2026-9"
NOMBRE = "Revisión UI"

#: La lista se llama así y es la de casa: es la que la portada enseña como «Mi cesta».
LISTA = "Casa"

#: Lo que se pone en la lista. Se busca en el catálogo real y se guarda el primero que
#: tenga grupo comparable; si algo no aparece ese día, se sigue sin inventar nada.
CARRITO = [
    ("leche semidesnatada", 2, ""),
    ("pan de molde", 1, ""),
    ("huevos", 1, ""),
    ("tomate", 1, "para la ensalada"),
    ("pechuga de pollo", 1, ""),
    ("arroz", 1, ""),
    ("aceite de oliva", 1, ""),
    ("yogur natural", 4, ""),
    ("cafe molido", 1, "el de siempre"),
    ("detergente", 1, ""),
]

#: Las rutas que se capturan. El nombre es el que llevará el fichero.
PANTALLAS = [
    ("01-portada", "/"),
    ("02-buscar", "/compra?q=leche"),
    ("03-ficha-producto", None),      # se rellena tras sembrar
    ("04-comparar-grupo", None),
    ("05-lista", None),
    ("06-comparar-cesta", None),
    ("07-favoritos", "/compra/favoritos"),
    ("08-ofertas", "/compra/ofertas"),
    ("09-recetario", "/recetas"),
    ("10-receta", None),
    ("11-plan-semanal", "/recetas/plan"),
    ("12-diario", "/calorias"),
    ("13-pautas", "/calorias/pautas"),
    ("14-alimentos", "/calorias/alimentos"),
    ("15-tendencias", "/calorias/tendencias"),
    ("16-despensa", "/compra/despensa"),
    ("17-importar-receta", "/compra/importar"),
    ("18-ajustes", "/ajustes"),
    ("19-avisos", "/avisos"),
    ("20-panel", "/panel"),
    ("21-matching", "/panel/matching"),
    ("22-escaner", "/escaner"),
    # No hay ruta `/entrar`: la puerta de sesión vive en `/compra/listas`, y se captura
    # **sin cookie** (si no, la pantalla que sale es la lista, no el formulario).
    ("23-entrar", "/compra/listas"),
]

#: Las que además se miran en escritorio (1440 x 900). El producto es móvil, pero la
#: revisión externa necesita ver que no se rompe en ancho.
ESCRITORIO = {"01-portada", "03-ficha-producto", "05-lista", "06-comparar-cesta",
              "09-recetario", "12-diario"}


def sesion() -> httpx.Client:
    """La cuenta de revisión, creada o reutilizada, con su cookie puesta."""
    c = httpx.Client(base_url=API, timeout=90)
    r = c.post("/api/registrarse",
               json={"usuario": USUARIO, "nombre": NOMBRE, "clave": CLAVE})
    if r.status_code == 409:
        r = c.post("/api/entrar", json={"usuario": USUARIO, "clave": CLAVE})
    if r.status_code not in (200, 201):
        raise SystemExit(f"no se pudo entrar: {r.status_code} {r.text[:300]}")
    if not c.cookies.get("cesta_sesion"):
        raise SystemExit("la API no devolvió la cookie de sesión")
    return c


def _nombre_con_marca(fila: dict) -> str:
    """El nombre que se enseña, sin repetir la marca cuando el nombre ya la lleva."""
    nombre = (fila.get("nombre") or "").strip()
    marca = (fila.get("marca") or "").strip()
    if marca and marca.lower() not in nombre.lower():
        return f"{nombre} {marca.title()}"
    return nombre


def _primero_por_grupo(c: httpx.Client, consulta: str) -> dict | None:
    r = c.get("/api/buscar", params={"q": consulta})
    if r.status_code != 200:
        return None
    for fila in r.json().get("resultados", []):
        if fila.get("grupo_id"):
            return fila
    return None


def siembra(c: httpx.Client) -> dict:
    """Cuenta lista para enseñar: lista de casa con cosas dentro y tres favoritos."""
    listas = c.get("/api/listas").json()
    casa = next((x for x in listas.get("listas", []) if x.get("nombre") == LISTA), None)
    if casa is None:
        r = c.post("/api/listas", json={"nombre": LISTA, "es_de_casa": True})
        casa = r.json()

    detalle = c.get(f"/api/listas/{casa['id']}").json()
    ya = {linea.get("nombre") for linea in detalle.get("lineas", [])}

    grupos: list[int] = []
    anadidas = 0
    for consulta, cantidad, nota in CARRITO:
        fila = _primero_por_grupo(c, consulta)
        if not fila:
            continue
        grupos.append(int(fila["grupo_id"]))
        nombre = _nombre_con_marca(fila)
        if nombre in ya:
            continue
        cuerpo = {
            "id": str(uuid.uuid4()),
            "nombre": nombre,
            "grupo_id": int(fila["grupo_id"]),
            "cantidad": cantidad,
        }
        if nota:
            cuerpo["nota"] = nota
        r = c.post(f"/api/listas/{casa['id']}/lineas", json=cuerpo)
        if r.status_code in (200, 201):
            anadidas += 1
        ya.add(nombre)

    # Un par de líneas en el carro, para que la pantalla no sea todo «sin coger».
    detalle = c.get(f"/api/listas/{casa['id']}").json()
    lineas = detalle.get("lineas", [])
    for linea in lineas[:2]:
        c.patch(f"/api/listas/{casa['id']}/lineas/{linea['id']}",
                json={"en_carrito": True, "momento": datetime.now().isoformat()})

    # Favoritos: tres cosas que existan de verdad.
    favoritos_grupos: list[int] = []
    for consulta in ("leche semidesnatada", "cafe molido", "detergente"):
        fila = _primero_por_grupo(c, consulta)
        if not fila:
            continue
        favoritos_grupos.append(int(fila["grupo_id"]))
        c.post("/api/favoritos", json={"grupo_id": int(fila["grupo_id"])})

    # Las cadenas cercanas, que son las que usa «dónde comprar».
    c.put("/api/preferencias", json={"clave": "cadenas_cerca",
                                     "valor": ["dia", "alcampo", "mercadona", "carrefour"]})

    # Una receta de verdad, si hay.
    recetas = c.get("/api/recetas")
    receta_id = None
    if recetas.status_code == 200:
        datos = recetas.json()
        filas = datos.get("recetas") or datos.get("resultados") or []
        if filas:
            receta_id = filas[0].get("id") or filas[0].get("receta_id")

    grupo = None
    if grupos:
        g = c.get(f"/api/grupo/{grupos[0]}")
        if g.status_code == 200:
            grupo = g.json()

    recetas_creadas = _recetas(c, grupos)
    if not receta_id and recetas_creadas:
        receta_id = recetas_creadas[0]

    return {
        "lista_id": casa["id"],
        "listas": len(listas.get("listas", [])),
        "lineas_anadidas": anadidas,
        "lineas": len(lineas),
        "favoritos": favoritos_grupos,
        "receta_id": receta_id,
        "recetas": recetas_creadas,
        "grupo_id": grupos[0] if grupos else None,
        "grupo": grupo,
    }


def _recetas(c: httpx.Client, grupos: list[int]) -> list[int]:
    """Dos recetas de casa con ingredientes del catálogo, para que Recetas no salga vacía.

    No se importa de ninguna web: se crean con la API, que es lo que hace la propia app
    cuando David escribe una receta. Una lleva ingredientes ligados a grupo para que el
    coste por ingrediente tenga algo que decir (y no invente nada si no hay precio).
    """
    ya = c.get("/api/recetas")
    existentes: dict[str, int] = {}
    if ya.status_code == 200:
        for fila in ya.json().get("recetas", []):
            if fila.get("nombre") and fila.get("id"):
                existentes[fila["nombre"]] = int(fila["id"])

    def liga(nombre: str, cantidad: float, unidad: str) -> dict:
        fila = _primero_por_grupo(c, nombre)
        ingrediente = {"texto": nombre, "cantidad": cantidad, "unidad": unidad}
        if fila:
            ingrediente["texto"] = _nombre_con_marca(fila)
            ingrediente["grupo_id"] = int(fila["grupo_id"])
        return ingrediente

    recetario = [
        {
            "nombre": "Tortilla de patatas",
            "raciones": 4,
            "minutos": 40,
            "etiquetas": "casa, cena",
            "preparacion": "Se pelan las patatas y se cortan en láminas finas. Se pochan despacio "
                           "con la cebolla. Se bate el huevo y se mezcla. Se cuaja en la sartén.",
            "ingredientes": [liga("patata", 1, "kg"), liga("huevos", 6, "ud"),
                             liga("cebolla", 1, "ud"), liga("aceite de oliva", 1, "l")],
        },
        {
            "nombre": "Macarrones con tomate",
            "raciones": 2,
            "minutos": 25,
            "etiquetas": "casa, rápido",
            "preparacion": "Se cuece la pasta. Se sofríe el tomate y se mezcla.",
            "ingredientes": [liga("macarrones", 250, "g"), liga("tomate", 400, "g")],
        },
    ]
    ids: list[int] = []
    for receta in recetario:
        if receta["nombre"] in existentes:
            ids.append(existentes[receta["nombre"]])
            continue
        r = c.post("/api/recetas", json=receta)
        if r.status_code in (200, 201):
            ids.append(int(r.json().get("receta_id") or r.json().get("id")))

    # Y una semana con comida puesta: sin esto, el plan es una lista vacía.
    if ids:
        from datetime import date, timedelta
        hoy = date.today()
        inicio = hoy - timedelta(days=hoy.weekday())
        for i, receta in enumerate(ids[:2]):
            for dia in (0, 2, 4):
                c.post("/api/recetas/plan", json={
                    "fecha": (inicio + timedelta(days=dia + i)).isoformat(),
                    "receta_id": receta,
                    "comensales": 2,
                    "comida": "comida" if dia % 2 == 0 else "cena",
                })
    return ids


def producto_de(grupo: dict | None) -> tuple[str, str] | None:
    """Un (fuente, id_fuente) real del grupo, para abrir su ficha."""
    if not grupo:
        return None
    for clave in ("productos", "miembros", "opciones"):
        for p in grupo.get(clave) or []:
            fuente = p.get("fuente") or p.get("cadena")
            ident = p.get("id_fuente") or p.get("id") or p.get("producto_id")
            if fuente and ident:
                return str(fuente), str(ident).split(":")[-1]
    return None


MEDIDA_JS = """
() => {
  const vw = window.innerWidth;
  const doc = document.documentElement;
  const desbordes = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    if (r.width <= 0) continue;
    if (s.position === 'fixed') continue;
    if (r.right > vw + 1) {
      desbordes.push({
        etiqueta: el.tagName.toLowerCase(),
        clase: String(el.className || '').slice(0, 60),
        texto: (el.textContent || '').trim().slice(0, 50),
        derecha: Math.round(r.right),
      });
      if (desbordes.length >= 8) break;
    }
  }
  const enlaces = [...document.querySelectorAll('a, button, [role="button"]')];
  const pequenos = enlaces.filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && (r.height < 24 || r.width < 24);
  }).map((el) => ({texto: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40),
                   alto: Math.round(el.getBoundingClientRect().height),
                   ancho: Math.round(el.getBoundingClientRect().width)}));
  const letraPequena = [...document.querySelectorAll('p, span, li, td, small, label, div')]
    .filter((el) => el.children.length === 0 && (el.textContent || '').trim())
    .filter((el) => parseFloat(getComputedStyle(el).fontSize) < 12)
    .length;
  const truncados = [...document.querySelectorAll('body *')]
    .filter((el) => el.children.length === 0 && (el.textContent || '').trim()
                    && el.clientWidth > 0 && el.scrollWidth > el.clientWidth + 1)
    .slice(0, 8)
    .map((el) => ({texto: (el.textContent || '').trim().slice(0, 70),
                   ancho: el.clientWidth, contenido: el.scrollWidth,
                   corte: getComputedStyle(el).textOverflow}));
  const imagenes = [...document.images];
  return {
    titulo: document.title,
    desborde_horizontal: Math.max(doc.scrollWidth, document.body.scrollWidth) - vw,
    desbordes,
    recortados: truncados.length,
    ejemplos_recortados: truncados,
    imagenes: imagenes.length,
    imagenes_rotas: imagenes.filter((i) => i.complete && i.naturalWidth === 0).length,
    controles_pequenos: pequenos.length,
    ejemplos_controles_pequenos: pequenos.slice(0, 5),
    letra_menor_12: letraPequena,
    alto_documento: doc.scrollHeight,
  };
}
"""


def captura(solo: set[str] | None = None) -> dict:
    SALIDA.mkdir(parents=True, exist_ok=True)
    c = sesion()
    datos = siembra(c)
    print(f"lista {datos['lista_id']} · {datos['lineas']} líneas · "
          f"{len(datos['favoritos'])} favoritos · receta {datos['receta_id']}")

    prod = producto_de(datos.get("grupo"))
    rutas: list[tuple[str, str]] = []
    for nombre, ruta in PANTALLAS:
        if nombre == "03-ficha-producto":
            ruta = f"/compra/productos/{prod[0]}/{prod[1]}" if prod else "/compra?q=leche"
        elif nombre == "04-comparar-grupo":
            ruta = f"/compra/comparar/{datos['grupo_id']}" if datos["grupo_id"] else "/compra?q=leche"
        elif nombre == "05-lista":
            ruta = f"/compra/listas/{datos['lista_id']}"
        elif nombre == "06-comparar-cesta":
            ruta = f"/compra/listas/{datos['lista_id']}/comparar"
        elif nombre == "10-receta":
            ruta = f"/recetas/{datos['receta_id']}" if datos["receta_id"] else "/recetas"
        rutas.append((nombre, ruta))

    cookie = c.cookies.get("cesta_sesion")
    manifiesto = {
        "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
        "api": API, "ui": UI,
        "cuenta": USUARIO, "lista": datos["lista_id"],
        "producto": prod, "grupo": datos["grupo_id"], "receta": datos["receta_id"],
        "pantallas": [],
    }

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)

        def nuevo_contexto(ancho: int, alto: int, movil: bool):
            ctx = navegador.new_context(
                viewport={"width": ancho, "height": alto},
                device_scale_factor=2,
                is_mobile=movil,
                has_touch=movil,
                locale="es-ES",
                timezone_id="Europe/Madrid",
            )
            ctx.add_cookies([{"name": "cesta_sesion", "value": cookie,
                              "domain": "127.0.0.1", "path": "/"}])
            return ctx

        ctx_movil = nuevo_contexto(390, 844, True)
        ctx_escritorio = nuevo_contexto(1440, 900, False)
        # La puerta de sesión, sin cookie: es la pantalla que ve quien no ha entrado.
        ctx_anonimo = navegador.new_context(
            viewport={"width": 390, "height": 844}, device_scale_factor=2,
            is_mobile=True, has_touch=True, locale="es-ES", timezone_id="Europe/Madrid")

        def mide(pagina, nombre: str, sufijo: str) -> dict:
            errores: list[str] = []
            pagina.on("console", lambda m: errores.append(f"consola {m.type}: {m.text[:200]}")
                      if m.type == "error" else None)
            pagina.on("requestfailed", lambda r: errores.append(f"petición fallida: {r.url[:160]}"))
            pagina.goto(f"{UI}{ruta}", wait_until="domcontentloaded", timeout=90000)
            with contextlib.suppress(ErrorNavegador):
                # Hay pantallas que no llegan a quedarse quietas: no es un fallo, se sigue.
                pagina.wait_for_load_state("networkidle", timeout=20000)
            # El esqueleto de carga no es la pantalla: se espera a que desaparezca.
            limite = time.time() + 30
            while time.time() < limite:
                with contextlib.suppress(ErrorNavegador):
                    texto = pagina.inner_text("body")
                    if "Cargando" not in texto:
                        break
                time.sleep(0.5)
            time.sleep(0.8)
            medidas = pagina.evaluate(MEDIDA_JS)
            archivo = SALIDA / f"{nombre}-{sufijo}.png"
            pagina.screenshot(path=str(archivo), full_page=True)
            visible = SALIDA / f"{nombre}-{sufijo}-visible.png"
            pagina.screenshot(path=str(visible), full_page=False)
            (SALIDA / "textos").mkdir(exist_ok=True)
            (SALIDA / "textos" / f"{nombre}-{sufijo}.txt").write_text(
                pagina.inner_text("body"), encoding="utf-8")
            medidas |= {"errores": errores[:6], "archivo": str(archivo.relative_to(RAIZ)),
                        "visible": str(visible.relative_to(RAIZ)),
                        "ancho": pagina.viewport_size["width"],
                        "alto": pagina.viewport_size["height"],
                        "bytes": archivo.stat().st_size}
            return medidas

        for nombre, ruta in rutas:
            if solo and nombre not in solo:
                continue
            print(f"· {nombre} {ruta}")
            ctx = ctx_anonimo if nombre == "23-entrar" else ctx_movil
            fila = {"nombre": nombre, "ruta": ruta, "movil": mide(ctx.new_page(), nombre, "movil")}
            if nombre in ESCRITORIO:
                fila["escritorio"] = mide(ctx_escritorio.new_page(), nombre, "escritorio")
            manifiesto["pantallas"].append(fila)

        navegador.close()

    if solo:
        # Recapturar una pantalla suelta no puede borrar el inventario de las demás.
        previo = SALIDA / "manifiesto.json"
        if previo.exists():
            anterior = json.loads(previo.read_text(encoding="utf-8"))
            hechas = {p["nombre"] for p in manifiesto["pantallas"]}
            manifiesto["pantallas"] = sorted(
                [p for p in anterior.get("pantallas", []) if p["nombre"] not in hechas]
                + manifiesto["pantallas"],
                key=lambda p: p["nombre"])
            manifiesto |= {k: v for k, v in anterior.items()
                           if k not in ("pantallas",) and k not in manifiesto}

    (SALIDA / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(manifiesto['pantallas'])} pantallas en {SALIDA}")
    return manifiesto


if __name__ == "__main__":
    if "--comprobar" in sys.argv:
        # Solo la siembra: para saber si el entorno está bien.
        c = sesion()
        print(siembra(c))
        sys.exit(0)
    solo = None
    for i, arg in enumerate(sys.argv):
        if arg == "--solo" and i + 1 < len(sys.argv):
            solo = {x.strip() for x in sys.argv[i + 1].split(",") if x.strip()}
    captura(solo)
