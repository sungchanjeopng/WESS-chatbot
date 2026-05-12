"""Rebuild WESS chatbot ChromaDB from product documents.

Usage:
    python load_docs.py --dry-run
    python load_docs.py --report ingest_report.json

The implementation lives in wessbot.ingest so Streamlit, API, and tests can share
extraction/chunking behavior.
"""
from wessbot.ingest import main


if __name__ == "__main__":
    raise SystemExit(main())
