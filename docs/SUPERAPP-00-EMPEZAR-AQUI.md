# Cesta: encargo de ejecución para DeepSeek

Fecha: 7 de octubre de 2026. Estado: **especificación investigada, no implementación terminada**.

## Encargo y precedencia

Convertir Cesta en una suite doméstica profesional con tres aplicaciones separadas:
**Compra**, **Recetas** y **Calorías**. Comparten acceso y datos de producto, no
pantallas, borradores, menús de sección ni acciones implícitas. El usuario pide
recorrer las fichas de **todas las cadenas y todos los productos pertinentes**,
no solo DIA ni solo los nuevos. Mantener consumibles y reutilizables domésticos
seleccionados; no transformar el proyecto en un catálogo de electrodomésticos.

Esta ampliación manda sobre las decisiones visuales anteriores incompatibles:
el menú lateral sustituye a la cabecera con destinos mezclados. Mantener las
garantías de datos, privacidad, teclado, móvil y CSP de los documentos previos.
No borrar los informes históricos ni atribuirles un alcance que no tuvieron.

Leer en este orden:

1. Este documento: ejecución, límites y aceptación.
2. [Diseño, pantallas y funcionalidades](SUPERAPP-01-DISENO-Y-PRODUCTO.md).
3. [Fichas completas, Lidl e identidad](SUPERAPP-02-DATOS-LIDL-IDENTIDAD.md).
4. [Fuentes y evidencia](SUPERAPP-03-INVESTIGACION.md).
5. `CESTA-REVISION-SUPERAPP-2026-10-06.md`, muro, contrato y tareas anteriores.

## Decisiones cerradas: no volver a preguntarlas

- Nombre de trabajo Cesta; no invertir tiempo en inventar otra marca.
- Menú lateral de aplicaciones en escritorio; cajón lateral accesible en móvil.
- Mantener React/Vite/TypeScript y backend actual; no migrar a Next, microservicios
  ni proveedores de pago por una maqueta generada.
- Datos e infraestructura locales. No despliegue público, compras ni cuotas nuevas.
- Calorías es privada por persona, aunque Compra sea compartida por hogar.
- Las recetas pueden ser privadas o compartidas expresamente con el hogar.
- Un ingrediente genérico no es un producto comercial exacto. Comprar no es consumir.
- Priorizar precisión a cantidad de comparaciones; la abstención es resultado válido.
- Aprovechar primero crudo histórico; renovar fichas conocidas mediante cola.
- No buscar paridad artificial de filas entre Lidl y Aldi. Sí agotar fuentes
  públicas pertinentes y medir lo que falta con evidencia.
- v0: se hizo **una consulta breve** de dirección visual. No seguir consumiendo
  allí generaciones. Continuar desde el proyecto Stitch indicado en investigación.

## Forma de trabajar sin consultas rutinarias

Inspeccionar git y los ficheros antes de modificarlos. Un solo escritor por fichero;
preservar cambios ajenos. Ejecutar los paquetes de abajo en orden de dependencias,
con entregas pequeñas y pruebas. Resolver decisiones reversibles con estos defaults.
Si un paquete se bloquea, documentar causa exacta y continuar con otro independiente.
No parar simplemente por terminar un paquete; tampoco declarar todo completo
cuando quedan fallos. No sustituir implementación por ampliar este plan otra vez.

Pedir intervención solo ante: credencial necesaria ausente, CAPTCHA o aceptación
de términos, coste nuevo, cambio destructivo irrecuperable, despliegue público,
fuente no autorizada o conflicto real con cambios simultáneos que no pueda aislarse.
No eludir bloqueos ni inventar datos para cumplir una cifra. Si Lidl no publica
un surtido completo accesible, dejar esa parte como **limitación de fuente**,
no «hecho»; avanzar todo lo demás. El trabajo continuo no significa reintento infinito.

## Paquetes y puerta de aceptación

