# Revisión y continuación de la etapa 61–80

Baseline inspeccionado: `a32957e`, árbol limpio antes de esta revisión.
La etapa sí construyó rutas, pantallas y almacenamiento que antes no existían.
Las declaraciones de paquete terminado requieren las correcciones siguientes.
Esta revisión es de código y pruebas; no certifica los recorridos en navegador
ni la seguridad de un despliegue. No se activó el motor de identidad en producción.

## Correcciones realizadas

En `core/diario.py`, cada macronutriente se suma independientemente de si la
entrada publica calorías. Antes una entrada con 12 g de proteína y energía
desconocida perdía la proteína del subtotal. La respuesta añade `cobertura`
por nutriente: entradas con dato, entradas totales y cobertura completa.
Se preserva `completo` como cobertura energética de las entradas registradas
para mantener compatibilidad; no representa toda la ingesta real del día.

El rango devuelve energía desconocida como `null`, en vez de inventar cero.
La escritura rechaza NaN e infinito en cantidades y nutrientes. La pantalla
del diario deja de afirmar que el subtotal equivale al día entero cuando
todas las entradas registradas tienen calorías. Pruebas nuevas cubren
nutrientes sin energía, cero publicado, rango desconocido y números no finitos.

## Prioridad 1: propiedad de Recetas y Calorías

Hallazgo de código: `plataforma/api/main.py` monta ambos routers sin dependencia
de sesión. Sus manejadores no usan `usuario_actual`; `_con()` abre una base
SQLite compartida. El esquema de `core/diario.py` no tiene propietario y las
consultas/borrados se hacen por fecha o identificador sin usuario. Estar en un
fichero local no proporciona privacidad entre las cuentas de la aplicación.

Implementar autenticación y autorización antes de usar esos módulos con datos
personales. Reutilizar la sesión existente; extraer su dependencia a un módulo
común si hace falta para evitar importaciones circulares. La identidad del
propietario procede exclusivamente de la sesión, nunca del cuerpo de petición.
Diario privado por usuario. Recetas privadas por defecto; compartir con hogar
requiere acción y permisos explícitos. Plan y versiones conservan el mismo
ámbito de acceso. Aplicar autorización también a archivo, actualización, rango,
enumeración y borrado, no solo al alta.

Migrar sin asignar los datos anteriores arbitrariamente al primer usuario.
Conservar los registros históricos sin propietario en un ámbito legado cerrado
hasta su asignación explícita. No borrar bases ni reinicializarlas. Añadir
pruebas HTTP de la aplicación montada: anónimo recibe 401; B no puede enumerar,
leer, cambiar ni borrar registros de A. Invalidar cachés de recetas, plan y
diario al cambiar de cuenta; revisar sus claves de consulta, hoy sin usuario.
Que una función pueda probarse por llamada directa no justifica omitir permisos.

## Prioridad 2: identidad y selección de coste

`plataforma/api/cesta.py::_candidatos` construye la referencia canónica por
`(grupo, fuente)`. Así un candidato de Carrefour se compara con un producto
canónico de Carrefour, no necesariamente con el elegido por el usuario ni con
una referencia común entre cadenas. `_resolver` calcula un veredicto pero
continúa calculando e incluyendo el coste incluso si no es exacto. Un aviso
no equivale a una autorización explícita de sustitución.

Separar la referencia solicitada de los candidatos: si la línea es exacta,
resolver contra su identidad y no contra el candidato local más conveniente.
Una petición genérica de familia tendrá otro contrato. En totales exactos,
excluir candidatos no exactos o no autorizados y explicar lo que falta. Ofrecer
alternativas en una propuesta separada que se confirma y persiste en esa línea.
Usar el modelo completo de presentación: el adaptador actual pasa nombre/GTIN
pero no todos los atributos de marca, cantidad y variante disponibles.

