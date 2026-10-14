"""Audita las rutas `GET` de la API: **ninguna debe escribir.**

**Por que existe.** *`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:348` (B14) pide, entre otras cosas:*
*** «*Auditar **GET sin cambios**, Origin/Referer/Fetch Metadata o token segun contrato *** y pruebas
negativas***»*

**Y por que con `ast` y no con `grep`.** *La primera version de esta auditoria fue un `grep` que miraba
30 lineas por debajo de cada `@app.get`, *y **no servia**:*
  *-- *cogia **comentarios** *(-- el patron `apunta` aparece en prosa 7 veces --)*
  *-- *y cogia **la funcion siguiente** *(-- una ventana de 30 lineas cruza la frontera de la ruta,
     asi que `GET /api/listas` parecia llamar a `crea_lista`, *que es **del POST de abajo** --)*
  *-- *y **una vez me dio una linea que no era** *(-- dije «`despensa.py:73` es un `INSERT`»,
     y la 73 es `@rutas.get("")` --)*

*Con `ast` **no pasa nada de eso**: *se sabe **donde empieza y acaba cada funcion**, *y **donde esta
cada llamada de verdad.** *-- *y **con el instrumento bueno salio una**, *que con el malo no habria
salido **nunca.***

**Que cuenta como escritura.** *Dos cosas, y las dos son mecanicas:*
  1. *que el cuerpo del `GET` llame a una funcion cuyo nombre empiece por un verbo de escritura*
     (`anade_`, `cambia_`, `crea_`, `borra_`, `guarda_`, `apunta`, `marca_`, `cierra_`, …)
  2. *o que ejecute un SQL que empiece por `insert`, `update`, `delete`, `drop`, `alter` o `truncate`*

*Y **lo que NO decide**: *si la escritura **esta justificada.*** *La encontrada lo esta en parte* --
*el `GET` de una lista **devuelve `novedades`**, *y para saber que hay de nuevo **necesita cuando miro
esto cada uno** --, *pero **un `GET` que escribe deja de ser seguro**, *y eso **hay que decidirlo**,
no suponerlo.* *Esta herramienta **dice lo que hay**; *lo que se hace con ello **no es su trabajo.***
"""
from __future__ import annotations

import ast
from pathlib import Path

#: *Los verbos que escriben, en el vocabulario de este proyecto.*
VERBOS = ("anade_", "cambia_", "crea_", "borra_", "guarda_", "apunta", "marca_",
          "cierra_", "consume_", "sincroniza", "comparte", "autoriza", "revoca", "reparte_")

#: *Y lo que escribe en SQL.* **Se mira el principio de la sentencia, no que la contenga.**
SQL_ESCRITURA = ("insert ", "update ", "delete ", "drop ", "alter ", "truncate ")


def sospechosas(raiz: Path | None = None) -> list[tuple[str, int, str, str]]:
    """**Las rutas `GET` que escriben**, con su fichero, su linea, su nombre y que hacen."""
    raiz = raiz or (Path(__file__).resolve().parents[1] / "plataforma" / "api")
    halladas: list[tuple[str, int, str, str]] = []
    for fichero in sorted(raiz.glob("*.py")):
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # *Se mira el DECORADOR, no el nombre de la funcion.*
            if not any(".get(" in ast.unparse(d) for d in nodo.decorator_list):
                continue
            # *Y se recorre SU cuerpo, delimitado por el AST.*
            for sub in ast.walk(nodo):
                if not isinstance(sub, ast.Call):
                    continue
                nombre = ast.unparse(sub.func)
                corto = nombre.split(".")[-1]
                if any(corto.startswith(v) for v in VERBOS):
                    halladas.append((fichero.name, nodo.lineno, nodo.name, f"llama a {nombre}"))
                elif corto == "execute" and sub.args:
                    try:
                        sql = ast.literal_eval(sub.args[0]).strip().lower()
                    except Exception:  # noqa: BLE001  - *un SQL que no es literal no se juzga*
                        continue
                    if sql.startswith(SQL_ESCRITURA):
                        halladas.append((fichero.name, nodo.lineno, nodo.name, f"SQL: {sql[:48]}"))
    return halladas


def _cli() -> int:
    halladas = sospechosas()
    print(f"  rutas GET revisadas en plataforma/api: {len(halladas)} sospechosas")
    for fichero, linea, nombre, que in halladas:
        print(f"    {fichero}:{linea}  {nombre}  ->  {que}")
    return 1 if halladas else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
