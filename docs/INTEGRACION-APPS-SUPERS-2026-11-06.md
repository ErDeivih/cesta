# Integración con las apps de los supermercados — qué es lícito y con qué límites

**Medido y documentado el 2026-11-06.** Punto 5 de la ampliación de David (`ALCANCE-APP.md` §5)
y casilla 7 de `WALL.md`. La investigación completa está en `INVESTIGACION-APP.md` §7; esto es
la decisión de producto y lo que la app hace hoy.

## 1. La respuesta corta

**No se puede «conectar tu cuenta de Carrefour/Lidl/Mercadona»**: ninguna de las seis cadenas
tiene una API pública para consumidores. Lo único documentado es la API de *marketplace* de
Carrefour (Mirakl), que sirve para **vendedores** publicar catálogo, no para leer tickets ni
cuentas. La app no promete lo que no hay.

La integración lícita y realista es **la importación manual**: la persona trae su lista o su
ticket pegando texto (y, más adelante, el CSV/JSON de una exportación RGPD). Cero credenciales,
cero login automatizado, cero scraping con la sesión de nadie.

## 2. Qué permite de verdad cada cadena (leído el 2026-11-05)

| Cadena | Lo que ofrece en su app | ¿API de consumidor? | Vía lícita para Cesta |
|---|---|---|---|
| Carrefour | Club, Mis listas, cupones, ChequeAhorro, ticket digital | No (solo Mirakl para vendedores) | Importar lo que la persona pegue o exporte |
| Lidl | Ticket digital, Lidl Pay, lista, cupones, Puntos Lidl | No | Importación manual; ofertas de club solo como condición |
| Mercadona | Compras anteriores, «productos habituales», login Google/Apple | No | Importación manual; el login es de la persona en Mercadona, no una puerta nuestra |
| DIA | Tickets, cupones Club, repetir compra, tarjeta digital | No | Importación manual |
| Alcampo | Favoritos, compra rápida, productos recurrentes, Mis listas | No | Importación manual; exportación RGPD por su DPO |
| Aldi | Folleto, listas, alertas de favoritos | No | Importación manual; ofertas de folleto |

**Exportación RGPD:** el derecho de portabilidad (AEPD) permite pedir a la cadena los datos en
formato estructurado y entregarlos a otro responsable cuando sea técnicamente posible. Alcampo y
Mercadona lo reconocen, pero **ninguna documenta una exportación autoservicio**: se pide por
correo al DPO. Por eso Cesta **no tramita la solicitud en nombre de nadie** (no somos
representantes) ni pide DNI: la persona la pide y, si quiere, nos pasa el fichero.

## 3. Lo que la app hace hoy

- **Importación manual desde texto pegado, CSV o JSON**: `PegarEnLaLista`
  (`componentes/PegarEnLaLista.tsx`) parte el texto, lee un CSV con cabecera
  `nombre,cantidad,nota` o un JSON de objetos con esas claves, enseña la previa y añade una línea
  por producto; se entra desde `Cesta.tsx`. También se puede subir el fichero. La cantidad va a la
  nota: **no se convierte en número de envases**. Es el camino real de «traer tu lista de otra app
  o tu ticket».
- **Vincular al catálogo, a mano**: cada línea de la previa puede buscar hasta tres candidatos
  con su precio y su cadena. La persona elige uno o la deja como texto; **nunca se vincula sola**.
  Una línea vinculada gana precio y comparación; una que no, se guarda como texto libre, como antes.
  Con varias líneas hay un botón **Buscar coincidencias en todas** que hace la búsqueda de una vez y
  deja los mismos candidatos revisables: no elige ninguna.
- **Exportación manual**: `ExportarLista` copia la lista como texto o descarga un CSV con
  `nombre,cantidad,nota`, para llevarla a otra app. Sin precios, sin cuenta y sin salir del
  aparato.
- **Copiar el ticket/lista a mano** y pegarlo: no se pide nada más.
- **Nada de cuentas**: no hay botón «conectar cuenta», ni campos de usuario/contraseña, ni
  OAuth a cadenas, ni sincronización en tiempo real. Si algún día una cadena publica API oficial
  con condiciones, se estudia entonces; no se finge antes.
- **Ofertas de club**: se enseñan como condición (`exige_club`, «Con Lidl Plus», «Con Club
  Alcampo, en tu tarjeta») y **no se restan** del total, porque son dinero diferido o condicionado
  (ChequeAhorro, Puntos, cupón en caja). Ver `docs/OFERTAS-2026-11-05.md`.

## 4. Lo que la app NO hace, y por qué

- Guardar credenciales, tokens o sesiones de las cadenas.
- Automatizar el login (navegador con la sesión de la persona, cookies o scraping autenticado),
  ni «con su permiso»: no hay base contractual y multiplica el riesgo para el usuario.
- Pedir DNI/certificado y tramitar la portabilidad en su nombre.
- Prometer sincronización en tiempo real.
- Restar precios de socio o cupones del total como si fueran precio de estantería.

## 5. Lo que ya se puede hacer, y lo que sigue fuera

Hecho el 8/11/2026:

1. **Importar** texto libre, CSV (`nombre,cantidad,nota`) o JSON (array de objetos con `nombre`,
   `cantidad`, `nota`; también `productos`/`items`) pegándolo o subiendo el fichero. La previa
   enseña cada línea y su nota antes de guardar nada. Si una fila no trae nombre, se descarta y se
   cuenta; no se inventa.
