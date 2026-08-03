# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [A3.1]
**Thành viên:** Trương Minh Tâm — 2A202602005 (lớp K4)
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng.

**Phạm vi cụ thể nhóm tập trung:**
> Quy trình **Trả hàng / Hoàn tiền của Shopee**, thu thập song song **hai phía**: tài liệu dành cho Người mua
> (`help.shopee.vn`) và tài liệu dành cho Người bán (`banhang.shopee.vn/edu`), cộng một văn bản chính sách gốc
> áp dụng cho cả hai. Chọn phạm vi này vì cùng một sự kiện (một đơn hoàn) được mô tả bằng hai bộ quy tắc khác
> nhau tùy vai — đó là điều kiện cần để kiểm chứng giá trị thật của `metadata_filter`.

### Danh sách tài liệu (Data Inventory)

| # | doc_id | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | `customer_role` | `category` |
|---|--------|--------------------|----------------------|----------|-----------------|------------|
| 1 | `buyer-return-eligibility` | help.shopee.vn/portal/4/article/188931 | 2026-08-03 / not-stated | 6.205 | buyer | return-eligibility |
| 2 | `buyer-refund-timeline` | help.shopee.vn/portal/4/article/189473 | 2026-08-03 / not-stated | 3.690 | buyer | refund-timeline |
| 3 | `buyer-return-process` | help.shopee.vn/portal/4/article/190242 | 2026-08-03 / not-stated | 8.595 | buyer | return-process |
| 4 | `buyer-return-shipping` | help.shopee.vn/portal/4/article/189477 | 2026-08-03 / not-stated | 5.488 | buyer | return-shipping |
| 5 | `seller-return-process` | banhang.shopee.vn/edu/article/563 | 2026-08-03 / not-stated | 7.467 | seller | seller-response |
| 6 | `seller-refund-appeal` | banhang.shopee.vn/edu/article/3647 | 2026-08-03 / **2025-11-03** | 4.625 | seller | seller-appeal |
| 7 | `seller-return-evidence` | banhang.shopee.vn/edu/article/25057 | 2026-08-03 / **2025-06-02** | 7.846 | seller | return-evidence |
| 8 | `return-refund-policy` | help.shopee.vn/portal/4/article/77251 | 2026-08-03 / **2026-03-11** | 13.483 | both | general-policy |

**Tổng: 8 tài liệu** (yêu cầu 5–10), **57.399 ký tự**, đặt tại `data/tra-hang-hoan-tien/` kèm `sources.csv`.
Phân bố vai: 4 buyer · 3 seller · 1 both.

