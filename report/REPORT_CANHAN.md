# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trương Minh Tâm — **MSSV:** 2A202602005
**Lớp:** K4 — Day07 Data Foundations (biến thể K4: chính sách TMĐT / hỗ trợ khách hàng)
**Nhóm:** [E2]
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

**`MarkdownHeadingChunker.chunk` / `_split_sections` / `_merge_short_sections`** — chunker TV4 tôi tự viết
(ngoài yêu cầu bắt buộc của bộ test, phục vụ phần benchmark):
> Corpus là văn bản chính sách viết theo **điều khoản có đánh số**, mỗi mục là một đơn vị ngữ nghĩa khép kín
> (quy tắc + điều kiện + ngoại lệ nằm cạnh nhau). Tôi tách bằng `re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)`
> và chỉ nhận heading cấp ≤ 3 — cấp sâu hơn (`####`) thường là chi tiết của cùng một quy tắc, tách ra sẽ vụn.
>
> Hai chỗ mà bản ngây thơ sẽ hỏng, tôi xử lý riêng:
> 1. **Mục quá ngắn** (`< min_chunk_size`) được gộp vào mục kế tiếp. Heading cha như `## B. Quy trình khiếu nại`
>    thường không có nội dung riêng; nếu không gộp sẽ sinh chunk chỉ chứa một dòng tiêu đề.
> 2. **Mục quá dài** được hạ xuống `RecursiveChunker`, nhưng **gắn lại dòng tiêu đề lên từng mảnh con**. Đây là
>    chi tiết dễ bỏ sót nhất: nếu cắt trần, mảnh thứ hai trở đi mất hoàn toàn ngữ cảnh "đây là mục nào".
>
> Tôi viết class mới thay vì sửa chunker có sẵn để **không phá contract** của bộ test — 42/42 vẫn pass sau khi
> thêm. Class được export trong `src/__init__.py` và đăng ký vào `bench.py` dưới tên `by_heading`.

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

**Demo đầu-cuối** (`main.py` chạy trọn pipeline: ingest → chunk → store → search → agent):

```
$ python main.py "Chunking là gì?"
=== Demo pipeline nạp dữ liệu (ingest.build_knowledge_base) ===
Thư mục dữ liệu: data/data-nhom
Backend nhúng: mock embeddings fallback
Đã nạp 131 chunk vào EmbeddingStore

=== Tìm kiếm (EmbeddingStore.search) ===
Câu hỏi: Chunking là gì?
1. score=0.365 source=data\data-nhom\buyer-return-eligibility.md
2. score=0.334 source=data\data-nhom\seller-return-evidence.md
3. ...
=== KnowledgeBaseAgent === (prompt có ngữ cảnh đánh số [1][2][3] kèm doc_id nguồn)
```

*(Câu hỏi demo "Chunking là gì?" cố tình nằm ngoài miền của corpus — corpus là chính sách trả hàng, không có
tài liệu nào nói về chunking. Kết quả top-3 vì vậy đều không liên quan, đúng như kỳ vọng: đây là phép thử
đường ống chạy được từ đầu đến cuối, không phải phép thử chất lượng truy xuất.)*

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

