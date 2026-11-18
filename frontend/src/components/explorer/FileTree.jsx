import { useMemo, useState } from 'react'
import { ChevronsDownUp, ChevronsUpDown, FolderOpen } from 'lucide-react'

import FileTreeNode from './FileTreeNode'
import {
  buildFileTree,
  countFolders,
  folderPathsFor,
} from '../../utils/buildFileTree'

// Very large repositories start collapsed so the explorer stays fast.
const LARGE_TREE_FILE_LIMIT = 400

function collectFolderPaths(nodes, paths = []) {
  nodes.forEach((node) => {
    if (node.type !== 'folder') return

    paths.push(node.path)
    collectFolderPaths(node.children, paths)
  })

  return paths
}

function FileTree({ files, selectedFile, onSelectFile }) {
  const tree = useMemo(() => buildFileTree(files || []), [files])
  const folderCount = useMemo(() => countFolders(tree), [tree])

  // Folders are expanded by default, so only collapsed paths are stored.
  // The stored paths belong to one tree: a new search starts fresh.
  const [collapseState, setCollapseState] = useState(() => ({
    tree: null,
    paths: new Set(),
  }))

  const defaultCollapsed = useMemo(
    () =>
      (files?.length || 0) > LARGE_TREE_FILE_LIMIT
        ? new Set(collectFolderPaths(tree))
        : new Set(),
    [tree, files]
  )

  const storedCollapsed =
    collapseState.tree === tree
      ? collapseState.paths
      : defaultCollapsed

  const collapsed = useMemo(() => {
    const paths = new Set(storedCollapsed)

    // Always reveal the selected file, even inside a collapsed folder.
    if (selectedFile?.relative_path) {
      folderPathsFor(selectedFile.relative_path).forEach((path) =>
        paths.delete(path)
      )
    }

    return paths
  }, [storedCollapsed, selectedFile])

  const hasCollapsed = storedCollapsed.size > 0

  const handleToggleFolder = (path) => {
    const next = new Set(storedCollapsed)

    if (next.has(path)) {
      next.delete(path)
    } else {
      next.add(path)
    }

    setCollapseState({ tree, paths: next })
  }

  const handleCollapseAll = () => {
    setCollapseState({
      tree,
      paths: new Set(collectFolderPaths(tree)),
    })
  }

  const handleExpandAll = () => {
    setCollapseState({ tree, paths: new Set() })
  }

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
          <FolderOpen size={17} />
          <span>Project Files</span>
        </div>

        <div className="file-tree-header-actions">
          <span className="file-tree-count">
            {files.length} files · {folderCount} folders
          </span>

          <button
            type="button"
            className="file-tree-toggle"
            onClick={hasCollapsed ? handleExpandAll : handleCollapseAll}
            title={
              hasCollapsed
                ? 'Expand every folder'
                : 'Collapse every folder'
            }
          >
            {hasCollapsed ? (
              <ChevronsUpDown size={14} />
            ) : (
              <ChevronsDownUp size={14} />
            )}
            {hasCollapsed ? 'Expand all' : 'Collapse all'}
          </button>
        </div>
      </div>

      <div className="file-tree-list">
        {tree.map((node) => (
          <FileTreeNode
            key={node.path}
            node={node}
            depth={0}
            collapsed={collapsed}
            onToggleFolder={handleToggleFolder}
            selectedFile={selectedFile}
            onSelectFile={onSelectFile}
          />
        ))}
      </div>
    </div>
  )
}

export default FileTree
