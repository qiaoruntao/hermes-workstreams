// Write THIRD_PARTY_LICENSES.md for every npm package bundled into desktop/plugin.js.
import { build } from 'esbuild'
import { readFileSync, readdirSync, writeFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'

const { metafile } = await build({ entryPoints: ['src/panel.js'], bundle: true, write: false, metafile: true, format: 'esm',
  external: ['@hermes/plugin-sdk', 'react', 'react/jsx-runtime', 'react-dom'], logLevel: 'silent' })
const pkgs = new Set()
for (const input of Object.keys(metafile.inputs)) {
  const m = /node_modules\/((?:@[^/]+\/)?[^/]+)\//.exec(input)
  if (m) pkgs.add(m[1])
}
let out = '# Third-party licenses\n\nPackages bundled into `desktop/plugin.js`.\n'
for (const name of [...pkgs].sort()) {
  const dir = join('node_modules', name)
  const pkg = JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8'))
  const file = readdirSync(dir).find((f) => /^(licen[cs]e|copying)(\.|$)/i.test(f))
  out += `\n## ${name}@${pkg.version} — ${pkg.license}\n\n`
  out += file && existsSync(join(dir, file)) ? '```\n' + readFileSync(join(dir, file), 'utf8').trim() + '\n```\n' : '(no license file shipped; see package.json)\n'
}
writeFileSync('THIRD_PARTY_LICENSES.md', out)
console.log(`THIRD_PARTY_LICENSES.md: ${pkgs.size} packages`)
