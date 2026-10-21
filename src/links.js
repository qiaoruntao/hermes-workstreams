// Link classification for FOCUS.md clicks (no SDK imports, so it unit-tests in Node).
// Files opened with their default app. Anything else (no extension, .app, .command, .sh, .pkg, …,
// and folders) is only REVEALED in Finder: opening an executable via LaunchServices would run it,
// and FOCUS.md is agent-written, so a link must never be one click from code execution.
const OPENABLE = new Set(['md', 'markdown', 'txt', 'log', 'csv', 'tsv', 'json', 'yaml', 'yml', 'toml', 'xml',
  'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'heic', 'mp4', 'mov', 'mp3', 'm4a', 'wav',
  'docx', 'xlsx', 'pptx', 'pages', 'numbers', 'key', 'rtf', 'har'])

/** Resolve a FOCUS.md href → { kind: 'url'|'open'|'reveal'|'blocked', target }. Pure; unit-tested. */
export function classifyLink(href, focusPath) {
  const raw = String(href || '').trim()
  if (/^(https?|mailto):/i.test(raw)) return { kind: 'url', target: raw }
  if (/^[a-z][a-z0-9+.-]*:/i.test(raw) && !/^file:/i.test(raw)) return { kind: 'blocked', target: raw }
  let path
  try {
    if (/^file:/i.test(raw)) path = decodeURIComponent(new URL(raw).pathname)
    else if (raw.startsWith('/') || raw.startsWith('~/')) path = decodeURIComponent(raw.split('#')[0])
    // Standard Markdown semantics: relative to the file that contains the link (./, ../, %20).
    else path = decodeURIComponent(new URL(raw.split('#')[0], new URL(`file://${focusPath}`)).pathname)
  } catch (_) {
    return { kind: 'blocked', target: raw }
  }
  if (!path || path.includes('\0')) return { kind: 'blocked', target: raw }
  const name = path.replace(/\/+$/, '').split('/').pop() || ''
  const ext = name.includes('.') ? name.split('.').pop().toLowerCase() : ''
  return { kind: ext && OPENABLE.has(ext) && !path.endsWith('/') ? 'open' : 'reveal', target: path }
}
