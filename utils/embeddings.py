import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
    return _embeddings

def embed_text(text: str) -> list:
    return get_embeddings().embed_query(text)


async def get_embedding(text: str) -> list:
    """
    Async wrapper around embed_text().

    vendor_search.py imports and awaits this name specifically, but it
    never existed here — only the synchronous embed_text() did. That
    ImportError was silently caught by vendor_search_similar's
    try/except, always surfacing as "Error searching vendors" instead
    of a real error. This fixes it without changing the call site.
    """
    return embed_text(text)
