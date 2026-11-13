import { FileCode2, FileText } from 'lucide-react'

function FileItem({ file, isSelected, onSelect }) {
  const isCodeFile = file.language !== 'Other'

  return (
    <button
      type="button"
      className={`file-item ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(file)}
      title={file.relative_path}
    >
      <span className="file-item-icon">
        {isCodeFile ? (
          <FileCode2 size={17} />
        ) : (
          <FileText size={17} />
        )}
      </span>

      <span className="file-item-details">
        <span className="file-item-name">{file.filename}</span>
        <span className="file-item-language">{file.language}</span>
      </span>

      <span className="file-item-size">
        {file.size_bytes < 1024
          ? `${file.size_bytes} B`
          : `${(file.size_bytes / 1024).toFixed(1)} KB`}
      </span>
    </button>
  )
}

export default FileItem
