"""app.py — web demo tối giản cho buổi trình bày Lab 7.

Không thêm dependency: chỉ dùng `http.server` của thư viện chuẩn. Trang web cho phép
nhập câu hỏi, chọn chiến lược chunking và bộ lọc metadata, rồi hiển thị top-k chunk
kèm score/doc_id/nguồn và câu trả lời của KnowledgeBaseAgent.

Chạy:
    python app.py                          # http://127.0.0.1:8000
    python app.py --port 8080
    EMBEDDING_PROVIDER=local python app.py # dùng embedding ngữ nghĩa thật

Mọi logic retrieval đều gọi lại đúng `src/` và `ingest.py` đang được chấm điểm —
web chỉ là lớp hiển thị, không cài đặt lại bất cứ thứ gì.
"""
from __future__ import annotations

import argparse
import html
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bench import CHUNKERS, QUERIES, extractive_llm, has_evidence
from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent

DEFAULT_DATA_DIR = Path(os.getenv("LAB_DATA_DIR", "data/tra-hang-hoan-tien"))
ROLES = ["(không lọc)", "buyer", "seller", "both"]

# Cache store theo (thư mục, tên chunker) để không phải nạp lại corpus mỗi request.
_STORES: dict[tuple[str, str], object] = {}
_EMBEDDER = None


def get_embedder():
    """Chọn backend nhúng theo EMBEDDING_PROVIDER, dùng lại logic của main.py."""
    global _EMBEDDER
    if _EMBEDDER is None:
        from main import _select_embedder

        _EMBEDDER = _select_embedder()
    return _EMBEDDER


def get_store(data_dir: Path, chunker_name: str):
    key = (str(data_dir), chunker_name)
    if key not in _STORES:
        _STORES[key] = build_knowledge_base(
            data_dir, embedding_fn=get_embedder(), chunker=CHUNKERS[chunker_name]()
        )
    return _STORES[key]


PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lab 7 — Demo truy xuất chính sách Trả hàng/Hoàn tiền</title>
<style>
 :root {{ color-scheme: light dark; --bg:#fff; --fg:#1a1a1a; --mut:#666; --line:#e0e0e0;
          --card:#fafafa; --accent:#0b6; --warn:#c60; }}
 @media (prefers-color-scheme: dark) {{
   :root {{ --bg:#16181c; --fg:#e8e8e8; --mut:#9aa; --line:#2c3038; --card:#1e2127; }} }}
 * {{ box-sizing:border-box; }}
 body {{ margin:0; padding:1.5rem; background:var(--bg); color:var(--fg);
        font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
 .wrap {{ max-width:960px; margin:0 auto; }}
 h1 {{ font-size:1.3rem; margin:0 0 .25rem; }}
 .sub {{ color:var(--mut); font-size:.87rem; margin-bottom:1.25rem; }}
 form {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:1rem; margin-bottom:1.25rem; }}
 .row {{ display:flex; gap:.6rem; flex-wrap:wrap; align-items:flex-end; }}
 label {{ display:block; font-size:.78rem; color:var(--mut); margin-bottom:.25rem; }}
 input[type=text], select {{ padding:.5rem .6rem; border:1px solid var(--line); border-radius:6px;
        background:var(--bg); color:var(--fg); font-size:.92rem; }}
 input[type=text] {{ flex:1 1 340px; }}
 button {{ padding:.55rem 1.1rem; border:0; border-radius:6px; background:var(--accent);
        color:#fff; font-size:.92rem; font-weight:600; cursor:pointer; }}
 .presets {{ margin-top:.7rem; font-size:.8rem; color:var(--mut); }}
 .presets a {{ color:var(--accent); margin-right:.7rem; }}
 .answer {{ background:var(--card); border-left:3px solid var(--accent); border-radius:0 8px 8px 0;
        padding:.9rem 1rem; margin-bottom:1.25rem; }}
 .answer h2 {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.05em;
        color:var(--mut); margin:0 0 .5rem; }}
 .chunk {{ border:1px solid var(--line); border-radius:8px; padding:.8rem .9rem; margin-bottom:.7rem; }}
 .chunk.hit {{ border-color:var(--accent); }}
 .meta {{ display:flex; gap:.5rem; flex-wrap:wrap; align-items:center;
        font-size:.78rem; color:var(--mut); margin-bottom:.4rem; }}
 .tag {{ background:var(--line); padding:.1rem .45rem; border-radius:4px; }}
 .tag.role {{ background:#0b61; color:var(--accent); }}
 .tag.ev {{ background:#0b62; color:var(--accent); font-weight:600; }}
 .score {{ font-variant-numeric:tabular-nums; font-weight:600; color:var(--fg); }}
 pre {{ margin:0; white-space:pre-wrap; word-break:break-word; font:13px/1.5 ui-monospace,monospace; }}
 .note {{ font-size:.8rem; color:var(--warn); margin-top:1rem; }}
 table {{ border-collapse:collapse; width:100%; font-size:.85rem; margin-top:.4rem; }}
 td,th {{ border-bottom:1px solid var(--line); padding:.35rem .5rem; text-align:left; }}
</style></head><body><div class="wrap">
<h1>Demo truy xuất — Chính sách Trả hàng/Hoàn tiền</h1>
<div class="sub">Corpus: <code>{data_dir}</code> · {n_chunk} chunk · backend nhúng:
  <strong>{backend}</strong>{backend_warn}</div>

<form method="get" action="/">
  <div class="row">
    <div style="flex:1 1 340px">
      <label for="q">Câu hỏi</label>
      <input type="text" id="q" name="q" value="{q}" placeholder="Nhập câu hỏi..." style="width:100%">
    </div>
    <div>
      <label for="chunker">Chiến lược chunking</label>
      <select id="chunker" name="chunker">{chunker_opts}</select>
    </div>
    <div>
      <label for="role">Lọc customer_role</label>
      <select id="role" name="role">{role_opts}</select>
    </div>
    <div>
      <label for="k">top-k</label>
      <select id="k" name="k">{k_opts}</select>
    </div>
    <button type="submit">Tìm</button>
  </div>
  <div class="presets">5 query benchmark: {presets}</div>
</form>
{result}
<p class="note">{note}</p>
</div></body></html>"""


def render(query: str, chunker_name: str, role: str, top_k: int, data_dir: Path) -> str:
    store = get_store(data_dir, chunker_name)
    n_chunk = store.get_collection_size()
    embedder = get_embedder()
    backend = getattr(embedder, "_backend_name", type(embedder).__name__)
    backend_warn = (
        ' — <span style="color:var(--warn)">mock: KHÔNG phản ánh ngữ nghĩa</span>'
        if backend == "mock embeddings fallback" else ""
    )

    result_html = ""
    if query:
        metadata_filter = {"customer_role": role} if role in ("buyer", "seller", "both") else None
        results = (store.search_with_filter(query, top_k=top_k, metadata_filter=metadata_filter)
                   if metadata_filter else store.search(query, top_k=top_k))

        # Nếu câu hỏi trùng một benchmark query, tô sáng chunk chứa chuỗi bằng chứng.
        evidence = next((q["evidence"] for q in QUERIES if q["text"] == query), [])

        agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
        answer = (agent.answer(query, top_k=top_k) if not metadata_filter else extractive_llm(
            "NGỮ CẢNH:\n" + "\n".join(r["content"] for r in results)
            + f"\n\nCÂU HỎI: {query}\n\nTRẢ LỜI:"))

        blocks = []
        for rank, r in enumerate(results, start=1):
            meta = r["metadata"]
            hit = evidence and has_evidence(r["content"], evidence)
            ev_tag = '<span class="tag ev">có bằng chứng</span>' if hit else ""
            blocks.append(
                f'<div class="chunk{" hit" if hit else ""}">'
                f'<div class="meta"><span class="score">#{rank} · {r["score"]:.4f}</span>'
                f'<span class="tag">{html.escape(str(meta.get("doc_id", "?")))}</span>'
                f'<span class="tag role">{html.escape(str(meta.get("customer_role", "?")))}</span>'
                f'<span class="tag">chunk {meta.get("chunk_index", "?")}</span>{ev_tag}</div>'
                f'<pre>{html.escape(r["content"][:700])}</pre></div>'
            )
        if not blocks:
            blocks.append('<div class="chunk"><em>Không có chunk nào khớp bộ lọc.</em></div>')

        result_html = (
            f'<div class="answer"><h2>Câu trả lời của KnowledgeBaseAgent</h2>'
            f'<div>{html.escape(answer)}</div></div>'
            f'<h2 style="font-size:.9rem;color:var(--mut)">Top-{top_k} chunk truy xuất được'
            f'{" (đã lọc " + html.escape(role) + ")" if metadata_filter else ""}</h2>'
            + "".join(blocks)
        )

    def opts(values, current):
        return "".join(
            f'<option value="{html.escape(str(v))}"{" selected" if str(v) == str(current) else ""}>'
            f"{html.escape(str(v))}</option>" for v in values
        )

    presets = " ".join(
        f'<a href="/?q={html.escape(q["text"], quote=True).replace(" ", "%20")}'
        f'&chunker={chunker_name}&role={q["filter"]["customer_role"] if q["filter"] else ROLES[0]}'
        f'&k={top_k}">{q["id"]}</a>' for q in QUERIES
    )

    return PAGE.format(
        data_dir=html.escape(str(data_dir)), n_chunk=n_chunk,
        backend=html.escape(backend), backend_warn=backend_warn,
        q=html.escape(query, quote=True),
        chunker_opts=opts(CHUNKERS.keys(), chunker_name),
        role_opts=opts(ROLES, role), k_opts=opts([3, 5, 10], top_k),
        presets=presets, result=result_html,
        note="Trang này chỉ là lớp hiển thị: mọi truy xuất đều gọi lại src/store.py, "
             "src/chunking.py và src/agent.py — cùng mã nguồn mà bench.py và pytest dùng.",
    )


class Handler(BaseHTTPRequestHandler):
    data_dir = DEFAULT_DATA_DIR

    def do_GET(self) -> None:  # noqa: N802 - chữ ký của BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        params = parse_qs(parsed.query)
        query = params.get("q", [""])[0].strip()
        chunker_name = params.get("chunker", ["by_heading"])[0]
        if chunker_name not in CHUNKERS:
            chunker_name = "by_heading"
        role = params.get("role", [ROLES[0]])[0]
        try:
            top_k = max(1, min(20, int(params.get("k", ["3"])[0])))
        except ValueError:
            top_k = 3

        body = render(query, chunker_name, role, top_k, self.data_dir).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"  {self.address_string()} — {fmt % args}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Web demo cho pipeline retrieval của Lab 7.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    if not args.data.exists():
        print(f"Không tìm thấy thư mục dữ liệu: {args.data}")
        return 1

    Handler.data_dir = args.data
    print(f"Corpus     : {args.data}")
    print("Đang nạp corpus (lần đầu có thể mất vài giây)...")
    store = get_store(args.data, "by_heading")
    embedder = get_embedder()
    print(f"Backend    : {getattr(embedder, '_backend_name', type(embedder).__name__)}")
    print(f"Đã nạp     : {store.get_collection_size()} chunk")
    print(f"\n  →  http://{args.host}:{args.port}\n")
    try:
        HTTPServer((args.host, args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
