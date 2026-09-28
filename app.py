"""차량관리대장 · 웨스글로벌 (공용 온라인판).

누구나 접속해 조회·수정할 수 있고, 데이터는 비공개 GitHub 저장소의
data.json(기본: sungchanjeopng/WESS-vehicle-data)에 저장된다.

필요한 Streamlit secrets:
    GITHUB_TOKEN = "..."            # data 저장소 Contents read/write 권한
    DATA_REPO    = "owner/repo"     # (선택) 기본 sungchanjeopng/WESS-vehicle-data
    DATA_PATH    = "data.json"      # (선택)
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

COLS = ("vehicles", "driving_logs", "inspections", "photos")
REFRESH_SEC = 10
API = "https://api.github.com"


def _cfg(name: str, default: str | None = None) -> str | None:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # secrets.toml 없음
        pass
    return os.environ.get(name, default)


TOKEN = _cfg("GITHUB_TOKEN")
REPO = _cfg("DATA_REPO", "sungchanjeopng/WESS-vehicle-data")
PATH = _cfg("DATA_PATH", "data.json")


def _headers(raw: bool = False) -> dict:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _empty() -> dict:
    return {c: {} for c in COLS}


def _normalize(d) -> dict:
    out = _empty()
    if isinstance(d, dict):
        for c in COLS:
            if isinstance(d.get(c), dict):
                out[c] = d[c]
    return out


def gh_load() -> tuple[dict, str | None]:
    url = f"{API}/repos/{REPO}/contents/{PATH}"
    r = requests.get(url, headers=_headers(), timeout=30)
    if r.status_code == 404:
        return _empty(), None
    r.raise_for_status()
    meta = r.json()
    sha = meta["sha"]
    if meta.get("encoding") == "base64" and meta.get("content"):
        text = base64.b64decode(meta["content"]).decode("utf-8")
    else:  # 1MB 초과 파일은 raw로 다시 받는다
        rr = requests.get(url, headers=_headers(raw=True), timeout=60)
        rr.raise_for_status()
        text = rr.content.decode("utf-8")
    return _normalize(json.loads(text) if text.strip() else {}), sha


def gh_save(data: dict, sha: str | None, message: str) -> str:
    body = {
        "message": message,
        "content": base64.b64encode(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).decode("ascii"),
    }
    if sha:
        body["sha"] = sha
    r = requests.put(
        f"{API}/repos/{REPO}/contents/{PATH}", headers=_headers(), json=body, timeout=60
    )
    if r.status_code in (409, 422):
        raise ConflictError(r.text[:200])
    r.raise_for_status()
    return r.json()["content"]["sha"]


class ConflictError(Exception):
    pass


class Store:
    """프로세스 공용 캐시. 모든 접속 세션이 같은 데이터를 본다."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.data: dict | None = None
        self.sha: str | None = None
        self.loaded_at = 0.0

    def _refresh(self, force: bool = False) -> None:
        if force or self.data is None or time.time() - self.loaded_at > REFRESH_SEC:
            self.data, self.sha = gh_load()
            self.loaded_at = time.time()

    def get(self) -> tuple[dict, str | None]:
        with self.lock:
            self._refresh()
            return self.data, self.sha

    def apply(self, ops: list) -> tuple[dict, str | None]:
        with self.lock:
            last_err: Exception | None = None
            for attempt in range(4):
                self._refresh(force=attempt > 0)
                new = json.loads(json.dumps(self.data))
                for op in ops:
                    col, doc_id, val = op[0], str(op[1]), op[2]
                    if col not in COLS:
                        continue
                    if val is None:
                        new[col].pop(doc_id, None)
                    else:
                        new[col][doc_id] = val
                try:
                    self.sha = gh_save(new, self.sha, f"차량관리대장 수정 ({len(ops)}건)")
                    self.data = new
                    self.loaded_at = time.time()
                    return self.data, self.sha
                except ConflictError as e:  # 다른 사람이 먼저 저장함 → 다시 받아서 재적용
                    last_err = e
            raise RuntimeError(f"동시 저장 충돌 재시도 실패: {last_err}")


@st.cache_resource
def get_store() -> Store:
    return Store()


st.set_page_config(
    page_title="차량관리대장 · 웨스글로벌",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)
st.markdown(
    """
    <style>
      [data-testid="stHeader"], [data-testid="stToolbar"], footer,
      [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
      .block-container, [data-testid="stMainBlockContainer"] {
        padding: 0 !important; max-width: 100% !important;
      }
      [data-testid="stAppViewContainer"] > .main { padding: 0 !important; }
      iframe { display: block; border: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

if not TOKEN:
    st.error("서버 설정 오류: GITHUB_TOKEN secret이 없습니다. 관리자에게 문의하세요.")
    st.stop()

vehicle_log = components.declare_component(
    "vehicle_log", path=str(Path(__file__).with_name("vehicle_component"))
)

store = get_store()
ss = st.session_state
ss.setdefault("ack", 0)
ss.setdefault("error", None)

value = ss.get("vehicle_log_widget")
if isinstance(value, dict):
    nonce = int(value.get("nonce") or 0)
    ops = value.get("ops") or []
    if ops and nonce > ss.ack:
        try:
            store.apply(ops)
            ss.ack = nonce
            ss.error = None
        except Exception as e:  # 실패 시 ack를 올리지 않아 브라우저가 다시 보낸다
            ss.error = str(e)[:200]
    elif not ops:
        ss.ack = max(ss.ack, nonce)

try:
    data, sha = store.get()
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

vehicle_log(data=data, rev=sha, ack=ss.ack, error=ss.error, key="vehicle_log_widget", default=None)
