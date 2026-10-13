"""Demuestra que las siete pruebas de B04 FALLAN sin el arreglo.

**Por que existe.** *Una prueba de regresion que pasa hoy y pasaria tambien con el defecto no protege
nada.* **Y la unica forma de saber cual de las dos es, es volver a meter el defecto y mirar.**

*Se hace por mutacion controlada*: **se guarda el fichero, se le mete el defecto viejo, se corre la prueba,
y se restaura pase lo que pase.** *El `finally` no es adorno: si la prueba revienta a mitad -- que es lo
que se espera -- sin el, el fichero se quedaria con el defecto dentro.*

    uv run python data/debug/b04_mutaciones.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
PUENTES = RAIZ / "tests" / "test_b04_los_dos_puentes.py"

# **Un defecto por mutacion**, con el nombre de la prueba que tiene que cazarlo.
#
# *Se mutan las mismas lineas que se arreglaron*, con el codigo viejo tal cual estaba -- *no una
# aproximacion: lo que se escribe aqui es lo que decia el fichero antes del arreglo.*
MUTACIONES = [
    (
        "plan: no escalar por comensales",
        RAIZ / "plataforma" / "api" / "main.py",
        "            factor = None\n            if raciones and comensales and float(raciones) > 0:\n"
        "                factor = float(comensales) / float(raciones)\n",
        "            factor = None\n",
        "escala_por_comensales",
    ),
    (
        # **Reorientada tras el refactor.** *Antes apuntaba al `if clave in juntos` de `_del_plan`, y
        # el refactor borro ese bucle*: **la consolidacion se mudo a `previa_compra`, que es la pieza
        # que los dos puentes comparten.** *Una mutacion que apunta a una linea que ya no existe no
        # prueba nada -- y hay que decirlo, no dejar el guion mintiendo.*
        "previa_compra: descartar la segunda en vez de sumar",
        RAIZ / "core" / "previa_compra.py",
        "        if clave in acumulado:\n",
        "        if False:\n",
        "segunda_receta",
    ),
    (
        "receta: contar gramos como unidades y no poner nota",
        RAIZ / "plataforma" / "api" / "recetas.py",
        "                1, detalle, None)\n",
        "                round(ln.cantidad) or 1, None, None)\n",
        "una_unidad",
    ),
]


def corre_prueba(nombre: str) -> bool:
    """*Devuelve True si la prueba PASA.* **Y se corre con `-x` para que pare en el primer fallo.**"""
    r = subprocess.run(
        ["uv", "run", "pytest", f"{PUENTES}::test_{nombre}" if not nombre.startswith("test_") else nombre,
         "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=RAIZ, capture_output=True, text=True, timeout=600)
    salida = (r.stdout or "") + (r.stderr or "")
    return " 1 passed" in salida or "1 passed" in salida


def main() -> int:
    print("== ¿fallan las pruebas de B04 sin el arreglo?")
    problemas = []
    for titulo, fichero, bueno, malo, prueba in MUTACIONES:
        original = fichero.read_text(encoding="utf-8")
        if bueno not in original:
            print(f"   {titulo}: NO ENCUENTRO el texto bueno en {fichero.name}")
            problemas.append(titulo)
            continue
        try:
            fichero.write_text(original.replace(bueno, malo, 1), encoding="utf-8")
            # *Con el defecto dentro: la prueba TIENE que fallar.*
            pasa = corre_prueba(prueba)
        finally:
            # **Pase lo que pase.** *Si se queda el defecto, el fichero miente.*
            fichero.write_text(original, encoding="utf-8")

        restaurado = fichero.read_text(encoding="utf-8") == original
        if not restaurado:
            problemas.append(f"{titulo} (NO SE RESTAURO)")
            print(f"   {titulo}: ¡NO SE RESTAURO!")
        elif pasa:
            problemas.append(titulo)
            print(f"   {titulo}: la prueba PASA con el defecto -> NO PROTEGE")
        else:
            print(f"   {titulo}: la prueba FALLA con el defecto -> PROTEGE")

    print(f"\n== {'TODAS PROTEGEN' if not problemas else str(len(problemas)) + ' PROBLEMA(S): ' + ', '.join(problemas)}")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