Además, `_candidatos` retiene primero el menor precio unitario del envase antes
de aplicar promociones y cantidad. Eso puede descartar una oferta más barata
para las unidades solicitadas. Evaluar todos los candidatos elegibles contra
la cantidad, fechas y condiciones de club/canal, y minimizar el coste final.
Verificar la fecha del precio y la versión del catálogo además de la partición
de promoción: `fecha_tope` en promociones no certifica toda la vigencia.

Pruebas de aceptación: grupo antiguo con dos marcas incompatibles en diferentes
cadenas; producto exacto con alternativa más barata no autorizada; compra de
dos unidades donde el envase de mayor precio obtiene menor coste por oferta;
precio o promoción futura; distintas variantes bajo el mismo GTIN.

No interpretar «2.222 grupos se partirían» como 2.222 errores demostrados:
es una propuesta del nuevo motor, pendiente de contraste independiente. Tampoco
una cuarentena demuestra que una ficha mienta: puede haber un error de parser,
unidad, dato antiguo o presentación incompleta. Clasificar conflictos por causa,
automatizar los comprobables con evidencia y mantener ambiguos aislados. No
hace falta revisar manualmente los 266 para publicar componentes verificados
en sombra o continuar las interfaces. No activar exactos sin validar su precisión.

## Prioridad 3: cerrar pantallas y comportamiento persistente

Las rutas de detalle de receta, alimentos y tendencias siguen sirviendo `Cocina`
con modo. El detalle por `recetaId` debe leer la receta persistida de esa ruta,
con versiones accesibles y error 404 real. Eliminar estados ficticios del módulo
compartido cuando sus reemplazos existan. Terminar edición, errores al archivar,
plan modificable y cálculo de raciones; tener un formulario de alta no cierra
todo S08. S09 necesita cantidades, origen y versiones reales, cobertura por
nutriente y tendencias con huecos en vez de ceros.

La versión del diario hoy es un texto: no verifica que exista esa receta/version
ni obtiene su contenido. Definir y probar el enlace autorizado a una versión
existente o guardar una instantánea autocontenida con procedencia. Evitar
referencias inventadas y distinguir receta vinculada de anotación manual.

Continuar los puentes S10 con vista previa e idempotencia. Separar comprar,
planificar y consumir. S11 debe explicar medida, cobertura y universo de cada
gráfica. S12 requiere prueba de dos cuentas y backup restaurado, no solo build.

## Datos y operación de continuación

Continuar fichas de todas las cadenas por lotes reanudables y presupuesto.
Reutilizar histórico antes de red. Medir nutrición por campo y familia, sin
extrapolar 0/26 a la cadena ni contar registros de la nueva cola como todo el
contenido histórico. No bloquear las tres aplicaciones por el inventario pendiente.

Orden de ejecución: aislamiento de usuarios → identidad solicitada y coste
elegible → pantallas pendientes → puentes → gráficas → ensayo integral.
Fichas y resolución de conflictos avanzan por lotes a lo largo de esta secuencia.
Actualizar SUPERAPP-ESTADO con evidencia y pendientes; no repetir cierres
documentales cuando haya un comportamiento concreto que implementar.

## Verificación ejecutada en esta revisión

- `uv run pytest -q`: **1.318 pruebas aprobadas**, dos avisos de dependencias,
  185,09 segundos. No se ejecutó el ensayo independiente de navegador.
- `uv run ruff check .`: limpio. Se corrigió también RUF005 en el adaptador
  de candidatos, sin cambiar su comportamiento de identidad.
- `npm run build`, desde `plataforma/web/app`: TypeScript y compilación correctos;
  sigue el aviso por el tamaño del paquete JavaScript (643,62 kB sin comprimir).
- `npm run test:cocina`: seis pruebas aprobadas. `git diff --check`: limpio.
- Cambios sin commit; no se modificaron bases reales, ni se hizo ingesta o despliegue.

Estas pruebas verifican las correcciones del diario y las regresiones cubiertas
por el proyecto. No convierten los hallazgos de autorización e identidad en
problemas resueltos: permanecen como los siguientes trabajos de implementación.
