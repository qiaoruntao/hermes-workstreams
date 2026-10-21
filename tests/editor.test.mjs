import { test } from 'node:test'
import assert from 'node:assert/strict'
import { Window } from 'happy-dom'

const window = new Window()
for (const key of ['window', 'document', 'navigator', 'Node', 'HTMLElement', 'Element', 'DOMParser', 'MutationObserver', 'getComputedStyle', 'Text', 'DocumentFragment', 'Range', 'Selection']) {
  try { globalThis[key] = window[key] } catch { Object.defineProperty(globalThis, key, { value: window[key], configurable: true }) }
}

const { createFocusEditor, toMarkdown, normalizeMarkdown, mergeFocus } = await import('../src/focus-editor.js')

function roundTrip(markdown) {
  const element = document.createElement('div')
  document.body.appendChild(element)
  const editor = createFocusEditor({ element, markdown })
  const out = toMarkdown(editor)
  editor.destroy()
  return out
}

const SAMPLES = {
  focus: '# Hermes Workstream Focus plugin\n\n- [ ] Move this chat via sidebar **Move to project**\n- [x] Decide on checks in `backlog.md`\n\nFinding: agent switch does not move gateway chats\n\nRepos: ~/projects/hermes-workstreams\n',
  nested: '# T\n\n- [ ] parent\n  - [ ] child\n',
  bullets: '# T\n\n- plain bullet\n- another\n',
}

for (const [name, sample] of Object.entries(SAMPLES)) {
  test(`round-trips ${name} unchanged`, () => assert.equal(roundTrip(sample), sample))
}

test('tables survive a round trip (cells, rows, header)', () => {
  const out = roundTrip('# T\n\n| a | b |\n| --- | --- |\n| c | d |\n')
  assert.match(out, /\| a\s*\| b\s*\|\n\|\s*-+\s*\|\s*-+\s*\|\n\| c\s*\| d\s*\|/)
  assert.equal(normalizeMarkdown(out), out, 'normalized form is stable')
})

test('normalize is idempotent for agent-style files', () => {
  const once = normalizeMarkdown('# T\n- [ ] a\n- [ ] b\nNext: x\nRepos: ~/y\n')
  assert.equal(normalizeMarkdown(once), once)
  assert.match(once, /Repos: ~\/y/)
})

test('merge keeps both sides when they touch different lines', () => {
  const base = normalizeMarkdown('# T\n\n- [ ] a\n- [ ] b\n\nRepos: x\n')
  const local = base.replace('- [ ] a', '- [x] a')
  const disk = base.replace('Repos: x', 'Repos: x, y')
  const { text, conflict } = mergeFocus(local, base, disk)
  assert.equal(conflict, false)
  assert.match(text, /- \[x\] a/)
  assert.match(text, /Repos: x, y/)
})

test('merge reports conflicts and takes disk', () => {
  const base = '# T\n\n- [ ] a\n'
  const { text, conflict } = mergeFocus('# T\n\n- [ ] mine\n', base, '# T\n\n- [ ] theirs\n')
  assert.equal(conflict, true)
  assert.equal(text, '# T\n\n- [ ] theirs\n')
})

test('merge fast paths', () => {
  assert.deepEqual(mergeFocus('a\n', 'a\n', 'b\n'), { text: 'b\n', conflict: false })
  assert.deepEqual(mergeFocus('b\n', 'a\n', 'a\n'), { text: 'b\n', conflict: false })
})

test('links round-trip (local path, relative, url)', () => {
  const sample = '# T\n\nRepos: [~/projects/x](/Users/me/projects/x)\n\nSee [backlog](./backlog.md) and [docs](https://example.com/a).\n'
  assert.equal(roundTrip(sample), sample)
})

test('links render as anchors', () => {
  const element = document.createElement('div')
  document.body.appendChild(element)
  const editor = createFocusEditor({ element, markdown: 'Repos: [x](/Users/me/x)\n' })
  const a = element.querySelector('a')
  assert.equal(a?.getAttribute('href'), '/Users/me/x')
  assert.equal(a?.textContent, 'x')
  editor.destroy()
})
