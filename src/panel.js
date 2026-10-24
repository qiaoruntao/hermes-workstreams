// Workstream side panel: the focused session's FOCUS.md in a TipTap editor, kept in sync with disk.
// Source for desktop/plugin.js (built by scripts/build.mjs; react and the SDK stay external).
import { Codicon, host, useQuery, useQueryClient, useValue } from '@hermes/plugin-sdk'
import { useEffect, useReducer, useRef } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'
import { createFocusEditor, mergeFocus, normalizeMarkdown, toMarkdown } from './focus-editor.js'
import { classifyLink } from './links.js'

const muted = 'text-[var(--ui-text-secondary)]'
const SAVE_IDLE_MS = 300 // save this long after the last keystroke…
const SAVE_MAX_MS = 1000 // …but never later than this after the first unsaved change
const POLL_MS = 2000
const STYLE = `
.ws-focus .ProseMirror{outline:none;font-size:13px;line-height:1.5;min-height:3em;padding:2px 0}
.ws-focus .ProseMirror>*:first-child{margin-top:0}
.ws-focus .ProseMirror h1,.ws-focus .ProseMirror h2,.ws-focus .ProseMirror h3{font-weight:600;margin:.5em 0 .2em;line-height:1.3}
.ws-focus .ProseMirror h1{font-size:15px}.ws-focus .ProseMirror h2{font-size:14px}.ws-focus .ProseMirror h3{font-size:13px}
.ws-focus .ProseMirror p{margin:.2em 0}
.ws-focus .ProseMirror ul,.ws-focus .ProseMirror ol{padding-left:1.3em;margin:.2em 0}
.ws-focus .ProseMirror ul{list-style:disc}.ws-focus .ProseMirror ol{list-style:decimal}
.ws-focus .ProseMirror ul[data-type=taskList]{list-style:none;padding-left:0}
.ws-focus .ProseMirror ul[data-type=taskList] ul[data-type=taskList]{padding-left:1.2em}
.ws-focus .ProseMirror ul[data-type=taskList]>li{display:flex;align-items:flex-start;gap:.45em;margin:.1em 0}
.ws-focus .ProseMirror ul[data-type=taskList]>li>label{flex:none;display:flex;align-items:center;height:1.5em;user-select:none}
.ws-focus .ProseMirror ul[data-type=taskList]>li>div{flex:1;min-width:0}
.ws-focus .ProseMirror ul[data-type=taskList]>li>div>p{margin:0}
.ws-focus .ProseMirror ul[data-type=taskList]>li[data-checked=true]>div{text-decoration:line-through;color:var(--ui-text-secondary)}
.ws-focus .ProseMirror input[type=checkbox]{accent-color:var(--ui-accent);cursor:pointer;margin:0;width:13px;height:13px}
.ws-focus .ProseMirror code{font-size:12px;padding:0 .25em;border-radius:3px;background:var(--ui-fill-secondary)}
.ws-focus .ProseMirror a{color:var(--ui-accent);text-decoration:underline;text-underline-offset:2px;cursor:pointer}
.ws-focus .ProseMirror pre{font-size:12px;padding:.4em .6em;border-radius:4px;background:var(--ui-fill-secondary);overflow:auto}
.ws-focus .ProseMirror blockquote{border-left:2px solid var(--ui-stroke-secondary);padding-left:.6em;color:var(--ui-text-secondary)}
.ws-focus .ProseMirror table{border-collapse:collapse;width:100%;margin:.3em 0;table-layout:fixed}
.ws-focus .ProseMirror th,.ws-focus .ProseMirror td{border:1px solid var(--ui-stroke-secondary);padding:2px 5px;vertical-align:top}
.ws-focus .ProseMirror th{font-weight:600;background:var(--ui-fill-secondary)}
.ws-focus .ProseMirror th p,.ws-focus .ProseMirror td p{margin:0}
.ws-focus .ProseMirror .selectedCell{background:var(--ui-fill-secondary)}
.ws-toolbar{display:flex;flex-wrap:wrap;gap:1px;padding:2px 0 4px;margin-bottom:4px;border-bottom:1px solid var(--ui-stroke-secondary)}
.ws-toolbar button{display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:22px;padding:0 4px;border-radius:4px;font-size:11px;font-weight:600;color:var(--ui-text-secondary)}
.ws-toolbar button:hover{background:var(--ui-fill-secondary)}
.ws-toolbar button[data-active=true]{color:var(--ui-accent);background:var(--ui-fill-secondary)}
.ws-toolbar button:disabled{opacity:.35}
.ws-toolbar .sep{width:1px;margin:3px 2px;background:var(--ui-stroke-secondary)}
`

