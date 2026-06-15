import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

_pc = None
_index = None

def get_pinecone_index():
    global _pc, _index
    if _index is None:
        _pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _index = _pc.Index(os.getenv("PINECONE_INDEX_NAME", "vendor-profiles"))
    return _index