**Chiến lược của tôi:** `MarkdownHeadingChunker(chunk_size=1000, min_chunk_size=120)` — chunker **TV4 tự viết**,
cắt theo tiêu đề Markdown (`##` / `###`). Sinh **115 chunk**, độ dài trung bình **497 ký tự**.
**Lệnh chạy:** `EMBEDDING_PROVIDER=local python bench.py --chunker by_heading` (corpus nhóm
`data/data-nhom/`, 5 query khóa tại `report/REPORT_NHOM.md` mục 3 — **dùng chung với cả nhóm**).
**Backend nhúng:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều, chạy offline).
Tôi chạy **cả hai** backend; bảng chính là local, đối chứng mock ở cuối mục.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Score | Có liên quan? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn gửi yêu cầu THHT? Thực phẩm tươi sống có khác? | `buyer-return-eligibility` — "Thời gian để Shopee tiếp nhận yêu cầu…" | **0.7539** | ✓ **hạng 1 có bằng chứng** | Nêu đúng "**24 giờ** kể từ lúc đơn cập nhật Giao hàng thành công" cho thực phẩm tươi sống → **CÓ grounding** |
| 2 | Thẻ tín dụng/ghi nợ: tiền về đâu, bao lâu? | `buyer-refund-timeline` — "\| Phương thức thanh toán \| Tiền hoàn trả được gửi qua \|…" | 0.7185 | ~ **hạng 1 là bảng** nhưng agent không trích đúng dòng | Trả về quy tắc "hoàn về đúng thẻ đã dùng", **không nêu 7–14 ngày làm việc** → thiếu grounding |
| 3 | Có những hình thức gửi hàng hoàn nào? Cái nào miễn phí? | `return-refund-policy` — "# Chính sách Trả hàng và Hoàn tiền ## 1. Đối tượng…" | 0.6355 | ~ gold ở **hạng 3** (`buyer-return-shipping`, 0.6159) | Trả về quy định hoàn phí, không liệt kê đủ 3 hình thức → thiếu grounding |
| 4 | Người bán có bao lâu để khiếu nại hoàn tiền ngay? | `seller-return-process` — "### 4. Mốc thời gian Người bán có thể khiếu nại" | **0.8705** | ~ **hạng 2** mới chứa đáp án (`seller-refund-appeal`, 0.8687) | "Người bán phải gửi khiếu nại **trong vòng 2 ngày** kể từ khi Shopee gửi thông báo" → **CÓ grounding**, đúng đáp án |
| 5 | Ai được trả hàng vì đổi ý? Hạn chế sản phẩm nào? | `seller-return-process` — "### 2. Các lý do Trả hàng/Hoàn tiền" | 0.5729 | ✗ đúng tài liệu (cả 3 hạng) nhưng **sai mục** | Trả về định nghĩa "Trả hàng COM", không nêu Kim Cương/Vàng/VIP → thiếu grounding |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4** / 5 (chấm ở mức chunk)

Chỉ số đầy đủ: `doc-hit@3 = 5/5` · `evidence-hit@3 = 4/5` · `evidence-hit@1 = 2/5` · `grounded = 2/5` →
**điểm retrieval = 5/10** theo `docs/SCORING.md`.

### So sánh với ba chiến lược còn lại (cùng corpus, cùng 5 query, cùng embedder local)

| Chiến lược | Số chunk | Dài TB | doc@3 | evid@3 | **evid@1** | grounded | Điểm /10 |
|---|---|---|---|---|---|---|---|
| `fixed_size` (500/50) | 131 | 485 | 5/5 | 4/5 | **3/5** | 2/5 | 6 |
| **`by_sentences` (3 câu)** | 179 | 319 | **5/5** | **5/5** | **3/5** | **3/5** | **8** |
| `recursive` (500) | 158 | 362 | 4/5 | 3/5 | 2/5 | 3/5 | 5 |
| **`by_heading` (của tôi)** | **115** | **497** | **5/5** | 4/5 | 2/5 | 2/5 | 5 |

**Nhận xét riêng của tôi về kết quả này.** Chiến lược của tôi **không** đứng đầu (5/10 so với 8/10 của
`by_sentences`), và điều đáng nói là **tôi đã dự đoán ngược**. Tôi kỳ vọng `by_heading` thắng vì văn bản
chính sách viết theo điều khoản, cắt theo heading thì giữ được *quy tắc + điều kiện + ngoại lệ* trong một
chunk. Lập luận đó đúng về cấu trúc dữ liệu nhưng **bỏ sót cơ chế xếp hạng** — và đây là điều tôi học được
nhiều nhất từ bài này.

**Vì sao tôi thua, đọc từ chính số liệu của mình:**

- `by_heading` đạt **doc@3 = 5/5** — ngang `by_sentences`, tức nó **tìm đúng tài liệu ở cả 5 query**. Ranh
  giới chunk theo heading hoạt động đúng như thiết kế.
- Nhưng **evid@1 chỉ 2/5** (so với 3/5) và evid@3 là 4/5 (so với 5/5). Nghĩa là chunk chứa đáp án **có** lọt
  top-3 nhưng thường xếp hạng 2–3 chứ không phải hạng 1.
