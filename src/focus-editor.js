// Shared TipTap setup for the Workstream panel (bundled into desktop/plugin.js).
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import { TableKit } from '@tiptap/extension-table'
import { Markdown } from '@tiptap/markdown'
import { merge } from 'node-diff3'

export function focusExtensions() {
  return [
    StarterKit.configure({
      underline: false,
      // Links open via the panel's click handler (local paths need the backend), never by navigation.
      link: { openOnClick: false, autolink: true, linkOnPaste: true, enableClickSelection: false,
        HTMLAttributes: { target: null, rel: null },
        // Accept local paths (/Users/…, ~/…, ./notes.md) as well as URLs.
        isAllowedUri: (url, { defaultValidate }) => /^(\/|~\/|\.{1,2}\/)/.test(url) || defaultValidate(url) },
    }),
    TaskList,
    TaskItem.configure({ nested: true }),
    TableKit.configure({ table: { resizable: false } }),
    Markdown.configure({ markedOptions: { gfm: true } }),
  ]
}

export function createFocusEditor({ element, markdown, onUpdate, onBlur, onTransaction }) {
  return new Editor({
    element,
    extensions: focusExtensions(),
    content: markdown,
    contentType: 'markdown',
    onUpdate: ({ editor }) => onUpdate?.(editor),
    onBlur: ({ editor }) => onBlur?.(editor),
    onTransaction: ({ editor }) => onTransaction?.(editor),
  })
}

export function toMarkdown(editor) {
  // Paths like ~/projects come back as \~/projects; FOCUS.md never uses ~ for strikethrough.
  const text = editor.getMarkdown().replace(/\u00a0/g, ' ').replace(/\\~/g, '~').replace(/\n{3,}/g, '\n\n').trimEnd()
  return text + '\n'
}

let headless = null
/** Markdown as the editor would write it, so disk text and editor text diff line-for-line. */
export function normalizeMarkdown(markdown) {
  headless ??= new Editor({ extensions: focusExtensions(), content: '' })
  headless.commands.setContent(markdown, { emitUpdate: false, contentType: 'markdown' })
  return toMarkdown(headless)
}

/** 3-way line merge of normalized texts: { text, conflict }. On conflict the disk side wins. */
export function mergeFocus(local, base, disk) {
  if (local === base) return { text: disk, conflict: false }
  if (disk === base || disk === local) return { text: local, conflict: false }
  const lines = (s) => s.replace(/\n$/, '').split('\n')
  const result = merge(lines(local), lines(base), lines(disk), { stringSeparator: '\n' })
  return result.conflict ? { text: disk, conflict: true } : { text: result.result.join('\n') + '\n', conflict: false }
}
