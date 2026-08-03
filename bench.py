"""bench.py — chạy 5 benchmark query của nhóm và đo chất lượng truy xuất.

Điểm khác biệt quan trọng so với cách chấm ngây thơ: **chấm ở mức CHUNK, không chỉ doc_id**.

Một chiến lược hoàn toàn có thể chiếm trọn cả ba slot bằng đúng tài liệu gold mà không
chunk nào chứa câu trả lời — hay gặp với chunker theo heading, vì các mục trong cùng tài
liệu nói về cùng chủ đề nên điểm sát nhau và mục nào lọt top-3 gần như ngẫu nhiên.
Vì vậy mỗi query khai báo thêm `evidence`: các chuỗi đặc trưng PHẢI xuất hiện trong nội
dung chunk truy xuất được thì mới tính là có bằng chứng trả lời.

Chạy:
    python bench.py                      # chunker mặc định (by_heading)
    python bench.py --chunker all        # so sánh cả 4 chiến lược
    python bench.py --baseline           # thêm bảng ChunkingStrategyComparator
    python bench.py --ablation           # thêm A/B có/không metadata filter

Bộ 5 query + gold answer: report/BENCHMARK_QUERIES.md (đã khóa, dùng chung cả nhóm).
"""
from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path

from ingest import build_knowledge_base, parse_front_matter
from src.agent import KnowledgeBaseAgent
from src.chunking import (ChunkingStrategyComparator, FixedSizeChunker,
                          MarkdownHeadingChunker, RecursiveChunker, SentenceChunker)
from src.embeddings import _mock_embed

DATA_DIR = Path("data/tra-hang-hoan-tien")
TOP_K = 3

# 5 benchmark query của nhóm.
#   gold     = tập doc_id chứa câu trả lời chuẩn (chấm mức TÀI LIỆU)
#   evidence = các chuỗi đặc trưng của đáp án (chấm mức CHUNK) — chỉ cần khớp 1 chuỗi
QUERIES = [
    {
        "id": "Q1",
        "kind": "số liệu + ngoại lệ",
        "text": "Người mua có bao lâu để gửi yêu cầu Trả hàng/Hoàn tiền sau khi đơn giao thành công? "
                "Đơn thực phẩm tươi sống, đông lạnh có khác không?",
        "filter": {"customer_role": "buyer"},
        "gold": {"buyer-return-eligibility", "return-refund-policy"},
        "evidence": ["24 giờ kể từ", "thực phẩm tươi sống"],
    },
    {
        "id": "Q2",
        "kind": "số liệu (tra bảng)",
        "text": "Tôi thanh toán bằng thẻ tín dụng ghi nợ. Sau khi Shopee chấp nhận hoàn tiền, "
                "tiền về đâu và mất bao lâu?",
        "filter": {"customer_role": "buyer"},
        "gold": {"buyer-refund-timeline"},
        "evidence": ["7–14 ngày làm việc"],
    },
    {
        "id": "Q3",
        "kind": "liệt kê + điều kiện",
        "text": "Sau khi được chấp nhận Trả hàng/Hoàn tiền, Người mua có những hình thức gửi hàng "
                "hoàn nào? Hình thức nào miễn phí?",
        "filter": None,
        "gold": {"buyer-return-shipping"},
        "evidence": ["Trả hàng tại bưu cục (Miễn phí", "Tự sắp xếp"],
    },
    {
        "id": "Q4",
        "kind": "quy trình + thời hạn (cần lọc metadata)",
        "text": "Khi Shopee quyết định hoàn tiền ngay mà không yêu cầu trả hàng, bên bán có bao lâu "
                "để khiếu nại nếu không đồng ý? Shopee xử lý khiếu nại trong bao lâu?",
        "filter": {"customer_role": "seller"},
        "gold": {"seller-refund-appeal", "seller-return-process"},
        # Corpus diễn đạt cùng một mốc theo 2 cách ("trong vòng 2 ngày" ở bảng, "2 ngày kể từ khi
        # Shopee gửi thông báo" ở phần văn xuôi) -> khai báo cả hai để không chấm sai vì câu chữ.
        "evidence": ["2 ngày kể từ khi shopee", "trong vòng 2 ngày", "3–5 ngày làm việc"],
    },
    {
        "id": "Q5",
        "kind": "điều kiện + ngoại lệ",
        "text": "Ai được trả hàng vì đổi ý hoặc không còn nhu cầu? Có hạn chế sản phẩm nào không?",
        "filter": None,
        "gold": {"buyer-return-eligibility", "return-refund-policy", "seller-return-process"},
        "evidence": ["Kim Cương", "hạng Vàng", "danh sách hạn chế trả hàng"],
    },
]

