import os
from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA, ConversationalRetrievalChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS, Chroma, DocArrayInMemorySearch
from langchain_community.llms import HuggingFaceHub, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI


# Embeddings

def get_embeddings(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=model_name)


# Vector store (FAISS preferred, Chroma fallback)

def _write_store_type(path: str, store_type: str) -> None:
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "store_type.txt"), "w", encoding="utf-8") as f:
        f.write(store_type)


def _read_store_type(path: str) -> str | None:
    try:
        with open(os.path.join(path, "store_type.txt"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def build_and_save_store(documents, embeddings: HuggingFaceEmbeddings, path: str, prefer: str = "faiss"):
    os.makedirs(path, exist_ok=True)
    if prefer.lower() == "faiss":
        try:
            store = FAISS.from_documents(documents, embeddings)
            store.save_local(path)
            _write_store_type(path, "faiss")
            return store
        except Exception:
            pass

    # Fallback to Chroma
    try:
        store = Chroma.from_documents(documents, embeddings, persist_directory=path)
        store.persist()
        _write_store_type(path, "chroma")
        return store
    except Exception:
        pass

    # Final fallback: in-memory DocArray with lightweight persistence of raw docs
    from langchain_core.documents import Document
    store = DocArrayInMemorySearch.from_documents(documents, embeddings)
    # persist raw documents to rebuild later
    import json
    raw = [{"page_content": d.page_content, "metadata": d.metadata} for d in documents]
    with open(os.path.join(path, "docs.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f)
    _write_store_type(path, "docarray")
    return store


def load_store(path: str, embeddings: HuggingFaceEmbeddings):
    stype = _read_store_type(path)
    if stype == "faiss":
        try:
            return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
        except TypeError:
            return FAISS.load_local(path, embeddings)
    if stype == "chroma":
        return Chroma(persist_directory=path, embedding_function=embeddings)
    if stype == "docarray":
        # rebuild from persisted raw docs
        import json
        from langchain_core.documents import Document
        with open(os.path.join(path, "docs.json"), "r", encoding="utf-8") as f:
            raw = json.load(f)
        docs = [Document(page_content=r["page_content"], metadata=r.get("metadata", {})) for r in raw]
        return DocArrayInMemorySearch.from_documents(docs, embeddings)

    # Unknown: try FAISS then Chroma
    try:
        return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    except TypeError:
        return FAISS.load_local(path, embeddings)
    except Exception:
        try:
            return Chroma(persist_directory=path, embedding_function=embeddings)
        except Exception:
            # attempt docarray reconstruction
            import json
            from langchain_core.documents import Document
            with open(os.path.join(path, "docs.json"), "r", encoding="utf-8") as f:
                raw = json.load(f)
            docs = [Document(page_content=r["page_content"], metadata=r.get("metadata", {})) for r in raw]
            return DocArrayInMemorySearch.from_documents(docs, embeddings)


# LLM

def get_llm(model_name: str = "google/flan-t5-base"):
    provider = os.getenv("LLM_PROVIDER", "hub")  # hub | endpoint | openrouter

    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter.")
        model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.1,
            max_tokens=512,
        )

    token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not token:
        raise RuntimeError("HUGGINGFACEHUB_API_TOKEN is required for HuggingFaceHub LLM.")

    task = os.getenv("LLM_TASK", "text2text-generation")

    if provider == "endpoint":
        endpoint_url = os.getenv("HF_ENDPOINT_URL")
        if not endpoint_url:
            raise RuntimeError("HF_ENDPOINT_URL is required when LLM_PROVIDER=endpoint.")
        return HuggingFaceEndpoint(
            endpoint_url=endpoint_url,
            task=task,
            huggingfacehub_api_token=token,
            model_kwargs={"temperature": 0.1, "max_new_tokens": 512},
        )

    # default: HuggingFace Hub (inference API)
    return HuggingFaceHub(
        repo_id=model_name,
        task=task,
        model_kwargs={"temperature": 0.1, "max_length": 512},
        huggingfacehub_api_token=token,
    )


# Retriever

def get_retriever(store, top_k: int = 3):
    return store.as_retriever(search_kwargs={"k": top_k})


# Prompt and QA chain

def _prompt() -> PromptTemplate:
    template = (
        "You are a helpful assistant. Use the provided context to answer the user question.\n"
        "When possible, cite sources with page numbers from the context metadata.\n"
        "If the answer is not in the documents, say you don't know.\n\n"
        "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    )
    return PromptTemplate(template=template, input_variables=["context", "question"])


def build_qa_chain(llm, retriever):
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": _prompt()},
    )


def build_conv_chain(llm, retriever):
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
