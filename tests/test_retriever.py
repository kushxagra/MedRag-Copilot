from app.services.retriever import Retriever


def test_retrieve_returns_most_relevant_chunk_first(tmp_path):
    retriever = Retriever(db_path=str(tmp_path), collection_name="test_chunks")

    retriever.index(
        ids=["1", "2", "3"],
        texts=[
            "Metformin is the first-line medication for type 2 diabetes.",
            "Aspirin is commonly used to reduce fever and mild pain.",
            "Regular exercise improves cardiovascular health.",
        ],
        metadatas=[
            {
                "doc_id": "1",
                "title": "Diabetes treatment",
                "source": "test",
                "url": "https://example.com/1",
            },
            {
                "doc_id": "2",
                "title": "Pain relief",
                "source": "test",
                "url": "https://example.com/2",
            },
            {
                "doc_id": "3",
                "title": "Exercise benefits",
                "source": "test",
                "url": "https://example.com/3",
            },
        ],
    )

    results = retriever.retrieve("What medication treats type 2 diabetes?", k=1)

    assert len(results) == 1
    assert results[0].chunk_id == "1"
