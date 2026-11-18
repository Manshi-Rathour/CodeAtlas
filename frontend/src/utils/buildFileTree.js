// Build a nested folder tree from the flat project file list.
//
// Files are returned by the API ordered by relative path, but grouping
// them here keeps the real directory structure visible in the explorer.

const isFolder = (node) => node.type === 'folder'

function sortChildren(node) {
  if (!node.children) return

  node.children.sort((a, b) => {
    if (a.type !== b.type) return isFolder(a) ? -1 : 1

    return a.name.localeCompare(b.name, undefined, {
      numeric: true,
      sensitivity: 'base',
    })
  })

  node.children.forEach(sortChildren)
}

export function buildFileTree(files = []) {
  const root = { type: 'folder', name: '', path: '', children: [] }
  const folders = new Map([['', root]])

  files.forEach((file) => {
    const relativePath = file.relative_path || file.filename || ''
    const segments = relativePath.split('/').filter(Boolean)

    if (segments.length === 0) return

    let parent = root

    segments.forEach((segment, index) => {
      const isFile = index === segments.length - 1
      const path = segments.slice(0, index + 1).join('/')

      if (isFile) {
        parent.children.push({
          type: 'file',
          name: segment,
          path,
          file,
        })
        return
      }

      let folder = folders.get(path)

      if (!folder) {
        folder = { type: 'folder', name: segment, path, children: [] }
        folders.set(path, folder)
        parent.children.push(folder)
      }

      parent = folder
    })
  })

  sortChildren(root)

  return root.children
}

export function countFolders(nodes = []) {
  return nodes.reduce(
    (total, node) =>
      total +
      (node.type === 'folder' ? 1 + countFolders(node.children) : 0),
    0
  )
}

// Return the folder paths that contain the given file path.
export function folderPathsFor(filePath = '') {
  const segments = filePath.split('/').filter(Boolean)
  const paths = []

  for (let index = 1; index < segments.length; index += 1) {
    paths.push(segments.slice(0, index).join('/'))
  }

  return paths
}

export default buildFileTree
