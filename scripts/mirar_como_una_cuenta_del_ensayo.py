"""*** Mirar la interfaz COMO UNA CUENTA DEL BANCO DE ENSAYO. ***

*Es lo que faltaba para poder revisar en pantalla sin tocar casa.*

*El problema que resuelve: levantar el ensayo (M00) no es entrar como una de sus personas.* *La
sesion es una cookie (`cesta_sesion`, httponly) que pone `POST /api/entrar`.* *Y `/compra` no
enseña formulario cuando ya hay una sesion previa del navegador, asi que desde fuera no habia forma
de cambiar de persona.*

*Este guion hace las cuatro cosas, en este orden:*

    1. prepara y siembra el ensayo (`plataforma.ensayo`)
    2. levanta la API en 8109 apuntando al DSN y al gold del ensayo
    3. entra con `POST /api/entrar` y se queda con la cookie
    4. abre el navegador con esa cookie y mide las pantallas que se le pidan

*Y al final lo desmonta todo, como el propio ensayo.*

*NO toca casa, NO toca facylf, y NO publica nada: todo en loopback.*
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUERTO = 8109
INTERFAZ = 5174


def _orden(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "plataforma.ensayo", *args], cwd=RAIZ, check=True)


def _espera(puerto: int, segundos: float = 40) -> bool:
    import socket

    # *** SE PRUEBAN LAS DOS FAMILIAS DE DIRECCIONES. ***
    # *Vite en Windows escucha en `::1` (IPv6) aunque se le diga `127.0.0.1`.* *Comprobarlo solo
    # contra `127.0.0.1` da «no arranco» cuando si arranco, y eso ya me paso mirando la interfaz a
    # mano: el primer intento dio ERR_CONNECTION_REFUSED y hubo que usar `localhost`.*
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        for donde in ("127.0.0.1", "::1", "localhost"):
            try:
                with socket.socket(socket.AF_INET6 if ":" in donde else socket.AF_INET) as s:
                    s.settimeout(0.4)
                    if s.connect_ex((donde, puerto)) == 0:
                        return True
            except OSError:
                continue
        time.sleep(0.5)
    return False


def _entra(usuario: str, clave: str) -> str:
    """*Devuelve el valor de la cookie de sesion.*"""
    cuerpo = json.dumps({"usuario": usuario, "clave": clave}).encode()
    pet = urllib.request.Request(
        f"http://127.0.0.1:{PUERTO}/api/entrar",
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(pet, timeout=20) as r:
        galletas = r.headers.get_all("Set-Cookie") or []
    for g in galletas:
        if g.startswith("cesta_sesion="):
            return g.split(";")[0].split("=", 1)[1]
    raise RuntimeError("no vino la cookie de sesion: " + str(galletas))


def main() -> int:
    usuario = sys.argv[1] if len(sys.argv) > 1 else "c_sin_listas"
    clave = sys.argv[2] if len(sys.argv) > 2 else "prueba-larga-1"
    rutas = sys.argv[3:] or ["/compra", "/grupo/900001", "/favoritos"]

    print("== 1. el ensayo ==")
    _orden("prepara", "propio")
    _orden("siembra", "propio")
    man = json.loads((RAIZ / "data/ensayo/propio.manifiesto.json").read_text(encoding="utf-8"))

    print("== 2. la API, con el DSN y el gold del ensayo ==")
    entorno = dict(os.environ, CESTA_POSTGRES=man["dsn"], CESTA_GOLD=man["gold"])
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "plataforma.api.main:app",
         "--host", "127.0.0.1", "--port", str(PUERTO)],
        cwd=RAIZ, env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    interfaz = None
    try:
        if not _espera(PUERTO):
            print("la API no arranco")
            return 1

        print("== 3. entrar como " + usuario + " ==")
        token = _entra(usuario, clave)
        print("   cookie obtenida (" + str(len(token)) + " caracteres)")

        print("== 4. el navegador, con esa cookie ==")
        entorno_web = dict(entorno, CESTA_API=f"http://127.0.0.1:{PUERTO}")
        interfaz = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", str(INTERFAZ)],
            cwd=RAIZ / "plataforma" / "web" / "app",
            env=entorno_web, shell=True,
            # *** GRUPO DE PROCESOS PROPIO, PARA PODER MATAR EL ARBOL. ***
            # *`npm run dev` arranca un hijo (Vite) que NO muere al matar el shell: con
            # `terminate()` quedaba un servidor escuchando en el puerto despues de «desmontar».*
            # *Medido: el 5174 seguia arriba tras la primera pasada.*
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if not _espera(INTERFAZ, 60):
            print("la interfaz no arranco")
            return 1

        from patchright.sync_api import sync_playwright

        with sync_playwright() as p:
            nav = p.chromium.launch(headless=True)
            ctx = nav.new_context(viewport={"width": 1280, "height": 900}, locale="es-ES")
            ctx.add_cookies([{
                "name": "cesta_sesion", "value": token,
                "domain": "localhost", "path": "/", "httpOnly": True, "sameSite": "Lax",
            }])
            pg = ctx.new_page()
            errores: list[str] = []
            pg.on("pageerror", lambda e: errores.append(str(e)[:80]))
            for ruta in rutas:
                pg.goto(f"http://localhost:{INTERFAZ}{ruta}", wait_until="domcontentloaded")
                pg.wait_for_timeout(6000)
                texto = pg.inner_text("body")
                print(f"   {ruta:20} main={pg.locator('main').count()} "
                      f"texto={len(texto):5} errores={errores}")
                for linea in texto.split("\n"):
                    if any(x in linea for x in
                           ("Diferencia", "sin dato", "del grupo", "Elige", "de casa",
                            "articulos distintos", "formatos diferentes")):
                        print("        | " + linea.strip()[:110])
            ctx.close()
            nav.close()
        return 0
    finally:
        for proceso in (interfaz, api):
            if proceso is None:
                continue
            # *En Windows, `taskkill /T` mata el arbol entero: el guion, npm y Vite.*
            if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proceso.pid)],
                               capture_output=True, check=False)
            else:
                proceso.terminate()
            try:
                proceso.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proceso.kill()
        print("== desmontando el ensayo ==")
        _orden("limpia", "propio")


if __name__ == "__main__":
    raise SystemExit(main())
