# RAG-Powered Website Chatbot using Ollama

## Project Overview
The RAG-Powered Website Chatbot is a production-quality, local-first application designed to recursively crawl any given website, extract meaningful content, embed it locally using Ollama's `nomic-embed-text`, and enable intelligent conversational retrieval using FAISS and `llama3.1:8b`. The system features a modern, animated "Warm Yellow" UI, built entirely on local AI models to ensure privacy, zero external API costs, and low latency.

---

## 🏗 System Architecture Diagram

```mermaid
graph TD
    User([User / Browser])
    subgraph Frontend [Frontend Interface]
        UI[index.html & chat.html]
        JS[script.js - Fetch API]
    end

    subgraph Backend [FastAPI Backend]
        API[app.py Endpoints]
        Crawler[crawler.py - Playwright]
        Extractor[extractor.py - BeautifulSoup]
        Chunker[chunker.py - LangChain]
        RAG[rag.py - Retrieval Pipeline]
        DB[(database.py - SQLite)]
    end

    subgraph AI Models [Local Ollama Provider]
        EmbedModel([nomic-embed-text])
        LLM([llama3.1:8b])
    end

    subgraph Vector Storage
        FAISS[(vector_store.py - FAISS Index)]
    end

    User <-->|HTTP/WS| UI
    UI <-->|REST/NDJSON| API
    
    API --> Crawler
    Crawler --> Extractor
    Extractor --> Chunker
    Chunker --> EmbedModel
    EmbedModel --> FAISS
    
    API --> DB
    API --> RAG
    RAG --> FAISS
    RAG --> LLM
```

---

## ⚙️ Installation & Setup

1. **Clone the Repository**
2. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **Start Ollama Models**
   Ensure Ollama is installed on your system.
   ```bash
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```
4. **Run the Backend**
   ```bash
   uvicorn backend.app:app --reload
   ```
5. **Open the Frontend**
   Open `frontend/index.html` in your web browser.

---

## 📂 Folder Structure

```text
.
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── app.py
│   ├── models.py
│   ├── crawler.py
│   ├── extractor.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── vector_store.py
│   ├── rag.py
│   ├── ollama_client.py
│   ├── chat_memory.py
│   ├── database.py
│   └── utils.py
├── frontend/
│   ├── index.html
│   ├── chat.html
│   ├── style.css
│   ├── script.js
└── README.md
```

---

## 🖼 Screenshots

*(Placeholders for screenshots)*
- **Homepage:** `![Homepage Setup](frontend/assets/setup.png)`
- **Chat Interface:** `![Chat Interface](frontend/assets/chat.png)`

---

## 🧠 How RAG Works

```mermaid
sequenceDiagram
    participant User
    participant App as RAG Pipeline
    participant FAISS as FAISS Database
    participant Ollama as Ollama Client

    User->>App: Sends Query ("What is X?")
    App->>Ollama: Generate Embeddings for Query (nomic-embed-text)
    Ollama-->>App: Query Vector [0.1, 0.4, ...]
    App->>FAISS: Search Top-K Similar Chunks (Vector)
    FAISS-->>App: Top 5 Relevant Texts
    App->>App: Build Context + Chat History
    App->>Ollama: Generate Answer Stream (llama3.1:8b)
    Ollama-->>User: Streaming Response chunks
```

---

## 🕷 How Crawling Works

```mermaid
flowchart TD
    Start[User Inputs URL] --> Validate[Validate URL Format]
    Validate --> InitCrawl[Initialize WebCrawler]
    InitCrawl --> Visit[Playwright visits Page]
    Visit --> Extract[BeautifulSoup removes ads/nav/scripts]
    Extract --> Parse[Parse text, headings, code]
    Parse --> Chunk[Recursive Character Splitter]
    Chunk --> Embed[Ollama embeds Chunks]
    Embed --> Store[Save to FAISS DB]
    Store --> Queue[Find & Queue valid internal links]
    Queue --> Loop{Queue Empty or Max Depth?}
    Loop -- No --> Visit
    Loop -- Yes --> Complete[Ready for Chat]
```

---

## 📘 API Documentation

### 1. `POST /crawl`
Initializes background crawling for a website.
**Body:** `{"url": "https://example.com"}`
**Response:** `{"message": "Crawling started", "kb_id": "md5_hash"}`

### 2. `GET /status?kb_id={id}`
Returns crawling progress.
**Response:** `{"kb_id": "...", "status": "crawling", "pages_crawled": 10, "chunks_created": 45}`

### 3. `POST /chat`
Conversational RAG endpoint (Returns NDJSON streaming).
**Body:** `{"message": "Hello", "kb_id": "...", "session_id": "..."}`

### 4. `DELETE /delete?kb_id={id}`
Deletes FAISS index and DB records for a knowledge base.

---

## 📐 Class Diagram

```mermaid
classDiagram
    class WebCrawler {
        +base_url: str
        +visited: Set
        +crawl()
    }
    class Extractor {
        +html_content: str
        +extract_content() Dict
    }
    class Chunker {
        +chunk_document() List
    }
    class VectorStore {
        +kb_id: str
        +add_embeddings()
        +search() List
    }
    class RAGPipeline {
        +get_context()
        +chat_stream()
    }

    WebCrawler --> Extractor : Uses
    WebCrawler --> Chunker : Uses
    WebCrawler --> VectorStore : Writes
    RAGPipeline --> VectorStore : Reads
```

---

## 🚀 Future Improvements

- **Multi-Tenant System:** Allow user accounts to manage their own knowledge bases securely.
- **WebSockets:** Upgrade the frontend-backend communication from HTTP Polling to WebSockets for live crawler updates.
- **Advanced Chunking:** Implement Semantic Chunking instead of fixed-length Recursive split.
- **Graph RAG:** Extract entities and relationships during crawling to power Graph RAG queries.


TO RUN : python -m uvicorn backend.app:app --port 8000 --reload
