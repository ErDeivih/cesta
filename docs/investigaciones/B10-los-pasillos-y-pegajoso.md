# B10 · **Los pasillos, y «pegajoso»** -- quince ensayos, y la doctrina otra vez con su palabra

*(13 de octubre de 2026. **Cuarta ronda de B10. Y «pegajoso» era `sticky`.**)*

## 1. `test_pasillos.py`: ocho ensayos -- **la logica**

```
test_el_pasillo_del_grupo_es_el_que_MAS_MIEMBROS_COMPARTEN      <- LA REGLA: por mayoria
test_el_empate_lo_rompe_EL_RECORRIDO_DE_LA_TIENDA                <- y EL EMPATE, por el recorrido REAL
test_un_grupo_sin_pasillo_NO_VIAJA_CON_PASILLO_NULO               <- *** no inventar pasillo ***
test_SIN_LA_COLUMNA_EN_GOLD_no_hay_pasillos_Y_NO_SE_INVENTAN       <- *** ¡la doctrina, con su palabra! ***
test_con_pasillos_no_reordena_y_no_toca_las_lineas_sin_grupo
test_el_orden_del_pasillo_es_el_DE_LA_TIENDA_Y_NO_EL_ALFABETO      <- *** el recorrido, no el abecedario ***
test_la_ruta_de_la_lista_manda_el_pasillo_en_cada_linea
test_sin_pasillos_la_ruta_devuelve_lo_de_siempre
```

> *** Y las dos primeras son **la regla y su desempate**, y las dos estan medidas: ***
>
>   - **el pasillo de un grupo es el que MAS MIEMBROS comparten** *-- *o sea: **la mayoria**, no el primero ni el
>     promedio;*
>   - **y el empate lo rompe EL RECORRIDO DE LA TIENDA** *-- *que es **el orden real de la tienda**, no el alfabetico
>     ni el azar: **`test_el_orden_del_pasillo_es_el_de_la_tienda_y_no_el_alfabeto` lo dice por su nombre.***
>
> *** Y `test_sin_la_columna_en_gold_no_hay_pasillos_y_no_se_inventan` es **la doctrina con su palabra exacta**: ***
> *si **el dato no esta**, **no hay pasillos** -- *y **no se inventan**.*
>
> *** Y hay que juntarlo con `test_un_grupo_sin_pasillo_no_viaja_con_pasillo_nulo`: *** *un grupo al que **no se le
> conoce pasillo** **no aparece con un pasillo vacio** -- *porque **«vacio» se veria como «pasillo 0»**, y **seria un
> dato falso.** * **

## 2. `test_pasillo_pegajoso.py`: cinco -- **la pantalla**

```
test_el_pasillo_esta_PEGADO_DEBAJO_DE_LA_CABECERA_Y_NO_DETRAS    <- *** «pegajoso» = `position: sticky` ***
test_la_altura_de_la_cabecera_SE_MIDE_Y_SE_PUBLICA                <- *** y se MIDE, no se supone ***
test_las_lineas_sin_pasillo_van_AL_FINAL_Y_SIN_ENCABEZADO
test_el_orden_de_DENTRO_DE_UN_PASILLO_no_se_toca
test_el_tipo_de_la_linea_lleva_el_pasillo_y_es_OPCIONAL
```

> *** «Pegajoso» no era una metafora: *** *es **`position: sticky`** -- *el encabezado del pasillo **se queda pegado
> debajo de la cabecera de la aplicacion** mientras se baja por la lista.*
>
> *** Y `test_la_altura_de_la_cabecera_se_mide_y_se_publica` es **la pieza fina**: *** *el desplazamiento del
> `sticky` **depende de la altura de la cabecera** -- *y **en vez de poner un numero fijo** (`60px`), **se MIDE y se
> publica**.*
>
> *** O sea: **ni un numero magico ni una suposicion** *** -- *que es **la doctrina aplicada a una medida de
> pantalla**: *si la altura cambia, **el orden no se rompe**, porque **nadie la escribio dos veces**.*
>
> *** Y `test_las_lineas_sin_pasillo_van_AL_FINAL_Y_SIN_ENCABEZADO` es **la otra mitad de «no inventar»**: *** *lo que
> no tiene pasillo **no se mete en uno cualquiera**: va **al final**, **y sin encabezado** -- *porque **un encabezado
> vacio seria una promesa de orden que no existe.** *

## 3. `test_lista_de_casa_unica.py`: dos, y uno es **el codigo correcto**

```
test_la_segunda_lista_de_casa_responde_409_Y_NO_500               <- *** 409: Conflicto. NO 500 ***
test_una_lista_normal_sin_marca_de_casa_sigue_creandose
```

> *** Y `409` es **la respuesta correcta**, no un detalle: *** *«ya existe una lista de casa» **es un conflicto**
> (409), **no un fallo del servidor** (500).*
>
> *** O sea: **el sistema distingue «no puedo porque choca» de «me he roto»** *** -- *que es **la misma disciplina
> que `test_quitar_dos_veces_da_404_y_no_dice_hecho_cuando_no_ha_hecho_nada` (B05) y que
> `test_el_404_se_distingue_de_un_fallo` (B07).* **Tercera vez.**
>
> *** Y `es_de_casa` es **una marca, no un tipo**: *** *`test_una_lista_normal_sin_marca_de_casa_sigue_creandose` --
> *o sea: **las listas normales siguen igual**, y **la marca es opcional** (`es_de_casa: bool = False`).*

## 4. Y B10, con cuatro rondas

```
  1) LOS ESTADOS           `cambia_linea` + `SIN_CAMBIAR`                          *cuerpo POR LEER*
  2) LAS LISTAS Y EL ORDEN *** HECHO, y con 15 ensayos: *** `es_de_casa` (marca, no tipo) · **409 y no 500**
                           · el pasillo **por mayoria** y **el empate por el recorrido REAL** · «no se inventan»
                           · `sticky` **con la altura MEDIDA y publicada** · y sin pasillo -> **al final y sin
                           encabezado**
  3) BUSCAR Y FILTRAR      *** POR MIRAR ***
  4) LA PAGINACION         MEDIDA -- hay `limite` con cotas; no hay `cursor`/`version`/`offset`
  5) EL GASTO Y EL AHORRO  HECHO -- 17 ensayos
  6) Y LA DUREZA           `cambia_linea` + `SIN_CAMBIAR`                          POR MIRAR
```

> *** Y quedan **dos**, y las dos son **la misma clase de cosa**: ***
>
>   - **(3) buscar y filtrar** *-- «buscqueda con marca/formato/EAN y filtros utiles»;*
>   - **(6) la dureza** *-- «reintento/offline/concurrencia no pierden cantidades ni revocaciones».*
>
> *** Y la (6) **es la que el encargo del propietario pone como restriccion**, y **la que B05 ya miro**: ***
> *`ON CONFLICT (id) DO UPDATE` + `borrado_en` + `COALESCE` + `SIN_CAMBIAR` -- *o sea: **la respuesta esta a la
> vista**, y **lo que falta es su ensayo de concurrencia**, no su mecanismo.*
