import { test } from 'node:test'
import assert from 'node:assert/strict'
import { classifyLink } from '../src/links.js'

const F = '/Users/q/kb/workstreams/ws/FOCUS.md'
const cases = [
  ['https://example.com/a?b=1', 'url', 'https://example.com/a?b=1'],
  ['mailto:me@example.com', 'url', 'mailto:me@example.com'],
  ['./backlog.md', 'open', '/Users/q/kb/workstreams/ws/backlog.md'],
  ['notes/a%20b.md', 'open', '/Users/q/kb/workstreams/ws/notes/a b.md'],
  ['../other/FOCUS.md', 'open', '/Users/q/kb/workstreams/other/FOCUS.md'],
  ['/Users/q/report.pdf', 'open', '/Users/q/report.pdf'],
  ['file:///Users/q/x.json', 'open', '/Users/q/x.json'],
  ['/Users/q/projects/repo', 'reveal', '/Users/q/projects/repo'],
  ['~/projects/repo/', 'reveal', '~/projects/repo/'],
  ['/Applications/Calculator.app', 'reveal', '/Applications/Calculator.app'],
  ['./run.command', 'reveal', '/Users/q/kb/workstreams/ws/run.command'],
  ['./install.sh', 'reveal', '/Users/q/kb/workstreams/ws/install.sh'],
  ['/tmp/x.pkg', 'reveal', '/tmp/x.pkg'],
  ['/usr/bin/python3', 'reveal', '/usr/bin/python3'],
  ['./evil.md.command', 'reveal', '/Users/q/kb/workstreams/ws/evil.md.command'],
  ['javascript:alert(1)', 'blocked', 'javascript:alert(1)'],
  ['vscode://file/x', 'blocked', 'vscode://file/x'],
  ['x-apple.systempreferences:com.apple.preference', 'blocked', 'x-apple.systempreferences:com.apple.preference'],
  ['ssh://host', 'blocked', 'ssh://host'],
]
for (const [href, kind, target] of cases) {
  test(`${href} → ${kind}`, () => assert.deepEqual(classifyLink(href, F), { kind, target }))
}
