# PDF Chatbot - Intelligent Document Q&A System

A production-ready Flask web application that enables natural language question-answering over PDF documents using Retrieval Augmented Generation (RAG) powered by LangChain, semantic embeddings, and LLM APIs.

## Overview

**PDF Chatbot** allows users to upload PDF documents and interact with their content through a conversational AI interface. The system employs advanced NLP techniques to extract, embed, and retrieve relevant passages while maintaining full context awareness through conversation history.

### Key Capabilities

- **Multi-PDF Support**: Upload single or multiple PDFs with drag-and-drop interface
- **Semantic Search**: Retrieve relevant document passages using vector embeddings
- **Context-Aware Responses**: Maintain conversation history for coherent multi-turn interactions
- **Source Attribution**: All answers include page numbers and source file citations
- **Session Isolation**: Per-user vector stores ensure data privacy and separation
- **Production Features**: CORS support, rate limiting, comprehensive error handling

## Features

### Core Functionality

- 📄 **PDF Processing**: Robust text extraction with pdfplumber and PyPDF2 fallback
- 🔍 **Intelligent Chunking**: Overlapping text chunks for optimal retrieval performance
- 📊 **Vector Storage**: FAISS (primary) with Chroma and DocArrayInMemorySearch fallbacks
- 💬 **Conversational AI**: Context-aware responses powered by OpenRouter LLM integration
- 📌 **Citation System**: Source tracking with exact page numbers for retrieved passages
- 🔐 **Session Management**: Secure, isolated session-based storage per user

### Technical Features

- **LangChain RAG**: Retrieval Augmented Generation with ConversationalRetrievalChain
- **HuggingFace Embeddings**: sentence-transformers for semantic understanding
- **Rate Limiting**: API endpoint protection with configurable limits
- **CORS Enabled**: Cross-origin resource sharing for flexible deployment
- **Environment Configuration**: Full control via `.env` variables

## Technology Stack

| Component          | Technology                                               |
| ------------------ | -------------------------------------------------------- |
| **Backend**        | Flask 3.0.0                                              |
| **LLM Framework**  | LangChain 1.2.0 + LangChain Classic                      |
| **LLM API**        | OpenRouter (mistralai/mistral-7b-instruct:free)          |
| **Embeddings**     | HuggingFace sentence-transformers 5.2.0                  |
| **Vector Store**   | FAISS 1.8.0 (+ Chroma/DocArray fallbacks)                |
| **PDF Processing** | pdfplumber 0.10.3 + PyPDF2 3.0.1                         |
| **Frontend**       | HTML5, vanilla JavaScript, CSS3                          |
| **Deployment**     | WSGI-compatible (Flask development / production servers) |

## Project Structure

```
pdf-chatbot/
├── app.py                          # Flask application with all routes
├── requirements.txt                # Python dependencies
├── .env                            # Environment configuration
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
│
├── static/                         # Frontend assets
│   ├── css/style.css              # Responsive UI with light/dark theme
│   └── js/script.js               # Client-side logic and AJAX calls
│
├── templates/
│   └── index.html                 # Main chat interface
│
├── uploads/                        # Temporary PDF storage
├── vector_store/                  # Session-based vector stores
│   └── session_<id>/              # Per-user storage
│
└── utils/                          # Core modules
    ├── pdf_processor.py           # PDF text extraction with pagination
    ├── chunking.py                # Document chunking with overlap
    └── rag_chain.py               # RAG pipeline and LLM configuration
```

## API Routes

| Method | Endpoint   | Purpose                                                        |
| ------ | ---------- | -------------------------------------------------------------- |
| `GET`  | `/`        | Serve main chat interface                                      |
| `POST` | `/upload`  | Process PDF uploads and build vector store                     |
| `POST` | `/chat`    | Query documents and return AI-generated answers with citations |
| `GET`  | `/history` | Retrieve conversation history for current session              |
| `POST` | `/clear`   | Reset conversation and delete session data                     |

### Response Formats

**POST /upload** (Success - 200)

```json
{
  "status": "processed",
  "files": ["document.pdf"],
  "pages": 42,
  "message": "Ready to chat!"
}
```

**POST /chat** (Success - 200)

```json
{
  "answer": "The answer to your question...",
  "citations": [
    { "source": "document.pdf", "page": 5 },
    { "source": "document.pdf", "page": 12 }
  ]
}
```

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- OpenRouter API key (free models available)
- Virtual environment support

### Step 1: Clone & Environment Setup

```bash
# Clone the repository
git clone https://github.com/yocho1/pdf-chatbot.git
cd pdf-chatbot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Create or edit `.env` file in the project root:

```bash
# LLM Configuration
OPENROUTER_API_KEY=sk-or-v1-YOUR_API_KEY_HERE

