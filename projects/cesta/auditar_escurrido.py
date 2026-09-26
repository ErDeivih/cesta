"""El peso escurrido: si sirve para comparar cadenas, y cuanto se gana usandolo.

Por que existe
--------------
El 26 de septiembre de 2026 se modifico el precio por unidad para que, cuando la
cadena publica el peso escurrido, se divida por el en vez de por el peso que da el
nombre. La primera version de la nota que lo justificaba decia que **las cinco
cadenas publican el precio por kilo escurrido**, y eso no era cierto: lo que se
habia medido era nuestra propia cuenta de ida y vuelta, no el dato de la cadena.

Un cambio de comparabilidad sostenido por una medicion mal leida es exactamente lo
que este proyecto no puede tener, asi que la medicion se escribe y se puede
repetir:

    uv run python -m projects.cesta.auditar_escurrido
    uv run python -m projects.cesta.auditar_escurrido --fecha 2026-09-25

Que contesta, en este orden
---------------------------
1. **Quien publica el peso escurrido.** Solo Mercadona, y en cuantos productos.
2. **A que peso corresponde el precio de referencia de la cadena.** Si su ficha
   cuadra con el peso declarado, con el escurrido o con ninguno de los dos.
3. **Quien tiene razon al comparar entre cadenas.** Para cada grupo donde
   Mercadona publica escurrido y hay al menos dos cadenas mas vendiendo lo mismo
   por kilo, se compara el precio por kilo de Mercadona contra la mediana de las
   demas, dividiendo por lo declarado y dividiendo por el escurrido. Si el
   escurrido es la base buena, el cociente se acerca a 1.
4. **A quien le cambia el mas barato.** Cuantos grupos cambian de ganador.

No hay umbral de aprobado: enseña los grupos uno a uno, incluidos los que quedan
fuera, porque el limite de este arreglo (la base no es la misma en todas las
cadenas) es parte del resultado.
"""
from __future__ import annotations

import argparse
import statistics
import sys

import duckdb
import polars as pl

from core import config
from projects.cesta.pipeline import cantidad_para_el_precio

CADENAS = ("alcampo", "aldi", "carrefour", "dia", "mercadona")
MARGEN = 0.20          # "cuadra" y "queda cerca" es estar dentro del 20 %


def _bronze(cadena: str, fecha: str | None) -> pl.DataFrame:
    raiz = config.BRONZE / f"fuente={cadena}"
    dias = sorted(raiz.glob("fecha=*"))
    if fecha:
        dias = [d for d in dias if d.name.endswith(fecha)]
    if not dias:
        return pl.DataFrame()
    return pl.read_parquet(dias[-1] / "part.parquet")


def quien_publica_el_escurrido(fecha: str | None) -> dict[str, pl.DataFrame]:
    """Cuantos productos traen peso escurrido, por cadena, y si es menor que lo declarado."""
    print("1. quien publica el peso escurrido")
    con = {}
    for cadena in CADENAS:
        df = _bronze(cadena, fecha)
        if not df.height:
            print(f"   {cadena:<10} sin bronze")
            continue
        if "peso_escurrido_g" not in df.columns:
            print(f"   {cadena:<10} 0   (el colector no lee ese campo)")
            continue
        filas = df.filter(pl.col("peso_escurrido_g").is_not_null())
        con[cadena] = filas
        print(f"   {cadena:<10} {filas.height} de {df.height} productos")
    return con