// [label-or-icon, title, isActive(editor), run(chain)]
const TOOLS = [
  [{ text: 'H1' }, 'Heading 1', (e) => e.isActive('heading', { level: 1 }), (c) => c.toggleHeading({ level: 1 })],
  [{ text: 'H2' }, 'Heading 2', (e) => e.isActive('heading', { level: 2 }), (c) => c.toggleHeading({ level: 2 })],
  [{ text: 'H3' }, 'Heading 3', (e) => e.isActive('heading', { level: 3 }), (c) => c.toggleHeading({ level: 3 })],
  null,
  [{ text: 'B' }, 'Bold', (e) => e.isActive('bold'), (c) => c.toggleBold()],
  [{ text: 'I', style: { fontStyle: 'italic' } }, 'Italic', (e) => e.isActive('italic'), (c) => c.toggleItalic()],
  [{ text: 'S', style: { textDecoration: 'line-through' } }, 'Strikethrough', (e) => e.isActive('strike'), (c) => c.toggleStrike()],
  [{ icon: 'code' }, 'Inline code', (e) => e.isActive('code'), (c) => c.toggleCode()],
  [{ icon: 'link' }, 'Link (⌘-click opens)', (e) => e.isActive('link'), (c, e) => {
    const current = e.getAttributes('link').href || ''
    const href = window.prompt('Link target (URL or path, empty to remove)', current)
    if (href === null) return c
    return href.trim() ? c.extendMarkRange('link').setLink({ href: href.trim() }) : c.extendMarkRange('link').unsetLink()
  }],
  null,
  [{ icon: 'tasklist' }, 'Todo list', (e) => e.isActive('taskList'), (c) => c.toggleTaskList()],
  [{ icon: 'list-unordered' }, 'Bullet list', (e) => e.isActive('bulletList'), (c) => c.toggleBulletList()],
  [{ icon: 'list-ordered' }, 'Numbered list', (e) => e.isActive('orderedList'), (c) => c.toggleOrderedList()],
  [{ icon: 'quote' }, 'Quote', (e) => e.isActive('blockquote'), (c) => c.toggleBlockquote()],
  [{ icon: 'table' }, 'Insert table', () => false, (c) => c.insertTable({ rows: 3, cols: 3, withHeaderRow: true })],
  null,
  [{ icon: 'discard' }, 'Undo', () => false, (c) => c.undo(), (e) => e.can().undo()],
  [{ icon: 'redo' }, 'Redo', () => false, (c) => c.redo(), (e) => e.can().redo()],
]
const TABLE_TOOLS = [
  [{ text: '+R' }, 'Add row below', (c) => c.addRowAfter()],
  [{ text: '+C' }, 'Add column right', (c) => c.addColumnAfter()],
  [{ text: '−R' }, 'Delete row', (c) => c.deleteRow()],
  [{ text: '−C' }, 'Delete column', (c) => c.deleteColumn()],
  [{ icon: 'trash' }, 'Delete table', (c) => c.deleteTable()],
]

function ToolButton({ face, title, active, disabled, onRun }) {
  return jsx('button', {
    type: 'button', title, 'data-active': active ? 'true' : 'false', disabled,
    onMouseDown: (event) => { event.preventDefault(); onRun() },
    children: face.icon ? jsx(Codicon, { name: face.icon }) : jsx('span', { style: face.style, children: face.text }),
  })
}