> **Lưu ý về hai bộ dữ liệu trong repo:** thư mục `data/corpus-canhan-v1/` là bộ tài liệu **bản đầu** (7 file
> crawl bằng `scripts/fetch_public_pages.py`, nội dung HTML bị duỗi thành text phẳng) — được giữ lại vì báo
> cáo cá nhân chạy benchmark trên bộ này. Bộ dùng cho báo cáo nhóm là `data/tra-hang-hoan-tien/` (8 file, giữ
> nguyên cấu trúc heading Markdown). Việc giữ cả hai cho phép so sánh trực tiếp ảnh hưởng của **chất lượng
> tiền xử lý dữ liệu** lên chiến lược chunk theo heading: cùng một chunker, bộ text phẳng không có `##` nào để
> cắt, còn bộ mới có 4–40 heading mỗi tài liệu.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa nguồn công khai và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated`) trong metadata.

**Ghi chú về quá trình thu thập — một nguồn đã bị loại:** nhóm ban đầu nhắm 3 trang Lazada, nhưng khi kiểm tra
thì cả ba đều redirect sang trang xác thực (`uac-pre.lazada.com`) dù `robots.txt` không cấm. Đây đúng là
trường hợp "giới hạn truy cập" mà `docs/DATA_COLLECTION.md` dặn không được cố vượt qua, nên nhóm **đổi nguồn**
thay vì tìm cách lách. Toàn bộ 8 tài liệu cuối cùng đều là trang tĩnh công khai, `robots.txt` cho phép.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | enum | `buyer` / `seller` / `both` | **Trường quyết định của bài.** Cùng một câu hỏi ("hàng hoàn có vấn đề thì làm gì?") có hai đáp án khác nhau tùy vai. Không lọc thì top-k lẫn lộn cả hai. |
| `category` | string | `refund-timeline`, `seller-appeal` | Thu hẹp theo *loại* thông tin (thời hạn / quy trình / bằng chứng), hữu ích khi corpus mở rộng và nhiều tài liệu cùng vai. |
| `document_version` | date/string | `2026-03-11`, `not-stated` | Chính sách TMĐT thay đổi theo thời điểm. 3/8 tài liệu có ngày hiệu lực rõ; giúp phát hiện khi hai tài liệu mâu thuẫn vì khác phiên bản. |
| `doc_id` | slug | `seller-refund-appeal` | Gom nhóm chunk theo tài liệu cha, phục vụ `delete_document()` và truy vết nguồn trong câu trả lời của agent. |
| `language` | string | `vi` | Dự phòng khi corpus có tài liệu song ngữ; hiện toàn bộ là `vi`. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `python bench.py --baseline` (`ChunkingStrategyComparator` trên phần body đã bỏ front matter qua
`ingest.parse_front_matter()` — dùng chung một đường parse với pipeline nạp dữ liệu để số liệu không lệch).

| Tài liệu | ký tự | `fixed_size` | `by_sentences` | `recursive` | `by_heading` |
|---|---|---|---|---|---|
| buyer-refund-timeline | 3.690 | 9 | 5 | 9 | **7** |
| buyer-return-eligibility | 6.205 | 14 | 12 | 17 | **12** |
| buyer-return-process | 8.595 | 19 | 26 | 23 | **16** |
| buyer-return-shipping | 5.488 | 13 | 21 | 15 | **9** |
| return-refund-policy | 13.483 | 30 | 35 | 40 | **31** |
| seller-refund-appeal | 4.625 | 11 | 26 | 12 | **12** |
| seller-return-evidence | 7.846 | 18 | 29 | 22 | **15** |
| seller-return-process | 7.467 | 17 | 25 | 20 | **13** |
| **Toàn corpus** | **57.399** | **131** (TB 485) | **179** (TB 319) | **158** (TB 362) | **115** (TB 497) |

**Đọc bảng này:** `by_heading` cho **ít chunk nhất nhưng dài nhất** — đúng kỳ vọng của một chiến lược cắt theo
ranh giới ngữ nghĩa thay vì theo độ dài. `by_sentences` ngược lại: 179 chunk ngắn (TB 319), vì tài liệu chính
sách có nhiều dòng liệt kê ngắn kết thúc bằng dấu chấm, mỗi 3 dòng thành một chunk rời rạc. Trường hợp
`seller-refund-appeal` lộ rõ nhất: 26 chunk `by_sentences` so với 12 chunk `by_heading` — gấp hơn hai lần.

### Chiến lược của từng thành viên

**Thành viên 1 — Trương Minh Tâm (2A202602005)**
- **Loại chiến lược:** **TV4 — Custom: chunk theo Markdown heading** (`##` / `###`), đáp ứng yêu cầu bắt buộc
  của K4 là có ít nhất một người chunk theo điều/khoản/heading.
- **Mô tả & lý do chọn cho chủ đề này:** Corpus là văn bản chính sách, mà chính sách được viết theo **điều
  khoản có đánh số** ("3.2. Thời gian tối đa…", "B.1. Trường hợp hoàn tiền ngay…"). Mỗi mục là một đơn vị ngữ
  nghĩa khép kín: nêu quy tắc, điều kiện áp dụng và ngoại lệ ngay cạnh nhau. Cắt theo độ dài cố định sẽ tách
  ngoại lệ ra khỏi quy tắc mà nó bổ nghĩa — đó chính là kiểu lỗi khiến RAG trả lời đúng chủ đề nhưng sai điều kiện.
- **Hai tinh chỉnh so với bản ngây thơ** (nếu thiếu thì chunker này hỏng ở đúng hai đầu):
  1. **Mục quá ngắn được gộp lên trước.** Heading cha như `## B. Quy trình Người bán khiếu nại` thường không
     có nội dung riêng, chỉ dẫn vào các mục con. Nếu không gộp sẽ sinh chunk chỉ có một dòng tiêu đề — vô dụng
     khi retrieval và làm nhiễu điểm số.
  2. **Mục quá dài được cắt tiếp bằng `RecursiveChunker`, nhưng gắn lại tiêu đề lên từng mảnh.** Mục
     `## 4. Danh sách sản phẩm hạn chế` dài hơn `chunk_size`; nếu cắt trần thì mảnh thứ hai mất hoàn toàn ngữ
     cảnh "đây là danh sách hạn chế cho lý do gì".
