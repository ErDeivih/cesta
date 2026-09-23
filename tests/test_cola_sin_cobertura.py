"""Los cambios sin cobertura: que tachar funcione sin red, y se suba solo.

Es el §3.5 del encargo, y es la parte que faltaba de la pantalla que *"merece mas cuidado
que el resto junto"*:

    - que tachar funcione igual sin red, sin ruedecita ni error;
    - una linea discreta cuando hay cambios sin subir: «3 cambios se subiran al volver
      la cobertura»;
    - y que al volver, se suba solo y se diga en una frase.
    - **Que no**: un aviso rojo de error. Estar sin cobertura en un supermercado no es
      un fallo de la aplicacion.

La mecanica de la API ya estaba desde el primer dia -- **el identificador de linea lo
genera el movil**, cada cambio viaja con **su hora** (`momento`) y existe
`POST /listas/{id}/sincronizar` para subirlos de golpe --; lo que no existia era
guardarlos.

Lo que se vigila aqui, y cada cosa por su motivo:

  - **Que se guarden en el aparato**, no en la memoria: si se cierra la pestaña en el
    pasillo, los cambios siguen ahi al volver a abrirla.
  - **Que la hora sea la del movil y se ponga al tocar**, no al subir: tachar a las 18:04
    sin cobertura y subirlo a las 18:20 tiene que contar como las 18:04, o el servidor
    se inventa el orden de los hechos.
  - **Que un cambio por linea gane el ultimo**, pero sin perder campos distintos: tachar
    y luego cambiar la cantidad son dos cosas del mismo PATCH.
  - **Que la cola se vacie solo cuando el servidor dice que los aplico.** Si se vaciara al
    mandarlos, un 500 en el camino perderia cambios que alguien hizo de pie en la tienda.
  - **Que sin cobertura no haya aviso rojo**: eso ya no es un error, es un cambio que
    espera. El rojo se queda para lo que la API contesta que no.

Como las de contraste y las de movil, esto lee el codigo: perder los cambios de alguien en
el supermercado no da ningun error de compilacion.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "plataforma" / "web" / "app" / "src"
COLA = SRC / "estado" / "cola.ts"
CESTA = SRC / "paginas" / "Cesta.tsx"
API = SRC / "api" / "cesta.ts"
GRUPO = SRC / "paginas" / "Grupo.tsx"


def _leer(f: Path) -> str:
    if not f.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    return f.read_text(encoding="utf-8")


def test_la_cola_se_guarda_en_el_aparato_y_lleva_version():
    cola = _leer(COLA)
    assert "window.localStorage" in cola, \
        "una cola en memoria se pierde al cerrar la pestaña, que es justo lo que pasa en el pasillo"
    assert re.search(r"const CLAVE = 'cesta\.cola\.v1'", cola), \
        "la clave lleva version: el dia que cambie el formato, lo viejo no revienta"
    assert cola.count("try {") >= 2 and "catch" in cola, \
        "sin try/catch, el modo privado del navegador tumba la lista entera"
    # Y si no se puede guardar, se dice: una cola que no se guarda es una promesa perdida.
    assert "return escribe(todo) ? cola : null" in cola


def test_la_hora_es_la_del_movil_y_se_pone_al_tocar():
    cesta = _leer(CESTA)
    assert re.search(r"momento: variables\.cambio\.momento \?\? new Date\(\)\.toISOString\(\)",
                     cesta), \
        "la hora del cambio tiene que ponerse al tocar, no al subir"
    cola = _leer(COLA)
    assert "La hora DEL MOVIL" in cola, "el porque tiene que estar donde se lee"


def test_un_cambio_por_linea_sin_perder_campos():
    cola = _leer(COLA)
    assert re.search(r"filter\(\(c\) => c\.lineaId !== nuevo\.lineaId\)", cola), \
        "dos cambios de la misma linea no pueden subir los dos: gana el ultimo"
    assert re.search(r"cambio: \{ \.\.\.\(antes\?\.cambio \?\? \{\}\), \.\.\.nuevo\.cambio \}", cola), \
        "tachar y luego cambiar la cantidad son dos campos del mismo PATCH: el segundo " \
        "no puede borrar al primero"


def test_la_cola_se_vacia_solo_cuando_el_servidor_dice_que_los_aplico():
    cesta = _leer(CESTA)
    # Las dos lineas que importan, y su orden: primero se manda, despues se vacia. Se
    # buscan con sus parentesis para no confundirlas con el `import`.
    llama = cesta.index("sincronizar(listaId as string, pendientes.map(")
    vacia = cesta.index("vaciaCola(listaId as string)")
    assert llama < vacia, \
        "la cola se vacia antes de mandarla: un fallo en el camino perderia cambios " \
        "hechos de pie en la tienda"
    assert "'online'" in cesta, \
        "nadie escucha el aviso del navegador de que ha vuelto la cobertura"
    assert "navigator.onLine" in cesta, \
        "sin red no se intenta subir: es exactamente lo que no funciona"


def test_sin_cobertura_no_hay_aviso_rojo_y_se_ve_lo_tocado():
    cesta = _leer(CESTA)
    # "Que tachar funcione igual sin red" no es que se guarde: es que se vea.
    assert "conPendientes(" in cesta, \
        "la linea tachada sin cobertura no se pinta tachada: no funciona igual"
    assert re.search(r"c\.tachado === true \? \(linea\.tachado_en \?\? pendiente\.momento\)",
                     cesta), "el tachado optimista tiene que usar la hora del movil"
    # El rojo, solo para lo que la API contesta que no.
    assert re.search(r"cambia\.isError && !esSinRed\(cambia\.error\)", cesta), \
        "sin cobertura sigue pintandose como un error"
    assert "se subirá al volver la cobertura" in cesta or "se subirán al volver la cobertura" in cesta, \
        "falta la linea discreta que dice cuantos cambios esperan"


def test_la_api_tiene_la_puerta_para_subirlos_de_golpe():
    api = _leer(API)
    assert "export async function sincronizar(" in api, \
        "la pantalla no tiene por donde subir la cola"
    assert "/sincronizar" in api, "la ruta de la cola de la API es `/listas/{id}/sincronizar`"


def test_las_mutaciones_no_se_quedan_pausadas_por_react_query():
    """`networkMode: 'always'`: sin esto la cola no se llena nunca.

    **Es el fallo que encontro el navegador** (23 sep 2026). Por defecto, React Query
    *pausa* una mutacion cuando `navigator.onLine` es falso: no la manda, **no falla** y
    no avisa -- y la reintenta sola al volver la red. Suena bien y es lo contrario de lo
    que hace falta:

      - el cambio vive **en memoria**, asi que si se cierra la pestaña en el pasillo se
        pierde, que es justo el caso que la cola existe para cubrir;
      - y como no hay error, **la pantalla no puede decir que hay cambios sin subir**:
        no sabe que los hay.

    Medido en el navegador antes del arreglo: se tachaba sin cobertura y no pasaba nada
    -- ni la linea tachada, ni el aviso, ni una entrada en la cola --, y el PATCH salia
    al volver la red. Con esto, la peticion se intenta, falla con un `TypeError` y el
    cambio acaba en la cola del movil con su hora.

    Ninguna prueba de codigo podia verlo: es una politica interna de la libreria.
    """
    cesta = _leer(CESTA)
    # Las dos mutaciones que importan: la que cambia una linea y la que sube la cola.
    assert cesta.count("networkMode: 'always'") >= 2, \
        "al cambiar una linea o al subir la cola, React Query las pausa sin avisar"
    assert "networkMode: 'always'" in cesta.split("const sube = useMutation(")[1][:400], \
        "la mutacion que sube la cola tambien tiene que intentarlo sin cobertura"


def test_la_frase_esta_tambien_en_el_grupo_y_antes_que_los_numeros():
    """La pantalla a la que se llega **buscando** tambien contesta en palabras.

    Punto 3 del encargo: *"«¿esto esta caro?» hoy se contesta con una tabla, y una tabla
    no es una respuesta"*. La frase estaba solo en la ficha del producto
    (`paginas/Producto.tsx`), y **el navegador enseno donde faltaba**: buscar "leche",
    abrir el resultado, y encontrarse «ALTERNATIVA QUE GANA CONTIGO / Dia / 1,05 €/l» con
    un «74 %» al lado. Numeros, ninguno con sujeto.

    Se usa la misma funcion que la ficha (`logica/frase.ts`) y **tambien la misma regla**:
    si el grupo no es de fiar, no hay frase. Y va antes de los numeros en el codigo, que
    es lo que hace que salga antes en la pantalla.
    """
    grupo = _leer(GRUPO)
    assert "fraseDePrecio(" in grupo, "la pantalla del grupo no contesta con una frase"
    assert "from '../logica/frase'" in grupo, \
        "la frase tiene que ser LA MISMA que la de la ficha, no una copia"
    assert grupo.index("fraseDePrecio(") < grupo.index("<dl "), \
        "los numeros salen antes que la frase"
    assert "p.comparable !== false" in grupo, \
        "sin senal de fiabilidad, la frase se inventa en grupos mal emparejados"
