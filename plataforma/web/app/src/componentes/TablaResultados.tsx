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
import { useMemo, useState } from 'react'
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
import { SelloComparable, SelloDudoso, SelloOferta, SelloRetirada, SelloNutriscore } from './Etiquetas'
import { Etiqueta, TablaScroll, Td, Th } from './ui'

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
                <span className="block text-xs text-tinta-suave">
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
            <span className="block text-xs text-tinta-suave">
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
            <span className="cifra font-semibold text-emerald-800 dark:text-emerald-400">
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

  return (
    <TablaScroll etiqueta="Resultados de la búsqueda" minAncho="52rem">
      <table className="w-full border-collapse text-sm">
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
              className="relative hover:bg-neutral-50 dark:hover:bg-neutral-800/60"
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

/** La celda del producto: foto, nombre, sellos y el enlace que ocupa la fila.
 *
 *  El enlace se estira con `after:inset-0` para que se pueda pulsar en cualquier
 *  parte de la fila sin anidar enlaces ni meter un `onClick` en el `<tr>`, que
 *  no funciona con el teclado.
 */
function Producto({ fila }: { fila: ResultadoBusqueda }) {
  return (
    <div className="flex min-w-[16rem] items-start gap-3">
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
          className="h-12 w-12 shrink-0 rounded border border-neutral-200 bg-white object-contain dark:border-neutral-700"
        />
      ) : (
        <span
          aria-hidden="true"
          className="h-12 w-12 shrink-0 rounded border border-dashed border-neutral-300 dark:border-neutral-600"
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
          />
          <SelloRetirada retirado={fila.con_retirada} />
          <SelloDudoso dudoso={fila.dudoso} />
        </div>
      </div>
    </div>
  )
}