- **Code snippet:**
```python
class MarkdownHeadingChunker:
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)

    def __init__(self, chunk_size=1000, min_chunk_size=120, max_heading_level=3): ...

    def chunk(self, text: str) -> list[str]:
        sections = self._split_sections(text)          # [(dòng heading, phần thân)]
        merged = self._merge_short_sections(sections)  # gộp mục quá ngắn
        chunks = []
        for heading, body in merged:
            block = f"{heading}\n{body}".strip()
            if len(block) <= self.chunk_size:
                chunks.append(block)
                continue
            # Mục dài: cắt tiếp nhưng giữ tiêu đề trên từng mảnh
            for i, piece in enumerate(RecursiveChunker(chunk_size=self.chunk_size).chunk(body)):
                chunks.append(f"{heading}\n{piece}".strip() if heading and i else piece.strip())
        return [c for c in chunks if c]
```

> **Ghi chú về quy mô nhóm:** báo cáo này do một thành viên thực hiện, nên phần "so sánh giữa các thành viên"
> được thay bằng **so sánh 4 chiến lược trên cùng corpus và cùng 5 query** — cùng mục đích đối chứng, và số
> liệu dưới đây đều sinh từ một lần chạy `bench.py` duy nhất.

### So Sánh Giữa Các Chiến Lược

| Chiến lược | Số chunk | Dài TB | doc-hit@3 | **evidence-hit@3** | grounded | Điểm /10 | Điểm mạnh | Điểm yếu |
|-----------|----------|--------|-----------|--------------------|----------|----------|-----------|----------|
| `fixed_size` (500/50) | 131 | 485 | 3/5 | **0/5** | 0/5 | 0 | Có overlap nên thông tin ở ranh giới có 2 cơ hội lọt top-k | Cắt ngang bảng và giữa câu; 3/5 query "đúng tài liệu sai mục" |
| `by_sentences` (3 câu) | 179 | 319 | 2/5 | **0/5** | 0/5 | 0 | Chunk gọn, không cắt giữa câu | Chunk quá vụn trên văn bản liệt kê; bảng không có dấu câu bị gộp thành khối lớn |
| `recursive` (500) | 158 | 362 | 4/5 | **1/5** | **1/5** | **2** | Tôn trọng ranh giới đoạn/câu theo thứ tự ưu tiên | Không biết khái niệm "mục", vẫn tách điều kiện khỏi ngoại lệ |
| **`by_heading` (TV4)** | **115** | **497** | 2/5 | **1/5** | **1/5** | 1 | **Ít "sai mục" nhất (1/5)**; giữ trọn điều kiện + ngoại lệ trong một chunk | Mục dài vẫn phải cắt tiếp; heading không đảm bảo chứa từ khóa của query |

