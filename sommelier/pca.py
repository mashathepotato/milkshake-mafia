import math
import random
from dataclasses import dataclass

from .linalg import dot, l2_normalize, mat_vec_mul, mean, scale, sub


@dataclass(frozen=True)
class PCAFit:
    mean: list
    components: list  # list[list[float]]; each unit-length in feature space
    eigenvalues: list  # list[float]


def _gram_matrix(centered_rows):
    n = len(centered_rows)
    g = [[0.0] * n for _ in range(n)]
    for i in range(n):
        g[i][i] = dot(centered_rows[i], centered_rows[i])
        for j in range(i + 1, n):
            v = dot(centered_rows[i], centered_rows[j])
            g[i][j] = v
            g[j][i] = v
    return g


def _power_iteration_topk_symmetric(mat, k: int, *, max_iter: int = 2000, tol: float = 1e-10):
    """
    Returns k approximate eigenpairs of a symmetric matrix using power iteration
    with Gram-Schmidt orthogonalization (no external deps).
    """
    n = len(mat)
    if n == 0:
        return [], []

    eigenvecs = []
    eigenvals = []

    for comp in range(int(k)):
        rng = random.Random(1337 + comp)
        b = [rng.uniform(-1.0, 1.0) for _ in range(n)]
        b = l2_normalize(b)

        for _ in range(max_iter):
            b_next = mat_vec_mul(mat, b)

            # Orthogonalize against previously found eigenvectors.
            for q in eigenvecs:
                proj = dot(q, b_next)
                if proj != 0.0:
                    b_next = [x - proj * y for x, y in zip(b_next, q)]

            b_next = l2_normalize(b_next)

            diff = math.sqrt(sum((x - y) * (x - y) for x, y in zip(b_next, b)))
            b = b_next
            if diff < tol:
                break

        ab = mat_vec_mul(mat, b)
        lam = dot(b, ab)
        if lam <= 1e-14:
            break
        eigenvecs.append(b)
        eigenvals.append(float(lam))

    return eigenvecs, eigenvals


def fit_pca(vectors, *, n_components: int = 3) -> PCAFit:
    if not vectors:
        raise ValueError("fit_pca() requires at least one vector")

    d = len(vectors[0])
    for v in vectors:
        if len(v) != d:
            raise ValueError("All vectors must share the same dimensionality")

    mu = mean(vectors)
    centered = [sub(v, mu) for v in vectors]
    g = _gram_matrix(centered)
    u_list, lam_list = _power_iteration_topk_symmetric(g, int(n_components))

    # Lift eigenvectors back into feature space: pc = X^T u / sqrt(lambda)
    pcs = []
    for u, lam in zip(u_list, lam_list):
        inv_sqrt = 1.0 / math.sqrt(lam)
        pc = [0.0] * d
        for row_weight, row in zip(u, centered):
            w = float(row_weight) * inv_sqrt
            if w == 0.0:
                continue
            for i, x in enumerate(row):
                pc[i] += w * float(x)
        pc = l2_normalize(pc)
        pcs.append(pc)

    return PCAFit(mean=mu, components=pcs, eigenvalues=lam_list)


def project(pca: PCAFit, vector) -> list:
    x = sub(vector, pca.mean)
    return [dot(x, pc) for pc in pca.components]


def max_abs_sign_fix(pc: list) -> list:
    if not pc:
        return pc
    idx = max(range(len(pc)), key=lambda i: abs(pc[i]))
    if pc[idx] < 0:
        return scale(pc, -1.0)
    return pc