# Optional: HuggingFace Token (for alternative models)
HUGGINGFACEHUB_API_TOKEN=hf_YOUR_TOKEN_HERE

# Model Settings
LLM_PROVIDER=openrouter              # Options: hub, endpoint, openrouter
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Application Settings
CHUNK_SIZE=1000                      # Characters per chunk
CHUNK_OVERLAP=200                    # Overlap between chunks
TOP_K_RESULTS=3                      # Retrieved documents per query
MAX_FILE_SIZE=10MB                   # Maximum PDF size
VECTOR_STORE=faiss                   # faiss, chroma, or docarray

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_APP=app.py
```

### Step 4: Run the Application

```bash
# Set Flask app
set FLASK_APP=app.py  # Windows
export FLASK_APP=app.py  # macOS/Linux

# Start development server
flask run --port 5000

# Or use Python directly
python app.py
```

Open your browser to **http://localhost:5000**

## Usage

1. **Upload Documents**: Drag and drop or select one or more PDF files
2. **Wait for Processing**: The system extracts text, creates embeddings, and builds the vector store
3. **Ask Questions**: Type natural language questions about the document content
4. **Review Answers**: Responses include cited page numbers and source files
5. **Continue Conversation**: The system maintains context across multiple turns
6. **Clear Session**: Use the Clear button to reset conversation history

## Configuration Options

### Environment Variables

```bash
# Chunking & Retrieval
CHUNK_SIZE=1000                 # Larger = broader context, fewer chunks
CHUNK_OVERLAP=200               # Overlap prevents context loss at boundaries
TOP_K_RESULTS=3                 # Number of document chunks to retrieve

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# Other options:
# - sentence-transformers/all-mpnet-base-v2 (slower, more accurate)
# - sentence-transformers/paraphrase-multilingual-mpnet-base-v2

# LLM Configuration
LLM_PROVIDER=openrouter
# Options: hub (HuggingFaceHub), endpoint (HuggingFaceEndpoint), openrouter (ChatOpenAI)

OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
# Free models: mistralai/mistral-7b-instruct:free, meta-llama/llama-2-7b:free

# Vector Store
VECTOR_STORE=faiss              # Primary: FAISS, Fallback: Chroma, DocArray

# File Upload
MAX_FILE_SIZE=10MB              # Supports: MB, KB, or bytes

# Rate Limiting
# Configured in app.py - defaults: 30/min global, 10/min upload, 30/min chat
```

## Troubleshooting

### Issue: "LLM processing error: 404"

**Solution**: Verify your OpenRouter API key in `.env` and ensure the model is available.

```bash
# Test API key
curl -X GET https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Issue: "No module named 'langchain.chains'"

**Solution**: Ensure all LangChain packages are correctly installed:

```bash
pip install --upgrade langchain langchain-classic langchain-community
```

### Issue: FAISS or Chroma installation failures

**Solution**: The system automatically falls back to DocArrayInMemorySearch. On Windows, FAISS is pre-built. For Chroma, install MSVC build tools or use the fallback.

### Issue: Slow embeddings on first run

**Solution**: HuggingFace embeddings download models on first use. This is a one-time operation and will be cached locally.

## Performance Considerations

- **Chunk Size**: Larger chunks (1500+) provide more context but fewer retrieval options. Smaller chunks (500) are more targeted.
- **Top K Results**: More results provide broader coverage but may dilute answer quality. 3-5 is optimal.
- **Model Selection**: Mistral 7B is fast and free. Larger models provide better quality but increased latency.
- **Vector Store**: FAISS is fastest for single-machine deployments. Chroma is better for persistent, distributed setups.

## Security Notes

- **API Keys**: Keep `OPENROUTER_API_KEY` and `HUGGINGFACEHUB_API_TOKEN` in `.env` (never commit to git)
- **Session Isolation**: Each user's vector store is isolated under `vector_store/session_<id>`
- **File Validation**: Only `.pdf` files allowed; filename sanitization prevents directory traversal
- **Rate Limiting**: Protects endpoints from abuse (adjustable in `app.py`)
- **CORS**: Currently allows all origins - restrict in production via Flask-CORS configuration

## Deployment

### Development

```bash
flask run --port 5000
```

### Production (using Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- **LangChain**: Framework for building LLM applications
- **OpenRouter**: Free LLM API access
- **FAISS**: Efficient similarity search
- **HuggingFace**: Open-source embeddings and models
- **Flask**: Lightweight Python web framework

## Support

For issues, questions, or feature requests:

- Open an issue on GitHub
- Check existing issues for solutions
- Review the troubleshooting section above

---

**Last Updated**: December 2025  
**Status**: Production Ready
