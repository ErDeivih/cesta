# Contraste posterior del traspaso aaff254

Fecha de inspección: 8 de octubre de 2026. Baseline: `aaff254`, árbol limpio.
Se leyeron los dos traspasos del agente y el código vigente. No se modificó la
base real, no se ejecutó ingesta, no se reconstruyeron contenedores. La cifra
1.467 corresponde al informe del agente; no se volvió a ejecutar la suite completa.

## Evidencia ejecutada

Las pruebas de cantidades repetidas, total autorizado, canónico común y endpoint
de autorización pasan: **16 aprobadas en 3,10 s**. Dos comprobaciones adicionales
con funciones reales y candidatos controlados muestran huecos en esa cobertura.

### 1. Selección conjunta, cobro separado

Con un producto a 100 céntimos y promoción `3x2`, `_candidatos` ya suma cantidades
para seleccionar el candidato. Sin embargo, `_resolver` aplica la promoción a
cada línea y `donde_comprar` suma esos costes separados.

Resultado observado, sustituyendo solo `_candidatos` por el mismo candidato:

| Peticiones del mismo producto en DIA | Total devuelto |
|---|---:|
| Una unidad + dos unidades, en dos líneas | 300 céntimos |
| Tres unidades, en una línea | 200 céntimos |

La promoción es la misma y la compra también. Una prueba de igualdad del
candidato elegido no verifica igualdad del total pagado.

Corrección requerida: aplicar promociones sobre una agrupación de compra por
producto efectivo, tienda y condiciones elegibles. Distribuir después el coste
en céntimos entre las líneas preservando exactamente el total; conservar los
identificadores originales para edición, carrito e historial. No agregar compras
en tiendas distintas ni aplicar descuentos con cantidades pendientes de autorización.
Probar totales, reparto, estimación y cierre; fijar tratamiento del redondeo.

### 2. Autorización de B aplicada a A

La migración guarda producto y cadena, y `_es_la_confirmada` comprueba ambos.
El fallo está en su consumidor: `_resolver` compara la confirmación contra el
diccionario `alternativa`, pero devuelve/cobra el producto de `hallado`. No
exige que ese producto devuelto sea el que el usuario aceptó.

Comprobación ejecutada: referencia con GTIN `4056489574392`; candidato A a
200 céntimos con GTIN distinto `8412345678905`; alternativa B a 100 céntimos;
usuario confirma `dia:B` en DIA. Resultado real:

```
confirmado=dia:B; elegido=dia:A; autorizada=True; coste=200
```

Esto vulnera la regla aunque la confirmación se haya persistido correctamente.
Si hay exacto A y se acepta alternativa B, tampoco debe decirse que se aplicó
la alternativa mientras se sigue devolviendo A: definir el estado de elección
y reflejarlo tanto en la respuesta como en la pantalla.

Corrección requerida: resolver una elección efectiva explícita. Una sustitución
autorizada puede contar únicamente cuando el producto/cadena efectivamente
devuelto y cobrado coincide con lo aceptado. Si B desaparece, cambia de identidad
o no resulta elegible, declarar confirmación pendiente; no sustituir por A.
Probar caso con A y B diferentes, lectura posterior de la lista, revocación y
cambio de catálogo, además del caso sencillo A=B ya cubierto.

### 3. Referencias exactas distintas dentro del mismo grupo

Hallazgo de lectura, no medición ejecutada: `_candidatos` guarda
`pedido[grupo] = producto_id`. Dos líneas del mismo grupo que soliciten artículos
concretos distintos pueden sobrescribir su referencia; además se suman cantidades
por grupo. Tener un canónico común corrige el defecto entre cadenas, pero no
garantiza identidad por línea en ese escenario.

Separar clave de petición/identidad solicitada de clave de agrupación de compra.
Preservar ambas elecciones exactas. Solo sumar para promociones después de
conocer el producto efectivo y la tienda. Añadir una prueba con dos artículos
incompatibles del mismo grupo antiguo y probar independencia del orden de las líneas.
Si el producto solicitado no aparece entre filas con precio, no usar el canónico
como sustituto de su identidad: leer su ficha o abstenerse.

## Plataforma servida y siguientes pasos

En esta inspección `localhost:8080` rechazó la conexión y Docker Compose no pudo
conectar al motor Linux (pipe inexistente). No se puede confirmar que terminó
el trabajo de publicación/reconstrucción citado en el informe. Es una limitación
del contraste actual, no una demostración de que el nuevo código esté roto.

Orden de continuación: pruebas rojas de los dos casos ejecutados y el tercero
de referencia por línea → corregir elección efectiva y agrupación de costes →
repetir ensayo desechable y restauración con los contratos nuevos → comprobar
publicación e imagen servida cuando el motor esté disponible → gráficas y
recorridos de las tres aplicaciones. Conservar el trabajo de aislamiento,
migraciones y puentes, revisando su integración con los cambios de costes.

No cerrar identidad y coste con pruebas de selección o de persistencia aisladas:
la condición exige que lo confirmado, lo mostrado y lo cobrado sean el mismo
producto y que dividir líneas no altere el coste de una misma compra elegible.
