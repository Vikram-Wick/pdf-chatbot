import os
import uuid
import shutil
from typing import List, Dict, Any

from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from utils.pdf_processor import extract_text_by_page
from utils.chunking import build_documents
from utils.rag_chain import (
    get_embeddings,
    build_and_save_store,
    load_store,
    get_retriever,
    get_llm,
    build_qa_chain,
    build_conv_chain,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
CORS(app, resources={r"/*": {"origins": "*"}})
limiter = Limiter(get_remote_address, app=app, default_limits=["30 per minute"])  # basic rate limit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
VECTOR_BASE = os.path.join(BASE_DIR, "vector_store")
ALLOWED_EXTENSIONS = {"pdf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VECTOR_BASE, exist_ok=True)

# Environment-driven settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "3"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "google/flan-t5-base")
VECTOR_STORE_PREF = os.getenv("VECTOR_STORE", "faiss").lower()


def _parse_size(size_str: str) -> int:
    try:
        s = size_str.strip().upper()
        if s.endswith("MB"):
            return int(s[:-2]) * 1024 * 1024
        if s.endswith("KB"):
            return int(s[:-2]) * 1024
        return int(s)
    except Exception:
        return 10 * 1024 * 1024  # default 10MB

MAX_FILE_SIZE = _parse_size(os.getenv("MAX_FILE_SIZE", "10MB"))


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        session["sid"] = sid
    return sid


def get_session_store_path() -> str:
    sid = get_session_id()
    path = os.path.join(VECTOR_BASE, f"session_{sid}")
    os.makedirs(path, exist_ok=True)
    return path


@app.route("/", methods=["GET"])
@limiter.exempt
def index():
    # Ensure session exists
    get_session_id()
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
@limiter.limit("10 per minute")
def upload():
    if "files" not in request.files:
        return jsonify({"error": "No files part in request."}), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded."}), 400

    all_pages: List[Dict[str, Any]] = []
    saved_files: List[str] = []

    for f in files:
        filename = secure_filename(f.filename)
        if not filename:
            return jsonify({"error": "Invalid filename."}), 400
        if not allowed_file(filename):
            return jsonify({"error": f"Unsupported file type for {filename}."}), 400

        # Basic size check: read stream length if available
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        if size and size > MAX_FILE_SIZE:
            return jsonify({"error": f"{filename} exceeds size limit."}), 413

        save_path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(save_path)
        saved_files.append(filename)

        pages = extract_text_by_page(save_path)
        # pages: list of {"page": int, "text": str, "source": filename}
        all_pages.extend(pages)

    # Build Documents from pages
    documents = build_documents(
        pages=all_pages,
        chunk_size=CHUNK_SIZE,
        overlap=CHUNK_OVERLAP,
    )

    # Build vector store and persist per session
    embeddings = get_embeddings(model_name=EMBEDDING_MODEL)
    store_path = get_session_store_path()
    try:
        build_and_save_store(documents, embeddings, store_path, prefer=VECTOR_STORE_PREF)
    except Exception as e:
        return jsonify({"error": f"Vector store build failed: {e}"}), 500

    # Reset conversation history for new upload
    session["history"] = []
    session["ready"] = True

    return jsonify({
        "status": "processed",
        "files": saved_files,
        "pages": len(all_pages),
        "message": "Ready to chat!"
    }), 200


@app.route("/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400

    if not session.get("ready"):
        return jsonify({"error": "Documents are not processed yet."}), 409

    store_path = get_session_store_path()
    embeddings = get_embeddings(model_name=EMBEDDING_MODEL)
    try:
        store = load_store(store_path, embeddings)
    except Exception as e:
        return jsonify({"error": f"Failed to load vector store: {e}"}), 500

    retriever = get_retriever(store, top_k=TOP_K_RESULTS)
    try:
        llm = get_llm(model_name=LLM_MODEL)
    except Exception as e:
        return jsonify({"error": f"LLM not configured: {e}"}), 500
    conv = build_conv_chain(llm, retriever)

    try:
        # Build chat history as list of (human, ai) pairs
        stored = session.get("history", [])
        chat_history = []
        last_user = None
        for msg in stored:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                last_user = content
            elif role == "assistant" and last_user is not None:
                chat_history.append((last_user, content))
                last_user = None

        result = conv.invoke({"question": question, "chat_history": chat_history})
    except Exception as e:
        return jsonify({"error": f"LLM processing error: {e}"}), 500

    answer = result.get("answer") or result.get("result", "")
    source_docs = result.get("source_documents", [])

    citations = []
    for d in source_docs:
        md = d.metadata or {}
        citations.append({
            "source": md.get("source"),
            "page": md.get("page"),
        })

    # Append to session history
    history = session.get("history", [])
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer, "citations": citations})
    session["history"] = history

    return jsonify({
        "answer": answer,
        "citations": citations
    }), 200


@app.route("/history", methods=["GET"])
@limiter.limit("60 per minute")
def history():
    return jsonify({"history": session.get("history", [])}), 200


@app.route("/clear", methods=["POST"])
@limiter.limit("10 per minute")
def clear():
    # Clear conversation history and vector store for session
    session["history"] = []
    session["ready"] = False

    store_path = get_session_store_path()
    try:
        if os.path.isdir(store_path):
            shutil.rmtree(store_path)
    except Exception:
        pass

    return jsonify({"status": "cleared"}), 200


@app.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