CHUNKERS = {
    "fixed_size": lambda: FixedSizeChunker(chunk_size=500, overlap=50),
    "by_sentences": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive": lambda: RecursiveChunker(chunk_size=500),
    "by_heading": lambda: MarkdownHeadingChunker(chunk_size=1000, min_chunk_size=120),
}


def _norm(text: str) -> str:
    """Chuẩn hóa để so khớp bằng chứng: bỏ dấu tổ hợp, gộp khoảng trắng, hạ chữ thường."""
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.split()).lower()


def has_evidence(chunk_text: str, evidence: list[str]) -> bool:
    body = _norm(chunk_text)
    return any(_norm(marker) in body for marker in evidence)


def extractive_llm(prompt: str) -> str:
    """LLM giả lập kiểu *trích xuất*: chỉ trả lại câu lấy nguyên văn từ NGỮ CẢNH.

    Không có API key trong lab này, nhưng dùng một hàm sinh ngẫu nhiên thì không đo được
    grounding. Hàm này cố tình chỉ được phép trích từ context, nhờ vậy "agent trả lời đúng"
    trở thành phép đo trung thực: nếu retrieval không đưa được câu chứa đáp án vào context
    thì agent KHÔNG THỂ trả lời đúng — đúng bản chất của RAG.
    """
    context = prompt.split("NGỮ CẢNH:", 1)[-1].split("CÂU HỎI:", 1)[0]
    question = prompt.split("CÂU HỎI:", 1)[-1].split("TRẢ LỜI:", 1)[0].strip()

    # Từ khóa nội dung của câu hỏi (bỏ từ chức năng) để chấm câu nào trong context liên quan nhất.
    stop = {"của", "và", "có", "là", "cho", "khi", "sau", "trong", "được", "thì", "bao", "nào",
            "không", "với", "này", "một", "các", "về", "đâu", "tôi", "bạn", "mất", "nếu", "để"}
    keywords = {w for w in _norm(question).replace("?", " ").replace(",", " ").split()
                if len(w) > 2 and w not in stop}

    best_sentences: list[tuple[int, str]] = []
    for raw_line in context.splitlines():
        line = raw_line.strip().lstrip("#>-* ").strip()
        if len(line) < 20:
            continue
        overlap = sum(1 for kw in keywords if kw in _norm(line))
        if overlap:
            best_sentences.append((overlap, line))

    if not best_sentences:
        return "Không tìm thấy thông tin liên quan trong ngữ cảnh được cung cấp."
    best_sentences.sort(key=lambda pair: -pair[0])
    return " ".join(line for _, line in best_sentences[:3])[:600]


def score_query(results: list[dict], query: dict, answer: str | None = None) -> tuple[int, str, dict]:
    """Chấm theo docs/SCORING.md — điều kiện 'liên quan' đo ở MỨC CHUNK.

    2đ: top-3 có chunk chứa bằng chứng **và** câu trả lời của agent chứa được bằng chứng đó
    1đ: top-3 có chunk chứa bằng chứng nhưng agent trả lời thiếu, hoặc chunk đó không ở top-1
    0đ: không chunk nào trong top-3 chứa bằng chứng
    """
    doc_hit_1 = bool(results) and results[0]["metadata"]["doc_id"] in query["gold"]
    doc_hit_3 = any(r["metadata"]["doc_id"] in query["gold"] for r in results)

    evidence_ranks = [
        rank for rank, r in enumerate(results, start=1)
        if has_evidence(r["content"], query["evidence"])
    ]
    ev_hit_1 = bool(evidence_ranks) and evidence_ranks[0] == 1
    ev_hit_3 = bool(evidence_ranks)

    # Grounding: câu trả lời của agent có thật sự mang bằng chứng lấy từ context không.
    answer_ok = has_evidence(answer, query["evidence"]) if answer else False

    if ev_hit_3 and answer_ok and ev_hit_1:
        score, label = 2, "FULL  "
    elif ev_hit_3:
        score, label = 1, "PART  "
    else:
        score, label = 0, "MISS  "

    detail = {
        "doc_hit_1": doc_hit_1, "doc_hit_3": doc_hit_3,
        "ev_hit_1": ev_hit_1, "ev_hit_3": ev_hit_3,
        "answer_ok": answer_ok, "evidence_ranks": evidence_ranks,
    }
    return score, label, detail


