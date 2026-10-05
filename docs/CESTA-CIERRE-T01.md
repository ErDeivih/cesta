# Cierre de T01 — Alcance de consumibles y presupuesto de extracción

Plantilla de `docs/CESTA-TAREAS-Y-ACEPTACION.md`, rellenada el **5 de octubre de 2026**.

## Estado

**EN CURSO (parcial, y a propósito).** Aplicado en **Alcampo** (ramas y producto) y **Carrefour**
(ramas). Pendientes: DIA, Mercadona y Aldi, y el informe de peticiones realizadas. **No se cierra
como terminado**: lo que falta está abajo con su condición concreta, y el contrato pide no cerrar
«todo correcto» si falta una verificación.

## Archivos y migraciones

    core/alcance.py                 la funcion unica: clasificar_alcance(nombre, categoria, contexto)
    core/datos/alcance.yml          la politica, version 2, versionada con el codigo
    core/cobertura.py               solo_cesta_familiar: una rama excluida no veta una incluida
    projects/cesta/revisar_alcance.py   la ejecucion seca y la comprobacion de seguridad
    projects/cesta/collectors/alcampo.py     no pide el bazar; clasifica el producto antes de bronze
    projects/cesta/collectors/carrefour.py   no pide sus categorias de bazar (lo sabe por la URL)
    tests/test_alcance.py, tests/test_waf_alcampo.py, tests/test_alcance_colectores.py

**Sin migraciones**: esto no toca la base de datos ni los datos guardados.

## Qué cambia para la persona

- **Menos ruido en el catálogo**: 3.191 productos (6,0 %) salen del catálogo de consumo, y 2.407
  quedan en `revisar` para que los mire una persona. Un electrodoméstico ya no compite con la
  leche.
- **Alcampo vuelve a traer datos.** Su captura del 5 de octubre se rechazó porque una rama de
  decoración venía hundida; esa rama ya no se pide, así que no puede vetar un día de comida.
- **Las cinco cadenas dejan de pedir bazar** donde pueden saberlo antes de pedir (Carrefour por la
  URL; Alcampo por su árbol de categorías), que es menos carga para sus servidores y para el WAF.

## Pruebas añadidas, resultado y limitaciones

    35 pruebas en tests/test_alcance.py        (frontera, familias, trampas de siempre, hoja/rama)
    10 pruebas en los colectores               (el bazar no se pide; la comida sí; ante la duda, sí)
    pytest: 1.097 pruebas, 0 fallos    ruff: limpio

**Limitación declarada:** el enganche dentro de los colectores se verifica con pruebas y con el
histórico, **no con una captura en vivo**: eso llega con la pasada siguiente. Y la frontera del
consumible es una **decisión de alcance inicial**, no una definición universal: se cambia en
`core/datos/alcance.yml` y la ejecución seca dice el efecto en un segundo.

## Métricas antes/después, con fecha (5 de octubre de 2026)

    catalogo clasificado                53.139
    entran                              47.541
    salen                                3.191   (6,0 %)
    a revisar                            2.407

    alcampo   7,3 % fuera   carrefour 7,0 %   aldi 2,8 %   mercadona 2,4 %   dia 2,0 %

    ramas sin un solo producto de cesta: 12, encabezadas por Hogar y Decoracion (133), que es
    exactamente la rama que tumbo la captura del dia

**Y la travesía del aviso de seguridad, que es la parte que justifica el retraso:**

    561  el aviso heredado, comparando por trozos
    348  palabras enteras, y dice que palabra dispara
    226  agua fuera (Eau de toilette) y complementos fuera de la regla de moda
    282  el vocabulario tenia PREFIJOS (carnicer, alimenta): no casaban y el aviso estaba ciego
     67  folletos fuera de la señal, frutos secos en pareja, cubo por frase
      5  el aviso pide DOS señales: comida en el nombre y pasillo de comida
      0  los cinco ultimos eran palabras que significan otra cosa: sarten, tablet, peluche,
         pelota para (cortes de carne, tableta de chocolate, un pack que trae un peluche)

## Compatibilidad y recuperación

- **No se toca la base de datos, ni los datos, ni la tarea diaria.** El histórico entero se
  conserva: lo que se deja de pedir es lo nuevo, no lo que ya está guardado.
- **La política es reversible en una línea por cadena**: desengancharla devuelve el
  comportamiento anterior sin tocar nada más. Ya se hizo una vez y se volvió a enganchar.
- La cobertura se mide **después** de aplicar la política, en los dos lados de la comparación, para
  que el corte de alcance no falsee el control.

## Pendientes, con su condición concreta

1. **DIA y Mercadona**: el mismo patrón que Carrefour. Volumen pequeño (2,0 % y 2,4 % fuera), así
   que van después.
2. **Aldi**: necesita una **decisión de diseño**. Su sitemap publica un solo fichero con URLs que
   solo llevan el id del producto, sin categoría, y el colector lo prefiere al menú: la categoría
   se conoce *después* de pedir el detalle. Para no pedir el bazar habría que volver al menú (que
   sí trae categorías) o cambiar de qué se fía. Es donde más peticiones se ahorrarían.
3. **Informe de peticiones realizadas frente a estimadas**: lo estimado ya se mide
   (`revisar_alcance --ramas`); lo realizado se cuenta cuando la política lleve una pasada entera
   dentro de los colectores.
4. **Verificación en vivo**: la captura de Alcampo de la próxima pasada. Si trae sus productos y el
   colector los acepta, el desbloqueo queda confirmado en el mundo real.
