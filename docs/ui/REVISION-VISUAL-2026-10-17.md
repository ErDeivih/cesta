# *** REVISION VISUAL *** *-- *17/10/2026, sobre las capturas de la ronda 121*

*** CINCO PANTALLAS MIRADAS, *Y TRES DEFECTOS CONCRETOS QUE NO SON DE ESTA REVISION.*** *No se
cuentan capturas: *se cuenta lo que esta mal, *donde, *y con que se prueba.*

*Las capturas estan en `docs/ui/capturas/ronda-121/`, hechas por `plataforma/prueba_navegador.py`
en un movil de 390 x 844. *Y una advertencia que vale para todas: **la barra de abajo aparece en
mitad de la imagen porque la captura es a pagina completa y los elementos fijos se pintan en su
posicion de ventana.** *Eso NO es un defecto, y no se cuenta.*

---

## *** 1 · LO QUE ESTA BIEN, *Y HAY QUE DECIRLO ANTES DE LO MALO ***

*** La honestidad del texto es lo mejor de esta aplicacion***, *y se ve en las cinco pantallas:*

| *donde* | *que dice* |
|---|---|
| *Diario* | *«Deja en blanco lo que no sepas: **no es cero, es que no se sabe**»* |
| *Diario, cabecera* | ***«sin dato»*** *en los cuatro macros, en vez de ceros* |
| *Tendencias* | *«Medido sobre lo anotado y lo que se sabe. **No es todo lo que comiste**»* |
| *Comparacion* | *«sin comparacion: esta en una sola cadena»* |
| *Comparacion, pesos* | *«Ninguna alternativa de este grupo tiene letra, asi que ese peso no esta haciendo nada»* |
| *Lista* | *«No puedo decir donde ... Puede que sean cosas que ninguna de las cinco cadenas venda»* |
| *Plan semanal* | *«Cada receta se guarda con la version que tenia el dia que se uso»* |

*** Eso es lo que se pedia, y esta hecho***: *ninguna de esas frases promete mas de lo que sabe.*

---

## *** 2 · LOS TRES DEFECTOS CONCRETOS ***

### 2.1 *** CONCORDANCIA: *el singular se escribe en plural ***

| *pantalla* | *lo que se ve* | *deberia decir* |
|---|---|---|
| *Comparar (`grupo-526-3.png`)* | ***«1 productos · 1 cadena»*** | *«1 producto · 1 cadena»* |
| *Listas (`cesta-13.png`)* | ***«1 lineas · 1 ya cogidas»*** | *«1 linea · 1 ya cogida»* |

*** Dos sitios, el mismo error***: *se escribe el numero y luego una palabra fija en plural.* *Es
un defecto de texto, no de datos, *y se ve en una pantalla normal sin buscarlo.*

### 2.2 *** FECHA: *dos formatos para lo mismo ***

| *pantalla* | *lo que se ve* |
|---|---|
| *Diario* | ***17/10/2026*** |
| *Listas* | ***Datos del 2026-10-16*** |
| *Plan semanal* | ***a la del 2026-10-24*** … *y justo debajo, «sabado 17»* |

*** Tres pantallas, dos formatos***, *y en el plan semanal **los dos en la misma tarjeta**: la
fecha en ISO y el dia de la semana en castellano.* *Para una persona que lee «sabado 17», *el
«2026-10-24» de al lado no es una fecha: es un codigo.*

### 2.3 *** NUMERO: *coma y punto en la misma pantalla ***

*** En `cesta-13.png`:*

```
0,96 €                        <- arriba, con COMA
0.00 € por coger · 0.96 € en el carro    <- abajo, con PUNTO
```

*** La misma cantidad, *en la misma pantalla, *escrita de dos formas.*** *Una de las dos esta mal
en castellano, *y ademas hace dudar de si son la misma cifra.*

---

## *** 3 · LO QUE NO ES UN DEFECTO, *Y SE DICE PARA NO INFLAR LA LISTA ***

- *** La barra de abajo en mitad de la imagen***: *artefacto de la captura a pagina completa.*
- *** La caja vacia grande de Tendencias***: *conserva el hueco de la grafica para que el diseno
  no salte cuando lleguen datos.* *Es deliberado.*
- *** Que el texto vaya sin tildes***: *es la convencion de toda la aplicacion, no un defecto de
  estas pantallas.*
- *** El vacio del plan semanal*** *(-- *siete tarjetas «Nada planificado» y luego «La semana esta
  vacia» --):* *** si es un problema de longitud*** *, pero no de correccion: *las siete tarjetas
  dicen la verdad. *Se anota como **mejora**, no como defecto.*

---

## *** 4 · LO QUE NO SE HA MIRADO ***

*** De 66 capturas se han mirado estas cinco***, *que son las que el encargo prioriza:* *listas
pobladas, *comparacion, *plan semanal, *diario *y *graficas.* ***Las otras 61 siguen sin mirar***,
*y no se dice nada de ellas.*

---

## *** 5 · COMO SE REPITE ***

```
uv run python -m plataforma.prueba_navegador      # con CESTA_UI y CESTA_CAPTURAS
```

*Y las capturas quedan en el directorio que diga `CESTA_CAPTURAS`.* *Las de esta revision, en*
`docs/ui/capturas/ronda-121/`, *que esta ignorado por git a proposito.*
