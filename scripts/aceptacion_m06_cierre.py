"""*** M06 POR HTTP: COTIZACION -> CONFIRMACION -> PERSISTENCIA. ***

*La regla 6 del contrato lo dice con estas palabras:*

> «La prueba del endpoint debe invocar el endpoint o cliente HTTP real sobre sandbox. Construir un
> diccionario esperado dentro del test no demuestra que devuelve `/cerrar`.»

*Y la 2: «cerrarCompra() todavia no envia sello y el endpoint permite omitirlo y escribir igualmente».

*Esto lo mide contra un servidor de verdad, con su base y su catalogo:*

    1. apuntar una linea y ponerla en el carro
    2. pedir la lista -> trae `cotizacion.sello`
    3. cerrar SIN sello            -> `confirmado: false` (compatibilidad, no certificado)
    4. cerrar con un sello FALSO   -> **409**, y **no se escribe** ninguna compra
    5. cerrar con el sello bueno   -> `confirmado: true`, y aparece una compra

*Todo en loopback y desechable: no toca casa, facylf ni 5432/5433/5434.*
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
sys.path.insert(0, str(RAIZ))
PUERTO = 8110


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
        with urllib.request.urlopen(pet, timeout=25) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"null")
        except Exception:  # noqa: BLE001
            return exc.code, None


def main() -> int:
    print("== el ensayo ==")
    _orden("prepara", "propio")
    _orden("siembra", "propio")
    man = json.loads((RAIZ / "data/ensayo/propio.manifiesto.json").read_text(encoding="utf-8"))
    # *** EL GOLD DEL ENSAYO ESTA FECHADO EL 1 DE ENERO, Y LA VENTANA ES DE 3 DIAS. ***
    # *O sea que hoy (18/10/2026) el catalogo del banco tiene 290 dias y **ningun precio vale**:
    # todas las lineas salen `sin_precio` y la cesta cotiza 0.*
    # *No es un fallo de la aplicacion -- con un catalogo viejo no hay precio, y decirlo es lo
    # correcto --, pero deja el banco sin poder probar el cierre con dinero.*
    # *Se abre la ventana **solo para el ensayo**: la aplicacion de casa sigue con sus 3 dias.*
    entorno = dict(os.environ, CESTA_POSTGRES=man["dsn"], CESTA_GOLD=man["gold"],
                   CESTA_RECETAS=man["sqlite"], CESTA_DIAS_PRECIO="100000")
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
        pet = urllib.request.Request(
            f"http://127.0.0.1:{PUERTO}/api/entrar",
            data=json.dumps({"usuario": "a_casa", "clave": "prueba-larga-1"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pet, timeout=20) as r:
            galletas = r.headers.get_all("Set-Cookie") or []
        galleta = next(g.split(";")[0] for g in galletas if g.startswith("cesta_sesion="))
        print("   a_casa: cookie ok")

        estado, listas = _pide("/api/listas", galleta)
        crudo = listas.get("listas") if isinstance(listas, dict) else listas
        lid = crudo[0]["id"]
        estado, nueva = _pide(f"/api/listas/{lid}/lineas", galleta, "POST",
                              {"nombre": "Arroz redondo marca A 1 kg", "grupo_id": 900001,
                               "producto_id": "ensayo:arroz-a"})
        _pide(f"/api/listas/{lid}/lineas/{nueva['id']}", galleta, "PATCH", {"en_carrito": True})
        print("   lista preparada: 1 linea en el carro")

        print("== la cotizacion del carrito ==")
        estado, detalle = _pide(f"/api/listas/{lid}", galleta)
        cot = (detalle or {}).get("cotizacion") or {}
        sello = cot.get("sello")
        print("   sello=" + str(sello) + "  total=" + str(cot.get("total_cent"))
              + "  sin_precio=" + str(cot.get("sin_precio"))
              + "  lineas=" + str(cot.get("lineas"))
              + "  lista_entera=" + str((detalle or {}).get("cotizacion_lista_cent")))
        vale("la lista trae la cotizacion con su sello", bool(sello))

        print("== cerrar SIN sello (compatibilidad) ==")
        estado, r = _pide(f"/api/listas/{lid}/cerrar", galleta, "POST")
        print("   -> " + str(estado) + "  confirmado=" + str((r or {}).get("confirmado"))
              + "  estimado=" + str((r or {}).get("estimado_cent")))
        vale("sin sello se puede cerrar, pero NO se marca confirmado",
             estado < 300 and (r or {}).get("confirmado") is False
             and (r or {}).get("estimado_cent") is None)
        vale("el importe dice de donde sale",
             (r or {}).get("procedencia_importe") == "calculado")

        print("== cerrar con un sello FALSO: 409 y sin escribir ==")
        _pide(f"/api/listas/{lid}/lineas", galleta, "POST",
              {"nombre": "Arroz redondo marca B 1 kg", "grupo_id": 900001,
               "producto_id": "ensayo:arroz-b"})
        estado, detalle2 = _pide(f"/api/listas/{lid}", galleta)
        lineas2 = (detalle2 or {}).get("lineas") or []
        ultima = lineas2[-1]["id"] if lineas2 else None
        if ultima:
            _pide(f"/api/listas/{lid}/lineas/{ultima}", galleta, "PATCH", {"en_carrito": True})
        _antes, compras_antes = _pide(f"/api/listas/{lid}/compras", galleta)
        # *La cotizacion se pide DESPUES de meter la linea en el carrito: si se pide antes,
        # el sello es el de un carrito vacio -- el sha256 de la cadena vacia -- y el cierre
        # contesta 409 por un motivo que no existe.* *Costo dos vueltas verlo.*
        _, detalle3 = _pide(f"/api/listas/{lid}", galleta)
        sello_bueno = ((detalle3 or {}).get("cotizacion") or {}).get("sello")
        print("   cotizacion del carrito: " + str((detalle3 or {}).get("cotizacion") or {}))
        estado, r = _pide(f"/api/listas/{lid}/cerrar?sello_esperado=NO-ES-EL-SELLO", galleta, "POST")
        print("   -> " + str(estado) + "  detail=" + str((r or {}).get("detail"))[:80])
        vale("un sello que no coincide da 409", estado == 409)
        _, compras_despues = _pide(f"/api/listas/{lid}/compras", galleta)
        cuantas_antes = len((compras_antes or {}).get("compras") or compras_antes or [])
        cuantas_despues = len((compras_despues or {}).get("compras") or compras_despues or [])
        print("   compras antes=" + str(cuantas_antes) + "  despues=" + str(cuantas_despues))
        vale("el 409 NO ha escrito ninguna compra", cuantas_despues == cuantas_antes)

        print("== cerrar con el sello bueno ==")
        estado, r = _pide(f"/api/listas/{lid}/cerrar?sello_esperado={sello_bueno}", galleta, "POST")
        nuevo = ((r or {}).get("detail") or {}).get("cotizacion_nueva") or {}
        print("   -> " + str(estado) + "  confirmado=" + str((r or {}).get("confirmado"))
              + "  diferencia=" + str((r or {}).get("diferencia_cent")))
        # *El 409 trae la cotizacion nueva: comparar los dos sellos dice si el conjunto cambio.*
        print("   sello que envie .... " + str(sello_bueno))
        print("   sello que hay ...... " + str(nuevo.get("sello")))
        print("   total cotizado ..... " + str(nuevo.get("total_cent"))
              + "  lineas=" + str(nuevo.get("lineas")))
        vale("con el sello bueno cierra y queda confirmado",
             estado < 300 and (r or {}).get("confirmado") is True)
        vale("con el sello bueno la diferencia es cero, no null",
             (r or {}).get("diferencia_cent") == 0)

        # *** CAMBIO ENTRE LA COMPROBACION Y LA PERSISTENCIA (regla 3). ***
        # *No entre dos llamadas a funciones: **entre la previa que se sirvio y el cierre**.* *Se
        # publica un catalogo nuevo con otro precio para el mismo producto, y el sello -- que ahora
        # lleva la version del catalogo -- deja de valer.*
        print("== cambiar el catalogo DESPUES de la previa ==")
        _pide(f"/api/listas/{lid}/lineas", galleta, "POST",
              {"nombre": "Arroz redondo marca A 1 kg", "grupo_id": 900001,
               "producto_id": "ensayo:arroz-a"})
        _, detalle4 = _pide(f"/api/listas/{lid}", galleta)
        lineas4 = (detalle4 or {}).get("lineas") or []
        for ln in lineas4:
            if ln.get("en_carrito") is False:
                _pide(f"/api/listas/{lid}/lineas/{ln['id']}", galleta, "PATCH", {"en_carrito": True})
        _, detalle5 = _pide(f"/api/listas/{lid}", galleta)
        sello_antes = ((detalle5 or {}).get("cotizacion") or {}).get("sello")
        print("   sello antes de publicar: " + str(sello_antes))

        import plataforma.construye_gold_ensayo as _cge
        for _of in _cge.OFERTAS:
            if _of.get("ean") == "9000000000017":
                _of["precio_cent"] = 200
                _of["precio_unidad_cent"] = 200.0
                _of["precio_ref_canon_cent"] = 200.0
        _cge.construye(Path(man["gold"]))
        print("   catalogo republicado: el arroz A pasa de 120 a 200")

        estado, r = _pide(f"/api/listas/{lid}/cerrar?sello_esperado={sello_antes}", galleta, "POST")
        nuevo2 = ((r or {}).get("detail") or {}).get("cotizacion_nueva") or {}
        print("   cerrar con el sello de antes -> " + str(estado)
              + "  sello nuevo=" + str(nuevo2.get("sello"))
              + "  total=" + str(nuevo2.get("total_cent")))
        vale("publicar otro catalogo invalida la previa y da 409", estado == 409)
        vale("y el sello nuevo es distinto del viejo", nuevo2.get("sello") != sello_antes)

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
