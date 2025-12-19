PDF Chatbot (Flask + LangChain RAG)

Overview

- Upload one or more PDFs and ask questions about their content.
- Uses HuggingFace embeddings + FAISS for retrieval (RAG).
- Answers include source citations with page numbers.

Features

- PDF upload with validation (.pdf only)
- Text extraction (pdfplumber with PyPDF2 fallback)
- Chunking with overlap to Document objects
- Vector store per session (saved under vector_store/)
- Chat interface with history and citations
- CORS + basic rate limiting

Project Structure

```
pdf-chatbot/
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── templates/
│   └── index.html
├── uploads/
├── vector_store/
└── utils/
    ├── pdf_processor.py
    ├── chunking.py
    └── rag_chain.py
```

Routes

- GET / → Homepage
- POST /upload → Handle PDF upload + processing
- POST /chat → Ask questions; returns answer + citations
- POST /clear → Reset conversation + session vector store
- GET /history → Fetch chat history

Setup

1. Create a virtual environment and install deps:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:

- Edit `.env` with your `HUGGINGFACEHUB_API_TOKEN`.
- Set `LLM_TASK` (default `text2text-generation` for flan-t5).
- Vector store preference: set `VECTOR_STORE=faiss` (default) or `VECTOR_STORE=chroma`.
- Optional: change models and chunk sizes.

3. Run the app:

```bash
set FLASK_APP=app.py
flask run --port 5000
```

Then open http://localhost:5000

Notes

- Vector stores are saved per session under vector*store/session*<id>.
- If you re-upload PDFs, previous history is cleared.
- Rate limiting defaults to 30/minute; adjust in app.py.
