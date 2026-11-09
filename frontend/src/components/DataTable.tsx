import type { ReactNode } from 'react'

export interface Column<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  className?: string
}

interface Props<T> {
  caption: string
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string | number
  rowClass?: (row: T) => string | undefined
}

/** Scrolls sideways on mid-size screens and turns into stacked cards on phones. */
export function DataTable<T>({ caption, columns, rows, rowKey, rowClass }: Props<T>) {
  return (
    <div className="table-scroll" role="region" aria-label={caption} tabIndex={0}>
      <table className="table">
        <caption className="visually-hidden">{caption}</caption>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col" className={c.className}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} className={rowClass?.(row)}>
              {columns.map((c) => (
                <td key={c.key} data-label={c.header} className={c.className}>
                  {c.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
