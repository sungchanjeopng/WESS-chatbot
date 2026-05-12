# WESS 제품 지원 챗봇

ENV120, ENV130, ENV200 제품 문서를 기반으로 답변하는 RAG 챗봇입니다.
Streamlit 웹 UI와 Flask REST/SSE API를 함께 제공합니다.

## 주요 개선 구조

- `app.py`: Streamlit UI 전용
- `api.py`: Android/iOS/외부 연동 REST API 전용
- `wessbot/products.py`: 제품 정의, 별칭, 제품 자동 감지
- `wessbot/prompts.py`: 제품별 답변 규칙과 프롬프트
- `wessbot/rag.py`: Chroma 검색, 재정렬, OpenAI 답변 생성
- `wessbot/ingest.py`: 문서 추출, chunking, ChromaDB 재생성
- `tests/`: 제품 감지, 프롬프트, chunking, API shape 테스트

## 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env에 OPENAI_API_KEY 설정
streamlit run app.py
```

API만 실행:

```bash
python api.py
# 또는
API_PORT=5000 python api.py
```

## Streamlit Community Cloud 배포

1. GitHub repo: `sungchanjeopng/WESS-chatbot`
2. Branch: `main`
3. Main file path: `app.py`
4. App secrets에 최소 아래 값을 등록

```toml
OPENAI_API_KEY="sk-..."
```

선택 secrets:

```toml
WESS_CHAT_MODEL="gpt-5.4-mini"
WESS_FAST_MODEL="gpt-5.4-nano"
WESS_EMBEDDING_MODEL="text-embedding-3-small"
CHROMA_DIR="./chroma_db"
```

바로가기 예시:
`https://share.streamlit.io/deploy?repository=https://github.com/sungchanjeopng/WESS-chatbot&branch=main&mainModule=app.py`

## API

### 상태 확인

```bash
curl http://localhost:5000/api/health
```

### 제품 목록

```bash
curl http://localhost:5000/api/products
```

### 일반 답변

```bash
curl -X POST http://localhost:5000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"ENV130 Threshold 설정 방법 알려줘","product":"auto","language":"ko"}'
```

### 스트리밍 답변

```bash
curl -N -X POST http://localhost:5000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"question":"ENV200 4-20mA 출력 설정 방법","product":"auto","language":"ko"}'
```

## 제품 키

| 제품 | API product 값 | Collection |
|---|---|---|
| ENV200 농도계 | `density` 또는 `ENV200` | `wess_density` |
| ENV130 계면계 | `interface` 또는 `ENV130` | `wess_interface` |
| ENV120 계면계 | `interface_120` 또는 `ENV120` | `wess_interface_120` |
| 자동 감지 | `auto` | 질문 내용 기반 |

## 문서 DB 재생성

먼저 chunk 수만 확인:

```bash
python load_docs.py --dry-run --report ingest_report.json
```

실제 ChromaDB 재생성:

```bash
python load_docs.py --report ingest_report.json
```

주의: 상위 폴더의 원본 DOCX/PPTX 문서 폴더가 없으면 기본적으로 실제 재생성을 중단합니다. 기존 DB를 적은 markdown 문서만으로 덮어쓰는 사고를 막기 위한 안전장치입니다. 정말 현재 repo 내부 문서만으로 재생성하려면 명시적으로 실행하세요.

```bash
python load_docs.py --allow-partial --report ingest_report.json
```

기본 문서 위치:

- `docs/` + 상위 폴더 `../농도계 (ENV200)` → ENV200
- `docs_interface/` + 상위 폴더 `../계면계 (ENV130)` → ENV130
- `docs_env120/` + 상위 폴더 `../계면계 (ENV120)` → ENV120

## 테스트

```bash
python -m unittest discover -s tests -v
python -m compileall app.py api.py wessbot tests
python scripts/evaluate_answers.py
```

## 보안 주의

이 저장소가 public이면 `chroma_db/` 공개에 주의해야 합니다.
ChromaDB는 단순 벡터만이 아니라 `chroma:document` 형태의 원문 chunk와 metadata를 포함할 수 있습니다.
회사 매뉴얼, 고객 문서, 내부 교육자료가 들어간 경우 다음 중 하나를 권장합니다.

1. 저장소를 private으로 전환
2. public repo에는 코드만 두고 `chroma_db/`는 서버에서 비공개로 생성
3. 공개 가능한 요약 문서만 남기고 원문 기반 DB는 배포 환경에서 별도 관리

## 환경 변수

- `OPENAI_API_KEY`: 필수
- `WESS_CHAT_MODEL`: 기본 정밀 답변 모델
- `WESS_FAST_MODEL`: 빠른 답변 모델
- `WESS_EMBEDDING_MODEL`: 기본 `text-embedding-3-small`
- `CHROMA_DIR`: ChromaDB 경로
- `API_PORT`: API 포트
- `WESS_API_KEY`: 설정 시 API 호출에 `X-API-Key` 또는 `Authorization: Bearer` 필요
- `CORS_ALLOW_ORIGIN`: CORS 허용 origin
- `START_EMBEDDED_API`: `1`이면 Streamlit 프로세스 안에서 Flask API도 같이 실행
