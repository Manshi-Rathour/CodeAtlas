import { FolderOpen, Files } from 'lucide-react'
import FileItem from './FileItem'

function FileTree({ files, selectedFile, onSelectFile }) {
  if (!files || files.length === 0) {
    return (
      <div className="file-tree-empty">
        <FolderOpen size={35} />
        <h3>No files found</h3>
        <p>Try changing your search or language filter.</p>
      </div>
    )
  }

  return (
    <div className="file-tree">
      <div className="file-tree-header">
        <div className="file-tree-title">
          <Files size={17} />
          <span>Project Files</span>
        </div>

        <span className="file-tree-count">
          {files.length} files
        </span>
      </div>

      <div className="file-tree-list">
        {files.map((file) => (
          <FileItem
            key={file.id}
            file={file}
            isSelected={selectedFile?.id === file.id}
            onSelect={onSelectFile}
          />
        ))}
      </div>
    </div>
  )
}

export default FileTree