- Nguyên nhân là **pha loãng tín hiệu**: cosine so sánh vector *trung bình hoá* của cả chunk. Chunk của tôi
  dài TB 497 ký tự và chứa nhiều ý trong cùng một mục; câu chứa đáp án bị trung bình hoá cùng các câu khác.
  Chunk `by_sentences` chỉ 319 ký tự nên tín hiệu đậm đặc hơn.
- Q3 minh hoạ rõ nhất: gold `buyer-return-shipping` bị đẩy xuống **hạng 3** (0.6159), hai slot đầu là
  `return-refund-policy` — văn bản chính sách gốc dài nhất, dùng ngôn ngữ bao quát nên "giống mọi query một
  cách chung chung". Với `by_sentences`, chính gold đó lên hạng 1 và đạt FULL 2đ.

**Điều tôi vẫn bảo lưu:** `by_heading` **ít chunk nhất (115 so với 179)** — tiết kiệm **36% token** phải
nhúng và lưu trữ cho cùng lượng nội dung, và khi chunk lọt top-k thì người đọc thấy trọn cả mục kèm ngoại lệ
thay vì 3 câu rời rạc. Đây là đánh đổi thật giữa *chi phí + khả năng đọc hiểu* và *độ chính xác xếp hạng*,
không phải một chiến lược thua toàn diện. **Cách sửa cụ thể tôi sẽ làm nếu có thêm thời gian:** hạ
`chunk_size` từ 1000 xuống ~350 để giữ ranh giới heading *và* có mật độ tín hiệu của chunk ngắn — cơ chế cắt
tiếp mục dài kèm gắn lại tiêu đề đã có sẵn trong `MarkdownHeadingChunker`, chỉ cần đổi tham số.

### Đối chứng mock vs local — vì sao tôi phải chạy lại toàn bộ

Vòng phân tích đầu tiên tôi chạy bằng `_mock_embed` và kết luận **ngược hẳn**:

| Chiến lược | Điểm (mock) | Điểm (local) |
|---|---|---|
| `fixed_size` | 0/10 | **6/10** |
| `by_sentences` | **0/10** | **8/10** ⬆ |
| `recursive` | **2/10** ⬅ *(cao nhất)* | 5/10 |
| `by_heading` (của tôi) | 1/10 | 5/10 |

Với mock, `recursive` đứng đầu và `by_sentences` đứng **chót**; với local, hai chiến lược này **hoán đổi vị
trí chính xác**. Nếu tôi nộp báo cáo chỉ dựa trên mock, kết luận "recursive tốt nhất" sẽ sai hoàn toàn — đúng
như cảnh báo tôi tự viết ở mục 4 rằng mock chỉ phân biệt được *trùng khớp tuyệt đối*. Bài học phương pháp:
**embedder là nền của mọi phép đo, không phải tham số tinh chỉnh sau cùng.** Phải chọn embedder gần với môi
trường thật *trước*, rồi mới benchmark chiến lược chunk.

Một chi tiết đáng chú ý: `recursive` là chiến lược **duy nhất không cải thiện doc@3** (4/5 → 4/5). Điểm mock
cao của nó đến từ **may mắn về độ dài chunk**, không phải chất lượng ranh giới — và may mắn đó không chuyển
thành lợi thế khi có ngữ nghĩa thật.

### Hai failure case tôi phân tích

Cả hai đều lấy từ lần chạy **embedding local** — tức là các lỗi này **vẫn còn** sau khi đã thay mock bằng mô
hình ngữ nghĩa thật, nên chúng là lỗi của *thiết kế chunk*, không phải của embedder.

**(1) Q4 — chunk đúng chủ đề nhưng không chứa số liệu lại thắng chunk có đáp án.**

| Hạng | Chunk | Score | Chứa bằng chứng? |
|---|---|---|---|
| 1 | `seller-return-process` — "### 4. Mốc thời gian Người bán có thể khiếu nại" | **0.8705** | ✗ |
| 2 | `seller-refund-appeal` — "### Thời hạn khiếu nại" | 0.8687 | **✓ "trong vòng 2 ngày"** |
| 3 | `seller-return-process` — "Shopee có thể quyết định hoàn tiền ngay…" | 0.8461 | **✓** |

