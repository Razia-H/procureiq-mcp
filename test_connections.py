import os
from dotenv import load_dotenv

load_dotenv()

print("Testing all connections...\n")

groq_key = os.getenv("GROQ_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print("1. Environment variables:")
print("   Groq:     " + ("OK" if groq_key else "MISSING"))
print("   Pinecone: " + ("OK" if pinecone_key else "MISSING"))
print("   Gemini:   " + ("OK" if gemini_key else "MISSING"))
print("   Supabase: " + ("OK" if supabase_url and supabase_key else "MISSING"))

print("\n2. Pinecone connection:")
try:
    from pinecone import Pinecone
    pc = Pinecone(api_key=pinecone_key)
    indexes = pc.list_indexes()
    print("   OK - indexes: " + str([i.name for i in indexes]))
except Exception as e:
    print("   FAILED: " + str(e))

print("\n3. Groq connection:")
try:
    from langchain_groq import ChatGroq
    llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile")
    response = llm.invoke("Say OK in one word")
    print("   OK - response: " + response.content)
except Exception as e:
    print("   FAILED: " + str(e))

print("\n4. Gemini embeddings:")
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=gemini_key
    )
    result = embeddings.embed_query("test vendor risk")
    print("   OK - dimensions: " + str(len(result)))
except Exception as e:
    print("   FAILED: " + str(e))

print("\n5. Supabase connection:")
try:
    from supabase import create_client
    client = create_client(supabase_url, supabase_key)
    print("   OK - Connected")
except Exception as e:
    print("   FAILED: " + str(e))

print("\n--- Done ---")