def run_baseline() -> None:
    """Baseline comparator trên BODY (đã bỏ front matter qua ingest.parse_front_matter)."""
    print("=" * 96)
    print("BASELINE — ChunkingStrategyComparator (chunk_size=500, body đã bỏ front matter)")
    print("=" * 96)
    comparator = ChunkingStrategyComparator()
    print(f"{'Tài liệu':30} {'ký tự':>7} {'fixed':>7} {'sentence':>9} {'recursive':>10} {'heading':>8}")
    print("-" * 96)
    for path in sorted(DATA_DIR.glob("*.md")):
        _, body = parse_front_matter(path.read_text(encoding="utf-8"))
        body = body.strip()
        result = comparator.compare(body, chunk_size=500)
        heading_chunks = MarkdownHeadingChunker(chunk_size=1000, min_chunk_size=120).chunk(body)
        print(f"{path.stem[:30]:30} {len(body):>7} "
              f"{result['fixed_size']['count']:>7} {result['by_sentences']['count']:>9} "
              f"{result['recursive']['count']:>10} {len(heading_chunks):>8}")


def run_benchmark(chunker_name: str, show_detail: bool = True) -> dict:
    store = build_knowledge_base(DATA_DIR, embedding_fn=_mock_embed, chunker=CHUNKERS[chunker_name]())
    size = store.get_collection_size()
    lengths = [len(r["content"]) for r in store._store]
    avg_len = sum(lengths) / len(lengths) if lengths else 0

    print(f"\n{'=' * 96}")
    print(f"CHIẾN LƯỢC: {chunker_name}  ({size} chunk, độ dài TB {avg_len:.0f} ký tự)")
    print("=" * 96)

    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)

    total = 0
    doc_hits_3 = ev_hits_3 = ev_hits_1 = grounded = 0
    for query in QUERIES:
        if query["filter"]:
            results = store.search_with_filter(query["text"], top_k=TOP_K, metadata_filter=query["filter"])
        else:
            results = store.search(query["text"], top_k=TOP_K)

        # Agent chạy trên đúng ngữ cảnh mà retrieval vừa lấy (agent.answer tự search lại
        # không filter, nên với query có filter ta chấm grounding trên context đã lọc).
        answer = agent.answer(query["text"], top_k=TOP_K) if not query["filter"] else \
            extractive_llm(f"NGỮ CẢNH:\n" + "\n".join(r["content"] for r in results)
                           + f"\n\nCÂU HỎI: {query['text']}\n\nTRẢ LỜI:")

        score, label, detail = score_query(results, query, answer)
        total += score
        doc_hits_3 += detail["doc_hit_3"]
        ev_hits_3 += detail["ev_hit_3"]
        ev_hits_1 += detail["ev_hit_1"]
        grounded += detail["answer_ok"]

        gap = "  <-- ĐÚNG TÀI LIỆU NHƯNG SAI MỤC" if detail["doc_hit_3"] and not detail["ev_hit_3"] else ""
        print(f"\n{query['id']} [{label}] {score}/2đ — {query['kind']}{gap}")
        print(f"   Query : {query['text'][:88]}")
        print(f"   Filter: {query['filter'] or '(không)'}")
        print(f"   Bằng chứng cần có: {query['evidence']}")
        if show_detail:
            for rank, r in enumerate(results, start=1):
                meta = r["metadata"]
                doc_mark = "D" if meta["doc_id"] in query["gold"] else " "
                ev_mark = "E" if has_evidence(r["content"], query["evidence"]) else " "
                preview = " ".join(r["content"].split())[:70]
                print(f"   [{doc_mark}{ev_mark}] {rank}. {meta['doc_id'][:26]:26} "
                      f"[{meta['customer_role']:6}] score={r['score']:.4f}")
                print(f"        {preview}...")
            ground_mark = "CÓ bằng chứng" if detail["answer_ok"] else "THIẾU bằng chứng"
            print(f"   Agent trả lời [{ground_mark}]: {' '.join(answer.split())[:150]}...")

    print(f"\n>>> {chunker_name}: điểm {total}/10 | doc-hit@3 = {doc_hits_3}/5 | "
          f"evidence-hit@3 = {ev_hits_3}/5 | evidence-hit@1 = {ev_hits_1}/5 | grounded = {grounded}/5")
    if doc_hits_3 > ev_hits_3:
        print(f"    Cảnh báo: {doc_hits_3 - ev_hits_3} query lấy ĐÚNG tài liệu nhưng SAI mục "
              f"— chấm theo doc_id sẽ thổi phồng kết quả.")
    return {"score": total, "size": size, "avg_len": avg_len, "doc_hit_3": doc_hits_3,
            "ev_hit_3": ev_hits_3, "ev_hit_1": ev_hits_1, "grounded": grounded}