**Cột `grounded`** đo tiêu chí *Grounding* của rubric: câu trả lời của `KnowledgeBaseAgent` có thật sự mang
bằng chứng lấy từ context đã retrieve hay không. Để phép đo này trung thực, `bench.py` dùng một **LLM giả lập
kiểu trích xuất** (`extractive_llm`) chỉ được phép trả lại câu lấy nguyên văn từ phần NGỮ CẢNH của prompt —
nếu retrieval không đưa được câu chứa đáp án vào context thì agent **không thể** trả lời đúng, đúng bản chất
của RAG. Nhờ vậy `grounded` bám sát `evidence-hit@3` (1/5 ở hai chiến lược tốt nhất) thay vì bị thổi phồng bởi
một mô hình biết "đoán" đáp án từ kiến thức sẵn có.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Xét **điểm tuyệt đối** thì `recursive` cao nhất (2/10), nhưng đó **không** phải căn cứ đáng tin: với mock
> embeddings, chênh lệch 1–2 điểm nằm trong vùng nhiễu (xem mục 3). Căn cứ đáng tin hơn là **tỷ lệ "đúng tài
> liệu nhưng sai mục"**, vì nó đo trực tiếp chất lượng ranh giới chunk chứ không phụ thuộc mô hình nhúng:
> `by_heading` chỉ sai mục **1/5 query**, trong khi `fixed_size` và `recursive` đều sai **3/5**.
>
> Nói cách khác, `by_heading` là chiến lược **đưa được câu trả lời vào đúng một chunk** thường xuyên nhất —
> đúng thứ quyết định chất lượng RAG khi thay mock bằng embedding ngữ nghĩa thật. Nó cũng tiết kiệm nhất:
> 115 chunk cho cùng lượng nội dung, ít hơn `by_sentences` 36%, nghĩa là ít token phải nhúng và lưu trữ hơn.
> Điểm yếu thật của nó là phụ thuộc vào **chất lượng heading của nguồn**: corpus này có heading Markdown sạch
> nên chunker hoạt động; nếu crawl HTML thô bị duỗi thành text phẳng (như bản corpus đầu của nhóm) thì chiến
> lược này mất hoàn toàn tác dụng.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu Trả hàng/Hoàn tiền sau khi đơn giao thành công? Đơn thực phẩm tươi sống/đông lạnh có khác không? | Hầu hết đơn: **15 ngày** kể từ khi cập nhật "Giao hàng thành công". Riêng **thực phẩm tươi sống & đông lạnh** (trừ lý do Chưa nhận được hàng): **24 giờ**. Đơn Người bán tự vận chuyển: 15 ngày từ khi bấm "Đã nhận được hàng", hoặc 20 ngày từ "Lấy hàng thành công" nếu chưa bấm. | `buyer-return-eligibility` mục **1.2**; đối chiếu `return-refund-policy` Điều **3.2** |
| 2 | Tôi thanh toán bằng thẻ tín dụng/ghi nợ. Sau khi Shopee chấp nhận hoàn tiền, tiền về đâu và mất bao lâu? | Tiền hoàn về **đúng thẻ tín dụng/ghi nợ đã dùng** khi thanh toán. Thời gian: **7–14 ngày làm việc** (tùy ngân hàng). | `buyer-refund-timeline` **Bảng 1**, dòng "Thẻ tín dụng/ghi nợ" |
| 3 | Sau khi được chấp nhận Trả hàng/Hoàn tiền, Người mua có những hình thức gửi hàng hoàn nào? Hình thức nào miễn phí? | **3 hình thức:** (1) ĐVVC đến lấy hàng — **miễn phí**; (2) Trả hàng tại bưu cục — **miễn phí**; (3) **Tự sắp xếp** — người mua trả phí trước, Shopee hỗ trợ hoàn phí (Shopee Mall) hoặc hoàn Shopee Xu 25.000/40.000 tùy cùng hay khác tỉnh. Với Tự sắp xếp cần đăng tải bằng chứng trả hàng trên app. | `buyer-return-shipping` mục **1.1**; phí ở mục **2.2** |
| 4 | **(Seller + cần lọc metadata)** Khi Shopee quyết định hoàn tiền ngay (không yêu cầu trả hàng), Người bán có bao lâu để khiếu nại nếu không đồng ý? Shopee xử lý trong bao lâu? | Người bán phải khiếu nại **trong vòng 2 ngày** kể từ khi Shopee thông báo hoàn tiền ngay. Shopee xem xét trong **3–5 ngày làm việc**. Quá hạn có thể mất quyền khiếu nại theo quy trình này. | `seller-refund-appeal` mục **"Tổng quan thời hạn"** và mục **6**; hoặc `seller-return-process` phần **B.1** |
| 5 | Ai được trả hàng vì "đổi ý / không còn nhu cầu" (Trả hàng COM)? Có hạn chế sản phẩm nào không? | Từ **24/11/2025**, áp dụng cho Người mua hạng **Kim Cương, Vàng** hoặc đang dùng **Shopee VIP**. Sản phẩm phải còn nguyên tem/nhãn/bao bì, chưa qua sử dụng. Không áp dụng với **danh sách hạn chế trả hàng**, hàng **Shopee Mart**, và một số sản phẩm Shopee loại trừ theo thời điểm. | `buyer-return-eligibility` mục **1.3**; `return-refund-policy` Điều **4**; `seller-return-process` mục **A.3–A.4** |

