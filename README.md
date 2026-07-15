# ProcureIQ MCP Server

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active--development-yellow)

An MCP (Model Context Protocol) server that connects Claude Desktop to enterprise vendor intelligence data. Ask Claude natural language questions about vendor risk, compliance, and contracts — and get answers backed by real data.

---

## Demo

> **"What is the risk status of DataBridge Ltd?"**

```
Risk Score: 72/100 — HIGH RISK 🔴

Category: Data Services | Country: India | Contract Value: $95,000
Last Assessment: April 10, 2026 | Status: Under Review

Key Risk Factors:
- GDPR compliance gap identified
- Data breach incident in March 2026
- Regulatory fine pending
```

> **"Has the risk changed recently for DataBridge Ltd?"**

```
Risk Delta Report: DataBridge Ltd
🔴 Risk Signal: Increased

Baseline Risk Score: 72/100
Estimated Delta: +8 pts
Projected Risk Score: 80/100

Drift Drivers:
- Ongoing regulatory investigation
- Negative press coverage increasing
```

---

## Tools

| Tool | Description | Stack |
|------|-------------|-------|
| `vendor_get_profile` | Full risk profile for a vendor | Supabase |
| `vendor_search_similar` | Semantic search across vendor profiles | Pinecone + Gemini Embeddings |
| `vendor_get_news` | Recent news with AI risk summary | DuckDuckGo + Groq |
| `vendor_check_regulatory` | Compliance assessment against GDPR, SOC2, ISO27001 | LangChain + Groq |
| `vendor_list_contracts` | Paginated contract list with filters | Supabase |
| `vendor_analyze_risk_delta` | Stateful risk drift detection | LangGraph + Groq |

---

## Architecture

```
Claude Desktop
     │
     │  MCP (stdio transport)
     ▼
ProcureIQ MCP Server (FastMCP)
     │
     ├── Supabase (PostgreSQL + pgvector)
     │     └── Vendor profiles, contracts, regulatory docs
     │
     ├── Pinecone
     │     └── Vendor profile embeddings (semantic search)
     │
     ├── Google Gemini
     │     └── Text embeddings (models/gemini-embedding-001, 3072 dims)
     │
     ├── Groq (llama-3.3-70b-versatile)
     │     └── News summarisation, compliance analysis, risk reasoning
     │
     └── LangGraph
           └── Stateful risk delta agent (fetch → analyse → report)
```

---

## Tech Stack

- **MCP Framework**: FastMCP (Python)
- **LLM**: Groq — `llama-3.3-70b-versatile`
- **Embeddings**: Google Gemini — `models/gemini-embedding-001` (3072 dimensions)
- **Vector Search**: Pinecone
- **Database**: Supabase (PostgreSQL + pgvector)
- **RAG**: LangChain
- **Stateful Agent**: LangGraph
- **News Search**: DuckDuckGo Search (no API key required)

---

## Project Structure

```
procureiq-mcp/
├── server.py                  # MCP server entry point — all 6 tools registered
├── tools/
│   ├── vendor_profile.py      # Tool 1: Get vendor risk profile
│   ├── vendor_search.py       # Tool 2: Semantic similarity search (Pinecone)
│   ├── vendor_news.py         # Tool 3: News intelligence (DuckDuckGo + Groq)
│   ├── vendor_regulatory.py   # Tool 4: Regulatory compliance (LangChain RAG)
│   ├── vendor_contracts.py    # Tool 5: Contract list with pagination
│   └── vendor_risk_delta.py   # Tool 6: Risk drift detection (LangGraph)
├── utils/
│   ├── supabase_client.py     # Supabase connection
│   ├── pinecone_client.py     # Pinecone connection
│   ├── embeddings.py          # Gemini embedding generation
│   └── error_handlers.py      # Shared error handling
├── data/
│   └── seed_vendors.py        # Seeds 8 vendors into Supabase
└── agents/
    └── __init__.py
```

---

## Setup

### Prerequisites
- Python 3.10+
- Claude Desktop
- Accounts: Supabase, Pinecone, Groq, Google AI Studio

### Installation

```bash
git clone https://github.com/Razia-H/procureiq-mcp.git
cd procureiq-mcp
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Environment Variables

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

### Seed the database

```bash
python data/seed_vendors.py
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "procureiq": {
      "command": "/path/to/venv/Scripts/python.exe",
      "args": ["/path/to/procureiq-mcp/server.py"],
      "env": {
        "GROQ_API_KEY": "your_key",
        "PINECONE_API_KEY": "your_key",
        "GEMINI_API_KEY": "your_key",
        "SUPABASE_URL": "your_url",
        "SUPABASE_KEY": "your_key",
        "PINECONE_INDEX_NAME": "vendor-profiles"
      }
    }
  }
}
```

Restart Claude Desktop. The server connects automatically.

---

## Example Prompts

```
"What is the risk status of TechCorp Solutions?"
"Find vendors similar to cloud storage providers in Europe"
"Get recent news about DataBridge Ltd"
"Check if CloudBase Inc is GDPR compliant"
"List all High risk vendors with contracts over $50,000"
"Has the risk changed recently for SecureNet Systems?"
```

---

## Testing

```bash
pytest
```

Test suite in progress — see [issues](https://github.com/Razia-H/procureiq-mcp/issues) for coverage roadmap.

---

## Roadmap

- [x] Core 6 tools (profile, search, news, regulatory, contracts, risk delta)
- [ ] `vendor_generate_report` — executive-ready markdown/PDF risk summaries
- [ ] Automated test suite (pytest)
- [ ] CI pipeline (GitHub Actions)
- [ ] Demo recording

---

## Built By

**Razia** — [@Razia-H](https://github.com/Razia-H)

Portfolio project targeting Forward Deployed Engineer roles.
Demonstrates: MCP server development, RAG pipelines, LangGraph agents, vector search, and LLM tool integration.
