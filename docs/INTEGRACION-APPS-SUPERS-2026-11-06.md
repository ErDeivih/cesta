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

- **Importación manual desde texto pegado**: `PegarEnLaLista` (`componentes/PegarEnLaLista.tsx`)
  parte el texto, enseña la previa y añade una línea por producto; se entra desde `Cesta.tsx`.
  Es el camino real de «traer tu lista de otra app o tu ticket».
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

## 5. Lo que faltaría para que la importación sea más útil

Nada de esto se ha construido todavía, y no se promete en la interfaz:

1. Formato de entrada acordado para una exportación RGPD (nombre, cantidad, precio, fecha,
   cadena) y su previsualización.
2. Mapeo de texto libre a `grupo_id` (el mismo problema del emparejador) y una marca de origen
   («importado por ti el …») que no se mezcle con la captura diaria.
3. Pegar desde CSV/JSON además de texto.

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