function Toolbar({ editor }) {
  if (!editor) return null
  const run = (fn) => fn(editor.chain().focus(), editor).run()
  const items = TOOLS.map((tool, index) => tool
    ? jsx(ToolButton, { key: index, face: tool[0], title: tool[1], active: tool[2](editor),
        disabled: tool[4] ? !tool[4](editor) : false, onRun: () => run(tool[3]) })
    : jsx('span', { key: index, className: 'sep' }))
  if (editor.isActive('table')) {
    items.push(jsx('span', { key: 'tsep', className: 'sep' }))
    TABLE_TOOLS.forEach((tool, index) => items.push(jsx(ToolButton, {
      key: `t${index}`, face: tool[0], title: tool[1], active: false, onRun: () => run(tool[2]) })))
  }
  return jsx('div', { className: 'ws-toolbar', children: items })
}

/**
 * Sync model: `base` is the last disk text both sides agreed on (normalized). Local edits save after a
 * short pause with base's mtime; the server refuses stale writes (409). Any newer disk text is 3-way
 * merged into the editor (local vs base vs disk); a real conflict keeps disk and says so.
 */
function FocusEditor({ ctx, sessionId, cwd, focus, onSynced }) {
  const mount = useRef(null)
  const [, rerender] = useReducer((n) => n + 1, 0)
  const s = useRef({ editor: null, mtimeNs: focus.mtimeNs, base: '', dirty: false, timer: null, saving: false,
    firstDirtyAt: 0, status: 'saved', error: '' }).current
  const setStatus = (status, error = '') => { s.status = status; s.error = error; rerender() }

  const local = () => toMarkdown(s.editor)
  const apply = (text) => {
    const { from, to } = s.editor.state.selection
    s.editor.commands.setContent(text, { emitUpdate: false, contentType: 'markdown' })
    const max = s.editor.state.doc.content.size
    try { s.editor.commands.setTextSelection({ from: Math.min(from, max), to: Math.min(to, max) }) } catch (_) { /* keep default */ }
  }

  const adoptDisk = (diskContent, mtimeNs) => {
    const disk = normalizeMarkdown(diskContent)
    const mine = local()
    const merged = mergeFocus(mine, s.base, disk)
    if (merged.conflict) host.notify({ kind: 'warning', message: 'FOCUS.md: your edit conflicted with a change on disk — kept the disk version.' })
    if (merged.text !== mine) apply(merged.text)
    s.base = disk
    s.mtimeNs = mtimeNs
    s.dirty = merged.text !== disk
    if (s.dirty) schedule()
  }

  const save = async () => {
    clearTimeout(s.timer)
    if (!s.editor || !s.dirty || s.saving) return
    const content = local()
    s.saving = true
    setStatus('saving')
    try {
      const next = await ctx.rest('/focus/save', { method: 'POST', body: { sessionId, cwd, content, mtimeNs: s.mtimeNs } })
      s.mtimeNs = next.focus.mtimeNs
      s.base = content
      s.dirty = local() !== content
      s.firstDirtyAt = s.dirty ? Date.now() : 0
      onSynced(next)
      setStatus(s.dirty ? 'unsaved' : 'saved')
    } catch (err) {
      const status = err?.statusCode ?? err?.status ?? Number(/^(\d{3}):/.exec(String(err?.message || ''))?.[1])
      if (status === 409) {
        // Stale write: pull disk and merge instead of dropping the edit; the merge re-schedules a save.
        const latest = await ctx.rest('/focus', { method: 'POST', body: { sessionId, cwd } }).catch(() => null)
        if (latest?.focus) { adoptDisk(latest.focus.content, latest.focus.mtimeNs); onSynced(latest) }
        setStatus(s.dirty ? 'unsaved' : 'saved')
      } else {
        // Anything else (backend down, old backend without /focus/save): keep the edit, show it, retry.
        setStatus('error', String(err?.message || err || 'save failed'))
      }
    } finally {
      s.saving = false
      if (s.dirty) schedule(s.status === 'error' ? 3000 : SAVE_IDLE_MS)
    }
  }
  const schedule = (idle = SAVE_IDLE_MS) => {
    if (!s.firstDirtyAt) s.firstDirtyAt = Date.now()
    const wait = Math.max(0, Math.min(idle, s.firstDirtyAt + SAVE_MAX_MS - Date.now()))
    clearTimeout(s.timer)
    s.timer = setTimeout(save, wait)
  }

  useEffect(() => {
    s.base = normalizeMarkdown(focus.content)
    s.editor = createFocusEditor({
      element: mount.current,
      markdown: focus.content,
      onUpdate: () => { s.dirty = true; if (s.status !== 'error') setStatus('unsaved'); schedule() },
      onBlur: () => void save(),
      onTransaction: () => rerender(),
    })
    rerender()
    return () => {
      clearTimeout(s.timer)
      void save().finally(() => s.editor?.destroy())
    }
  }, [])

  useEffect(() => {
    if (!s.editor || s.saving || focus.mtimeNs === s.mtimeNs) return
    adoptDisk(focus.content, focus.mtimeNs)
  }, [focus.mtimeNs, focus.content])

  return jsxs('div', { className: 'ws-focus px-1', children: [
    jsxs('div', { className: 'flex items-start', children: [
      jsx('div', { className: 'min-w-0 flex-1', children: jsx(Toolbar, { editor: s.editor }) }),
      jsx(SaveState, { status: s.status, error: s.error }),
    ] }),
    jsx('div', { ref: mount, onClick: (event) => openLink(ctx, focus.path, event) }),
  ] })
}