**Độ phủ loại câu hỏi:** số liệu (Q1, Q2) · liệt kê (Q3) · quy trình + thời hạn (Q4) · điều kiện (Q5) ·
ngoại lệ (Q1 "trừ thực phẩm tươi sống", Q5 "danh sách hạn chế"). Q4 là query **bắt buộc cần lọc metadata**
theo `K4_VARIANT.md`.

### Cách chấm: mức CHUNK, không chỉ doc_id

Đây là quyết định phương pháp quan trọng nhất của nhóm. Nếu chỉ kiểm "doc_id gold có xuất hiện trong top-3
không", một chiến lược có thể chiếm trọn cả ba slot bằng đúng tài liệu gold mà **không chunk nào chứa câu trả
lời**. Vì vậy mỗi query khai báo thêm một **chuỗi bằng chứng** phải thực sự xuất hiện trong nội dung chunk:

| Query | Chuỗi bằng chứng bắt buộc |
|---|---|
| Q1 | `"24 giờ kể từ"` hoặc `"thực phẩm tươi sống"` |
| Q2 | `"7–14 ngày làm việc"` |
| Q3 | `"Trả hàng tại bưu cục (Miễn phí"` hoặc `"Tự sắp xếp"` |
| Q4 | `"2 ngày kể từ khi Shopee"` / `"trong vòng 2 ngày"` / `"3–5 ngày làm việc"` |
| Q5 | `"Kim Cương"` / `"hạng Vàng"` / `"danh sách hạn chế trả hàng"` |

### Tổng hợp chất lượng truy xuất của nhóm

Thang điểm theo `docs/SCORING.md` (2đ nếu chunk có bằng chứng đứng top-1, 1đ nếu nằm trong top-3, 0đ nếu không):

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk chứa **bằng chứng** trong top-3? | Agent trả lời đúng? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------------------|---------|
| 1 | Thời hạn gửi yêu cầu | *(không chiến lược nào)* | ✗ ở cả 4 | ✗ | `by_sentences`/`recursive` lấy đúng tài liệu nhưng sai mục |
| 2 | Hoàn tiền thẻ tín dụng | *(không chiến lược nào)* | ✗ ở cả 4 | ✗ | `fixed_size`/`recursive` lấy đúng `buyer-refund-timeline` nhưng trượt dòng bảng cần tìm |
| 3 | Hình thức gửi hàng hoàn | *(không chiến lược nào)* | ✗ ở cả 4 | ✗ | Query không filter — top-3 bị tài liệu seller chiếm chỗ |
| 4 | Thời hạn khiếu nại của người bán | **`recursive` (2đ — FULL)**, `by_heading` (1đ) | ✓ ở `recursive` và `by_heading` | **✓ ở `recursive`** | **Query duy nhất đạt điểm tối đa** — nhờ metadata filter |
| 5 | Ai được trả hàng COM | *(không chiến lược nào)* | ✗ ở cả 4 | ✗ | `by_heading` lấy đúng tài liệu nhưng sai mục |

**Một bài học về chính cách chấm:** lần chạy đầu, Q4 bị chấm 1đ vì chuỗi bằng chứng khai báo là
`"2 ngày kể từ khi Shopee"`, trong khi corpus diễn đạt cùng mốc đó theo hai cách — văn xuôi dùng
*"2 ngày kể từ khi Shopee gửi thông báo"*, còn bảng tóm tắt dùng *"Trong vòng 2 ngày"*. Agent đã trích đúng
dòng bảng và **trả lời đúng nội dung**, nhưng bị chấm là thiếu chỉ vì khác câu chữ. Sau khi khai báo cả hai
biến thể, Q4 đạt **FULL 2/2đ**. Điều này cho thấy chấm bằng chuỗi cứng vẫn có thể **chấm oan**: nó chặt hơn
doc_id nhưng phải bao được mọi cách diễn đạt của cùng một dữ kiện trong corpus.

**Chênh lệch giữa hai cách chấm — phát hiện đáng giá nhất của buổi lab:**

| Chiến lược | doc-hit@3 (chấm theo doc_id) | **evidence-hit@3 (chấm theo chunk)** | Chênh lệch |
|---|---|---|---|
| `fixed_size` | 3/5 | **0/5** | −3 |
| `by_sentences` | 2/5 | **0/5** | −2 |
| `recursive` | **4/5** | **1/5** | **−3** |
| `by_heading` | 2/5 | **1/5** | **−1** |

