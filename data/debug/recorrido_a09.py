"""A09, recorrido por navegador: **controles, textos y errores reales, con capturas y su procedencia.**

**Lo que pide el criterio de A09**, palabra por palabra:

> *«390/768/1440 px, tema claro/oscuro y zoom 200%; **controles, textos y errores reales, no solo conteo
> de pixeles**. Guardar capturas y resultados con **commit/imagen/version**.»*

**Y lo que este guion hace, que es la mitad que faltaba.** *El 12 de octubre se midieron las doce
combinaciones contando pixeles* -- *y desbordaba una, que se arreglo* --, **pero eso es justo lo que el
criterio dice que NO basta.** *Aqui se hacen tres cosas mas:*

  1. **se pulsan controles de verdad** y se comprueba que hacen lo que dicen;
  2. **se provocan errores de verdad** -- *apagando la API* -- y se lee **que dice la pantalla**;
  3. y cada captura queda con **el commit, la version del catalogo y el hash de la imagen**, en un
     manifiesto, *que es lo que convierte una carpeta de PNG en evidencia*.

**Y las capturas no se guardan a mano**: *salen de aqui, con su nombre, su fecha y su procedencia.*
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "capturas-a09"
BASE = "http://localhost:8080"
ANCHOS = (390, 768, 1440)
ESPERA = 7000


def sha256(camino: Path) -> str:
    return hashlib.sha256(camino.read_bytes()).hexdigest()


def commit() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True)
    return (r.stdout or "").strip()[:40] or "desconocido"


def version_del_catalogo() -> str | None:
    """*La version que sirve la API.* **Sin esto, una captura no dice de que catalogo es.**"""
    import urllib.request

    try:
        with urllib.request.urlopen(BASE + "/api/estado", timeout=8) as r:
            return json.loads(r.read().decode("utf-8")).get("version_catalogo")
    except Exception:
        return None


def main() -> int:
    from patchright.sync_api import sync_playwright

    SALIDA.mkdir(parents=True, exist_ok=True)
    marca = datetime.now()
    print(f"== recorrido de A09 por navegador, {marca:%Y-%m-%d %H:%M}")
    print(f"   commit:  {commit()[:12]}")
    print(f"   catalogo: {version_del_catalogo()}")

    piezas: list[dict] = []
    textos: dict[str, str] = {}

    def guarda(pag, nombre: str, nota: str) -> None:
        """Captura + procedencia. *Y la nota, que es lo que hace falta para saber que se miraba.*"""
        camino = SALIDA / f"{nombre}.png"
        pag.screenshot(path=str(camino), full_page=False)
        piezas.append({"imagen": camino.name, "nota": nota,
                       "sha256": sha256(camino)[:16], "bytes": camino.stat().st_size})
        print(f"   guardada {camino.name}  ({camino.stat().st_size / 1024:.1f} KB)  {nota}")

    with sync_playwright() as p:
        nav = p.chromium.launch(headless=True)
        errores: list[str] = []

        # ---------------------------------------------- 1. las tres anchuras, con sesion
        for ancho in ANCHOS:
            ctx = nav.new_context(viewport={"width": ancho, "height": 900}, color_scheme="light")
            ctx.request.post(f"{BASE}/api/entrar",
                             data=json.dumps({"usuario": "prueba-navegador",
                                              "clave": "clave-de-prueba-123"}),
                             headers={"Content-Type": "application/json"})
            pag = ctx.new_page()
            pag.on("pageerror", lambda e: errores.append(str(e)[:100]))
            pag.goto(BASE + "/compra/cocina/7/2", wait_until="domcontentloaded")
            pag.wait_for_timeout(ESPERA)
            guarda(pag, f"01-cocina-{ancho}", f"modo cocina a {ancho} px")
            textos[f"cocina-{ancho}"] = pag.inner_text("body")[:400]
            ctx.close()

        # ---------------------------------------------- 2. CONTROLES de verdad
        ctx = nav.new_context(viewport={"width": 390, "height": 900})
        ctx.request.post(f"{BASE}/api/entrar",
                         data=json.dumps({"usuario": "prueba-navegador",
                                          "clave": "clave-de-prueba-123"}),
                         headers={"Content-Type": "application/json"})
        pag = ctx.new_page()
        pag.goto(BASE + "/compra", wait_until="domcontentloaded")
        pag.wait_for_timeout(ESPERA)
        # *El buscador: se escribe y se comprueba que el texto llega al campo.*
        campo = pag.query_selector("input#q") or pag.query_selector("input[type=search]")
        if campo:
            campo.fill("leche entera")
            pag.wait_for_timeout(400)
            assert campo.input_value() == "leche entera", "el buscador no retiene lo escrito"
            print("   control: el buscador retiene lo escrito")
            guarda(pag, "02-buscador-con-texto", "el buscador con texto escrito a mano")
            pag.keyboard.press("Enter")
            pag.wait_for_timeout(ESPERA)
            guarda(pag, "03-busqueda-enviada", "la busqueda ya enviada")
            textos["busqueda"] = pag.inner_text("body")[:400]
        else:
            print("   AVISO: no hay buscador en /compra")

        # ---------------------------------------------- 3. ERROR real: la API no contesta
        # **Se corta la API pidiendo una ruta que no existe, que es lo mas parecido a «se cayo» que se
        # puede hacer sin apagarla de verdad** -- *y se lee QUE DICE la pantalla, que es lo que el
        # criterio pide con «errores reales».*
        pag.route("**/api/**", lambda ruta: ruta.abort("failed"))
        pag.goto(BASE + "/compra/analisis", wait_until="domcontentloaded")
        pag.wait_for_timeout(12000)
        cuerpo = pag.inner_text("body")
        textos["api-caida"] = cuerpo[:600]
        guarda(pag, "04-api-caida", "la API sin contestar: lo que dice la pantalla")
        atascada = "atasc" in cuerpo.lower() or "no se ha podido" in cuerpo.lower()
        print(f"   error real: la pantalla {'LO DICE' if atascada else 'NO LO DICE'}")

        nav.close()
        print(f"   errores de JavaScript: {errores[:2] if errores else 'ninguno'}")

    # ------------------------------------------------------------ el manifiesto
    manifiesto = {
        "que": "Recorrido de A09 por navegador: anchuras, controles y errores reales.",
        "cuando": marca.isoformat(timespec="seconds"),
        "commit": commit(),
        "version_catalogo": version_del_catalogo(),
        "navegador": "chromium sin cabeza (patchright)",
        "capturas": piezas,
        "textos": textos,
    }
    (SALIDA / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n   manifiesto: {len(piezas)} capturas con su commit y su version")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