/** Click handling: web/mail links → default browser/mail app; safe document types → default app;
 *  everything else → reveal in Finder. All via Desktop's audited system opener (ctx.os). */
function openLink(ctx, focusPath, event) {
  const anchor = event.target?.closest?.('a[href]')
  if (!anchor) return
  event.preventDefault()
  const href = (anchor.getAttribute('href') || '').trim()
  const { kind, target } = classifyLink(href, focusPath)
  const fail = (why) => host.notify({ kind: 'error', message: `Could not open ${href}: ${why}` })
  if (kind === 'blocked') return fail('link type not allowed (only http, https, mailto and local paths)')
  const action = kind === 'reveal' ? ctx.os.revealPath(target) : ctx.os.openExternal(target)
  Promise.resolve(action)
    .then((ok) => {
      if (ok === false) fail('Desktop refused it (missing path or unsupported)')
      else if (kind === 'reveal') host.notify({ kind: 'info', message: `Revealed in Finder (not opened): ${target}` })
    })
    .catch((err) => fail(err?.message || String(err)))
}

const SAVE_STATES = {
  saved: ['check', 'Saved to FOCUS.md', 'var(--ui-text-quaternary)'],
  unsaved: ['circle-filled', 'Unsaved — writing to disk…', 'var(--ui-text-secondary)'],
  saving: ['sync', 'Writing to disk…', 'var(--ui-text-secondary)'],
  error: ['warning', 'Not saved', 'var(--ui-accent)'],
}

function SaveState({ status, error }) {
  const [icon, label, color] = SAVE_STATES[status] || SAVE_STATES.saved
  return jsx('span', {
    className: 'flex h-[26px] flex-none items-center pl-1 text-xs', style: { color },
    title: error ? `${label}: ${error} (retrying)` : label,
    children: jsx(Codicon, { name: icon, spinning: status === 'saving', size: status === 'unsaved' ? '8px' : undefined }),
  })
}

/**
 * Background link worker (plugin-level, not tied to the pane): carries out every pending
 * `workstream_link` request with the same `session.workspace.move` the sidebar's Move to project uses.
 * The session owner refuses a move while that chat's turn runs, so a refusal just retries.
 */