`recursive` chấm theo doc_id được **4/5** — trông gần như hoàn hảo. Chấm theo bằng chứng thật: **1/5**. Nếu
nhóm chỉ kiểm doc_id, con số báo cáo sẽ bị **thổi phồng gấp 4 lần**. Tổng cộng có **9/20 lượt chạy** rơi vào
tình trạng "đúng tài liệu nhưng sai mục". Nguyên nhân đúng như dự đoán: các mục trong cùng một tài liệu nói về
cùng chủ đề nên điểm cosine sát nhau, mục nào lọt top-3 gần như ngẫu nhiên — đặc biệt rõ với `by_heading`
(mọi chunk của cùng tài liệu đều mở đầu bằng heading giống dạng).

> **Điểm score cao là tín hiệu xếp hạng, không phải bằng chứng rằng nội dung đúng.** Q4 minh họa trực tiếp:
> chunk có score cao nhất (0.3242) là mục "5. Thông tin Người bán nên chuẩn bị" — **không chứa mốc thời gian
> nào**; chunk chứa đáp án ("6. Các mốc thời gian quan trọng") chỉ xếp thứ 2 với score thấp hơn (0.2515).

### Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?

Chạy `python bench.py --chunker by_heading --ablation` — A/B trên cả 3 query có filter:

| Query | Không filter (top-3) | Có filter (top-3) | Kết quả |
|---|---|---|---|
| **Q4** (seller) | `buyer-return-process`, `seller-refund-appeal`, `buyer-return-eligibility` → **0đ** | `seller-refund-appeal` ×2, `seller-return-evidence` → **1đ** | **Filter CẢI THIỆN 0 → 1** |
| Q1 (buyer) | `buyer-return-shipping`, `seller-return-evidence`, `return-refund-policy` → 0đ | 3 chunk buyer → 0đ | Đổi kết quả, không đổi điểm |
| Q2 (buyer) | `seller-refund-appeal`, `return-refund-policy`, `buyer-return-shipping` → 0đ | 3 chunk buyer → 0đ | Đổi kết quả, không đổi điểm |

**Kết luận trung thực:** metadata filter **có tác dụng thật nhưng chỉ ở một trong ba query**. Ở Q4, không lọc
thì 2/3 slot bị chunk **buyer** chiếm — hệ thống sẽ trả lời câu hỏi của người bán bằng quy trình dành cho
người mua, tức **sai vai hoàn toàn** dù mọi chunk đều "liên quan" về mặt từ khóa. Bật filter thì cả 3 slot đều
là seller và bằng chứng lọt vào top-3.

Ở Q1 và Q2 filter **có đổi kết quả** (loại được các chunk seller lạc đề) nhưng **không đổi điểm**, vì vấn đề ở
hai query này không phải nhiễu vai mà là **chunk chứa đáp án không được xếp hạng cao** — một lỗi thuộc về
embedding chứ không phải metadata. Đây là ranh giới rõ ràng: **filter sửa được nhiễu chéo vai, không sửa được
xếp hạng kém trong cùng vai.**

**Chi phí của filter — đánh đổi precision lấy recall:** **31/115 chunk (27%)** của corpus mang
`customer_role: both` (toàn bộ `return-refund-policy`). Vì `search_with_filter` so khớp chính xác từng cặp
key/value (`src/store.py:107`), giá trị `"both"` **không** khớp `"buyer"` lẫn `"seller"` — nên hơn một phần tư
kho tri thức bị vô hiệu hoá ở **mọi** filter theo vai, kể cả khi nội dung của nó đúng cho vai đang hỏi. Cụ
thể: Điều 5 "Quyền của Người Bán" (`return-refund-policy`) nêu đúng mốc **02 ngày lịch** mà Q4 cần, nhưng bị
`filter=seller` loại mất. Đây không phải ca lẻ mà là **hệ quả có hệ thống của việc gắn tag ở mức file thay vì
mức chunk**.

### Ba failure case có bằng chứng

**FC1 — Q4: chunk đúng chủ đề nhưng không chứa số liệu lại thắng chunk có đáp án** *(cosine đo độ giống chủ
đề, không đo mật độ thông tin trả lời được)*

