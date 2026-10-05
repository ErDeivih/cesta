# Auditoría de Cesta: identidad, cesta familiar y fiabilidad

Revisión del 5 de octubre de 2026. Base: código local en `7e55b26`, datos presentes en
disco y traspaso de DeepSeek. Se conservan los cambios previos de `core/datos/secciones.yml`
y `docs/CIFRAS.md`. Esta revisión no regenera datos ni cambia la aplicación en producción.

## Dictamen

Hay una plataforma bastante desarrollada y una base aprovechable. Sin embargo, **hoy no
se puede prometer que el ahorro mostrado corresponda al mismo producto en distintas cadenas**.
La razón principal es de modelo: se usa un único grupo tanto para identidad como para
alternativas. Mejorar el parecido entre nombres no resuelve esa ambigüedad.

Las pruebas existentes comprueban muchos comportamientos, pero algunos de esos comportamientos
contradicen el encargo actual. Por ejemplo, las pruebas aceptan llamar «idénticos» a dos
productos de la misma marca sin códigos que permitan confirmar su identidad.

## Comprobaciones ejecutadas

- Suite Python: **1.049 pruebas pasan**, dos avisos de deprecación de dependencias.
- TypeScript: `npm run tipos` termina correctamente.
- Verificador documental: pasan las cifras comprobadas, 23 campos, 715 referencias de
  archivo/línea y 145 comandos. Esto verifica estructura y recuentos, no la verdad de todas
  las afirmaciones de los documentos.
- Lectura de `grupos.parquet` y de las últimas particiones bronze/silver.
- Reproducción directa del selector de candidatos de la cesta contra gold real.
- La tarea «Cesta diaria» existe, está lista y anuncia la siguiente ejecución para el
  6 de octubre a las 06:00, en modo interactivo.
- La aplicación en `localhost:8080` no respondió: navegación y petición de salud agotaron
  sus tiempos de espera. `docker ps` no mostró contenedores activos. Por ello **no se
  certifica la experiencia visual ni el funcionamiento actual de las cuentas y listas**.
  Se revisó su código, sin ejecutar las puertas que crean cuentas en la base real.

Se añadió un instrumento de lectura reproducible:

    uv run python -m projects.cesta.auditar_identidad

Lee Parquet y emite JSON; no escribe en `data/`, no recolecta y no recalcula grupos.

## Estado medido del catálogo

| Fuente | Último bronze y silver aceptado | Productos |
|---|---|---:|
| Alcampo | 2026-10-01 | 23.842 |
| Aldi | 2026-10-05 | 2.536 |
| Carrefour | 2026-10-05 | 16.585 |
| DIA | 2026-10-05 | 5.855 |
| Mercadona | 2026-10-05 | 4.321 |

Total: **53.139 productos**, **8.812 grupos multicadena**. En esos grupos:

- **2.276** contienen más de un EAN normalizado.
- **593** contienen más de una combinación de cantidad y unidad marcada como fiable.

Son señales de revisión, **no tasas de error**: códigos distintos pueden requerir una
equivalencia validada, y comparar tamaños distintos por litro puede ser útil. Pero esas
comparaciones no pueden presentarse automáticamente como el mismo artículo y envase.

## Hallazgos prioritarios

### 1. La elección exacta se pierde al añadir a la cesta — crítico

`plataforma/web/app/src/componentes/BotonAnadirACesta.tsx` guarda `grupo_id` y pone
`producto_id: null`, incluso cuando el botón se usa desde una ficha concreta.
`plataforma/api/cesta.py::_candidatos` después admite todos los miembros del grupo.

Reproducción real: grupo **10643**.

| Cadena | Producto | Precio del envase |
|---|---|---:|
| Alcampo | Asturiana entera, botella, 6 × 1 l | 7,56 € |
| DIA | Celta entera, 6 × 1 l | 6,54 € |

Una petición de Asturiana devuelve ambos candidatos. Los 1,02 € de diferencia son entre
marcas distintas y, además, capturas de fechas distintas. Son una posible sustitución,
no un ahorro confirmado en Asturiana.

El grupo **15729** también mezcla La Colmenareña con Asturiana. El **11627** mezcla
descripciones de botella y brik de Asturiana de un litro; hay varios EAN. Requiere revisar
presentación, no dar por idéntico porque coinciden marca y volumen.

### 2. «Comparación fiable» no significa identidad — crítico

`core/matching.py::nivel` devuelve `identico` por marca igual cuando falta un EAN.
`projects/cesta/emparejar.py` construye los grupos mezclando enlaces de distintos niveles.
Su columna `comparacion_fiable` se calcula por pertenencia a las unidades admitidas,
no por una demostración de identidad.

Además, `SelloComparable` explica al usuario «El mismo producto está en más de una cadena»
con solo comprobar el número de cadenas. El texto promete más de lo que mide el dato.

El porcentaje de «acierto» del traspaso tampoco certifica precisión global: el método
`emparejar.medir` oculta el EAN y cuenta cuántos pares conocidos recupera. Es una medida de
recuperación sobre ese subconjunto. Se necesitan precisión de identidad, falsos positivos,
cobertura y una muestra revisada por separado.

