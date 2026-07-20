"""Placeholder for the future document ingestion pipeline.

There is no real RAG or vector store yet — app/services/retrieval_service.py returns
hardcoded mock sources. This script only validates that data/samples/documents/*.json
is well-formed and shaped like a Source (see backend/app/schemas/explanation.py), so the
ingestion contract is decided before the real pipeline is built.

Usage:
    python scripts/ingest_documents.py
"""

import json
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "data" / "samples" / "documents"
REQUIRED_FIELDS = {"id", "type", "title", "publisher", "published_at", "url", "excerpt"}


def main() -> None:
    total = 0
    for path in sorted(DOCUMENTS_DIR.glob("*.json")):
        documents = json.loads(path.read_text())
        for doc in documents:
            missing = REQUIRED_FIELDS - doc.keys()
            if missing:
                raise ValueError(f"{path.name}: document {doc.get('id')} missing fields {missing}")
        total += len(documents)
        print(f"{path.name}: {len(documents)} document(s) OK")

    print(f"Total: {total} document(s) validated (no vector store — ingestion not implemented yet)")


if __name__ == "__main__":
    main()
