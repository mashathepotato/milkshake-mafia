import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

// GLB has 12-byte header + chunks. First chunk is JSON describing meshes,
// accessors etc. POSITION accessors carry min/max bounds — sum across meshes
// gives the model's overall bounding box without needing a WebGL context.

const __dirname = dirname(fileURLToPath(import.meta.url))
const path = join(__dirname, '..', 'public', 'models', 'blender.glb')
const buf = readFileSync(path)

const header = buf.subarray(0, 12)
const magic = header.subarray(0, 4).toString('ascii')
if (magic !== 'glTF') throw new Error(`Not a GLB: magic=${magic}`)

const jsonChunkLength = buf.readUInt32LE(12)
const jsonChunkType = buf.subarray(16, 20).toString('ascii')
if (jsonChunkType !== 'JSON') throw new Error(`Expected JSON chunk, got ${jsonChunkType}`)
const jsonStr = buf.subarray(20, 20 + jsonChunkLength).toString('utf8')
const gltf = JSON.parse(jsonStr)

let min = [Infinity, Infinity, Infinity]
let max = [-Infinity, -Infinity, -Infinity]
let positionAccessors = 0

for (const mesh of gltf.meshes ?? []) {
  for (const prim of mesh.primitives) {
    const idx = prim.attributes.POSITION
    if (idx == null) continue
    const acc = gltf.accessors[idx]
    if (!acc?.min || !acc?.max) continue
    positionAccessors++
    for (let i = 0; i < 3; i++) {
      if (acc.min[i] < min[i]) min[i] = acc.min[i]
      if (acc.max[i] > max[i]) max[i] = acc.max[i]
    }
  }
}

const size = [max[0] - min[0], max[1] - min[1], max[2] - min[2]]
const center = [(max[0] + min[0]) / 2, (max[1] + min[1]) / 2, (max[2] + min[2]) / 2]

console.log(JSON.stringify({
  positionAccessors,
  meshCount: gltf.meshes?.length ?? 0,
  nodeCount: gltf.nodes?.length ?? 0,
  min, max, size, center,
}, null, 2))
