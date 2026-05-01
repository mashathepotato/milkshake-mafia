import * as THREE from 'three'
import { shaderMaterial } from '@react-three/drei'
import { extend, type ThreeElement } from '@react-three/fiber'

// Custom liquid surface shader.
// Vertex: vWorldPos for world-space clipping; FBM displacement on the surface.
// Fragment: discards above uFillLevel — gives a clean flat fill line that
// rises during the blend. Without this, animating with mesh.scale.y squishes
// the whole tapered lathe and the wider top pokes through the jar's narrow
// base. Discarding by world-Y keeps the geometry full-size; only what's
// "below the fill line" actually renders.

const vertex = /* glsl */ `
  uniform float uTime;
  uniform float uViscosity;
  uniform float uFreshness;
  varying vec2 vUv;
  varying vec3 vNormal;
  varying vec3 vWorldPos;
  varying float vDisp;

  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p); vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
  }
  float fbm(vec2 p) {
    float v = 0.0; float a = 0.5;
    for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.0; a *= 0.5; }
    return v;
  }

  void main() {
    vUv = uv;
    float speed = mix(2.4, 0.6, uViscosity);
    float amp   = mix(0.04, 0.18, uViscosity);
    float n = fbm(uv * 4.0 + vec2(uTime * speed * 0.15, uTime * speed * 0.1));
    float disp = (n - 0.5) * amp;
    vDisp = disp;
    vec3 displaced = position + normal * disp;
    vec4 worldPos = modelMatrix * vec4(displaced, 1.0);
    vWorldPos = worldPos.xyz;
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`

const fragment = /* glsl */ `
  uniform float uTime;
  uniform vec3 uColor;
  uniform vec3 uAccent;
  uniform float uViscosity;
  uniform float uFreshness;
  uniform float uFillLevel;
  varying vec2 vUv;
  varying vec3 vNormal;
  varying vec3 vWorldPos;
  varying float vDisp;

  void main() {
    // Hard cut at the fill line. Anti-alias band of 1px is tiny enough that
    // we don't bother — the cut reads like a real liquid surface against the
    // jar wall.
    if (vWorldPos.y > uFillLevel) discard;

    vec3 viewDir = normalize(cameraPosition - vWorldPos);
    float fres = pow(1.0 - max(dot(vNormal, viewDir), 0.0), 2.5);

    float radial = length(vUv - 0.5) * 2.0;
    vec3 col = mix(uAccent, uColor, smoothstep(0.0, 0.7, radial));

    float bub = step(0.985, fract(sin(dot(floor(vUv * 80.0), vec2(12.9, 78.2))) * 437.0));
    col += bub * uFreshness * 0.6;
    col += fres * mix(0.05, 0.55, uFreshness);
    col += vDisp * 0.8;

    gl_FragColor = vec4(col, 1.0);
  }
`

export const LiquidMaterial = shaderMaterial(
  {
    uTime: 0,
    uColor: new THREE.Color('#ff5b8a'),
    uAccent: new THREE.Color('#ffd2dd'),
    uViscosity: 0.5,
    uFreshness: 1.0,
    uFillLevel: 0.0,
  },
  vertex,
  fragment,
)

extend({ LiquidMaterial })

declare module '@react-three/fiber' {
  interface ThreeElements {
    liquidMaterial: ThreeElement<typeof LiquidMaterial>
  }
}
