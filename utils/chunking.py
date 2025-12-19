from typing import List, Dict
from langchain_core.documents import Document


def _chunk_text(text: str, size: int, overlap: int) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    step = max(1, size - overlap)
    while start < n:
        end = min(n, start + size)
        chunks.append(text[start:end])
        if end >= n:
            break
        start += step
    return chunks


def build_documents(pages: List[Dict], chunk_size: int, overlap: int) -> List[Document]:
    docs: List[Document] = []
    for p in pages:
        page_no = p.get("page")
        source = p.get("source")
        text = p.get("text", "")
        for idx, ch in enumerate(_chunk_text(text, chunk_size, overlap)):
            docs.append(
                Document(
                    page_content=ch,
                    metadata={
                        "page": page_no,
                        "source": source,
                        "chunk_id": f"{source}-p{page_no}-c{idx}",
                    },
                )
            )
    return docs
