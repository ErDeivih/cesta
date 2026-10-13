# B02 · **El mapa del paquete, leido del plan** -- antes de tocar nada

*(13 de octubre de 2026. **Lo siguiente es B02, y esto es lo que pide, desglosado. No se ha escrito codigo.**)*

## 1. El criterio, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:222`:

> **B02 · Carrefour y Alcampo resistentes**
>
> *Medir **requests efectivos, cobertura de ramas, productos unicos, tiempo y motivo de cada reintento**. **Parser
> de cero resultados valido versus HTML de desafio/error**; **429/503 y `Retry-After`**, **backoff con limite**,
> **circuit breaker** y **checkpoints**. **HTTP 200 no garantiza datos; desafios no son catalogo vacio.** No eludir
> CAPTCHA, no aumentar presion ni introducir proxies furtivos. Si exige interaccion humana, marcar
> **`requiere_interaccion`**, **conservar ultimo valido** y **continuar otras cadenas**. No declarar «Alcampo
> nunca publica nutricion» por muestras insuficientes: **registrar URL/tipo de ficha/fecha/numero de muestras y
> donde el campo si/no fue encontrado**. Aceptar **fixtures** de desafios, esquema cambiado, pagina vacia, corte a
> mitad, reanudar y publicacion final, **mas captura acotada real cuando sea posible**.*

## 2. Y desglosado, son siete cosas, y cuatro son de MEDIR

```
MEDIR (4)
  1) requests efectivos          -- cuantas peticiones de verdad, no cuantas se intentaron
  2) cobertura de ramas          -- que caminos del parser se han ejercitado
  3) productos unicos            -- y no filas repetidas
  4) tiempo y motivo de cada reintento

DISTINGUIR (1)
  5) CERO RESULTADOS VALIDO  vs  HTML DE DESAFIO/ERROR
     -> y la frase que lo gobierna: «HTTP 200 NO GARANTIZA DATOS;
        DESAFIOS NO SON CATALOGO VACIO»

RESISTIR (1)
  6) 429/503 + Retry-After · backoff CON LIMITE · circuit breaker · checkpoints
     -> y los limites del encargo: NO eludir CAPTCHA, NO aumentar presion, NO proxies furtivos
     -> y si exige interaccion humana: marcar `requiere_interaccion`, CONSERVAR ULTIMO VALIDO,
        y SEGUIR CON OTRAS CADENAS

NO CONCLUIR DE MAS (1)
  7) no decir «Alcampo nunca publica nutricion» por muestras insuficientes
     -> registrar URL / tipo de ficha / fecha / NUMERO DE MUESTRAS / y donde el campo si o no se encontro
```

## 3. Y la aceptacion, que tiene dos mitades

```
FIXTURES (deterministas, sin red):
  - desafio
  - esquema cambiado
  - pagina vacia
  - corte a mitad
  - reanudar
  - publicacion final

Y ADEMAS: «captura acotada real cuando sea posible»
```

> **Esa segunda mitad importa y es facil saltarsela**: *el plan no pide solo fixtures.* *Pide **una captura real,
> acotada** -- que es lo que B03 hizo para Lidl (79 fichas) y lo que aqui hay que repetir para Carrefour y
> Alcampo, **con el mismo cuidado**: sin duplicar capturas, sin aumentar presion, y sin eludir nada.*

## 4. Y lo que ya existe, que hay que mirar antes de escribir

**El paquete tiene que empezar por leer lo que ya hay**, *porque el plan lo dice de B03 y vale igual aqui:*

```
  projects/cesta/collectors/carrefour.py
  projects/cesta/collectors/alcampo.py
  projects/cesta/run.py
  y los ensayos de colectores que ya existan
```

> *Y la pregunta primera no es «que escribo», sino **«que hace hoy este colector cuando recibe un desafio»*** --
> *que es la forma de pregunta que en B03 encontro que el veto estaba en una linea y que el motivo no lo llamaba
> produccion.*
>
> **Y la segunda: «¿por donde ENTRA el dato?»** -- *la leccion de la ronda 99, que costo quince sitios.*

## 5. Y el estado de B03, comprobado contra SU criterio, que es lo que se acaba de cerrar

*Para no dejar duda de por que B03 se dio por cerrado:*

```
EL PLAN PIDE (B03)                                  ESTADO
  ejecucion desde el mismo runner diario            HECHO -- `ARGUMENTOS` en run.py
  bronze -> silver -> gold -> API -> UI             HECHO -- medido en cada parada
  region / club / fechas / nutricion / ausencias    PROBADOS (club y fechas; nutricion dicha ausente)
  captura acotada                                   HECHA -- 79 fichas
  contador visible                                  HECHO -- la cobertura y el contador por campo
  validar tienda/region, no CP->region sin correspondencia   HECHO -- `acreditada` o no sigue
  no confundir IAN con EAN                          RESPETADO -- 0 EAN, y no se invento
  promocion semanal vs catalogo total               DICHO -- `ofertas_semanales_parcial`
  eliminar veto global                              HECHO -- las seis dan el mismo 401
  Lidl no gana cesta completa si faltan lineas      RESPETADO -- el reparto decide con lo observado
  no declararlo por el sitemap                      RESPETADO -- la captura son fichas con precio
```

*Y lo unico que queda fuera del criterio -- **usar la zona para elegir** -- esta dicho con su nombre.*