def a_que_peso_cuadra_su_referencia(filas: pl.DataFrame) -> None:
    """El precio de referencia de la cadena: sobre el peso declarado o sobre el escurrido."""
    print()
    print("2. el precio de referencia de Mercadona, a que peso corresponde")
    if not filas.height:
        print("   (no hay filas con escurrido)")
        return
    d = filas.filter(pl.col("precio_ref_nativo_cent").is_not_null()
                     & (pl.col("precio_ref_nativo_cent") > 0)
                     & (pl.col("unidad_declarada") == "kg"))
    declarado = d.filter(
        pl.col("cantidad_declarada").is_not_null()
        & ((pl.col("precio_cent") / pl.col("cantidad_declarada")
            - pl.col("precio_ref_nativo_cent")).abs()
           <= 0.01 * pl.col("precio_ref_nativo_cent")))
    escurrido = d.filter(
        (pl.col("precio_cent") / (pl.col("peso_escurrido_g") / 1000.0)
         - pl.col("precio_ref_nativo_cent")).abs()
        <= 0.01 * pl.col("precio_ref_nativo_cent"))
    sin_declarar = d.filter(pl.col("cantidad_declarada").is_null())
    con_declarar = d.filter(pl.col("cantidad_declarada").is_not_null())
    ni_uno = con_declarar.height - declarado.height
    print(f"   {d.height} productos con referencia por kilo y escurrido publicado")
    print(f"   de esos, {con_declarar.height} declaran peso en el nombre:")
    print(f"       su referencia cuadra con lo declarado:  {declarado.height}")
    print(f"       no cuadra con ninguno de los dos:       {ni_uno}")
    print(f"   y {sin_declarar.height} no declaran peso: su referencia cuadra con el "
          f"escurrido ({escurrido.height}), porque no hay otra base que dar")

    print()
    print("   cuanto baja el escurrido sobre lo declarado:")
    bajan = filas.filter(pl.col("cantidad_declarada").is_not_null()
                         & (pl.col("peso_escurrido_g") < pl.col("cantidad_declarada") * 1000))
    if bajan.height:
        proporcion = (bajan["peso_escurrido_g"] / (bajan["cantidad_declarada"] * 1000)).to_list()
        por_debajo_de_mitad = sum(1 for p in proporcion if p < 0.5)
        print(f"   {bajan.height} productos; el escurrido es el "
              f"{100 * statistics.mean(proporcion):.1f} % de lo declarado de media, "
              f"y en {por_debajo_de_mitad} casos menos de la mitad")


def precio_por_kilo(precio_cent: float, cantidad_kg: float | None,
                    escurrido_g: float | None) -> tuple[float, float]:
    """El precio por kilo con la regla vieja y con la nueva, para el mismo producto.

    La regla nueva no se copia aqui: se le pide al pipeline, para que esto no pueda
    auditar una regla distinta de la que se usa de verdad.
    """
    marco = pl.DataFrame({"cantidad": [cantidad_kg], "escurrido": [escurrido_g]})
    cantidad = marco.select(cantidad_para_el_precio(pl.col("cantidad"),
                                                   pl.col("escurrido"))).item()
    if not cantidad:
        return (0.0, 0.0)
    return (precio_cent / cantidad_kg if cantidad_kg else 0.0, precio_cent / cantidad)


