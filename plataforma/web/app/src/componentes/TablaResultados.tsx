/** La tabla de resultados, con TanStack Table.
 *
 *  TanStack Table no pinta nada: solo lleva el estado de ordenacion y las
 *  columnas. El HTML lo escribo yo, que es lo que permite que la tabla sea una
 *  `<table>` de verdad (con `scope="col"`, `aria-sort` y navegable con el
 *  teclado) en vez de cuarenta `<div>` con pinta de tabla.
 *
 *  El orden que se puede pulsar se aplica **a los resultados que ya han
 *  llegado**, no a los 51.781 del catálogo. Por eso la pantalla lo dice: un
 *  "más barato" que solo mira 40 filas es una respuesta distinta de la que
 *  parece.
 */
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingFn,
  type SortingState,
} from '@tanstack/react-table'

import { euros, eurosUnidad, porcentaje } from '../api/formato'
import type { ResultadoBusqueda } from '../tipos'
import {
  SelloAhorro,
  SelloComparable,
  SelloDudoso,
  SelloNutriscore,
  SelloEcoscore,
  SelloOferta,
  SelloRetirada,
} from './Etiquetas'
import { Etiqueta, Resumen, TablaScroll, Td, Th } from './ui'

/** Si la pantalla es de móvil. **La tabla de resultados no cabe en 390 px.**
 *
 *  Son seis columnas y 52rem de ancho mínimo, así que en un móvil hay que deslizar en
 *  horizontal, y lo que quedaba fuera era justo el precio. Medido en la captura de
 *  `/buscar?q=leche entera` del 27 de septiembre de 2026, a 390 x 844: se veían «Producto» y
 *  «Cadena», y el PVP y el €/L **no**. El aviso «Desliza la tabla para ver todas las
 *  columnas →» es una instrucción, no una respuesta: quien viene a saber si lo que tiene en la
 *  mano está caro no lo averigua deslizando una tabla en un pasillo.
 *
 *  Por debajo de 640 px se pintan **filas de dos líneas**: nombre, cadena y sellos a la
 *  izquierda, el precio y el precio por unidad a la derecha, sin deslizar nada. La tabla sigue
 *  siendo lo bueno en pantalla ancha, que es donde se comparan columnas de verdad.
 */
function usePantallaEstrecha() {
  const [estrecha, setEstrecha] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(max-width: 639px)').matches,
  )
  useEffect(() => {
    const m = window.matchMedia('(max-width: 639px)')
    const oye = (e: MediaQueryListEvent) => setEstrecha(e.matches)
    m.addEventListener('change', oye)
    return () => m.removeEventListener('change', oye)
  }, [])
  return estrecha
}

/** Los que no tienen dato, al final. Un `null` que se cuela en el comparador
 *  acaba colocando arriba justo lo que no se sabe, que es lo peor que puede
 *  hacer una tabla ordenada por precio. */
const porNumero: SortingFn<ResultadoBusqueda> = (a, b, id) => {
  const va = a.getValue<number | null>(id)
  const vb = b.getValue<number | null>(id)
  const sinA = va === null || va === undefined || !Number.isFinite(va)
  const sinB = vb === null || vb === undefined || !Number.isFinite(vb)
  if (sinA && sinB) return 0
  if (sinA) return 1
  if (sinB) return -1
  return (va as number) - (vb as number)
}

