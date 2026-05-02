import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const path = join(__dirname, '..', 'public', 'models', 'blender.glb')
const buf = readFileSync(path)
const jsonChunkLength = buf.readUInt32LE(12)
const gltf = JSON.parse(buf.subarray(20, 20 + jsonChunkLength).toString('utf8'))

console.log('Per-primitive bboxes (helps identify handle / jar / base / lid):')
for (const [mi, mesh] of (gltf.meshes ?? []).entries()) {
  for (const [pi, prim] of mesh.primitives.entries()) {
    const acc = gltf.accessors[prim.attributes.POSITION]
    if (!acc?.min || !acc?.max) continue
    const min = acc.min
    const max = acc.max
    const size = [max[0] - min[0], max[1] - min[1], max[2] - min[2]]
    const center = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2]
    const matIdx = prim.material
    const mat = matIdx != null ? gltf.materials?.[matIdx]?.name ?? `mat#${matIdx}` : 'no material'
    console.log(`  mesh#${mi} prim#${pi} [${mat}]:`)
    console.log(`    min ${min.map(v=>v.toFixed(1))}  max ${max.map(v=>v.toFixed(1))}`)
    console.log(`    size ${size.map(v=>v.toFixed(1))}  center ${center.map(v=>v.toFixed(1))}`)
  }
}
