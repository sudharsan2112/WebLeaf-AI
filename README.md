# WebLeaf AI

WebLeaf AI turns a public website into a searchable knowledge base. Enter a URL, let the app crawl its internal pages, then ask questions about the indexed content in a browser-based chat interface.

It combines a FastAPI backend, Playwright crawler, local `all-MiniLM-L6-v2` embeddings, FAISS vector search, SQLite chat memory, and Groq's streaming chat-completions API.

## Features

- Crawls same-domain pages up to the configured depth and page limits.
- Extracts page content, splits it into chunks, and stores embeddings in a per-site FAISS index.
- Streams retrieval-augmented answers grounded in the crawled website content.
- Saves crawl status and chat history in SQLite.
- Serves the frontend from the FastAPI application; no separate frontend server is needed.

## Requirements

- Python 3.10 or later
- A [Groq API key](https://console.groq.com/keys)
- Playwright's Chromium browser
- Internet access on first run to download the `all-MiniLM-L6-v2` sentence-transformers model

## Setup

1. Create and activate a virtual environment (recommended).

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install Python dependencies and the Playwright browser.

   ```powershell
   python -m pip install -r requirements.txt
   python -m playwright install chromium
   ```

   On Windows, `setup.bat` performs both commands for you.

3. Create a `.env` file in the project root and add your Groq key.

   ```env
   GROQ_API_KEY=your_groq_api_key
   ```

4. Start the application.

   ```powershell
   python -m uvicorn backend.app:app --port 8000 --reload
   ```

5. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Using the app

1. Enter a full website URL, including `https://`.
2. Wait for the crawl to finish. Progress shows the number of pages and chunks created.
3. Ask questions in the chat panel. Answers are generated from the most relevant crawled chunks and stream into the interface.

Website data is kept under `data/`:

- `data/chatbot.db` stores knowledge-base metadata and chat history.
- `data/faiss_store/` stores the FAISS index and metadata for each crawled site.

## Configuration

Default settings live in `backend/config.py`.

| Setting | Default | Purpose |
| --- | --- | --- |
| `LLM_MODEL` | `groq/compound` | Groq model sent to the chat-completions API |
| `CHUNK_SIZE` | `1000` | Maximum chunk size in characters |
| `CHUNK_OVERLAP` | `200` | Overlap between consecutive chunks |
| `TOP_K_RETRIEVAL` | `3` | Number of chunks used as answer context |
| `MAX_CRAWL_DEPTH` | `3` | Maximum internal-link depth from the submitted URL |
| `MAX_CRAWL_PAGES` | `50` | Maximum pages crawled per site |

Embeddings are generated locally with `all-MiniLM-L6-v2` (384 dimensions). Change the Groq model or crawler/RAG defaults in `backend/config.py` as needed.

## API

The frontend uses the following endpoints. Interactive API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) while the server is running.

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/crawl` | Starts a background crawl. Body: `{"url":"https://example.com"}` |
| `GET` | `/status?kb_id=<id>` | Returns crawl status, pages crawled, chunks created, and any error. |
| `POST` | `/chat` | Streams NDJSON answer chunks. Body: `{"message":"...","kb_id":"...","session_id":"..."}` |
| `GET` | `/history?session_id=<id>` | Returns stored messages for a chat session. |
| `DELETE` | `/delete?kb_id=<id>` | Deletes a knowledge base's database record and FAISS files. |
| `POST` | `/refresh?kb_id=<id>` | Starts a new crawl using the knowledge base's original URL. |
| `GET` / `POST` | `/settings` | Reads or updates the in-memory RAG and generation settings. |
| `GET` | `/health` | Lightweight health-check endpoint for deployment platforms. |

## Deploying

The repository includes a `Dockerfile` for container platforms. Railway is a good fit because it can run the Playwright-based crawler and attach persistent storage; Render is a comparable alternative.

### Railway

1. Push the repository to GitHub. Do not push `.env`, `data/`, or any API keys.
2. In Railway, create a project from the GitHub repository. Railway detects the included `Dockerfile`.
3. Add a persistent volume and mount it at `/app/data`. This preserves the SQLite database and FAISS indexes between deploys.
4. Add the `GROQ_API_KEY` environment variable in the Railway service settings.
5. Set the health-check path to `/health`, then deploy. Railway supplies the `PORT` environment variable automatically.

The first build installs Chromium and its Linux dependencies. The first running instance may also download the embedding model, so allow a little extra startup time.

### Render

Create a Docker web service from the repository, set `GROQ_API_KEY`, and attach a persistent disk at `/app/data`. Configure `/health` as the health-check path. The image listens on the provider-supplied `PORT`.

## Project structure

```text
.
|-- backend/
|   |-- app.py             # FastAPI routes and static frontend hosting
|   |-- crawler.py         # Playwright-based website crawler
|   |-- extractor.py       # HTML content extraction
|   |-- chunker.py         # Document chunking
|   |-- embedder.py        # Local sentence-transformers embeddings
|   |-- vector_store.py    # FAISS persistence and similarity search
|   |-- rag.py             # Retrieval and streamed answer pipeline
|   |-- groq_client.py     # Groq streaming client
|   |-- database.py        # SQLite knowledge-base metadata
|   `-- chat_memory.py     # SQLite-backed conversation history
|-- frontend/              # Static HTML, CSS, and JavaScript UI
|-- data/                  # Runtime SQLite and FAISS data (created automatically)
|-- requirements.txt
`-- setup.bat
```

## Notes

- Crawling is limited to links on the submitted URL's domain; unsupported media and archive extensions are skipped.
- The API accepts requests from any origin by default. Restrict CORS before deploying publicly.
- Never commit `.env` or expose your Groq API key.
