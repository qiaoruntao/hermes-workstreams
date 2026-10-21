# Hermes Workstreams

Keep track of work that spans several Hermes sessions — debugging one issue, shipping one feature —
with a short, always-visible **FOCUS.md** beside the chat.

- **One workstream = one Hermes Project** whose only folder is a docs directory
  (`<workstreams_root>/<slug>/`). Put any notes, logs or backlogs there; the plugin only relies on
  `FOCUS.md`.
- **Side panel** (Hermes Desktop): shows the focused chat's workstream — project icon, name, and
  `FOCUS.md` in a rich editor (headings, todos, lists, tables, links). Edits are written to disk
  within a second, and changes made on disk (by you or the agent) appear live; concurrent edits
  are merged line by line.
- **Agent context**: when a chat belongs to a workstream, its `FOCUS.md` is added to the agent's
  context — once, and again whenever it changes. Unlinked chats get a one-line hint listing
  existing workstreams.
- **Agent linking**: the `workstream_link` tool creates a workstream (folder, starter `FOCUS.md`,
  Project) or picks an existing one; right after that turn, Desktop moves the chat into the
  project — the same operation as the sidebar's **Move to project**. No clicks needed.
- **Bundled skill** `hermes-workstreams:workstream-focus` tells the agent when to link and how to
  keep `FOCUS.md` short (≈12 lines / 100 words — the panel flags overruns).

## Install

Requires Hermes with Desktop (tested on 0.21.x) and Node.js ≥ 20 for building.

```bash
git clone https://github.com/qiaoruntao/hermes-workstreams ~/.hermes/plugins/hermes-workstreams
cd ~/.hermes/plugins/hermes-workstreams
npm ci && npm run build        # bundles desktop/plugin.js (a prebuilt copy is committed)
hermes plugins enable hermes-workstreams
hermes config set plugins.entries.hermes-workstreams.settings.workstreams_root '~/hermes-workstreams'
```

Then in Hermes Desktop: **Capabilities → Plugins → Hermes Workstreams → turn on Desktop**, and
restart the gateway (`hermes gateway restart`) so the tool and hook load.

## Use

Just describe the issue in a new chat ("this will take a few sessions…"). The agent links the
chat to a new or existing workstream; the **Workstream** pane shows its `FOCUS.md`. You can also
move a chat yourself with the sidebar's **Move to project**.

Settings (`plugins.entries.hermes-workstreams.settings` in `config.yaml`):

| Key | Default | Meaning |
|---|---|---|
| `workstreams_root` | `~/hermes-workstreams` | Where workstream folders live |
| `max_words` / `max_lines` | `100` / `12` | FOCUS.md budget shown in the panel and to the agent |

## Links in FOCUS.md

Clicking a link uses Desktop's system opener. `http(s)` and `mailto` open in your default apps;
local document and media files (`.md`, `.pdf`, `.png`, …) open with their default app; relative
links resolve against `FOCUS.md`'s folder. Folders, executables, app bundles, scripts and files
without an extension are only **revealed in Finder**, never opened, and other URL schemes are
refused — `FOCUS.md` is agent-written, so a link is never one click away from running code.

## Privacy

Everything stays local: workstream files in `workstreams_root`, pending links in Hermes' plugin
data folder. The plugin makes no network requests.

## Known limits

- The rich editor bundles TipTap/ProseMirror, which `hermes plugins validate` flags as prototype
  patching; it loads fine as a local plugin but would need a sandboxed frame for the catalog.
- Linking moves the chat after the turn ends (Hermes refuses a move mid-turn) and needs Desktop
  running; elsewhere use **Move to project**.
- The first panel edit normalizes Markdown spacing (e.g. blank lines between blocks).

## Development

```bash
npm ci && npm run build && npm test                       # editor, merge, link-safety tests
<hermes>/venv/bin/python -m unittest discover -s tests    # backend tests
hermes plugins validate .
```

Source of the Desktop bundle is `src/`; `desktop/plugin.js` is the built output.

## License

MIT. The Desktop bundle includes MIT-licensed TipTap, ProseMirror, marked, linkifyjs and node-diff3;
see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) (regenerate with `node scripts/licenses.mjs`).
