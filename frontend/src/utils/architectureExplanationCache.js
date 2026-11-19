// AI architecture explanations are expensive to generate and are not
// stored in PostgreSQL, so keep them for the current browser session.
// Memory survives route changes; sessionStorage also survives reloads.

const STORAGE_PREFIX = 'codeatlas:architecture-explanation:'

const memoryCache = new Map()

function storageKey(projectId) {
  return `${STORAGE_PREFIX}${projectId}`
}

export function getCachedExplanation(projectId) {
  const key = String(projectId)

  if (memoryCache.has(key)) {
    return memoryCache.get(key)
  }

  try {
    const stored = window.sessionStorage.getItem(storageKey(key))

    if (stored) {
      memoryCache.set(key, stored)
      return stored
    }
  } catch {
    // Storage can be unavailable in private modes; memory still works.
  }

  return null
}

export function setCachedExplanation(projectId, explanation) {
  const key = String(projectId)

  if (!explanation) {
    memoryCache.delete(key)

    try {
      window.sessionStorage.removeItem(storageKey(key))
    } catch {
      // Ignore storage failures.
    }

    return
  }

  memoryCache.set(key, explanation)

  try {
    window.sessionStorage.setItem(storageKey(key), explanation)
  } catch {
    // Ignore quota or privacy-mode failures; memory still works.
  }
}
