import math


def dot(a, b) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


def l2_norm(a) -> float:
    return math.sqrt(dot(a, a))


def l2_normalize(a, *, eps: float = 1e-12):
    n = l2_norm(a)
    if n < eps:
        return list(a)
    return [x / n for x in a]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def scale(a, s: float):
    return [x * s for x in a]


def mean(vectors):
    if not vectors:
        raise ValueError("mean() requires at least one vector")
    d = len(vectors[0])
    acc = [0.0] * d
    for v in vectors:
        for i, x in enumerate(v):
            acc[i] += float(x)
    inv = 1.0 / float(len(vectors))
    return [x * inv for x in acc]


def mat_vec_mul(mat, vec):
    return [dot(row, vec) for row in mat]


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def clamp01(x: float) -> float:
    return clamp(float(x), 0.0, 1.0)

