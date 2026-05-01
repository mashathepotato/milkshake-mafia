import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

// Walk the GLB's node tree to identify named parts. Lid / blade / jar / base
// often appear as separate nodes in stylized blender models — we need that to
// know whether we can animate them independently.

const __dirname = dirname(fileURLToPath(import.meta.url))
const path = join(__dirname, '..', 'public', 'models', 'blender.glb')
const buf = readFileSync(path)
const jsonChunkLength = buf.readUInt32LE(12)
const gltf = JSON.parse(buf.subarray(20, 20 + jsonChunkLength).toString('utf8'))

console.log('Top-level scenes:', gltf.scenes?.length, 'nodes:', gltf.nodes?.length, 'meshes:', gltf.meshes?.length)
console.log('\nNode tree:')
function walk(idx, depth = 0) {
  const n = gltf.nodes[idx]
  const meshName = n.mesh != null ? gltf.meshes[n.mesh]?.name ?? `mesh#${n.mesh}` : null
  console.log('  '.repeat(depth) + `${n.name || `<unnamed#${idx}>`}` + (meshName ? `  [mesh: ${meshName}]` : ''))
  if (n.children) for (const c of n.children) walk(c, depth + 1)
}
const sceneNodes = gltf.scenes[0].nodes
for (const i of sceneNodes) walk(i)

console.log('\nMesh names:')
for (const [i, m] of (gltf.meshes ?? []).entries()) {
  console.log(`  #${i}: ${m.name || '<unnamed>'}  (${m.primitives.length} prim)`)
}
