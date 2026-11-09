interface Props {
  page: number
  pages: number
  total: number
  pageSize: number
  onPage: (page: number) => void
}

export function Pagination({ page, pages, total, pageSize, onPage }: Props) {
  if (total === 0) return null
  const first = (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, total)
  return (
    <nav className="pagination" aria-label="Pagination">
      <p className="pagination-info" aria-live="polite">
        Showing {first}-{last} of {total}
      </p>
      <div className="pagination-controls">
        <button type="button" className="btn btn-small" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Previous
        </button>
        <span className="pagination-page">
          Page {page} of {pages}
        </span>
        <button type="button" className="btn btn-small" disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Next
        </button>
      </div>
    </nav>
  )
}