function startLinkWorker(ctx) {
  let running = false
  const failures = new Map()
  const tick = async () => {
    if (running) return
    running = true
    try {
      const { links = [] } = await ctx.rest('/links', { method: 'POST', body: {} })
      for (const link of links) {
        if ((failures.get(link.sessionId) || 0) >= 20) continue
        try {
          await host.request('session.workspace.move', { session_key: link.sessionId, cwd: link.cwd })
          await ctx.rest('/link/ack', { method: 'POST', body: { sessionId: link.sessionId } })
          failures.delete(link.sessionId)
          host.notify({ kind: 'success', message: `Linked chat to workstream ${link.slug}` })
        } catch (err) {
          const busy = /busy/i.test(String(err?.message || err?.data?.reason || ''))
          if (!busy) failures.set(link.sessionId, (failures.get(link.sessionId) || 0) + 1)
        }
      }
    } catch (_) { /* backend not ready; next tick */ }
    finally { running = false }
  }
  ctx.setInterval(tick, 1500)
  ctx.onEvent('message.complete', () => void setTimeout(tick, 300))
}

function WorkstreamPane({ ctx }) {
  const cwd = useValue(host.state.cwd)
  const sessionId = useValue(host.state.focusedStoredSessionId)
  useValue(host.state.busyBySession)
  const queryClient = useQueryClient()
  const queryKey = ['hermes-workstreams', sessionId, cwd]
  const query = useQuery({
    queryKey,
    enabled: Boolean(sessionId || cwd),
    queryFn: () => ctx.rest('/focus', { method: 'POST', body: { sessionId, cwd } }),
    refetchInterval: POLL_MS,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
  })
  const message = (text) => jsx('div', { className: `p-3 text-sm ${muted}`, children: text })
  if (!sessionId && !cwd) return message('No session.')
  if (query.isLoading) return message('Loading…')
  if (query.isError) return jsx('button', { className: 'm-3 text-sm underline', onClick: () => query.refetch(), children: 'Could not load workstream — retry' })
  const data = query.data || {}
  if (!data.workstream) {
    return message(data.pendingLink ? `Linking to ${data.pendingLink.slug} when this turn ends…` : 'This session is not linked to a workstream.')
  }
  const { workstream, focus } = data
  const project = workstream.project || {}
  const onSynced = (next) => queryClient.setQueryData(queryKey, next)

  const header = jsxs('div', {
    className: 'flex items-center gap-1.5 px-1 pb-1 text-sm font-medium',
    children: [
      jsx(Codicon, { name: project.icon || 'target', style: project.color ? { color: project.color } : undefined }),
      jsx('span', { className: 'truncate', children: project.name || workstream.slug }),
      jsxs('span', { className: 'ml-auto flex items-center gap-2', children: [
        focus.overBudget ? jsx('span', {
          className: 'text-xs text-[var(--ui-accent)]',
          title: `${focus.words}/${focus.maxWords} words, ${focus.lines}/${focus.maxLines} lines`,
          children: 'over budget',
        }) : null,
        jsx('button', {
          className: muted, title: 'Reveal workstream folder',
          onClick: () => void ctx.os.revealPath(workstream.path),
          children: jsx(Codicon, { name: 'folder-opened' }),
        }),
      ] }),
    ],
  })
  return jsxs('div', { className: 'h-full overflow-auto p-2', children: [
    jsx('style', { children: STYLE }),
    header,
    focus.exists
      ? jsx(FocusEditor, { key: workstream.path, ctx, sessionId, cwd, focus, onSynced })
      : message('FOCUS.md is missing.'),
  ] })
}

export default {
  id: 'hermes-workstreams',
  name: 'Workstream',
  register(ctx) {
    ctx.register({
      // A tab in the Files zone: Hermes minimizes per zone, so this shares the Files
      // rail. New id (was 'workstream-pane') so saved layouts re-adopt it via `dock`.
      id: 'workstream-panel', area: 'panes', title: 'Workstream',
      data: { placement: 'right', width: '320px', collapsible: true, dock: { pane: 'files', pos: 'center' } },
      render: () => jsx(WorkstreamPane, { ctx }),
    })
    startLinkWorker(ctx)
  },
}