- **Query:** "Khi Shopee quyết định hoàn tiền ngay…, bên bán có bao lâu để khiếu nại?"
- **Bằng chứng từ top-k** (`by_heading`, filter seller):

  | Hạng | Chunk | Score | Có bằng chứng? |
  |---|---|---|---|
  | 1 | `seller-refund-appeal` — "## 5. Thông tin Người bán nên chuẩn bị" | **0.3242** | ✗ |
  | 2 | `seller-refund-appeal` — "## 6. Các mốc thời gian quan trọng" | 0.2515 | **✓ chứa "2 ngày" + "3–5 ngày làm việc"** |
  | 3 | `seller-return-evidence` — "video đóng gói…" | 0.2434 | ✗ |

- **Nguyên nhân:** mục 5 liệt kê "lý do khiếu nại, thông tin đơn hàng, mã vận đơn…" — dày đặc từ vựng trùng
  với query ("khiếu nại", "Người bán"), nên cosine cao. Mục 6 là một bảng ngắn chỉ có cặp *nội dung → thời
  hạn*, ít từ trùng hơn dù chứa đúng con số cần tìm.
- **Thay đổi đề xuất:** với câu hỏi dạng "bao lâu", thêm một bước **rerank ưu tiên chunk chứa mẫu số + đơn vị
  thời gian** (regex `\d+\s*(ngày|giờ|tháng)`), hoặc chuyển sang embedding ngữ nghĩa thật thay mock.

**FC2 — Q2: top-3 đúng tài liệu nhưng sai section, và bảng bị tách khỏi tiêu đề dòng**

- **Query:** "Thanh toán bằng thẻ tín dụng/ghi nợ… tiền về đâu và mất bao lâu?" — gold là **một dòng** trong
  Bảng 1 của `buyer-refund-timeline`.
- **Bằng chứng:** với `fixed_size` và `recursive`, top-3 **có** `buyer-refund-timeline` nhưng là các mảnh khác
  của bảng (dòng ShopeePay, dòng SPayLater) chứ không phải dòng "Thẻ tín dụng/ghi nợ → 7–14 ngày làm việc".
  Với `by_heading`, top-3 thậm chí không có tài liệu này: `buyer-return-shipping` ×2 + `buyer-return-process`.
- **Nguyên nhân:** bảng 9 dòng nằm gọn trong một mục `## Bảng 1`, nên `by_heading` gộp cả bảng thành **một
  chunk lớn**; tín hiệu của dòng "thẻ tín dụng" bị pha loãng giữa 8 dòng phương thức khác. Ngược lại,
  `fixed_size` cắt bảng thành nhiều mảnh — mỗi thông tin chỉ có **một cơ hội** lọt top-k vì không có overlap
  ở mức dòng bảng.
- **Thay đổi đề xuất:** với nội dung dạng bảng, chunk **theo hàng** và **lặp lại dòng tiêu đề bảng** lên mỗi
  hàng (`| Phương thức | Gửi qua | Thời gian |` + hàng dữ liệu). Đây là mở rộng tự nhiên của TV4 và là việc
  nhóm sẽ làm đầu tiên nếu có thêm thời gian.

**FC3 — Q3: query không filter bị tài liệu sai vai chiếm trọn top-3**

- **Query:** "Người mua có những hình thức gửi hàng hoàn nào? Hình thức nào miễn phí?" — cố ý **không** đặt
  filter để làm đối chứng.
- **Bằng chứng** (`by_heading`): top-3 = `seller-refund-appeal` (0.2921), `return-refund-policy` (0.2647),
  `seller-return-process` (0.2599). **Hai trong ba là tài liệu dành cho người bán**, gold
  (`buyer-return-shipping`) không xuất hiện.
- **Nguyên nhân:** cụm "Trả hàng/Hoàn tiền" xuất hiện dày đặc ở **cả 8 tài liệu**, nên nó không mang thông tin
  phân biệt. Phần thực sự phân biệt của query là "hình thức gửi hàng" và "miễn phí" thì lại là từ hiếm, bị
  lấn át.
