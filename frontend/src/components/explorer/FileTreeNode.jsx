import {
  ChevronDown,
  ChevronRight,
  FileCode2,
  FileJson,
  FileText,
  Folder,
  FolderOpen,
} from 'lucide-react'

const INDENT_PX = 14

function formatSize(sizeBytes) {
  if (sizeBytes < 1024) return `${sizeBytes} B`

  return `${(sizeBytes / 1024).toFixed(1)} KB`
}

function FileIcon({ language }) {
  if (['JSON', 'YAML'].includes(language)) {
    return <FileJson size={15} />
  }

  if (language && language !== 'Other') {
    return <FileCode2 size={15} />
  }

  return <FileText size={15} />
}

function FileTreeNode({
  node,
  depth,
  collapsed,
  onToggleFolder,
  selectedFile,
  onSelectFile,
}) {
  const paddingLeft = 8 + depth * INDENT_PX

  if (node.type === 'folder') {
    const isCollapsed = collapsed.has(node.path)

    return (
      <div className="file-tree-node">
        <button
          type="button"
          className={`file-tree-folder ${
            isCollapsed ? 'collapsed' : ''
          }`}
          style={{ paddingLeft }}
          onClick={() => onToggleFolder(node.path)}
          title={node.path}
          aria-expanded={!isCollapsed}
        >
          {isCollapsed ? (
            <ChevronRight size={14} className="file-tree-chevron" />
          ) : (
            <ChevronDown size={14} className="file-tree-chevron" />
          )}

          <span className="file-tree-folder-icon">
            {isCollapsed ? (
              <Folder size={15} />
            ) : (
              <FolderOpen size={15} />
            )}
          </span>

          <span className="file-tree-folder-name">{node.name}</span>

          <span className="file-tree-folder-count">
            {node.children.length}
          </span>
        </button>

        {!isCollapsed && (
          <div className="file-tree-children">
            {node.children.map((child) => (
              <FileTreeNode
                key={child.path}
                node={child}
                depth={depth + 1}
                collapsed={collapsed}
                onToggleFolder={onToggleFolder}
                selectedFile={selectedFile}
                onSelectFile={onSelectFile}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  const isSelected = selectedFile?.id === node.file.id

  return (
    <button
      type="button"
      className={`file-tree-file ${isSelected ? 'selected' : ''}`}
      style={{ paddingLeft }}
      onClick={() => onSelectFile(node.file)}
      title={node.file.relative_path}
    >
      <span className="file-tree-file-icon">
        <FileIcon language={node.file.language} />
      </span>

      <span className="file-tree-file-details">
        <span className="file-tree-file-name">{node.name}</span>
        <span className="file-tree-file-language">
          {node.file.language}
        </span>
      </span>

      <span className="file-tree-file-size">
        {formatSize(node.file.size_bytes)}
      </span>
    </button>
  )
}

export default FileTreeNode