def grupos_con_escurrido(filas: pl.DataFrame) -> list[dict]:
    """Los grupos donde Mercadona publica escurrido y hay con quien comparar.

    Devuelve, por grupo: los precios por kilo de cada cadena (el de Mercadona con la regla
    vieja y con la nueva), la mediana de las otras y los dos cocientes.
    """
    esc = {str(r["id_fuente"]): r for r in filas.iter_rows(named=True)}
    if not esc:
        return []
    grupos = pl.read_parquet(config.GOLD / "grupos.parquet",
                             columns=["grupo_id", "fuente", "id_fuente", "nombre",
                                      "cantidad", "unidad_canon", "precio_cent",
                                      "precio_unidad_cent"])
    grupos = grupos.filter(pl.col("unidad_canon") == "kg")
    miembros: dict[int, list[dict]] = {}
    for r in grupos.iter_rows(named=True):
        miembros.setdefault(r["grupo_id"], []).append(r)

    salida = []
    for gid, ms in miembros.items():
        mio = next((m for m in ms if m["fuente"] == "mercadona"
                    and str(m["id_fuente"]) in esc
                    and esc[str(m["id_fuente"])]["precio_cent"] == m["precio_cent"]), None)
        otros = [m["precio_unidad_cent"] for m in ms
                 if m["fuente"] != "mercadona" and m["precio_unidad_cent"]]
        if mio is None or len(otros) < 2:
            continue
        mediana = statistics.median(otros)
        if not mediana:
            continue
        fila = esc[str(mio["id_fuente"])]
        declarado = fila["cantidad_declarada"]
        if not declarado:
            continue
        con_declarado, con_escurrido = precio_por_kilo(
            mio["precio_cent"], declarado, fila["peso_escurrido_g"])
        salida.append({
            "grupo_id": gid,
            "nombre": (mio["nombre"] or "")[:46],
            "declarado_g": declarado * 1000,
            "escurrido_g": fila["peso_escurrido_g"],
            "antes": con_declarado / mediana,
            "ahora": con_escurrido / mediana,
            "antes_cent": con_declarado,
            "ahora_cent": con_escurrido,
            "otros_cent": otros,
            # Si el oro no lleva el precio del escurrido es que el arreglo no llego al
            # final del pipeline, y entonces los numeros de la app no son los de aqui.
            "coincide_con_el_oro": abs(mio["precio_unidad_cent"] - con_escurrido)
                                   <= 0.01 * con_escurrido,
        })
    return salida


def comparar_entre_cadenas(casos: list[dict]) -> None:
    print()
    print("3. comparar entre cadenas: cociente de Mercadona contra la mediana de las otras")
    if not casos:
        print("   (no hay grupos comparables)")
        return
    for etiqueta, clave in (("dividiendo por lo declarado", "antes"),
                            ("dividiendo por el escurrido", "ahora")):
        cocientes = [c[clave] for c in casos]
        dentro = sum(1 for r in cocientes if 1 - MARGEN <= r <= 1 + MARGEN)
        print(f"   {etiqueta:<28} mediana {statistics.median(cocientes):5.3f}   "
              f"dentro del mas-menos 20 %: {dentro} de {len(cocientes)}")
    # La mediana de las otras es una referencia fragil cuando hay dos rivales que se llevan x3
    # (una marca cara y una marca blanca). Esta segunda medida es mas dificil de enganar:
    # ¿el precio de Mercadona cae cerca de **algun** rival del mismo grupo?
    print()
    for etiqueta, clave in (("por lo declarado", "antes_cent"),
                            ("por el escurrido", "ahora_cent")):
        coincide = sum(1 for c in casos
                       if any(abs(c[clave] / o - 1) <= MARGEN for o in c["otros_cent"]))
        print(f"   {etiqueta:<28} coincide con algun rival del grupo: "
              f"{coincide} de {len(casos)}")
    print()
    print("   grupo a grupo (ordenado por lo que se desvia ahora):")
    for c in sorted(casos, key=lambda x: abs(x["ahora"] - 1), reverse=True):
        print(f"     {c['nombre']:<46.46} {c['declarado_g']:>5.0f} g declarados, "
              f"{c['escurrido_g']:>4.0f} g escurridos   antes {c['antes']:5.2f}   "
              f"ahora {c['ahora']:5.2f}")