- **Thay đổi đề xuất:** query kiểu này đáng lẽ nên có `metadata_filter={"customer_role": "buyer"}`. Nhóm giữ
  nó không filter **có chủ đích** để chứng minh: khi corpus có hai vai nói cùng chủ đề, **không lọc là một lựa
  chọn tồi**, kể cả khi câu hỏi đã nêu rõ "Người mua". Về lâu dài nên suy ra filter từ chính câu hỏi thay vì
  bắt người dùng chỉ định.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Chấm theo doc_id thổi phồng kết quả gấp 4 lần.** `recursive` được 4/5 khi kiểm doc_id, còn 1/5 khi kiểm
   chunk có thật chứa đáp án. 9/20 lượt chạy là "đúng tài liệu, sai mục". Đây là bẫy dễ mắc nhất khi tự chấm
   một hệ RAG, và chỉ cần thêm một chuỗi bằng chứng cho mỗi query là phát hiện được.
2. **Score cao ≠ nội dung đúng.** Ở Q4, chunk score cao nhất (0.3242) không chứa mốc thời gian nào; chunk chứa
   đáp án xếp thứ 2 với score thấp hơn. Score là tín hiệu xếp hạng, không phải bằng chứng.
3. **Metadata filter sửa được nhiễu chéo vai, không sửa được xếp hạng kém trong cùng vai** — và nó có chi phí:
   27% corpus mang `role: both` bị loại ở mọi filter theo vai, kể cả khi nội dung đúng cho vai đang hỏi.
4. **Ngay cả cách chấm chặt hơn cũng có thể chấm oan.** Q4 lúc đầu bị trừ điểm chỉ vì corpus diễn đạt cùng một
   mốc thời gian theo hai cách khác nhau ("2 ngày kể từ khi Shopee gửi thông báo" vs "Trong vòng 2 ngày").
   Chuỗi bằng chứng phải bao được mọi biến thể câu chữ của cùng một dữ kiện, nếu không thì lại rơi vào lỗi
   ngược với lỗi doc_id: thay vì thổi phồng, nó dìm kết quả xuống.

**Bài học rút ra khi so sánh trong nhóm:**
> Bốn chiến lược chạy trên **cùng corpus và cùng 5 query** cho khoảng điểm rất sát nhau (0–2/10), nên xếp hạng
> theo điểm là vô nghĩa với mock embeddings. Chỉ số phân biệt được chúng lại là thứ **không phụ thuộc mô hình
> nhúng**: số chunk (115 với `by_heading` so với 179 của `by_sentences`) và tỷ lệ "đúng tài liệu nhưng sai
> mục" (1/5 so với 3/5). Bài học là **chọn chỉ số đo phù hợp với công cụ mình đang có** — nếu đo bằng thứ mà
> mock không phản ánh được, mọi kết luận đều là nhiễu.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> **Một:** gắn `customer_role` ở **mức chunk** thay vì mức file. `return-refund-policy` có Điều 5 rõ ràng dành
> cho người bán và Điều 6 dành cho người mua, nhưng cả file phải mang một nhãn `both` duy nhất — mất 27%
> corpus mỗi lần lọc. **Hai:** xử lý bảng riêng (chunk theo hàng, lặp tiêu đề cột), vì 2/5 query của nhóm có
> đáp án nằm trong bảng và cả hai đều trượt. **Ba:** chạy lại toàn bộ với `EMBEDDING_PROVIDER=local` để biết
> chiến lược nào thật sự tốt hơn — hiện tại nhóm chỉ có thể kết luận về *hình dạng chunk*, chưa kết luận được
> về *chất lượng truy xuất ngữ nghĩa*.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 | 8 tài liệu, hai phía buyer/seller có chủ đích, metadata đủ 5 trường + 3 tài liệu có ngày hiệu lực thật; đã loại nguồn Lazada vì bị chặn đăng nhập thay vì cố lách |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 | TV4 custom có 2 tinh chỉnh được giải thích bằng lý do cụ thể; so sánh 4 chiến lược trên baseline + benchmark. Trừ điểm vì nhóm chỉ có 1 thành viên nên thiếu đối chứng người-với-người |
| Chất lượng truy xuất (Retrieval Quality) | 6 / 10 | Chỉ 1/5 query đạt điểm với mock embeddings. Tự trừ vì kết quả thật sự thấp — nhưng phương pháp chấm (mức chunk + A/B filter + 3 failure case có bằng chứng top-k) là đầy đủ |
| Thuyết trình (Demo) | 4 / 5 | 3 insight có số liệu hậu thuẫn; chưa demo trực tiếp trước lớp tại thời điểm viết báo cáo |
| **Tổng phần nhóm** | **32 / 40** | |
