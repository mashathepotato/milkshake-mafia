import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

// Per-mesh bbox + per-node transform from the blender GLB. Tells us:
//  - where the Cap pivots in world space
//  - bowl interior dimensions (for liquid + collider)
//  - whether the cap has its origin at a hinge (for animation) or its center

const __dirname = dirname(fileURLToPath(import.meta.url))
const path = join(__dirname, '..', 'public', 'models', 'blender.glb')
const buf = readFileSync(path)
const jsonChunkLength = buf.readUInt32LE(12)
const gltf = JSON.parse(buf.subarray(20, 20 + jsonChunkLength).toString('utf8'))

function meshBox(meshIdx) {
  const mesh = gltf.meshes[meshIdx]
  let min = [Infinity, Infinity, Infinity]
  let max = [-Infinity, -Infinity, -Infinity]
  for (const prim of mesh.primitives) {
    const idx = prim.attributes.POSITION
    const acc = gltf.accessors[idx]
    if (!acc?.min || !acc?.max) continue
    for (let i = 0; i < 3; i++) {
      if (acc.min[i] < min[i]) min[i] = acc.min[i]
      if (acc.max[i] > max[i]) max[i] = acc.max[i]
    }
  }
  return { min, max, size: [max[0] - min[0], max[1] - min[1], max[2] - min[2]] }
}

for (const [i, n] of gltf.nodes.entries()) {
  console.log(`\n[node ${i}] ${n.name}`)
  console.log('  translation:', n.translation ?? [0, 0, 0])
  console.log('  rotation   :', n.rotation ?? [0, 0, 0, 1])
  console.log('  scale      :', n.scale ?? [1, 1, 1])
  if (n.mesh != null) {
    const box = meshBox(n.mesh)
    console.log(`  mesh bbox  : min=${box.min.map(v=>v.toFixed(2))} max=${box.max.map(v=>v.toFixed(2))} size=${box.size.map(v=>v.toFixed(2))}`)
  }
}
