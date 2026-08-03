# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trương Minh Tâm — **MSSV:** 2A202602005
**Lớp:** K4 — Day07 Data Foundations (biến thể K4: chính sách TMĐT / hỗ trợ khách hàng)
**Nhóm:** [Tên nhóm]
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine đo **góc** giữa hai vector, không đo độ dài. Giá trị gần 1 nghĩa là hai vector chỉ về cùng một
> hướng trong không gian ngữ nghĩa — tức mô hình embedding "hiểu" hai đoạn văn bản nói về cùng một chuyện,
> bất kể chúng dài ngắn khác nhau hay dùng từ khác nhau. Gần 0 là không liên quan (vuông góc), gần −1 là
> ngược hướng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Thời gian hoàn tiền về ví ShopeePay là 24 giờ."
- Câu B: "Tiền sẽ được chuyển vào ví điện tử trong vòng một ngày."
- Tại sao tương đồng: cùng nói về **thời hạn chuyển tiền hoàn vào ví**, chỉ khác cách diễn đạt
  ("24 giờ" ↔ "một ngày", "ShopeePay" ↔ "ví điện tử"). Với embedding ngữ nghĩa, hai câu này phải gần nhau
  dù gần như không dùng chung từ nào.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Người bán cần thêm chi phí khi hàng hoàn bị thất lạc."
- Câu B: "Công thức tính diện tích hình tròn là pi nhân bán kính bình phương."
- Tại sao khác: khác hoàn toàn cả chủ đề lẫn miền tri thức — một bên là quy trình vận hành TMĐT, một bên là
  công thức hình học. Không có khái niệm nào chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì cosine **chuẩn hoá theo độ dài vector**, mà độ dài vector embedding thường tỉ lệ với độ dài văn bản chứ
