import { FileCode2 } from 'lucide-react'

function SourceReference({ source }) {
  const lineLabel =
    source.start_line === source.end_line
      ? `Line ${source.start_line}`
      : `Lines ${source.start_line}–${source.end_line}`

  return (
    <div className="source-reference">
      <FileCode2 size={15} />

      <div>
        <strong>{source.file_path}</strong>

        <span>
          {lineLabel}
          {source.name ? ` · ${source.name}` : ''}
          {source.chunk_type ? ` · ${source.chunk_type}` : ''}
        </span>
      </div>
    </div>
  )
}

export default SourceReference
