import type { CountItem } from '../api/types'

interface Props {
  title: string
  items: CountItem[]
  /** CSS class suffix per key for coloring, e.g. status-OPEN */
  toneClass?: (key: string) => string
}

/** Horizontal bars drawn with div widths. The numbers are shown as text, so color is never the only cue. */
export function BarList({ title, items, toneClass }: Props) {
  const max = Math.max(1, ...items.map((i) => i.count))
  return (
    <section className="panel" aria-label={title}>
      <h2 className="panel-title">{title}</h2>
      {items.length === 0 ? (
        <p className="muted">No data.</p>
      ) : (
        <ul className="bars">
          {items.map((item) => (
            <li key={item.key} className="bar-row">
              <span className="bar-label">{item.label}</span>
              <span className="bar-track" aria-hidden="true">
                <span
                  className={`bar-fill ${toneClass ? toneClass(item.key) : ''}`}
                  style={{ width: `${(item.count / max) * 100}%` }}
                />
              </span>
              <span className="bar-count">{item.count}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
