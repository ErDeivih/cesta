# La version realmente servida, *verificada*

*15/10/2026, ronda 2 del objetivo de validacion. *Esto responde a la primera mitad del
punto 7: *** verificar la version realmente servida, *no solo el codigo local.*** *

---

## 1. *Que sirve `cesta-web-1`, y de donde*

```
*** montajes ***: *`docker inspect cesta-web-1` da cuatro, *y el que importa es este:*
   *** bind *** `F:\aprendizaje\scrap\plataforma\web\dist` *** -> *** `/srv` *** ✓✓✓
*** -> *** sirve el `dist` LOCAL por bind mount ***, *no una imagen construida aparte ✓
*** -> *y por eso el hash coincide: *`/assets/index-BqRTD47s.js`, *
   *** 336.690 bytes ***, *los dos -- el servido por HTTP y el del disco ✓
```

*** Y eso cambia la conclusion ***: *la version servida **no es una version vieja
congelada**: *es *** tan actual como el ultimo `npm run build`.*** *

---

## 2. *Y ahora, *lo que se servia **no** era evidente*

*** Al comprobar el chunk principal, *`index-BqRTD47s.js`, *no aparecian los marcadores
del trabajo de esta sesion.* *Y eso **no** era un problema: *`Cesta`, *`Ajustes`,
*`Panel` y las demas son `lazy()`, *asi que su texto vive en *** su propio chunk.*** *

*** Se comprobaron los ocho chunks, *y el resultado es coherente *** con las rondas: *

| *chunk* | *`flex min-h-full flex-col gap-4`* | *`Etiqueta tono="mal"`* | *y es correcto porque* |
|---|---|---|---|
| *`Ajustes`* | *** SI *** | *no* | *ronda 60* |
| *`Avisos`* | *** SI *** | *no* | *ronda 60* |
| *`Cesta`* | *** SI *** | *** SI *** | *rondas 58 y 64 · ronda 41* |
| *`Unirse`* | *** SI *** | *** SI *** | *ronda 62 · ronda 41* |
| *`Escaner`* | *** SI *** | *** SI *** | *rondas 45 y 41* |
| *`Panel`* | *** SI *** | *** SI *** | *rondas 47 y 41* |
| *`Favoritos`* | *no* | *no* | *** correcto ***: *su `Vacio` lleva `grow` y su raiz no se toco, porque la ronda 63 midio que **no hacia falta*** |
| *`Grupo`* | *no* | *no* | *correcto*: *no se le toco la raiz* |

*** Y todos los chunks son de las 23:02:24 ***, *del ultimo build.* *

---

## 3. *Que queda de este punto*

*** VERIFICADO ***: *la publicacion servida **es** el `dist` local, *y **lleva los cambios
de esta sesion**, *con los dos casos negativos (`Favoritos` *y `Grupo`) *** explicados
y correctos.*** *

*** Y ESO SE VERIFICO DESPUES, *en la ronda 35 *** *(-- *actualizado en la 45 --)*: *
*la puerta del navegador (`prueba_navegador.py`) *** navega la aplicacion servida,
*pulsa, *y pasa 87 comprobaciones con cero fallos*** *-- *incluidos el recorrido de
la lista, *la compra, *los envases, *el sustituto autorizado, *el diario y la
persistencia. *O sea que *** lo servido no solo tiene el codigo: *se comporta.*** *

*** Y LO QUE SIGUE SIN VERIFICAR, *medido***: *las *** siete pantallas con sesion, *
*sin captura*** *(-- *la puerta las recorre y las pasa --)*, *y *** la seccion de
los toques ***, *cuya causa esta medida.* *