| ID | Trabajo y ficheros orientativos | Depende | Se acepta cuando |
|---|---|---|---|
| S00 | Congelar baseline; `docs/CESTA-MURO.md` | — | Estado git, comandos y cifras fechadas; conservar cambios previos; no secretos |
| S01 | Publicación versionada, `core/manifiesto.py`, storage y lectores | S00 | Crash entre escrituras no mezcla versiones; rollback y concurrencia probados |
| S02 | Cola de fichas, todos los collectors, nuevo inventario de cobertura | S01 | Todo producto incluido tiene estado, próxima revisión y evidencia; reanuda sin duplicar |
| S03 | Ampliar Lidl por sitemap, fichas y ofertas | S02 | Informe por fuente y familia; no se cierra por 76 ofertas; ninguna ausencia supone retirada |
| S04 | Modelo de identidad y banco independiente; matching y API | S02 | Exactos, formatos y alternativas separados; conflictos bloqueados; métricas por familia |
| S05 | Selector único y optimizador, `plataforma/api/cesta.py` y consumidores | S04 | Fechas, tienda, club y cantidad se aplican en todos los endpoints, no solo UI |
| S06 | Armazón y sistema visual, `App.tsx`, `Cabecera.tsx`, `Nav.tsx`, estilos | S00 | Tres layouts, rutas y estados aislados; drawer, teclado, responsive y CSP comprobados |
| S07 | Compra: búsqueda, ficha, favoritos, listas, reparto, historial | S05,S06 | Recorrido real con producto exacto y alternativa explícita; sin regresiones de listas |
| S08 | Recetas: persistencia, biblioteca, editor, modo cocina, planificador | S02,S06 | Varias recetas, recarga, edición, aislamiento, raciones y lista propuesta verificadas |
| S09 | Calorías: diario propio y tendencias | S02,S06,S08 | Alimento/receta versionados; días incompletos; exportación y permisos; no compras como comidas |
| S10 | Puentes optativos entre aplicaciones | S07,S08,S09 | Repetir una petición no duplica lista/comida; vista previa y consentimiento explícito |
| S11 | Gráficas, aprendizaje y rendimiento | S07,S09 | Cada gráfica define medida y universo, tabla accesible; ejemplos crudo→pantalla |
| S12 | Ensayo integral y cierre | Todas | Datos reales, dos cuentas, backup restaurado, móvil/desktop y límites publicados |

No bloquear S06 por S01: diseño y aislamiento pueden avanzar con fixtures etiquetados.
No bloquear toda la suite porque una cadena no publique nutrición; mostrar cobertura.

## Evidencia obligatoria por paquete

Actualizar `docs/SUPERAPP-ESTADO.md` (crearlo al iniciar): estado, commit o diff,
ficheros, pruebas ejecutadas, datos medidos, capturas, pendientes y siguiente paso.
Mantener IDs anteriores T02/T03/T05/T11 relacionados, no dos tableros contradictorios.
No editar pruebas para ocultar regresiones; cambios de contrato llevan explicación.
No reutilizar «1.195 tests» como cifra actual sin volver a ejecutar.

Comandos actuales: `uv run pytest -q`, `uv run ruff check .`; en
`plataforma/web/app`, `npm run build`, `npm run test:cocina`.
Añadir pruebas de integración nuevas al comando habitual, no dejar suites olvidadas.
Las pruebas de producción/navegador existentes se inspeccionan antes de ejecutarlas:
pueden crear cuentas o modificar datos; usar entorno de ensayo separado.

Pruebas finales: 360/390/768/1440 px, zoom 200 %, teclado, red caída y recuperación,
dos usuarios sin filtración, recarga sin pérdida, publicación fallida sin corruptela,
productos sin precio, sin GTIN, pack, granel, club, cambio de fórmula y fecha futura.

La calificación final tiene tres ejes separados: **función**, **calidad/cobertura
del dato** y **operación/seguridad**. Un build verde no certifica ninguno de los
otros dos. No abrir a terceros hasta un encargo posterior y su puerta de seguridad.