*Nguyên nhân:* chunk hạng 1 có **tiêu đề trùng gần như từng chữ với query** ("mốc thời gian", "khiếu nại"),
nên cosine cao nhất — nhưng phần thân chỉ dẫn chiếu sang mục khác chứ không nêu con số nào. Đây là minh chứng
trực tiếp cho câu **"score cao là tín hiệu xếp hạng, không phải bằng chứng nội dung đúng"**, và nó **sắc hơn
với embedding thật**: chênh lệch giữa hạng 1 và hạng 2 chỉ **0.0018** — nhỏ hơn cả sai số làm tròn, tức thứ
tự giữa chúng gần như ngẫu nhiên. Một chunk vô dụng và một chunk có đáp án được mô hình coi là *giống query
ngang nhau*.
*Điều tôi học được:* loại lỗi này **embedding tốt hơn không sửa được** — chunk hạng 1 *thật sự* nói về đúng
chủ đề, nó chỉ không chứa dữ kiện. Cần tín hiệu bổ sung ngoài ngữ nghĩa.
*Thay đổi đề xuất:* với câu hỏi dạng "bao lâu", thêm bước rerank ưu tiên chunk chứa mẫu **số + đơn vị thời
gian** (regex `\d+\s*(ngày|giờ|tháng)`).

**(2) Q5 — top-3 đúng tài liệu nhưng sai section (điểm yếu riêng của chunker theo heading).**

Top-3 (`by_heading`, không filter): `seller-return-process` mục **2. Các lý do Trả hàng/Hoàn tiền** (0.5729,
đúng tài liệu — sai mục), `return-refund-policy` mục **3. Điều kiện yêu cầu** (0.5303), `buyer-return-eligibility`
— "Bạn có thể yêu cầu Trả hàng/Hoàn tiền trong các trường hợp sau" (0.5275, đúng tài liệu — sai mục). Đáp án
thật ("Kim Cương", "hạng Vàng") nằm ở `buyer-return-eligibility` mục **1.3** và `seller-return-process` mục
**A.3–A.4**. **MISS 0/2đ** — trong khi `fixed_size` và `by_sentences` đều lấy được 1đ.

*Nguyên nhân:* đây đúng là hiện tượng đề bài cảnh báo với chunker theo heading — **mọi mục trong cùng tài
liệu đều nói về Trả hàng/Hoàn tiền nên điểm sát nhau** (0.5729 / 0.5303 / 0.5275, chênh nhau chưa tới 0.05),
mục nào lọt top-3 gần như ngẫu nhiên. Đáng chú ý: đây là query có **score thấp nhất toàn benchmark** — dấu
hiệu cho thấy không chunk nào thật sự khớp, vì bằng chứng bị **rải ở 3 tài liệu khác nhau** và mỗi chỗ chỉ
nhắc thoáng qua "Kim Cương/Vàng". Thêm nữa, `by_heading` **không có overlap**: mỗi thông tin chỉ có **một cơ
hội duy nhất** lọt top-k, không như `fixed_size` có 50 ký tự chồng lấn — và đó chính là lý do `fixed_size`
lấy được điểm ở query này còn tôi thì không.
*Thay đổi đề xuất:* thêm overlap ở mức mục (gắn 1–2 câu cuối của mục trước vào đầu mục sau), hoặc **prepend
chuỗi heading cha** (`# Tài liệu > ## Mục A > ### Mục A.3`) vào mỗi chunk để embedding phân biệt được các mục
cùng tài liệu thay vì chỉ thấy chúng "cùng nói về trả hàng".

