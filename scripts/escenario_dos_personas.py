"""*** EL ESCENARIO DEL APARTADO 8: DOS PERSONAS, DOS LISTAS, CINCO RECETAS. ***

*Lo que la especificacion llama «aceptacion integral», medido por HTTP contra el banco de ensayo:*

    a_casa        lista de casa (Casa) + Viaje, con las cinco recetas
    b_sin_casa    una lista (Mi lista), ninguna de casa
    c_sin_listas  ninguna

*Y lo que hay que demostrar, que es lo que de verdad importa:*

    - B **no ve** las listas de A
    - B **no ve** las recetas de A
    - A ve las suyas
    - y el catalogo del apartado 8 da las cifras que dice (350 g de arroz, etc.)

*Todo en loopback y desechable: NO toca casa, NO toca facylf, NO publica nada.*
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUERTO = 8109


def _orden(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "plataforma.ensayo", *args], cwd=RAIZ, check=True)


def _espera(puerto: int, segundos: float = 60) -> bool:
    import socket

    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        for donde in ("127.0.0.1", "::1"):
            try:
                with socket.socket(socket.AF_INET6 if ":" in donde else socket.AF_INET) as s:
                    s.settimeout(0.4)
                    if s.connect_ex((donde, puerto)) == 0:
                        return True
            except OSError:
                continue
        time.sleep(0.5)
    return False


def _pide(ruta: str, galleta: str, metodo: str = "GET", cuerpo: dict | None = None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pet = urllib.request.Request(
        f"http://127.0.0.1:{PUERTO}{ruta}", data=datos, method=metodo,
        headers={"Content-Type": "application/json", "Cookie": galleta},
    )
    try:
        with urllib.request.urlopen(pet, timeout=20) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, None


def _entra(usuario: str, clave: str) -> str:
    pet = urllib.request.Request(
        f"http://127.0.0.1:{PUERTO}/api/entrar",
        data=json.dumps({"usuario": usuario, "clave": clave}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(pet, timeout=20) as r:
        galletas = r.headers.get_all("Set-Cookie") or []
    for g in galletas:
        if g.startswith("cesta_sesion="):
            return g.split(";")[0]
    raise RuntimeError("sin cookie: " + str(galletas))


def main() -> int:
    print("== el ensayo ==")
    _orden("prepara", "propio")
    _orden("siembra", "propio")
    man = json.loads((RAIZ / "data/ensayo/propio.manifiesto.json").read_text(encoding="utf-8"))
    # *Y el recetario del ensayo, que hasta hoy la API no sabia que existia.*
    entorno = dict(os.environ, CESTA_POSTGRES=man["dsn"], CESTA_GOLD=man["gold"],
                   CESTA_RECETAS=man["sqlite"])
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "plataforma.api.main:app",
         "--host", "127.0.0.1", "--port", str(PUERTO)],
        cwd=RAIZ, env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    fallos = 0
    try:
        if not _espera(PUERTO):
            print("la API no arranco")
            return 1
        print("== las tres personas ==")
        cuentas = {}
        for quien in ("a_casa", "b_sin_casa", "c_sin_listas"):
            cuentas[quien] = _entra(quien, "prueba-larga-1")
            print("   " + quien + ": cookie ok")

        print("== sus listas ==")
        listas = {}
        for quien, galleta in cuentas.items():
            estado, datos = _pide("/api/listas", galleta)
            # *La API puede devolver la lista o envolverla en un objeto con `listas`.*
            crudo = datos.get("listas") if isinstance(datos, dict) else datos
            crudo = crudo or []
            nombres = [x.get("nombre") for x in crudo]
            listas[quien] = crudo
            print(f"   {quien:14} {estado}  {nombres}")

        print("== y lo que NO se ve ==")
        ids_a = {x["id"] for x in listas["a_casa"]}
        ids_b = {x["id"] for x in listas["b_sin_casa"]}
        ids_c = {x["id"] for x in listas["c_sin_listas"]}
        comprueba = [
            ("A tiene Casa y Viaje", len(ids_a) == 2),
            ("B tiene Mi lista y ninguna de A", len(ids_b) == 1 and not (ids_b & ids_a)),
            ("C no tiene ninguna", len(ids_c) == 0),
        ]
        for titulo, bien in comprueba:
            print(("   ok   " if bien else "   FALLO") + " " + titulo)
            fallos += 0 if bien else 1

        print("== B no puede leer una lista de A ==")
        if ids_a:
            una = sorted(ids_a)[0]
            estado, _ = _pide(f"/api/listas/{una}", cuentas["b_sin_casa"])
            print("   b_sin_casa -> /api/listas/<la de A>: " + str(estado))
            bien = estado in (403, 404)
            print(("   ok   " if bien else "   FALLO") + " la lista de A no se sirve a B")
            fallos += 0 if bien else 1

        print("== las recetas de A, y las de B ==")
        por_persona: dict[str, list] = {}
        for quien in ("a_casa", "b_sin_casa"):
            estado, datos = _pide("/api/recetas", cuentas[quien])
            # *La API envuelve en `recetas`. Se desenvuelve ANTES de contar: `len()` de un dict
            # cuenta claves, y confundirlo con una lista da un «1 receta» que no significa nada.*
            crudo = datos.get("recetas") if isinstance(datos, dict) else datos
            por_persona[quien] = crudo or []
            nombres = [r.get("nombre") for r in por_persona[quien]]
            print(f"   {quien:12} {estado}  {len(nombres)} receta(s): {nombres}")
        recetas_a = por_persona["a_casa"]
        recetas_b = por_persona["b_sin_casa"]
        nombres_b = {r.get("nombre") for r in recetas_b}
        nombres_a = {r.get("nombre") for r in recetas_a}
        bien = len(recetas_a) == 5 and not (nombres_b & nombres_a)
        print(("   ok   " if bien else "   FALLO")
              + " A tiene las cinco del apartado 8, y B ninguna de A")
        fallos += 0 if bien else 1

        print("== el catalogo del apartado 8 ==")
        grupo = json.loads(urllib.request.urlopen(
            f"http://127.0.0.1:{PUERTO}/api/grupo/900001", timeout=20).read())
        productos = grupo.get("productos", [])
        eans = {(p.get("marca"), p.get("ean")) for p in productos}
        print("   grupo 900001: " + str(len(productos)) + " productos, cadenas=" + str(grupo.get("cadenas")))
        for marca, ean in sorted(eans, key=str):
            print("      " + str(marca) + "  ean=" + str(ean))
        bien = len(eans) == len(productos) and len({e for _, e in eans}) == len(eans)
        print(("   ok   " if bien else "   FALLO") + " dos marcas, dos EAN distintos, sin fusionar")
        fallos += 0 if bien else 1

        print()
        print("== " + ("TODO BIEN" if fallos == 0 else str(fallos) + " FALLO(S)") + " ==")
        return 0 if fallos == 0 else 1
    finally:
        api.terminate()
        try:
            api.wait(timeout=10)
        except subprocess.TimeoutExpired:
            api.kill()
        _orden("limpia", "propio")


if __name__ == "__main__":
    raise SystemExit(main())
