from rag.filing_rag import chunk_text, embed_chunks
from sentence_transformers import SentenceTransformer

import pytest

@pytest.fixture(scope="module")
def embedding_model():
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def test_chunk_text_produces_multiple_chunks_for_long_text():
    text = "word " * 600  # 3000 chars
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1


def test_chunk_text_each_non_final_chunk_is_chunk_size():
    text = "x" * 2000
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    for chunk in chunks[:-1]:
        assert len(chunk) == 500


def test_chunk_text_short_text_returns_single_chunk():
    text = "this is a short text"
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_last_chunk_ends_at_text_boundary():
    text = "abcde" * 200  # 1000 chars
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert text.endswith(chunks[-1])


def test_chunk_text_adjacent_chunks_share_overlap():
    text = "x" * 2000
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    # The end of chunk[i] should match the start of chunk[i+1]
    assert chunks[0][-50:] == chunks[1][:50]


def test_embed_chunks_returns_correct_shape(embedding_model):
    chunks = ["Apple reported strong quarterly earnings.", "The company faces regulatory headwinds."]
    embeddings = embed_chunks(chunks, embedding_model)
    assert embeddings.shape == (2, 384)


def test_embed_chunks_single_input_shape(embedding_model):
    chunks = ["Macroeconomic headwinds weigh on consumer spending."]
    embeddings = embed_chunks(chunks, embedding_model)
    assert embeddings.shape == (1, 384)
