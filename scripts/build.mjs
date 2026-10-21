// Bundle src/panel.js (+ TipTap) into desktop/plugin.js. The Desktop host supplies
// @hermes/plugin-sdk, react and react/jsx-runtime, so they stay external.
import { build } from 'esbuild'

const result = await build({
  entryPoints: ['src/panel.js'],
  outfile: 'desktop/plugin.js',
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: 'es2022',
  minify: true,
  legalComments: 'eof',
  external: ['@hermes/plugin-sdk', 'react', 'react/jsx-runtime', 'react-dom'],
  define: { 'process.env.NODE_ENV': '"production"' },
  metafile: true,
})
const bytes = Object.values(result.metafile.outputs).reduce((sum, o) => sum + o.bytes, 0)
console.log(`desktop/plugin.js ${(bytes / 1024).toFixed(0)} KB`)
