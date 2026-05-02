import { readFileSync, readdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const dir = join(__dirname, '..', 'public', 'models', 'ingredients')

function inspect(buf) {
  const jsonChunkLength = buf.readUInt32LE(12)
  const jsonStr = buf.subarray(20, 20 + jsonChunkLength).toString('utf8')
  const gltf = JSON.parse(jsonStr)
  let min = [Infinity, Infinity, Infinity]
  let max = [-Infinity, -Infinity, -Infinity]
  for (const mesh of gltf.meshes ?? []) {
    for (const prim of mesh.primitives) {
      const idx = prim.attributes.POSITION
      if (idx == null) continue
      const acc = gltf.accessors[idx]
      if (!acc?.min || !acc?.max) continue
      for (let i = 0; i < 3; i++) {
        if (acc.min[i] < min[i]) min[i] = acc.min[i]
        if (acc.max[i] > max[i]) max[i] = acc.max[i]
      }
    }
  }
  const size = [max[0] - min[0], max[1] - min[1], max[2] - min[2]]
  const center = [(max[0] + min[0]) / 2, (max[1] + min[1]) / 2, (max[2] + min[2]) / 2]
  return { min, max, size, center }
}

const files = readdirSync(dir).filter((f) => f.endsWith('.glb'))
const out = {}
for (const f of files) {
  const buf = readFileSync(join(dir, f))
  out[f.replace('.glb', '')] = inspect(buf)
}
console.log(JSON.stringify(out, null, 2))