def run_ablation(chunker_name: str = "by_heading") -> None:
    """A/B có/không metadata filter, chạy trên mọi query có filter."""
    print(f"\n{'=' * 96}")
    print(f"ABLATION — A/B metadata filter (chunker={chunker_name})")
    print("=" * 96)
    store = build_knowledge_base(DATA_DIR, embedding_fn=_mock_embed, chunker=CHUNKERS[chunker_name]())

    total = store.get_collection_size()
    both = sum(1 for r in store._store if r["metadata"].get("customer_role") == "both")
    print(f"Corpus: {total} chunk, trong đó {both} chunk role='both' ({both / total:.0%}) "
          f"— bị loại ở MỌI filter theo vai.\n")

    for query in QUERIES:
        if not query["filter"]:
            continue
        no_f = store.search(query["text"], top_k=TOP_K)
        with_f = store.search_with_filter(query["text"], top_k=TOP_K, metadata_filter=query["filter"])

        def answer_for(results: list[dict]) -> str:
            return extractive_llm("NGỮ CẢNH:\n" + "\n".join(r["content"] for r in results)
                                  + f"\n\nCÂU HỎI: {query['text']}\n\nTRẢ LỜI:")

        s_no, l_no, _ = score_query(no_f, query, answer_for(no_f))
        s_with, l_with, _ = score_query(with_f, query, answer_for(with_f))
        identical = [r["id"] for r in no_f] == [r["id"] for r in with_f]

        def fmt(results: list[dict]) -> list[str]:
            return [
                "{}({})".format(r["metadata"]["doc_id"][:22], r["metadata"]["customer_role"][:3])
                for r in results
            ]

        print(f"{query['id']} ({query['filter']}): {query['text'][:66]}")
        print(f"   KHÔNG filter [{l_no}] {s_no}/2đ: {fmt(no_f)}")
        print(f"   CÓ filter    [{l_with}] {s_with}/2đ: {fmt(with_f)}")
        if identical:
            print("   => HAI KẾT QUẢ GIỐNG HỆT NHAU: filter không thay đổi gì cho query này.")
        elif s_with > s_no:
            print(f"   => Filter CẢI THIỆN {s_no} -> {s_with} điểm.")
        elif s_with < s_no:
            print(f"   => Filter LÀM XẤU ĐI {s_no} -> {s_with} điểm (loại nhầm đáp án).")
        else:
            print("   => Filter đổi kết quả nhưng không đổi điểm.")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark retrieval trên corpus của nhóm.")
    parser.add_argument("--chunker", default="by_heading", choices=[*CHUNKERS, "all"])
    parser.add_argument("--baseline", action="store_true", help="In bảng baseline comparator")
    parser.add_argument("--ablation", action="store_true", help="In A/B metadata filter")
    parser.add_argument("--quiet", action="store_true", help="Chỉ in tổng kết")
    args = parser.parse_args()

    if not DATA_DIR.exists():
        print(f"Không tìm thấy thư mục dữ liệu: {DATA_DIR}")
        return 1

    print(f"Corpus: {DATA_DIR} | Embeddings: mock (hash-based, KHÔNG phản ánh ngữ nghĩa)")
    print(f"Bộ query: 5 câu khóa tại report/BENCHMARK_QUERIES.md | top_k={TOP_K}")
    print("Chấm ở MỨC CHUNK: chunk phải chứa chuỗi bằng chứng, không chỉ đúng doc_id.")

    if args.baseline:
        run_baseline()

    names = list(CHUNKERS) if args.chunker == "all" else [args.chunker]
    summary = {name: run_benchmark(name, show_detail=not args.quiet) for name in names}

    if len(names) > 1:
        print(f"\n{'=' * 96}")
        print("TỔNG HỢP SO SÁNH CHIẾN LƯỢC")
        print("=" * 96)
        print(f"{'Chiến lược':16} {'chunk':>6} {'dài TB':>7} {'doc@3':>7} {'evid@3':>7} "
              f"{'evid@1':>7} {'ground':>7} {'Điểm':>7}")
        print("-" * 96)
        for name, s in summary.items():
            print(f"{name:16} {s['size']:>6} {s['avg_len']:>7.0f} "
                  f"{s['doc_hit_3']:>5}/5 {s['ev_hit_3']:>5}/5 {s['ev_hit_1']:>5}/5 "
                  f"{s['grounded']:>5}/5 {s['score']:>5}/10")

    if args.ablation:
        run_ablation()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