**Điều hay nhất tôi học được từ thành viên nhóm (qua demo):**
> **Từ TV1 (`fixed_size`) — overlap có giá trị thật mà tôi đã đánh giá thấp.** Tôi từng coi cắt theo độ dài cố
> định là chiến lược "ngây thơ" nhất, nhưng nó về **nhì (6/10)** và đạt `evidence-hit@1 = 3/5` — cao hơn tôi
> (2/5). Lý do là **overlap 50 ký tự**: mỗi thông tin nằm ở ranh giới có hai cơ hội lọt top-k. Chunker của tôi
> **không có overlap**, và đó chính xác là lý do tôi MISS ở Q5 trong khi TV1 lấy được điểm. Đây là bài học cụ
> thể tôi sẽ áp dụng ngay: thêm overlap ở mức mục cho `MarkdownHeadingChunker`.
>
> **Từ TV2 (`by_sentences`) — chunk ngắn thắng chunk "đúng cấu trúc".** Tôi tối ưu cho *ranh giới ngữ nghĩa
> đúng*, TV2 tối ưu cho *chunk ngắn*, và TV2 thắng (8/10 so với 5/10). Điều này buộc tôi nhìn lại một giả định
> nền: retrieval **không thưởng cho chunk có cấu trúc đẹp, nó thưởng cho chunk có tín hiệu đậm đặc**. Hai mục
> tiêu đó không trùng nhau như tôi tưởng — và tôi chỉ nhận ra khi thấy số liệu của TV2 đặt cạnh của mình.
>
> **Từ TV3 (`recursive`) — bài học về việc tin số liệu của chính mình.** Với mock, TV3 đứng đầu; với local,
> TV3 chót bảng. Nếu cả nhóm chỉ chạy mock rồi kết luận, chúng tôi đã trao "quán quân" cho chiến lược thực ra
> kém nhất. Đây là lý do tôi tin phần giá trị nhất của bài này không phải điểm số, mà là việc **biết số liệu
> của mình đáng tin tới đâu**.
>
> *(Điểm muốn mang ra thảo luận với nhóm khác sau demo)* — liệu nhóm khác có gặp cùng hiện tượng tài liệu
> "dùng chung" (`role: both`) làm hỏng metadata filter không, và họ gắn tag ở mức file hay mức chunk.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Khởi động (Warm-up) | 5 / 5 | Bài 1.1 có ví dụ cụ thể + giải thích cosine vs Euclid; bài 1.2 trình bày công thức, đáp án 23, đã verify bằng code (overlap=100 → 25) |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 | Giải thích đủ 5 phần; nêu được lựa chọn có chủ ý (cosine thay dot product) và 2 lỗi tự phát hiện — bug regex `\.\n`, dead code trong `delete_document` |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 | `pytest tests -v` → **42 passed** trong `.venv` Python 3.11.9 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | Dự đoán viết trước khi chạy; phân tích được nghịch lý cặp 2 vs 3 và hiệu ứng thác đổ của MD5 (kiểm chứng riêng: 0.1623) |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 | `doc-hit@3 = 5/5`, `evidence-hit@3 = 4/5`, `grounded = 2/5` trên `by_heading` với embedding local; chấm mức chunk theo `docs/SCORING.md`; có đối chứng mock/local và 2 failure case có bằng chứng top-k |
| **Tổng phần cá nhân** | **57 / 60** | |

> **Về mục "Kết quả truy xuất":** chiến lược của tôi được 5/10, thấp hơn `by_sentences` (8/10). Tôi vẫn tự
> chấm 8/10 cho *mục báo cáo* này — không phải cho điểm benchmark — vì thứ đề bài yêu cầu ở đây là **phân
> tích kết quả**, và phần có giá trị nhất lại đến từ việc tôi **dự đoán sai**: tôi đã tin chunk theo heading
> sẽ thắng vì nó giữ được cấu trúc điều khoản, nhưng bỏ qua rằng cosine trung bình hoá cả chunk nên chunk
> càng dài thì tín hiệu càng loãng. Chỉ chạy benchmark thật mới phát hiện ra, và tôi truy được nguyên nhân
> đến tận cơ chế (`doc@3 = 5/5` nhưng `evid@1 = 2/5` — tìm đúng tài liệu, sai thứ hạng trong tài liệu).
>
> Tôi giữ cách chấm ở **mức chunk** thay vì `doc_id`, dù `doc_id` cho tôi 5/5 nghe đẹp hơn nhiều: chunk đúng
> tài liệu nhưng sai mục thì agent vẫn không trả lời được. Chính khoảng cách giữa hai cách chấm này (5/5 so
> với 4/5, và tệ hơn nhiều khi chạy mock: 2/5 so với 1/5) là phát hiện tôi thấy đáng giá nhất.