export function TablaResultados({ filas }: { filas: ResultadoBusqueda[] }) {
  const [orden, setOrden] = useState<SortingState>([
    // Por defecto, lo que pide el backend: primero los comparables entre
    // cadenas y, dentro, el más barato. Cambiarlo por defecto seria quitarle
    // al orden del servidor la unica decision que sabe tomar mejor que yo.
    { id: 'orden_servidor', desc: false },
  ])

  const columnas = useMemo<ColumnDef<ResultadoBusqueda>[]>(
    () => [
      {
        id: 'orden_servidor',
        header: 'Producto',
        enableSorting: false,
        cell: ({ row }) => <Producto fila={row.original} />,
      },
      {
        id: 'cadena',
        header: 'Cadena',
        // La cadena más barata del grupo. No es "donde cómpralo": eso necesita
        // mirar la lista entera.
        accessorFn: (f) => f.cadena_mas_barata ?? '',
        cell: ({ getValue }) => (
          <span className="font-medium">{getValue<string>() || 'no lo sé'}</span>
        ),
      },
      {
        id: 'marca',
        header: 'Marca',
        // La marca del miembro más barato, que es el que la fila enseña. La API
        // no la mandaba y esta columna no existía: sacarla del nombre sería
        // adivinarla, y en un catálogo donde media tienda es marca propia,
        // adivinarla mal se nota mucho.
        accessorFn: (f) => f.marca ?? '',
        cell: ({ getValue }) => (
          <span className="text-tinta-suave">{getValue<string>() || '—'}</span>
        ),
      },
      {
        id: 'precio',
        header: 'Precio',
        accessorFn: (f) => f.precio_cent,
        sortingFn: porNumero,
        cell: ({ row }) => (
          <span className="cifra font-semibold">{euros(row.original.precio_cent)}</span>
        ),
      },
      {
        id: 'unidad',
        header: 'Por unidad',
        accessorFn: (f) => f.precio_unidad_cent,
        sortingFn: porNumero,
        cell: ({ row }) => {
          const { precio_unidad_cent, precio_unidad_max_cent, unidad } = row.original
          const texto = eurosUnidad(precio_unidad_cent, unidad)
          // Si en el grupo hay precios por unidad distintos, se enseña el
          // abanico. Enseñar solo el mínimo hace creer que todo el grupo está
          // a ese precio.
          const hayAbanico =
            precio_unidad_cent !== null &&
            precio_unidad_max_cent !== null &&
            precio_unidad_max_cent > precio_unidad_cent
          return (
            <span className="cifra">
              {texto}
              {hayAbanico && (
                <span className="block text-etiqueta text-tinta-suave">
                  hasta {eurosUnidad(precio_unidad_max_cent, unidad)}
                </span>
              )}
            </span>
          )
        },
      },
      {
        id: 'cadenas',
        header: 'Dónde',
        accessorFn: (f) => f.cadenas,
        sortingFn: porNumero,
        cell: ({ row }) => (
          <span className="cifra">
            {row.original.cadenas} {row.original.cadenas === 1 ? 'cadena' : 'cadenas'}
            <span className="block text-etiqueta text-tinta-suave">
              {row.original.productos} {row.original.productos === 1 ? 'producto' : 'productos'}
            </span>
          </span>
        ),
      },
      {
        id: 'ahorro',
        header: 'Ahorro',
        accessorFn: (f) => (f.comparable && !f.dudoso ? f.ahorro_pct : null),
        sortingFn: porNumero,
        cell: ({ row }) => {
          const f = row.original
          // `ahorro_pct: 0.0` es el centinela de "no comparable" o "dudoso", no
          // un cero de verdad. Pintarlo como 0 % diría "aquí no ahorras nada".
          if (!f.comparable || f.dudoso) {
            return (
              <Etiqueta
                tono="dato"
                titulo="Sin comparación fiable no hay ahorro que dar"
              >
                no lo sé
              </Etiqueta>
            )
          }
          return (
            <span className="cifra font-semibold text-bien ">
              {porcentaje(f.ahorro_pct)}
            </span>
          )
        },
      },
    ],
    [],
  )

  const tabla = useReactTable({
    data: filas,
    columns: columnas,
    state: { sorting: orden },
    onSortingChange: setOrden,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  const estrecha = usePantallaEstrecha()

  if (estrecha) {
    return (
      <div>
        <BarraDeOrden orden={orden} onOrden={setOrden} />
        {/* La cabecera de las dos columnas de precio, que es lo que en la tabla hacen los
            `th`: sin ella, «0,95 €» y «0,95 €/L» son dos números sin nombre. */}
        <div className="grid grid-cols-[1fr_auto_auto] gap-x-3 border-b border-borde px-1 pb-1 text-etiqueta uppercase tracking-wide text-tinta-suave ">
          <span>Producto</span>
          <span className="text-right">PVP</span>
          <span className="text-right">Por unidad</span>
        </div>
        <ul
          aria-label="Resultados de la búsqueda"
          className="divide-y divide-borde "
        >
          {tabla.getRowModel().rows.map((fila) => (
            <FilaCompacta
              key={`${fila.original.grupo_id ?? 'suelto'}-${fila.original.nombre}-${fila.index}`}
              fila={fila.original}
            />
          ))}
        </ul>
      </div>
    )
  }

  return (
    <TablaScroll etiqueta="Resultados de la búsqueda" minAncho="52rem">
      <table className="w-full border-collapse text-cuerpo">
        <thead>
          <tr>
            {tabla.getHeaderGroups()[0]?.headers.map((h) => (
              <Th
                key={h.id}
                ordenable={h.column.getCanSort()}
                activo={h.column.getIsSorted() !== false}
                direccion={h.column.getIsSorted()}
                onClick={h.column.getToggleSortingHandler()}              >
                {flexRender(h.column.columnDef.header, h.getContext())}
              </Th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tabla.getRowModel().rows.map((fila) => (
            <tr
              key={`${fila.original.grupo_id ?? 'suelto'}-${fila.original.nombre}-${fila.index}`}
              className="relative hover:bg-marfil"
            >
              {fila.getVisibleCells().map((celda) => (
                <Td key={celda.id}>{flexRender(celda.column.columnDef.cell, celda.getContext())}</Td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </TablaScroll>
  )
}

/** El orden, en el móvil: la tabla ordena por sus cabeceras, y aquí no hay cabeceras.
 *
 *  Los mismos cuatro órdenes que la tabla, con las mismas palabras que su `header`, y el
 *  sentido en la propia etiqueta («Precio ▾»). Pulsar el que ya está puesto le da la vuelta,
 *  que es lo que hace cualquier cabecera de tabla.
 *
 *  **Y va plegado.** Abierto son cinco botones de 44 px -- dos filas, 110 px -- por encima de
 *  los resultados, y el orden no es lo que se viene a mirar: lo que se viene a mirar es el
 *  precio, y en un móvil cada 110 px de controles son una fila de resultados menos en la
 *  primera pantalla. El `summary` dice el orden que hay puesto, así que plegado **también
 *  informa**; abierto, se cambia.
 */
function BarraDeOrden({ orden, onOrden }: {
  orden: SortingState
  onOrden: (o: SortingState) => void
}) {
  const cual = orden[0]?.id ?? 'orden_servidor'
  const arriba = orden[0]?.desc === false
  const botones: [string, string][] = [
    ['orden_servidor', 'Lo de siempre'],
    ['precio', 'Precio'],
    ['unidad', 'Precio por unidad'],
    ['ahorro', 'Ahorro'],
    ['cadenas', 'Dónde'],
  ]
  const puesto = botones.find(([id]) => id === cual)?.[1] ?? 'Lo de siempre'
  return (
    <details className="mb-2">
      <Resumen className="text-etiqueta uppercase tracking-wide text-tinta-suave">
        Ordenar por
        <span className="font-semibold normal-case tracking-normal text-tinta">
          {puesto}
          {/* El sentido, **con palabras y no con una flecha**: la flecha de esta linea es la del
              desplegable (`Resumen`), y dos triangulos juntos se leen como uno solo mal puesto.
              «De mayor a menor» no se puede confundir con nada. */}
          {cual !== 'orden_servidor' && (arriba ? ' (de menor a mayor)' : ' (de mayor a menor)')}
        </span>
      </Resumen>
      <div className="flex flex-wrap items-center gap-2 pb-1">
        {botones.map(([id, texto]) => {
          const esElPuesto = cual === id
          return (
            <button
              key={id}
              type="button"
              aria-pressed={esElPuesto}
              onClick={() => {
                // **Pulsar el que ya esta puesto le da la vuelta, y no lo hacia.** Estaba
                // escrito `desc: !arriba` con `arriba = orden[0]?.desc === false`, que con el
                // orden puesto sale `desc: !true = false`: o sea **volvia a poner el mismo
                // sentido**, y el boton parecia no hacer nada. Lo midio la puerta de las
                // funciones el 28 de septiembre de 2026, comparando el primer resultado de un
                // orden con el ultimo del otro. Ahora se le da la vuelta al `desc` que hay.
                return esElPuesto && id !== 'orden_servidor'
                  ? onOrden([{ id, desc: !(orden[0]?.desc ?? true) }])
                  : onOrden([{ id, desc: false }])
              }}
              className={
                esElPuesto
                  ? 'min-h-[44px] rounded-campo border border-terracota bg-terracota px-3 text-cuerpo font-medium text-white '
                  : 'min-h-[44px] rounded-campo border border-borde bg-papel px-3 text-cuerpo '
              }
            >
              {texto}
              {esElPuesto && id !== 'orden_servidor' && (
                <span aria-hidden="true">{arriba ? ' ▴' : ' ▾'}</span>
              )}
            </button>
          )
        })}
      </div>
    </details>
  )
}

/** Una fila del móvil: dos líneas, y el precio siempre visible.
 *
 *  El enlace se estira por toda la fila con `after:inset-0`, igual que en la tabla: se puede
 *  pulsar en cualquier parte sin anidar enlaces.
 */
function FilaCompacta({ fila }: { fila: ResultadoBusqueda }) {
  const hayAbanico =
    fila.precio_unidad_cent !== null &&
    fila.precio_unidad_max_cent !== null &&
    fila.precio_unidad_max_cent > fila.precio_unidad_cent
  return (
    <li className="relative hover:bg-marfil">
      <div className="grid grid-cols-[1fr_auto_auto] items-start gap-x-3 py-2">
        <div className="flex min-w-0 items-start gap-2">
          {fila.imagen ? (
            <img
              src={fila.imagen}
              alt=""
              loading="lazy"
              width={40}
              height={40}
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
              className="h-10 w-10 shrink-0 rounded border border-borde bg-papel object-contain "
            />
          ) : (
            <span
              aria-hidden="true"
              className="h-10 w-10 shrink-0 rounded border border-dashed border-borde "
            />
          )}
          <div className="min-w-0">
            <p className="text-cuerpo font-medium leading-snug">
              {fila.grupo_id === null ? (
                fila.nombre
              ) : (
                <Link to={`/grupo/${fila.grupo_id}`} className="after:absolute after:inset-0">
                  {fila.nombre}
                </Link>
              )}
            </p>
            <p className="text-etiqueta text-tinta-suave">
              {fila.cadena_mas_barata ?? 'no lo sé'}
              {fila.marca && fila.marca !== fila.cadena_mas_barata ? ` · ${fila.marca}` : ''}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-1">
              <SelloAhorro pct={fila.ahorro_pct} comparable={fila.comparable} dudoso={fila.dudoso} />
              <SelloOferta
                texto={fila.con_oferta ? 'Hay promoción que baja lo que pagas hoy en caja' : null}
                club={fila.con_oferta_club}
                unidades={fila.oferta_unidades ?? null}
              />
              <SelloRetirada retirado={fila.con_retirada} />
              <SelloDudoso dudoso={fila.dudoso} />
              <SelloComparable cadenas={fila.cadenas} />
              <SelloNutriscore valor={fila.nutriscore} />
              <SelloEcoscore valor={fila.ecoscore} />
            </div>
          </div>
        </div>
        <span className="cifra text-cuerpo font-semibold">{euros(fila.precio_cent)}</span>
        <span className="cifra text-right text-cuerpo">
          {eurosUnidad(fila.precio_unidad_cent, fila.unidad)}
          {hayAbanico && (
            <span className="block text-etiqueta text-tinta-suave">
              hasta {eurosUnidad(fila.precio_unidad_max_cent, fila.unidad)}
            </span>
          )}
        </span>
      </div>
    </li>
  )
}

/** La celda del producto: foto, nombre, sellos y el enlace que ocupa la fila.
 *
 *  El enlace se estira con `after:inset-0` para que se pueda pulsar en cualquier
 *  parte de la fila sin anidar enlaces ni meter un `onClick` en el `<tr>`, que
 *  no funciona con el teclado.
 */
function Producto({ fila }: { fila: ResultadoBusqueda }) {
  return (
    <div className="flex min-w-0 items-start gap-3">
      {fila.imagen ? (
        <img
          src={fila.imagen}
          alt=""
          loading="lazy"
          width={48}
          height={48}
          // Una imagen que no carga no puede dejar un icono roto en medio de la
          // lista: se esconde y queda el nombre, que es el dato.
          onError={(e) => {
            e.currentTarget.style.display = 'none'
          }}
          className="h-12 w-12 shrink-0 rounded border border-borde bg-papel object-contain "
        />
      ) : (
        <span
          aria-hidden="true"
          className="h-12 w-12 shrink-0 rounded border border-dashed border-borde "
        />
      )}
      <div className="min-w-0">
        <p className="font-medium leading-snug">
          {fila.grupo_id === null ? (
            fila.nombre
          ) : (
            <Link to={`/grupo/${fila.grupo_id}`} className="after:absolute after:inset-0">
              {fila.nombre}
            </Link>
          )}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-1">
          <SelloNutriscore valor={fila.nutriscore} />
          <SelloComparable cadenas={fila.cadenas} />
          <SelloOferta
            texto={fila.con_oferta ? 'Hay promoción que baja lo que pagas hoy en caja' : null}
            club={fila.con_oferta_club}
            unidades={fila.oferta_unidades ?? null}
          />
          <SelloRetirada retirado={fila.con_retirada} />
          <SelloDudoso dudoso={fila.dudoso} />
        </div>
      </div>
    </div>
  )
}