def acuerdo_con_la_ficha(fechas: list[str]) -> None:
    """El acuerdo con el precio de referencia de cada cadena, y **de que son las diferencias**.

    Se mide sobre silver (la cuenta que se publica), con la definicion escrita para poder
    comparar dos dias: comparables son las filas donde nosotros derivamos el precio por unidad
    y la cadena publica el suyo, apartando las que se llevan x2 o mas (que el pipeline no
    compara porque no se sabe quien tiene razon).

    Y las que no cuadran se separan en dos cosas que no tienen nada que ver: el redondeo de la
    cadena (su referencia va al centimo; en productos de 8 centimos por unidad, medio centimo
    parece un 6 %) y las diferencias de verdad.
    """
    print()
    print("5. el acuerdo con la ficha de cada cadena (silver, tolerancia del 2 %)")
    for fecha in fechas:
        print(f"   {fecha}")
        for cadena in CADENAS:
            ruta = config.SILVER / f"fuente={cadena}" / f"fecha={fecha}" / "part.parquet"
            if not ruta.exists():
                continue
            con = duckdb.connect()
            filas = con.execute(f"""
                select precio_unidad_cent, precio_ref_canon_cent
                from read_parquet('{ruta.as_posix()}')
                where proc_precio_unidad = 'derivado'
                  and precio_unidad_cent is not null
                  and precio_ref_canon_cent is not null and precio_ref_canon_cent > 0
                  and precio_unidad_cent < 2 * precio_ref_canon_cent
                  and precio_ref_canon_cent < 2 * precio_unidad_cent
            """).fetchall()
            if not filas:
                continue
            malas = [(n, s) for n, s in filas if abs(n - s) > 0.02 * s]
            acuerdo = 100 * (len(filas) - len(malas)) / len(filas)
            cola = ""
            if malas:
                difs = [abs(n - s) for n, s in malas]
                de_redondeo = sum(1 for d in difs if d <= 1.0)
                cola = (f"   sin cuadrar {len(malas)}: mediana "
                        f"{statistics.median(difs):.2f} centimos, {de_redondeo} de ellos de "
                        f"1 centimo o menos")
            print(f"     {cadena:<10} {len(filas):>6} comparables   {acuerdo:5.1f} % coinciden"
                  f"{cola}")


def cambia_el_mas_barato(casos: list[dict]) -> None:
    """En cuantos de esos grupos el mas barato deja de ser quien era.

    El ganador de antes se calcula con los mismos precios de las otras cadenas y el de
    Mercadona por lo declarado; el de ahora, con el de Mercadona por el escurrido. Asi la
    unica diferencia entre los dos es el arreglo.
    """
    print()
    print("4. a quien le cambia el mas barato")
    if not casos:
        print("   (no hay grupos comparables)")
        return
    cambian = []
    for c in casos:
        antes = min(c["otros_cent"] + [c["antes_cent"]])
        ahora = min(c["otros_cent"] + [c["ahora_cent"]])
        if abs(antes - ahora) > 0.005:
            cambian.append((c, antes == c["antes_cent"], ahora == c["ahora_cent"]))
    pierde_mercadona = sum(1 for _, gana_antes, gana_ahora in cambian
                           if gana_antes and not gana_ahora)
    gana_mercadona = sum(1 for _, gana_antes, gana_ahora in cambian
                         if gana_ahora and not gana_antes)
    print(f"   {len(casos)} grupos afectados; el mas barato cambia en {len(cambian)}")
    print(f"   de esos, Mercadona deja de ser el mas barato en {pierde_mercadona} "
          f"y pasa a serlo en {gana_mercadona}")
    desajustes = [c["nombre"] for c in casos if not c["coincide_con_el_oro"]]
    if desajustes:
        print(f"   ojo: el oro no coincide con la regla del pipeline en "
              f"{len(desajustes)} grupos: {', '.join(desajustes[:3])}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fecha", help="fecha del bronze (por defecto, la ultima)")
    ap.add_argument("--acuerdo", nargs="*", metavar="FECHA",
                    help="fechas de silver para el acuerdo con la ficha, por ejemplo "
                         "--acuerdo 2026-09-25 2026-09-26 (por defecto, ninguna)")
    a = ap.parse_args(argv)

    con = quien_publica_el_escurrido(a.fecha)
    mercadona = con.get("mercadona", pl.DataFrame())
    a_que_peso_cuadra_su_referencia(mercadona)
    casos = grupos_con_escurrido(mercadona)
    comparar_entre_cadenas(casos)
    cambia_el_mas_barato(casos)
    if a.acuerdo:
        acuerdo_con_la_ficha(a.acuerdo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