2. **Exportar** la lista como texto o como CSV con esas tres columnas. La exportación no incluye
   precios ni datos de la cuenta.
3. **Vincular al catálogo**: cada línea importada puede pedir candidatos a `/api/buscar` (hasta
   tres), ver su nombre, precio y cadena, y elegir uno. Con varias líneas, **Buscar coincidencias
   en todas** llena esas mismas tarjetas de una vez. Si no elige, se guarda como texto; no hay
   vínculo automático.
4. Las cantidades de la importación **siguen yendo a la nota**: el formato no cambia la regla de
   «2 kg no son dos envases».

Sigue fuera, y no se promete en la interfaz: el mapeo **automático** de texto libre a `grupo_id`
(lo que hay es asistido y revisable) y una marca de origen separada de la captura diaria. El
formato aceptado es el simple de arriba; una exportación RGPD con columnas distintas se adapta
cuando haya un ejemplo real.

## 6. Fuentes

- Carrefour, [El Club Carrefour](https://www.carrefour.es/clubcarrefour/) y [App Mi
  Carrefour](https://www.carrefour.es/clubcarrefour/app-mi-carrefour/) (leído 2026-11-05).
- Lidl, [nota de prensa «Puntos Lidl» (01/07/2026)](https://empresa.lidl.es/sala-de-prensa/actualidad-lidl/lidl-lanza-puntos-lidl-una-nueva-funcionalidad-de-su-app-dirigida-al-ahorro-de-sus-clientes-a-traves-de-recompensas-personalizables).
- Mercadona, [política de privacidad (rev. 20/07/2026)](https://tienda.mercadona.es/legal/privacy/en/)
  y [ficha de la app](https://apps.apple.com/es/app/mercadona/id1368037685).
- DIA, [ficha de la app](https://apps.apple.com/es/app/dia-supermercado-online-y-club/id660175630).
- Alcampo, [política de privacidad Club Alcampo (rev. feb. 2025)](https://www.compraonline.alcampo.es/content/politica-privacidad-club-alcampo).
- Aldi, [ficha de la app](https://apps.apple.com/es/app/aldi-supermercados/id669956906).
- AEPD, [derecho a la portabilidad](https://www.aepd.es/preguntas-frecuentes/1-tus-derechos/2-tus-derechos-de-proteccion-de-datos/FAQ-0113-que-es-el-derecho-a-la-portabilidad-de-los-datos).
- Channable, [canal de Carrefour en Mirakl](https://helpcenter.channable.com/list-advertise/list-and-advertise-es/vende-en-marketplaces/marketplaces-mirakl/como-a-configurar-un-canal-de-carrefour-spain)
  (leído: es para vendedores, no para tickets).

## 7. Verificación (08/11/2026)

- **`PegarEnLaLista`**: 11 pruebas verdes. La previa se enseña antes de guardar nada; al añadir,
  cada línea llama a `alAnadir` una vez; «2 kg» va a la nota, no a un número de envases; el CSV y
  el JSON se leen con la misma regla; subir un `.csv` lo deja en la previa; los candidatos no se
  buscan solos, el vínculo lo elige la persona y **Buscar coincidencias en todas** no elige ninguna;
  si falla a medias, se dice en vez de callarlo.
- **`pegar.ts`**: 7 pruebas del lector (texto, CSV con comillas, filas sin nombre, JSON de
  objetos y envuelto en `productos`, JSON roto y CSV sin cabecera).
- **`ExportarLista` / `exportarLista.ts`**: 3 pruebas de la vista y 3 del contenido: CSV con
  cabecera `nombre,cantidad,nota` y comillas escapadas, texto legible y nombre de fichero seguro.
- **`Mosaico`**: 7 pruebas verdes. «Rellenar de una vez (N)» enseña los nombres y cuántos son; no
  ofrece ni repite lo que ya está en la lista; «La siguiente sería…» sale del orden de la API; si
  falla a medias, cuenta cuántos entraron y cuántos no.
- **`tsc --noEmit` y `vite build`** sin errores. El servicio de la app se ha vuelto a sellar.
- **Límites**: ninguna cadena tiene API de consumidor; no se guardan credenciales ni sesiones; no
  hay login automatizado ni OAuth; no se pide DNI ni se tramita la portabilidad en nombre de
  nadie; no se exportan precios ni datos de cuenta; el CSV/JSON acepta el formato simple de esta
  ficha y no promete adaptar cualquier exportación RGPD. Las ofertas de club no se restan del
  total.

## 8. Pendiente de David (08/11/2026)

Lo que queda no se puede cerrar sin una decisión o un dato suyo:

1. **Mapeo automático de nombres a grupos.** Hoy el vínculo es asistido: se enseñan hasta tres
   candidatos y la persona elige. Automatizarlo exige decidir el umbral de confianza y qué hacer
   cuando dos productos se parecen; un mal vínculo pone un precio que no es.
2. **Una exportación RGPD real.** El formato aceptado es el simple `nombre,cantidad,nota`; para
   adaptar las columnas de Mercadona/Alcampo/Carrefour hace falta un ejemplo real (CSV o JSON) de
   lo que entrega la cadena. Sin ese ejemplo no se adivinan columnas.
3. **Precios en la exportación.** Hoy no se exportan precios ni datos de cuenta; si los quiere, es
   una decisión de producto y hay que decir de qué fecha y de qué cadena.

No hay nada de esto prometido en la interfaz. La integración lícita sigue siendo manual: sin
cuentas, sin credenciales y sin login automatizado.
