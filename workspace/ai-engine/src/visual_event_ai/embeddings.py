"""Small, explainable CPU embeddings for registered objects/persons.

This module intentionally does not claim face recognition or a learned model.
It turns a grayscale frame matrix (or a caller-provided numeric vector) into a
stable normalized vector and uses cosine similarity for registry lookup. A
later verified model can replace the feature extractor without changing the
registry match contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum, hypot, isfinite
from numbers import Integral, Real
from typing import Iterable, Mapping, Sequence


class EmbeddingError(ValueError):
    """Raised when a feature vector or grayscale matrix is malformed."""


def normalize_vector(values: Iterable[float], *, expected_dim: int | None = None) -> list[float]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise EmbeddingError("embedding values must be a numeric sequence")
    try:
        raw_values = list(values)
    except (TypeError, ValueError, OverflowError) as exc:
        raise EmbeddingError("embedding values must be a numeric sequence") from exc
    if not raw_values:
        raise EmbeddingError("embedding vector must not be empty")
    if expected_dim is not None and (
        isinstance(expected_dim, bool)
        or not isinstance(expected_dim, Integral)
        or expected_dim < 1
    ):
        raise EmbeddingError("expected_dim must be a positive integer")
    if expected_dim is not None and len(raw_values) != expected_dim:
        raise EmbeddingError(f"embedding dimension mismatch: expected {expected_dim}, got {len(raw_values)}")
    vector: list[float] = []
    for value in raw_values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise EmbeddingError("embedding values must be numeric non-Boolean values")
        try:
            numeric = float(value)
        except (ValueError, OverflowError) as exc:
            raise EmbeddingError("embedding values must be finite numbers") from exc
        if not isfinite(numeric):
            raise EmbeddingError("embedding vector must contain finite values")
        vector.append(numeric)
    norm = hypot(*vector)
    if norm == 0:
        raise EmbeddingError("embedding vector must not be all zeros")
    return [value / norm for value in vector]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    try:
        normalized_left = normalize_vector(left)
        normalized_right = normalize_vector(right)
    except EmbeddingError:
        return 0.0
    similarity = fsum(a * b for a, b in zip(normalized_left, normalized_right))
    return max(-1.0, min(1.0, similarity))


def gray_embedding(matrix: Sequence[Sequence[int | float]], *, grid_size: int = 4, bins: int = 16) -> list[float]:
    """Build a fixed-size feature vector from a grayscale matrix.

    The vector contains one mean intensity per grid cell and a coarse
    intensity histogram. It is deliberately a baseline for registry matching,
    not a semantic detector; callers must label results as heuristic.
    """

    if isinstance(matrix, (str, bytes, bytearray)) or not isinstance(matrix, Sequence) or not matrix or not all(
        isinstance(row, Sequence) and not isinstance(row, (str, bytes)) and len(row) > 0
        for row in matrix
    ):
        raise EmbeddingError("gray matrix must be non-empty")
    width = len(matrix[0])
    height = len(matrix)
    if any(len(row) != width for row in matrix):
        raise EmbeddingError("gray matrix rows must have equal width")
    if (
        isinstance(grid_size, bool)
        or not isinstance(grid_size, Integral)
        or isinstance(bins, bool)
        or not isinstance(bins, Integral)
        or grid_size < 1
        or bins < 2
    ):
        raise EmbeddingError("invalid gray matrix or feature configuration")
    grid_size = int(grid_size)
    bins = int(bins)
    pixels: list[list[float]] = []
    for row in matrix:
        pixel_row: list[float] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, Real):
                raise EmbeddingError("gray matrix values must be numeric non-Boolean values")
            try:
                intensity = float(value)
            except (ValueError, OverflowError) as exc:
                raise EmbeddingError("gray matrix values must be finite numbers") from exc
            if not isfinite(intensity) or not 0.0 <= intensity <= 255.0:
                raise EmbeddingError("gray matrix values must be finite numbers in [0, 255]")
            pixel_row.append(intensity)
        pixels.append(pixel_row)
    features: list[float] = []
    for gy in range(grid_size):
        y0 = gy * height // grid_size
        y1 = max(y0 + 1, (gy + 1) * height // grid_size)
        for gx in range(grid_size):
            x0 = gx * width // grid_size
            x1 = max(x0 + 1, (gx + 1) * width // grid_size)
            cell = [pixels[y][x] for y in range(y0, min(y1, height)) for x in range(x0, min(x1, width))]
            features.append(sum(cell) / (255.0 * len(cell)))
    histogram = [0.0] * bins
    for row in pixels:
        for value in row:
            histogram[min(bins - 1, int(value / 256.0 * bins))] += 1.0
    total = float(width * height)
    features.extend(value / total for value in histogram)
    return normalize_vector(features)


@dataclass(frozen=True)
class RegistryMatch:
    registry_id: str
    label: str
    kind: str
    similarity: float
    accepted: bool


def match_embeddings(
    query: Sequence[float],
    candidates: Iterable[tuple[str, str, str, Sequence[float]]],
    *,
    threshold: float = 0.8,
) -> list[RegistryMatch]:
    if isinstance(threshold, bool) or not isinstance(threshold, Real):
        raise EmbeddingError("threshold must be a finite real number between 0 and 1")
    try:
        threshold = float(threshold)
    except (ValueError, OverflowError) as exc:
        raise EmbeddingError("threshold must be a finite real number between 0 and 1") from exc
    if not isfinite(threshold) or not 0.0 <= threshold <= 1.0:
        raise EmbeddingError("threshold must be a finite real number between 0 and 1")
    normalized_query = normalize_vector(query)
    matches: list[RegistryMatch] = []
    for registry_id, label, kind, candidate in candidates:
        try:
            normalized_candidate = normalize_vector(candidate, expected_dim=len(normalized_query))
        except (EmbeddingError, TypeError, ValueError):
            continue
        similarity = cosine_similarity(normalized_query, normalized_candidate)
        matches.append(RegistryMatch(registry_id, label, kind, similarity, similarity >= threshold))
    return sorted(matches, key=lambda item: item.similarity, reverse=True)