### 3. Fechas, disponibilidad y tienda no protegen el optimizador — crítico

Gold no contiene `disponible`, `capturado_en` ni `tienda_id`.
`_candidatos` recibe `fecha_tope` pero no la usa; tampoco usa el valor de
`comparacion_fiable` que selecciona. La llamada real aceptó Alcampo del 1 de octubre el
día 5. `dias_precio_valido=3` está configurado, pero no se aplica en ese selector.

Antes de recomendar una tienda hay que resolver una oferta de un producto exacto en una
zona, con fecha, disponibilidad y confianza de precio. Un precio antiguo puede consultarse
en el histórico sin decidir el lugar de compra de hoy.

### 4. Se confunde estimación con gasto realizado — alto

`main.cerrar_compra` llama a `cesta.coste_por_linea`. Esta función elige el precio del
catálogo de la cadena elegida o, si no lo encuentra, el más barato de otra cadena.
No recibe el precio confirmado del ticket. Tampoco aplica en ese punto la misma mecánica
promocional de `_resolver`.

La compra archivada es, por tanto, una estimación. No debe sostener un gráfico denominado
«gasto real mensual» ni un ahorro realizado sin distinguir su origen. Hace falta guardar
producto comprado, tienda real, cantidad, importe pagado y procedencia: ticket, entrada
manual o estimación. Si falta el precio de la tienda elegida, no sustituirlo silenciosamente
por el precio de otra.

### 5. Promociones y club: base útil, personalización incompleta — alto

`core/promos.py` interpreta 3×2, segunda unidad y otras mecánicas. Eso es útil.
Sin embargo, agrupa textos de club, tarjeta, cupón y monedero como acumulables; no todos
esos casos representan la misma condición comercial.

`_promos_vigentes` selecciona únicamente texto, usa la fecha global más reciente y cachea
por día. No transporta al cálculo `promo_hasta`, `promo_club`, `promo_solo_online` ni
un perfil de tarjetas del comprador. Una segunda captura del mismo día puede no refrescar
esa caché. `_resolver` aplica porcentajes al precio actual sin una señal explícita de si
ya incluye el descuento: hay riesgo de doble descuento que exige comprobar casos reales.

Modelo necesario: importe a pagar ahora, saldo futuro, requisitos de tarjeta/cupón,
canal online/tienda, vigencia, mínimo de unidades y límite de usos. Las reglas no interpretadas
se muestran como información pendiente de confirmar, sin restarlas del total.

### 6. El alcance familiar no se aplica de extremo a extremo — alto

Ya existe una exclusión de bazar en `core/config.py`, aplicada al árbol de Alcampo.
Pero gold contiene **245 productos de Alcampo cuya rama está expresamente excluida**:
fundas de sofá, juguetes, sombrillas y otros. El buscador añade resultados sin aplicar
ese filtro por producto; además pueden aparecer artículos cruzados entre categorías.

`core/cobertura.py::revisa` compara todas las ramas del bronze anterior. No recibe la
política de alcance. El colector ejecuta ese veto antes de algunas comprobaciones del
cambio de alcance. Por eso «Hogar y Decoración» puede bloquear datos alimentarios frescos.

La corrección debe aplicar la misma política a descubrimiento, admisión de producto,
referencia histórica de cobertura y publicación. No basta con relajar el umbral del WAF.
Queda pendiente reconstruir por IDs la captura rechazada para determinar cuánto fue
reubicación de categorías y cuánto pérdida real.

Alcance propuesto: alimentación, bebidas, limpieza, lavado, higiene, consumibles de bebé,
mascotas y hogar que se reponen. Fuera: tecnología, electrodomésticos, mobiliario,
decoración duradera, juguetes y textil. Los casos ambiguos se revisan por producto.
Mercadona es una referencia de necesidades, no una lista exclusiva de productos permitidos.

### 7. Las estadísticas requieren varias correcciones semánticas — alto

- `core/derive.py` usa ventanas de 7, 30 y 90 **observaciones**, aunque las etiquetas dicen
  días. Con capturas ausentes dejan de ser ventanas de calendario.
- `duracion_tipica_promo` suma todas las observaciones promocionales por producto, sin
  separar episodios. No mide la duración típica de una promoción.
- El índice de `api/analisis.py` compara cada producto consigo mismo entre capturas,
  una base más defendible que promediar surtidos. Aun así debe controlar cambios de
  presentación bajo el mismo identificador. No representa por sí solo el gasto familiar.
- La posición de cada cadena por sección hereda los grupos actuales: una agregación
  correcta no arregla identidades incorrectas en su entrada.
- Con 30 días acumulados no se ha demostrado estacionalidad anual ni ahorro anual observado.
  Cualquier extrapolación debe explicitar periodo, cantidades y cobertura.

### 8. La puntuación de calidad ya existe, pero es una heurística — alto

