"""DOCX 문서를 읽어서 ChromaDB에 벡터로 저장하는 스크립트"""
import os
import docx
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")


def extract_text_from_docx(filepath):
    """DOCX 파일에서 텍스트 추출 (단락 + 테이블)"""
    doc = docx.Document(filepath)
    texts = []

    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            texts.append(t)

    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                texts.append(" | ".join(cells))

    return "\n".join(texts)


def chunk_text(text, chunk_size=500, overlap=50):
    """텍스트를 일정 크기로 분할"""
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_len = 0

    for line in lines:
        line_len = len(line)
        if current_len + line_len > chunk_size and current_chunk:
            chunks.append("\n".join(current_chunk))
            # overlap: 마지막 몇 줄 유지
            overlap_lines = []
            overlap_len = 0
            for prev_line in reversed(current_chunk):
                if overlap_len + len(prev_line) > overlap:
                    break
                overlap_lines.insert(0, prev_line)
                overlap_len += len(prev_line)
            current_chunk = overlap_lines
            current_len = overlap_len

        current_chunk.append(line)
        current_len += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def get_embedding(text):
    """OpenAI 임베딩 생성"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def main():
    # DOCX 파일 찾기
    docx_files = []
    for f in os.listdir(DOCS_DIR):
        if f.lower().endswith(".docx"):
            docx_files.append(os.path.join(DOCS_DIR, f))

    if not docx_files:
        print("DOCX 파일을 찾을 수 없습니다.")
        return

    print(f"발견된 문서: {len(docx_files)}개")
    for f in docx_files:
        print(f"  - {os.path.basename(f)}")

    # ChromaDB 초기화
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    # 기존 컬렉션 삭제 후 재생성
    try:
        chroma_client.delete_collection("wess_docs")
    except Exception:
        pass
    collection = chroma_client.create_collection(
        name="wess_docs",
        metadata={"hnsw:space": "cosine"}
    )

    # 문서별 처리
    total_chunks = 0
    for filepath in docx_files:
        filename = os.path.basename(filepath)
        print(f"\n처리 중: {filename}")

        text = extract_text_from_docx(filepath)
        print(f"  텍스트 길이: {len(text)}자")

        chunks = chunk_text(text)
        print(f"  청크 수: {len(chunks)}개")

        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}_{i}"
            embedding = get_embedding(chunk)

            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": filename, "chunk_index": i}]
            )

            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{len(chunks)} 임베딩 완료...")

        total_chunks += len(chunks)
        print(f"  완료!")

    print(f"\n전체 완료! 총 {total_chunks}개 청크 저장됨")


if __name__ == "__main__":
    main()
