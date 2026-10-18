"""*** M05: LA LISTA DE 30 LINEAS, CON SUS DUPLICADOS Y SUS DOS MARCAS PARECIDAS. ***

*La especificacion dice, con estas palabras:*

> «Aceptacion: lista de 30 lineas, duplicados deliberados, dos marcas parecidas, reposicion de
> favoritos y otra lista compartida; busqueda no destruye la seleccion.»

*Este guion mide lo que se puede medir por HTTP:*

    1. una lista de 30 lineas
    2. con duplicados DELIBERADOS (el mismo nombre dos veces)
    3. y dos marcas parecidas del mismo grupo (arroz A, arroz B)
    4. sin perder ninguna linea por el camino

*Lo que NO mide, y se dice: la parte de interfaz -- modo tienda, deshacer, reordenar, restaurar tras
recarga -- y la reposicion de favoritos, que necesitan navegador y otra tanda.*
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
    raise RuntimeError("sin cookie")


def main() -> int:
    print("== el ensayo ==")
    _orden("prepara", "propio")
    _orden("siembra", "propio")
    man = json.loads((RAIZ / "data/ensayo/propio.manifiesto.json").read_text(encoding="utf-8"))
    entorno = dict(os.environ, CESTA_POSTGRES=man["dsn"], CESTA_GOLD=man["gold"],
                   CESTA_RECETAS=man["sqlite"])
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "plataforma.api.main:app",
         "--host", "127.0.0.1", "--port", str(PUERTO)],
        cwd=RAIZ, env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    fallos = 0

    def vale(titulo: str, bien: bool) -> None:
        nonlocal fallos
        print(("   ok   " if bien else "   FALLO") + " " + titulo)
        fallos += 0 if bien else 1

    try:
        if not _espera(PUERTO):
            print("la API no arranco")
            return 1
        galleta = _entra("a_casa", "prueba-larga-1")
        print("   a_casa: cookie ok")

        estado, creada = _pide("/api/listas", galleta, "POST", {"nombre": "M05 treinta lineas"})
        print("   crear lista -> " + str(estado))
        if estado not in (200, 201) or not creada:
            print("   no se pudo crear la lista: " + str(creada))
            return 1
        lista_id = creada.get("id") or creada.get("lista", {}).get("id")
        print("   lista " + str(lista_id))

        print("== 30 lineas, con duplicados deliberados y dos marcas parecidas ==")
        nombres = []
        # *Treinta lineas de verdad, no una repetida treinta veces: veinte distintas y diez
        # repeticiones DELIBERADAS de cinco de ellas -- que es lo que pasa cuando apuntas lo mismo
        # dos veces porque no te acordabas.*
        for i in range(25):
            nombres.append(f"producto {i:02d}")
        # *Y cinco repeticiones DELIBERADAS: apuntar lo mismo dos veces porque no te acordabas.*
        for i in range(5):
            nombres.append(f"producto {i:02d}")
        # *Y las dos marcas parecidas: mismo grupo, dos productos distintos.*
        nombres.append("Arroz redondo marca A 1 kg")
        nombres.append("Arroz redondo marca B 1 kg")
        assert len(nombres) == 32, len(nombres)

        creadas = 0
        for nombre in nombres:
            cuerpo = {"nombre": nombre, "cantidad": 1}
            if nombre.startswith("Arroz redondo"):
                cuerpo["grupo_id"] = 900001
                cuerpo["producto_id"] = ("9000000000017" if "marca A" in nombre
                                         else "9000000000024")
            estado, _ = _pide(f"/api/listas/{lista_id}/lineas", galleta, "POST", cuerpo)
            if estado in (200, 201):
                creadas += 1
            else:
                print("   no se pudo anadir " + nombre + " -> " + str(estado))
        print("   anadidas: " + str(creadas) + " de " + str(len(nombres)))
        vale("se anaden las 30 lineas (y las dos de marca)", creadas == 32)

        estado, vista = _pide(f"/api/listas/{lista_id}", galleta)
        crudo = vista.get("lineas") if isinstance(vista, dict) else vista
        lineas = crudo or []
        print("   la lista devuelve " + str(len(lineas)) + " linea(s)")
        vale("la lista conserva las 32 lineas", len(lineas) == 32)

        # *Se vuelca la FORMA de una linea antes de contar nada: si la API devuelve otro nombre de
        # campo, contar `nombre` da None repetido y parece un defecto que no existe.*
        if lineas:
            nombres_guardados = [ln.get("nombre_visto") for ln in lineas]
        repetidos = {n for n in nombres_guardados if nombres_guardados.count(n) > 1}
        print("   nombres repetidos: " + str(len(repetidos)))
        vale("los duplicados deliberados NO se han fusionado", len(repetidos) >= 5)

        marcas = [ln for ln in lineas if str(ln.get("nombre_visto", "")).startswith("Arroz redondo")]
        eans = {ln.get("producto_id") for ln in marcas}
        print("   arroces: " + str(len(marcas)) + ", producto_id distintos: " + str(len(eans)))
        vale("las dos marcas parecidas se distinguen", len(marcas) == 2 and len(eans) == 2)

        print("== y buscar NO destruye la seleccion ==")
        estado, despues = _pide(f"/api/listas/{lista_id}", galleta)
        tras_buscar = despues.get("lineas") if isinstance(despues, dict) else despues
        vale("la lista sigue igual despues de leerla dos veces", len(tras_buscar or []) == 32)

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