El traspaso dice que falta decidir la fórmula, pero `core/calidad.py::puntua` ya resta
puntos por aditivos, palma y longitud de ingredientes. No es una validación de calidad
nutricional. `por_precio` también asigna letras por precio relativo.

Medido: **8.492** filas con origen `precio`, **633** con `ingredientes` y **330** con
`ingredientes_off`. La interfaz distingue gama de precio y calidad, lo cual ayuda;
no obstante, conviene retirar cualquier promesa de calidad objetiva del resultado.
Mantener separados precio, composición publicada, Nutri-Score con procedencia y
preferencias personales. No introducir una nueva nota propia para tapar datos ausentes.

### 9. El informe diario puede presentar una ejecución rechazada como captura — medio

`cifras._ultima_de_cada_cadena` lee la última fila de `runs.csv` y el documento la titula
«última captura». Así `CIFRAS.md` muestra Alcampo del día 5, con 23.859 productos y cero
errores, aunque el bronze y silver aceptados son del día 1, con 23.842.

Deben separarse: última ejecución, productos recibidos, captura aceptada, fecha de los
precios publicados y motivo de rechazo. Un código 0 de la pasada global puede significar
cuatro cadenas actualizadas; no debe interpretarse como cinco cadenas completas.

## Modelo que cumple el encargo

| Concepto | Identidad | Uso |
|---|---|---|
| Familia | Leche | Explorar todas las marcas y variantes |
| Alternativa compatible | Leche entera de vaca, con restricciones elegidas | Sugerir sustituciones autorizadas |
| Producto exacto | Marca + gama + variante + presentación + pack | Comparar el mismo artículo |
| Oferta | Producto exacto + cadena + tienda/zona + canal + momento | Calcular precio y disponibilidad |

Confirmar identidad con GTIN normalizado y validado, comprobando contradicciones de
presentación. EAN iguales mal publicados no anulan un conflicto evidente de pack o variante.
Sin código, las coincidencias por atributos son candidatas pendientes de validación;
marca igual o parecido alto no bastan. Los embeddings pueden proponer, no certificar.

Cada línea de la lista necesita un modo explícito:

- **Este producto**: conserva su identidad exacta y busca ofertas del mismo.
- **Acepto alternativas**: conserva restricciones (entera, sin lactosa, etc.) y autoriza
  sustituciones, mostrando el producto elegido y el cambio de marca o formato.

Un pack de seis y un envase de un litro pueden compararse por litro, pero la cesta debe
calcular envases enteros, desembolso, cantidad sobrante y límites de la promoción.

Los IDs existentes se migran conservando listas, favoritos y compras. No regenerar todos
los grupos en producción sin mapear las referencias guardadas.

## Interfaz y análisis que priorizar

Conservar la aplicación existente y hacer visible la intención de compra:

1. **Mi compra**: productos pendientes, en el carro y compra finalizada. Un favorito es
   persistente; necesitarlo esta semana es un estado distinto.
2. **Buscar**: familias para explorar y fichas exactas para comparar. «Leche» puede traer
   todas; «Asturiana entera 1 l» debe respetar marca, variante y presentación.
3. **Comparar**: separar «mismo producto» de «alternativas». Mostrar fecha, zona, precio del
   envase y por unidad, condiciones del club y motivo si no se puede comparar.
4. **Mis gastos**: distinguir pagos confirmados de estimaciones; gráfico semanal/mensual,
   desglose por sección y ahorro contrafactual sobre una cesta de composición constante.
5. **Dónde comprar**: una tienda o un máximo elegido; cobertura de líneas, faltantes,
   desembolso, saldo futuro y coste de desplazamiento opcional. Sin faltantes invisibles.

Gráficas prioritarias: histórico del artículo exacto, coste de una cesta fija entre tiendas,
gasto confirmado por semana y sección, contribución de cada línea al ahorro y porcentaje
de la cesta con comparación exacta y fresca. El panel técnico puede seguir separado.

## Orden de implementación y aceptación

1. Contrato de identidad/oferta y política única de alcance. Pruebas con ejemplos reales:
   Asturiana/Celta, entera/desnatada, con/sin lactosa, brik/botella y pack/unidad.
2. Conservar el producto elegido en listas y favoritos; sustituir solo con autorización
   explícita. Migración ensayada en copia y sin pérdida de referencias.
3. Candidatos elegibles: zona, fecha, stock, precio válido y presentación. Un precio viejo
   nunca debe ganar una recomendación de hoy.
4. Mecánicas comerciales verificadas, perfil de club y tickets/importe confirmado. La
   misma cuenta debe alimentar vista previa, reparto y compra archivada.
5. Ventanas de calendario, episodios promocionales y gráficos basados en identidad exacta.
6. Pruebas de recorridos en móvil con servicios activos, incluyendo desconexión y
   sincronización. Validación humana de claridad antes de dar la interfaz por terminada.

No se ha desplegado ni publicado nada. Tampoco se ha recalificado la legalidad del proyecto,
estimado el coste de servirlo a terceros ni certificado seguridad de producción: son revisiones
separadas. La prioridad actual es que una comparación y un ahorro signifiquen lo que dicen.
