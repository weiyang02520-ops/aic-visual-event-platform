import pytest

from visual_event_ai.embeddings import EmbeddingError, cosine_similarity, gray_embedding, match_embeddings, normalize_vector
from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.models import RegisteredObjectCreate
from visual_event_ai.storage import SQLiteStore


def test_gray_embedding_is_fixed_and_normalized():
    vector = gray_embedding([[0, 0, 255, 255], [0, 0, 255, 255]])
    assert len(vector) == 32
    assert cosine_similarity(vector, vector) == pytest.approx(1.0)


def test_match_embeddings_sorts_and_marks_threshold():
    matches = match_embeddings(
        [1.0, 0.0],
        [
            ("a", "药盒", "object", [1.0, 0.0]),
            ("b", "人员", "person", [0.0, 1.0]),
            ("bad", "坏数据", "object", [1.0]),
        ],
        threshold=0.8,
    )
    assert [match.registry_id for match in matches] == ["a", "b"]
    assert matches[0].accepted is True
    assert matches[1].accepted is False


def test_normalize_vector_rejects_zero_and_wrong_dimension():
    with pytest.raises(EmbeddingError):
        normalize_vector([0, 0])
    with pytest.raises(EmbeddingError):
        normalize_vector([1, 0], expected_dim=3)
    with pytest.raises(EmbeddingError):
        normalize_vector(["not-a-number"])


@pytest.mark.parametrize("values", [[True, False], [1, "0"], "10"])
def test_normalize_vector_rejects_boolean_and_coercible_string_inputs(values):
    with pytest.raises(EmbeddingError):
        normalize_vector(values)


def test_normalize_vector_handles_large_finite_values_without_overflow():
    vector = normalize_vector([1e308, 1e308])
    assert vector == pytest.approx([2 ** -0.5, 2 ** -0.5])


def test_gray_embedding_rejects_ragged_and_non_finite_matrices():
    with pytest.raises(EmbeddingError, match="equal width"):
        gray_embedding([[0, 1], [2]])
    with pytest.raises(EmbeddingError, match="finite numbers"):
        gray_embedding([[0, float("nan")]])


@pytest.mark.parametrize("matrix", [[[True]], [[-0.01]], [[255.01]], [["1"]], [[float("inf")]]])
def test_gray_embedding_rejects_boolean_out_of_range_and_coercible_pixels(matrix):
    with pytest.raises(EmbeddingError):
        gray_embedding(matrix)


def test_gray_embedding_accepts_tiny_matrix_with_stable_shape():
    vector = gray_embedding([[127]], grid_size=4, bins=16)
    assert len(vector) == 32
    assert sum(value * value for value in vector) == pytest.approx(1.0)


def test_gray_embedding_preserves_fractional_intensity():
    lower = gray_embedding([[100.1]], grid_size=1, bins=16)
    higher = gray_embedding([[100.9]], grid_size=1, bins=16)
    assert lower[0] != pytest.approx(higher[0])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_size": 0},
        {"grid_size": 1.5},
        {"grid_size": True},
        {"bins": 1},
        {"bins": True},
    ],
)
def test_gray_embedding_rejects_invalid_configuration(kwargs):
    with pytest.raises(EmbeddingError):
        gray_embedding([[0]], **kwargs)


@pytest.mark.parametrize("threshold", [True, False, "0.8", float("nan"), float("inf"), -0.1, 1.1])
def test_match_embeddings_rejects_invalid_threshold_types_and_ranges(threshold):
    with pytest.raises(EmbeddingError):
        match_embeddings([1, 0], [("id", "item", "object", [1, 0])], threshold=threshold)


def test_local_fixture_fact_includes_registry_match(tmp_path):
    fixture = tmp_path / "objects.jsonl"
    fixture.write_text(
        '{"payload":{"objects":[{"label":"药盒","confidence":0.9,"bbox":[1,1,4,4],"embedding":[1,0]}]}}\n',
        encoding="utf-8",
    )
    store = SQLiteStore(tmp_path / "registry.db")
    store.save_object(RegisteredObjectCreate(name="药盒", embedding=[1, 0]))
    facts = FrameFactExtractor(registry_provider=store.registry_embeddings).extract(str(fixture))
    assert facts[0].metadata["registry_matches"][0]["label"] == "药盒"
    assert facts[0].metadata["registry_matches"][0]["accepted"] is True