> không phải mức độ liên quan. Nếu dùng Euclid, một đoạn dài và một câu ngắn nói **cùng một nội dung** vẫn bị
> coi là xa nhau chỉ vì độ lớn vector chênh lệch — trong RAG điều này rất tai hại vì các chunk có độ dài rất
> khác nhau. Cosine bỏ qua độ lớn và chỉ so hướng, nên so sánh được chunk dài với query ngắn một cách công bằng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Mỗi vòng lặp con trỏ `start` tiến một bước `step = chunk_size - overlap = 500 - 50 = 450`, nhưng lát cắt
> lấy ra dài `chunk_size = 500`. Chunk đầu phủ 500 ký tự, mỗi chunk sau phủ thêm 450 ký tự mới, nên:
> `n = 1 + ceil((10000 - 500) / 450) = 1 + ceil(21.11) = 1 + 22 = 23`.
> Viết gọn thành một công thức: `n = ceil((L - overlap) / (chunk_size - overlap)) = ceil(9950 / 450) = ceil(22.11)`.
>
> *Đáp án:* **23 chunks** (đã verify bằng `FixedSizeChunker(chunk_size=500, overlap=50).chunk("x"*10000)` → 23).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk **tăng** lên **25** (`ceil((10000-100)/(500-100)) = ceil(24.75) = 25`, đã verify bằng code): overlap
> lớn hơn làm `step` nhỏ lại nên `start` tiến chậm hơn, cần nhiều lát cắt hơn để phủ hết tài liệu. Ta chấp nhận
> đánh đổi này — tốn thêm token khi embed/truy vấn và tốn thêm dung lượng lưu trữ — để giảm rủi ro một câu hoặc
> một điều kiện quan trọng bị cắt đôi đúng ranh giới chunk, khiến không chunk nào chứa đủ ngữ cảnh trả lời.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi tách câu bằng `re.split(r"(?<=[.!?])\s+", text)`: dùng lookbehind `(?<=[.!?])` để **giữ lại** dấu
> câu ở cuối mỗi câu (nếu split trực tiếp trên `". "` thì dấu chấm bị nuốt mất), rồi `\s+` nuốt mọi khoảng
> trắng phía sau — bao gồm cả `\n`, nên không cần nhánh riêng cho xuống dòng. Sau đó `strip()` từng câu và
> lọc bỏ chuỗi rỗng để các dòng trống không bị tính thành câu.
>
> *Một lỗi tôi đã sửa:* bản đầu tôi viết `r"(?<=[.!?])\s+|\.\n"`. Nhánh `\.\n` vừa thừa (vì `\s+` đã khớp
> `\n`) vừa gây bug: với `"...end.\nNext..."`, `re.split` quét từ trái sang và tại vị trí dấu `.` nhánh
> `\.\n` khớp được ngay, trong khi nhánh lookbehind phải đợi đến vị trí *sau* dấu chấm. Alternation chọn
> nhánh khớp ở vị trí sớm hơn, nên cả `".\n"` bị nuốt làm delimiter và câu trước **mất dấu chấm** —
> đúng thứ mà lookbehind sinh ra để tránh. Kiểm chứng: regex cũ trả `'First sentence end'`, regex mới trả
> `'First sentence end.'`. Bộ test không bắt được lỗi này vì `SAMPLE_TEXT` không có ca chấm liền `\n`.
> Cuối cùng gộp theo lát cắt `range(0, len(sentences), limit)` — cách này tự xử lý nhóm cuối bị thiếu câu.
> Edge case: text rỗng trả `[]`, và text không có dấu câu nào vẫn trả về 1 chunk chứa toàn bộ text.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `chunk()` chỉ là wrapper: chặn text rỗng rồi gọi `_split(text, self.separators)`; toàn bộ đệ quy nằm trong
> `_split`. Thuật toán thử separator theo thứ tự ưu tiên (`"\n\n"` → `"\n"` → `". "` → `" "` → `""`): cắt text
> bằng separator hiện tại rồi **gom các mảnh lại** vào buffer chừng nào còn ≤ `chunk_size`, nhờ vậy giữ được
> ranh giới ngữ nghĩa thay vì cắt cứng giữa câu. Có ba base case: (1) text ngắn hơn `chunk_size` → trả về
> nguyên vẹn; (2) text rỗng → `[]`; (3) **hết separator** → cắt cứng theo `chunk_size`.
> Điểm dễ sai nhất mà tôi phải chú ý: mỗi lần đệ quy đều truyền `remaining_separators[1:]` chứ không phải danh
> sách cũ — nếu gọi lại `_split` với cùng text và cùng separator thì hàm lặp vô hạn. Trường hợp separator không
> cắt được gì (`len(pieces) == 1`) cũng phải hạ xuống separator kế tiếp vì lý do tương tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hoá thành một record dict qua `_make_record`: `{id, content, metadata, embedding,
> index}`, trong đó `embedding` được tính **một lần lúc nạp** (không tính lại khi search). Metadata được
> **copy** bằng `dict(doc.metadata or {})` chứ không gán tham chiếu — nếu gán thẳng, sửa metadata trong store
> sẽ vô tình sửa cả object `Document` gốc bên ngoài.
>
> `search()` chỉ là `self._search_records(query, self._store, top_k)`. Toàn bộ logic xếp hạng nằm trong
> helper `_search_records`: nhúng query **một lần trước vòng lặp**, tính `compute_similarity` với từng
> record, sort giảm dần rồi cắt `top_k`. Tôi cố ý tách helper này để `search_with_filter` dùng lại được
> nguyên vẹn — nhờ vậy hai đường tìm kiếm không bao giờ lệch nhau về cách tính điểm.
>
> Một lựa chọn có chủ ý: docstring gợi ý dùng **dot product**, nhưng tôi dùng **cosine**. Với `_mock_embed`
> thì hai cách cho kết quả giống nhau vì vector đã được chuẩn hoá sẵn (`src/embeddings.py:27-28`). Tuy nhiên
> `OpenAIEmbedder` (`src/embeddings.py:58-60`) **không** chuẩn hoá; nếu đổi backend, dot product sẽ thiên vị
> chunk dài. Dùng cosine để kết quả không phụ thuộc vào việc backend nào đang chạy.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc TRƯỚC, xếp hạng SAU.** Tôi lọc `self._store` giữ lại record khớp *toàn bộ* cặp key/value của
> `metadata_filter`, rồi mới đưa danh sách đã hẹp vào chính `_search_records` mà `search()` dùng. Làm ngược
> lại (lấy top-k rồi mới lọc) là bug thật chứ không chỉ chậm: nếu top-k toàn chunk sai vai thì kết quả trả về
> rỗng dù store vẫn còn tài liệu hợp lệ. Dùng chung một helper cũng đảm bảo `metadata_filter=None` cho kết
> quả giống hệt `search()` cùng `top_k`.
>
> `delete_document` lọc theo `metadata['doc_id']`. Điều này hoạt động cho cả hai đường nạp dữ liệu là nhờ
> `_make_record` dùng `metadata.setdefault("doc_id", doc.id)`: tài liệu thô (metadata rỗng) được suy `doc_id`
> từ chính `Document.id`, còn chunk đi qua `ingest.py` thì giữ nguyên `doc_id` của tài liệu cha mà ingest đã
> đặt. Nếu gán thẳng `metadata["doc_id"] = doc.id` thì chunk `x::chunk_0` sẽ mang `doc_id = "x::chunk_0"`,
> và `delete_document("x")` sẽ không gom được chunk nào — `setdefault` là điểm giao thỏa mãn cả hai.
>
> *Một chỗ tôi đã dọn:* bản đầu tôi viết điều kiện lọc kép `metadata['doc_id'] != doc_id and record['id'] !=
> doc_id`. Rà lại thì vế thứ hai là **dead code**: vì mọi record đều đã có `metadata['doc_id']`, tình huống
> `record['id']` khớp mà `metadata['doc_id']` không khớp chỉ xảy ra nếu ai đó tự truyền `metadata={"doc_id":
> "giá trị khác"}` — không có trong test lẫn pipeline. Tôi bỏ vế thừa để code khớp đúng docstring
> ("remove all stored chunks where metadata['doc_id'] == doc_id"); 42/42 test vẫn pass và smoke test trên
> corpus thật vẫn xóa đúng 5 chunk (129 → 124).
>
> Về `record['id']`: tôi giữ nguyên `id = doc.id` và để số thứ tự ở field `index` riêng. Lý do là để
> `record['id']` luôn truy ngược được về `Document.id` gốc khi debug, **không phải** vì `delete_document`
> cần — như trên, nó chỉ đọc `metadata['doc_id']`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `__init__` chỉ lưu tham chiếu `store` và `llm_fn`, không tính toán gì — mọi việc nặng để dành cho lúc gọi
> `answer()`. `answer()` theo đúng ba bước RAG: lấy top-k chunk → dựng prompt → gọi `llm_fn`.
>
> Ngữ cảnh được **đánh số `[1] [2] [3]` và gắn kèm `doc_id` nguồn** cho từng đoạn, thay vì nối thẳng các
> chunk thành một khối văn bản. Đây là phần tôi đầu tư nhất vì nó phục vụ tiêu chí **grounding** trong
> `docs/EVALUATION.md`: có đánh số thì mô hình mới trích dẫn được `[1]`, và người đọc mới truy ngược được
> câu trả lời về đúng tài liệu gốc. Prompt cũng nêu rõ hai ràng buộc: **chỉ dùng thông tin trong ngữ cảnh**
> và **nói rõ khi không đủ dữ kiện** — để hạn chế mô hình bịa khi retrieval trượt.
>
> Trường hợp store rỗng (hoặc filter loại hết ứng viên) thì trả về thông báo "không tìm thấy thông tin liên
> quan" và **không gọi `llm_fn`** — gọi LLM với ngữ cảnh rỗng vừa tốn tiền vừa gần như chắc chắn tạo ra câu
> trả lời bịa.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ .venv\Scripts\python.exe -m pytest tests -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\minht\K4-Day07-Data-2A202602005-TRUONGMINHTAM
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker (7 tests) PASSED
tests/test_solution.py::TestSentenceChunker (4 tests) PASSED
tests/test_solution.py::TestRecursiveChunker (4 tests) PASSED
tests/test_solution.py::TestEmbeddingStore (8 tests) PASSED
tests/test_solution.py::TestKnowledgeBaseAgent (2 tests) PASSED
tests/test_solution.py::TestComputeSimilarity (4 tests) PASSED
tests/test_solution.py::TestCompareChunkingStrategies (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument (3 tests) PASSED

============================= 42 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** **42** / 42

Chạy trong `.venv` Python 3.11.9 (môi trường chuẩn của lớp), không phải Python hệ thống.

**Demo đầu-cuối** (`main.py` đọc thư mục qua biến `LAB_DATA_DIR` — mặc định trong file trỏ tới
`data/k4_ecommerce` là bộ khởi động mẫu, nhóm tôi dùng corpus thật):

```
$ LAB_DATA_DIR=data/tra-hang-hoan-tien python main.py "Chunking là gì?"
Đã nạp 109 chunk vào EmbeddingStore
=== Tìm kiếm (EmbeddingStore.search) ===
1. score=0.304 source=data\tra-hang-hoan-tien\chinh-sach-tra-hang-hoan-tien.md
2. score=0.280 source=data\tra-hang-hoan-tien\chinh-sach-tra-hang-hoan-tien.md
3. score=0.276 source=data\tra-hang-hoan-tien\quan-ly-don-tra-hang-hoan-tien.md
=== KnowledgeBaseAgent === (prompt có ngữ cảnh đánh số [1][2][3] kèm doc_id nguồn)
```

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Dự đoán được viết **trước khi chạy code**. Cột "Dự đoán" ghi kỳ vọng với một embedding **ngữ nghĩa thật**;
cột "Thực tế" là điểm đo bằng `_mock_embed` (hash MD5) — chính sự lệch nhau giữa hai cột mới là điều đáng
phân tích.

| Cặp | Câu A | Câu B | Dự đoán (ngữ nghĩa) | Thực tế (mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Người mua được hoàn tiền trong bao lâu?" | "Sau bao lâu thì người mua nhận được tiền hoàn?" | **cao** (diễn đạt lại cùng câu hỏi) | **−0.0070** | ✗ (mock) |
| 2 | "Thời gian hoàn tiền về ví ShopeePay là 24 giờ." | "Tiền sẽ được chuyển vào ví điện tử trong vòng một ngày." | **cao** (cùng ý, khác từ) | **0.2104** | ✗ (mock) |
| 3 | "Người bán cần thêm chi phí khi hàng hoàn bị thất lạc." | "Công thức tính diện tích hình tròn là pi nhân bán kính bình phương." | **thấp** (khác miền hoàn toàn) | **0.1330** | ~ (thấp, nhưng...) |
| 4 | "Chính sách trả hàng và hoàn tiền của Shopee." | *(y hệt câu A)* | **1.0** (vector trùng nhau) | **1.0000** | ✓ |
| 5 | "Mã giảm giá sẽ được hoàn lại." | "Mã giảm giá **không** được hoàn lại." | **rất cao** (khác 1 từ, dù nghĩa ngược) | **0.0965** | ✗ (mock) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 2 (0.2104) lại cao hơn cặp 3 (0.1330)** — tức hai câu cùng nghĩa *đúng là* gần nhau
> hơn hai câu khác miền hoàn toàn. Nhưng khoảng cách giữa chúng chỉ **0.077**, quá nhỏ để tin cậy: cặp 1
> (hai câu gần như đồng nghĩa) lại về **−0.0070**, thấp hơn cả cặp 3 vốn chẳng liên quan gì. Nghĩa là thứ tự
> đúng ở cặp 2/3 chỉ là **ngẫu nhiên**, không phải do mô hình hiểu nghĩa.
>
> Lý do nằm ở bản chất `MockEmbedder`: nó băm MD5 chuỗi rồi sinh số giả ngẫu nhiên từ hạt giống đó
> (`src/embeddings.py:20-28`). MD5 có **hiệu ứng thác đổ** — đổi một ký tự thì toàn bộ digest đổi. Tôi kiểm
> chứng riêng: `"Chính sách trả hàng"` so với chính nó **thêm một dấu chấm** chỉ được **0.1623**. Vì vậy mock
> chỉ phân biệt được đúng một quan hệ: **trùng khớp tuyệt đối** (cặp 4 = 1.0) và **mọi thứ còn lại ≈ nhiễu
> quanh 0**.
>
> Cặp 5 là ví dụ sắc nhất về giới hạn *của cả embedding thật lẫn mock*, theo hai hướng ngược nhau. Với mock:
> 0.0965 — thêm chữ "không" làm digest đổi hoàn toàn. Với embedding ngữ nghĩa thật thì ngược lại, hai câu này
> sẽ **rất gần nhau** vì chỉ khác một từ phủ định — và đó mới là điều đáng lo cho RAG: hệ thống có thể truy
> xuất đúng chunk nhưng chunk đó nói **ngược lại** điều người dùng cần. Đây chính là lý do câu trả lời phải
> trích dẫn nguồn để người đọc tự kiểm chứng, chứ không thể tin vào điểm similarity.
>
> **Hệ quả trực tiếp cho bài này:** mọi số liệu retrieval ở mục 5 đều chạy trên mock, nên chúng **không đo
> được chất lượng ngữ nghĩa** của chiến lược chunking. Chúng chỉ đo được thứ mock vẫn phản ánh trung thực:
> tác dụng của **metadata filter** (lọc theo trường, không phụ thuộc embedding) và **kích thước/số lượng
> chunk**. Tôi giữ nguyên nhận định này khi đọc kết quả bên dưới thay vì diễn giải quá tay.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Chiến lược của tôi:** `SentenceChunker(max_sentences_per_chunk=3)` — 92 chunk.
**Lệnh chạy:** `python bench.py --chunker by_sentences` (bộ 5 query khóa tại `report/BENCHMARK_QUERIES.md`).
**Backend nhúng:** mock (xem cảnh báo ở mục 4 — điểm số không đo được chất lượng ngữ nghĩa).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua được hoàn tiền trong bao lâu sau khi gửi trả hàng? | `cam-nang-tra-hang-hoan-tien` — "Người mua cần cung cấp những bằng chứng gì?" | 0.2561 | ✗ (gold không có trong top-3) | Trả lời về bằng chứng khiếu nại, **không** nêu được mốc 24 giờ / 2 ngày / 7-14 ngày |
| 2 | Khi hàng hoàn trả bị thất lạc/hư hỏng trên đường về, ai chịu trách nhiệm và cần làm gì? | `quan-ly-don-giao-khong-thanh-cong` — "Hướng dẫn xử lý các đơn Shopee giao không thành công" | 0.1643 | ✓ **top-1 đúng**, cả top-3 đều gold | Nêu đúng nhánh seller: Thêm chi phí → đền bù từ Shopee |
| 3 | Những voucher/mã giảm giá nào không được hoàn lại khi trả hàng? | `chinh-sach-tra-hang-hoan-tien` — "Hạn mức còn lại của tháng trước không được cộng dồn" | 0.3040 | ~ (gold ở **hạng 3**) | Có chạm tới Shop Voucher nhưng hai chunk đầu lạc đề |
| 4 | Người bán xử lý đơn giao không thành công thế nào trên Kênh Quản Lý Shop? | `quan-ly-don-giao-khong-thanh-cong` — "Tính năng Quản lý đơn giao không thành công giúp shop theo dõi…" | 0.1771 | ✓ **top-1 đúng** | Nêu đúng hai nhánh: Nhập lại kho / Thêm chi phí |
| 5 | Người mua có bắt buộc phải gửi trả hàng để được hoàn tiền không? | `quy-trinh-xu-ly-yeu-cau-tra-hang` | — | ✓ **top-1 đúng** | Nêu được hai phương án: Hoàn Tiền Ngay / Trả hàng & Hoàn tiền |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4** / 5
(hit@1 = 3/5, hit@3 = 4/5 → điểm retrieval theo `docs/SCORING.md` = **7/10**)

### So sánh ba chiến lược trên cùng bộ query

Số liệu lấy từ `python bench.py --chunker all` (một lần chạy, đã kiểm tra tính lặp lại — xem ghi chú dưới).

| Chiến lược | Số chunk | Q1 | Q2 | Q3 | Q4 | Q5 | hit@1 | hit@3 | Điểm /10 |
|---|---|---|---|---|---|---|---|---|---|
| `fixed_size` (500/50) | 109 | hit@3 | **HIT@1** | MISS | hit@3 | **HIT@1** | 2/5 | 4/5 | 6 |
| **`by_sentences` (3 câu)** ← của tôi | **92** | MISS | **HIT@1** | hit@3 | **HIT@1** | **HIT@1** | **3/5** | **4/5** | **7** |
| `recursive` (500) | 129 | MISS | **HIT@1** | hit@3 | hit@3 | hit@3 | 1/5 | 4/5 | 5 |

**Cảnh báo khi đọc bảng này:** cả ba đều đạt hit@3 = 4/5, chênh lệch chỉ nằm ở hit@1. Với mock embeddings,
thứ hạng trong top-3 gần như là nhiễu (xem mục 4), nên **không** kết luận được `by_sentences` tốt hơn
`recursive`. Bảng này chỉ cho hai tín hiệu đáng tin: **Q2 đạt HIT@1 ở cả ba chiến lược** (nhờ metadata
filter, không phụ thuộc chunking) và **không chiến lược nào đạt trọn 5/5**.

> **Ghi chú về tính tái lập:** `_mock_embed` băm MD5 nên hoàn toàn tất định — chạy lại `bench.py` hai lần cho
> kết quả giống hệt từng câu. Nhưng chính vì vậy nó **cực kỳ nhạy với thay đổi nhỏ nhất trong chuỗi query**:
> bản nháp đầu tiên tôi gõ query **không dấu** ("Nguoi mua duoc hoan tien…") và nhận được kết quả khác hẳn
> cho `fixed_size` (Q1/Q5 từ hit thành miss). Đây là hệ quả trực tiếp của hiệu ứng thác đổ đã phân tích ở
> mục 4. Bài học: mọi số liệu báo cáo phải sinh từ **một nguồn query duy nhất** — ở đây là hằng số `QUERIES`
> trong `bench.py`, khóa theo `report/BENCHMARK_QUERIES.md` — chứ không gõ lại thủ công ở script nháp.

### Hai failure case tôi phân tích

**(1) Q1 — trượt ở hai trong ba chiến lược: truy vấn số liệu trên nội dung dạng bảng.**
Đáp án nằm trong bảng "phương thức thanh toán → thời gian hoàn tiền" của `thoi-gian-nhan-tien-hoan.md:22-95`.
Nhưng trang HTML gốc bị duỗi thành các dòng rời rạc khi crawl: "Ví ShopeePay" và "24 giờ" nằm cách nhau vài
dòng, không còn quan hệ hàng-cột. Với `by_sentences`, cả bảng gần như không có dấu câu nên bị gộp thành **3
chunk dài trung bình 1234 ký tự** (so với 456 của `fixed_size`) — dài gấp 2.5 lần `chunk_size` mong muốn,
làm loãng tín hiệu; đây là lý do `by_sentences` MISS còn `fixed_size` vẫn vớt được hit@3. Đó là giới hạn của
**chunking theo câu trên văn bản không có câu**, và là điểm yếu thật sự của chiến lược tôi chọn.

**(2) Q5 — top-1 bị chunk `role: both` chiếm chỗ khi không lọc.**
Ablation cho thấy khi **không** filter, top-3 của Q5 **toàn bộ là chunk `both`** từ
`chinh-sach-tra-hang-hoan-tien` (0/3 gold); bật filter `buyer` mới lôi được tài liệu buyer lên (1/3 gold).
Nguyên nhân: 60/129 chunk (**47%**) của corpus mang `role: both`, nên chúng áp đảo mọi truy vấn không lọc.
Chi tiết và ba hướng khắc phục ghi ở `report/BENCHMARK_QUERIES.md`.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(điền sau buổi demo)* — Điểm tôi muốn mang ra thảo luận: liệu nhóm khác có gặp cùng hiện tượng tài liệu
> "dùng chung" (`role: both`) làm hỏng metadata filter không, và họ gắn tag ở mức file hay mức chunk.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Khởi động (Warm-up) | 5 / 5 | Bài 1.1 có ví dụ cụ thể + giải thích cosine vs Euclid; bài 1.2 trình bày công thức, đáp án 23, đã verify bằng code (overlap=100 → 25) |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 | Giải thích đủ 5 phần; nêu được lựa chọn có chủ ý (cosine thay dot product) và 2 lỗi tự phát hiện — bug regex `\.\n`, dead code trong `delete_document` |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 | `pytest tests -v` → **42 passed** trong `.venv` Python 3.11.9 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | Dự đoán viết trước khi chạy; phân tích được nghịch lý cặp 2 vs 3 và hiệu ứng thác đổ của MD5 (kiểm chứng riêng: 0.1623) |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 | hit@1 = 3/5, hit@3 = 4/5 trên `by_sentences`; chấm theo `docs/SCORING.md` |
| **Tổng phần cá nhân** | **56 / 60** | |

> Tôi tự trừ điểm ở mục "Kết quả truy xuất" vì Q1 trượt ở **cả ba** chiến lược — đó là hạn chế thật của
> corpus (bảng HTML bị duỗi khi crawl) chứ không phải xui rủi, và tôi chưa kịp thử chunker theo heading để
> khắc phục.
