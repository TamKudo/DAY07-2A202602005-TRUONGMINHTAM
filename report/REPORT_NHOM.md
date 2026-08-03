# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [E2]
**Thành viên (5):**
Trần Văn Toàn - 2A202601218 (TV1)
Phạm Hải Yến - 2A202601152 (TV2)
Trần Hoàng Khôi - 2A202601778 (TV3)
Trương Minh Tâm — 2A202602005 (TV4) ·
Trần Minh Hiển-2A202601812 (TV5)
 — lớp D303 K4
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

**Tổng: 8 tài liệu** (yêu cầu 5–10), **57.399 ký tự phần thân** (59.600 kể cả front matter), đặt tại
`data/data-nhom/` kèm `sources.csv`. Phân bố vai: **4 buyer · 3 seller · 1 both**.

**Đọc bảng inventory — bốn đặc điểm định hình toàn bộ kết quả benchmark về sau:**

1. **Cân bằng hai vai là có chủ đích, không ngẫu nhiên.** 4 buyer / 3 seller là điều kiện cần để `metadata_filter`
   có gì để lọc. Nếu corpus lệch hẳn một phía (ví dụ 7 buyer / 1 seller), query seller sẽ không có đủ tài liệu
   cạnh tranh và phép đo A/B filter ở mục 3 trở nên vô nghĩa.
2. **Độ dài lệch nhau 3,7 lần** — `buyer-refund-timeline` chỉ 3.690 ký tự, `return-refund-policy` tới 13.483.
   Tài liệu dài nhất chiếm **23% toàn corpus** và mang nhãn `both`, nên nó vừa là nguồn quan trọng nhất vừa là
   nguồn bị filter loại nhiều nhất (xem chi phí filter ở mục 3).
3. **Mật độ heading rất khác nhau**, quyết định chiến lược `by_heading` hoạt động tốt tới đâu ở từng tài liệu:

   | doc_id | ký tự | heading (h1–h3) | ký tự / heading | dòng bảng |
   |---|---|---|---|---|
   | `buyer-refund-timeline` | 3.690 | 5 | 738 | **11** |
   | `buyer-return-eligibility` | 6.205 | 9 | 690 | **15** |
   | `buyer-return-process` | 8.595 | 13 | 661 | 5 |
   | `buyer-return-shipping` | 5.488 | 10 | 549 | 0 |
   | `return-refund-policy` | 13.483 | **41** | **329** | 0 |
   | `seller-refund-appeal` | 4.625 | 14 | 330 | 10 |
   | `seller-return-evidence` | 7.846 | 13 | 604 | 9 |
   | `seller-return-process` | 7.467 | 14 | 533 | **13** |

   `return-refund-policy` có 41 heading (văn bản pháp lý đánh số điều khoản dày đặc) nên chunk theo heading rất
   mịn; ngược lại `buyer-refund-timeline` chỉ có 5 heading cho 3.690 ký tự — mỗi mục trung bình 738 ký tự, quá
   dài để giữ tín hiệu tìm kiếm sắc nét. **Đây chính là tài liệu chứa đáp án Q2, và Q2 là query không chiến
   lược nào đạt điểm tối đa.**
4. **63 dòng bảng Markdown nằm rải ở 6/8 tài liệu.** Nội dung dạng bảng (phương thức thanh toán → thời gian
   hoàn tiền, lý do trả hàng → điều kiện áp dụng) là **điểm yếu chung của cả bốn chiến lược chunk**: không
   chiến lược nào trong `src/chunking.py` hiểu khái niệm "hàng của bảng". Nhóm nhận ra điều này khi phân tích
   failure case FC2, và ghi lại thành đề xuất cải tiến ở mục 4.

> **Nhận xét về `document_version`:** chỉ **3/8 tài liệu** công bố ngày hiệu lực (`2026-03-11`, `2025-11-03`,
> `2025-06-02`); 5 tài liệu còn lại ghi `not-stated` vì trang nguồn **không nêu**. Nhóm chọn ghi `not-stated`
> thay vì điền ngày thu thập vào — vì hai thứ đó khác nhau về bản chất, và điền bừa sẽ tạo cảm giác an toàn
> giả về độ mới của dữ liệu.

> **Lưu ý về hai bộ dữ liệu trong repo:** thư mục `data/data-canhan/` là bộ tài liệu **bản đầu** (7 file
> crawl bằng `scripts/fetch_public_pages.py`, nội dung HTML bị duỗi thành text phẳng) — được giữ lại để đối
> chứng. Bộ dùng cho **cả hai báo cáo** là `data/data-nhom/` (8 file, giữ nguyên cấu trúc heading Markdown).
> Việc giữ cả hai cho phép so sánh trực tiếp ảnh hưởng của **chất lượng tiền xử lý dữ liệu** lên chiến lược
> chunk theo heading: cùng một chunker, bộ text phẳng cho 57 chunk (TB 861 ký tự) vì không có `##` nào để cắt,
> còn bộ mới cho 115 chunk (TB 497) nhờ 4–40 heading mỗi tài liệu.

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
| `source_url` | URL | `help.shopee.vn/portal/4/article/188931` | Trích dẫn nguồn trong câu trả lời để người đọc tự kiểm chứng — bắt buộc theo checklist quản trị dữ liệu. |
| `retrieved_at` | date | `2026-08-03` | Phân biệt "ngày nhóm lấy về" với "ngày chính sách có hiệu lực" (`document_version`). |
| `title` | string | `Chính sách Trả hàng và Hoàn tiền` | Hiển thị nguồn dễ đọc cho người dùng thay vì slug kỹ thuật. |

**Đủ 8 trường ở cả 8/8 tài liệu** — kiểm bằng `ingest.parse_front_matter()`, không tài liệu nào thiếu trường.

**Đánh giá sau khi benchmark — trường nào thực sự đáng giá:**

| Trường | Có dùng để lọc? | Kết luận sau khi đo |
|---|---|---|
| `customer_role` | **Có** — trường duy nhất được dùng trong `metadata_filter` | **Hữu ích nhưng không như kỳ vọng.** Với embedding local, filter *không tăng điểm* ở cả 3 query có lọc; giá trị thật là **chặn câu trả lời sai vai** (mục 3). Chi phí: 27% corpus mang `both` bị loại ở mọi filter theo vai. |
| `category` | Không dùng trong bộ query này | **Chưa chứng minh được giá trị.** Với 8 tài liệu, `category` gần như trùng một-một với `doc_id` (mỗi tài liệu một category riêng) nên lọc theo nó tương đương lọc theo tài liệu — không thu hẹp thêm gì. Chỉ có ích khi corpus mở rộng và nhiều tài liệu chia sẻ cùng category. |
| `document_version` | Không | **Có giá trị tiềm năng chưa khai thác.** 3 tài liệu có ngày hiệu lực thật, và `seller-return-evidence` (2025-06-02) cũ hơn `return-refund-policy` (2026-03-11) gần 9 tháng — đủ để hai văn bản mâu thuẫn nhau. Nhóm chưa gặp mâu thuẫn nào trong 5 query, nhưng đây là trường cần dùng đầu tiên nếu corpus mở rộng theo thời gian. |
| `doc_id` | Không lọc, nhưng **dùng để chấm** | **Quan trọng nhất về mặt phương pháp** — nhưng theo hướng cảnh báo: chấm retrieval bằng `doc_id` là cái bẫy chính của bài lab này (mục 3). |
| `source_url`, `title`, `retrieved_at`, `language` | Không | Phục vụ **truy vết nguồn và quản trị dữ liệu**, không phục vụ lọc. `language` hiện vô dụng vì corpus thuần `vi`; giữ lại để schema không phải đổi khi thêm tài liệu song ngữ. |

> **Bài học về thiết kế metadata:** nhóm khai báo 8 trường nhưng **chỉ 1 trường (`customer_role`) thực sự được
> dùng để lọc**, và ngay cả nó cũng không cải thiện điểm số. Điều này không có nghĩa metadata vô ích — mà có
> nghĩa **giá trị của metadata phụ thuộc vào việc corpus có thật sự chứa xung đột mà metadata giải quyết được
> hay không.** Ở đây xung đột buyer/seller là thật (cùng một sự kiện, hai bộ quy tắc), nên `customer_role`
> đáng giá; còn `category` thì không, vì nó không tách được thứ gì mà `doc_id` chưa tách. **Nếu làm lại, nhóm
> sẽ gắn `customer_role` ở mức chunk thay vì mức file** — đó là thay đổi mang lại nhiều giá trị nhất, vì nó
> giải phóng 27% corpus đang bị khoá sau nhãn `both`.

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

Nhóm có **4 thành viên**, dùng **chung corpus `data/data-nhom/` (8 tài liệu) và chung 5 query** ở mục 3; mỗi
người nhận **một chiến lược chunk khác nhau** để so sánh công bằng. Toàn bộ số liệu dưới đây sinh từ cùng một
lệnh `python bench.py --chunker all` nên hoàn toàn đối chứng được với nhau.

| | Thành viên | Chiến lược | Cấu hình | Số chunk | Dài TB | Điểm (local) |
|---|---|---|---|---|---|---|
| TV1 | *[Tên — MSSV]* | `fixed_size` | `FixedSizeChunker(500, overlap=50)` | 131 | 485 | 6/10 |
| TV2 | *[Tên — MSSV]* | `by_sentences` | `SentenceChunker(3 câu)` | 179 | 319 | **8/10** |
| TV3 | *[Tên — MSSV]* | `recursive` | `RecursiveChunker(500)` | 158 | 362 | 5/10 |
| TV4 | **Trương Minh Tâm — 2A202602005** | **`by_heading` (custom)** | `MarkdownHeadingChunker(1000, min=120)` | 115 | 497 | 5/10 |

---

**TV1 — Chia theo kích thước cố định (`FixedSizeChunker`, 500 ký tự, overlap 50)**
- **Vai trò trong nhóm:** đường cơ sở (baseline). Không dùng thông tin cấu trúc nào của văn bản — chỉ cắt theo
  độ dài — nên nó là mốc để đo xem ba chiến lược còn lại có thật sự tốt hơn nhờ hiểu cấu trúc hay không.
- **Lý do chọn tham số:** `chunk_size=500` xấp xỉ độ dài một mục chính sách trung bình trong corpus (xem bảng
  ký tự/heading ở mục 1: phần lớn tài liệu rơi vào 530–740). `overlap=50` (10%) để một câu nằm ở ranh giới
  chunk vẫn xuất hiện đầy đủ trong ít nhất một chunk.
- **Kết quả thực tế — bất ngờ theo hướng tích cực:** đạt **6/10** và **evidence-hit@1 = 3/5**, cao ngang chiến
  lược tốt nhất. Overlap là thứ tạo khác biệt: mỗi thông tin ở ranh giới có **hai cơ hội** lọt top-k, trong
  khi ba chiến lược còn lại đều **không có overlap**. Ở Q5, đây là chiến lược duy nhất cùng `by_sentences` lấy
  được điểm.
- **Điểm yếu quan sát được:** cắt mù nên chẻ đôi bảng và cắt giữa câu. Ở Q2, cả 3 slot top-3 đều đúng tài liệu
  `buyer-refund-timeline` nhưng **không slot nào chứa dòng bảng cần tìm** — MISS 0/2đ.

**TV2 — Chia theo câu (`SentenceChunker`, nhóm 3 câu)**
- **Vai trò trong nhóm:** đại diện cho hướng "tôn trọng ranh giới ngôn ngữ tự nhiên" — không bao giờ cắt giữa
  câu, nhưng cũng không quan tâm tới cấu trúc tài liệu.
- **Lý do chọn tham số:** 3 câu/chunk là mức nhỏ nhất còn giữ được ngữ cảnh cục bộ (một quy tắc + một điều
  kiện đi kèm). Tách regex `(?<=[.!?])\s+` giữ nguyên dấu câu cuối — chi tiết này quan trọng: bản đầu nhóm
  viết `(?<=[.!?])\s+|\.\n` và nhánh thứ hai **nuốt mất dấu chấm**, đã sửa (ghi ở `REPORT_CANHAN.md` mục 2).
- **Kết quả thực tế — chiến lược thắng cuộc:** **8/10**, **evidence-hit@3 = 5/5** — chiến lược **duy nhất**
  đưa được bằng chứng vào top-3 ở *cả năm* query, và `grounded = 3/5` cũng cao nhất.
- **Vì sao thắng:** chunk ngắn nhất (TB 319 ký tự) nên **tín hiệu đậm đặc nhất**. Cosine so sánh vector trung
  bình hoá của cả chunk; chunk càng ngắn thì câu chứa đáp án càng ít bị pha loãng bởi các câu xung quanh.
- **Điểm yếu quan sát được:** sinh **nhiều chunk nhất (179)** — tốn 56% token nhúng/lưu trữ so với TV4. Văn
  bản liệt kê bị vụn: `seller-refund-appeal` cho 26 chunk so với 12 của TV4.

**TV3 — Chia đệ quy theo dấu phân tách (`RecursiveChunker`, 500 ký tự)**
- **Vai trò trong nhóm:** phương án "thoả hiệp" phổ biến nhất trong thực tế (LangChain dùng mặc định) — thử
  cắt theo `\n\n` trước, không được thì `\n`, rồi `. `, cuối cùng mới cắt cứng theo độ dài.
- **Lý do chọn:** trên lý thuyết đây là chiến lược tốt nhất khi không biết trước cấu trúc tài liệu, vì nó
  luôn ưu tiên ranh giới ngữ nghĩa lớn nhất còn khả dụng.
- **Kết quả thực tế — kém nhất, và đây là phát hiện đáng giá:** **5/10**, `doc-hit@3 = 4/5` (**thấp nhất
  nhóm** — chiến lược duy nhất không tìm đúng tài liệu ở cả 5 query), `evidence-hit@3 = 3/5`.
- **Vì sao thua:** thứ tự ưu tiên `\n\n → \n → . ` **không tương ứng với ranh giới điều khoản**. Nó cắt theo
  đoạn văn, mà một mục chính sách thường gồm nhiều đoạn; kết quả là vừa tách điều kiện khỏi ngoại lệ (như
  `fixed_size`) vừa không có overlap để bù (không như `fixed_size`) — **chịu nhược điểm của cả hai hướng**.
- **Ghi chú quan trọng:** với **mock** embeddings, TV3 lại là chiến lược **đứng đầu** (2/10). Đây là ví dụ rõ
  nhất cho kết luận ở mục 3.5: điểm cao của nó đến từ may mắn về độ dài chunk, không phải chất lượng ranh
  giới — và may mắn đó biến mất khi có ngữ nghĩa thật.

**TV4 — Trương Minh Tâm (2A202602005) — Custom: chunk theo Markdown heading**
- **Loại chiến lược:** **Custom tự viết** (`MarkdownHeadingChunker`), cắt theo tiêu đề Markdown (`##` /
  `###`), đáp ứng yêu cầu bắt buộc của K4 là có ít nhất một người chunk theo điều/khoản/heading.
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

- **Kết quả thực tế:** **5/10**, `doc-hit@3 = 5/5` (tìm đúng tài liệu ở **cả 5 query** — ngang TV2, cao nhất
  nhóm) nhưng `evidence-hit@1` chỉ **2/5**. Sinh **ít chunk nhất (115)**, tiết kiệm **36% token** so với TV2.
- **Vì sao không thắng dù tìm đúng tài liệu nhiều nhất:** chunk dài TB 497 ký tự ⇒ **pha loãng tín hiệu**.
  Chunk chứa đáp án *có* lọt top-3 nhưng thường xếp hạng 2–3 thay vì hạng 1. Chi tiết ở `REPORT_CANHAN.md`
  mục 5 — đây là điều TV4 dự đoán sai trước khi chạy benchmark.

**Điều nhóm rút ra khi đặt 4 chiến lược cạnh nhau:** bốn người đi bốn hướng khác nhau và kết quả **không xếp
hạng theo mức độ "thông minh" của chiến lược**. TV1 đơn giản nhất (cắt mù theo độ dài) lại về **nhì** (6/10),
trong khi TV3 tinh vi nhất về mặt thuật toán lại **chót** (5/10, doc@3 thấp nhất). Hai yếu tố dự báo kết quả
tốt hơn hẳn "độ thông minh" là: **(a) độ dài chunk** — ngắn thì tín hiệu đậm (TV2 thắng), và **(b) có overlap
hay không** — TV1 là chiến lược duy nhất có overlap và đó là lý do nó cứu được Q5 trong khi TV3, TV4 đều MISS.

### So Sánh Giữa Các Chiến Lược (đối chứng 4 thành viên)

Nhóm chạy **hai lần** với hai backend nhúng khác nhau trên cùng corpus, cùng 5 query, cùng cách chấm.
Bảng dưới là kết quả với **embedding ngữ nghĩa thật** (`EMBEDDING_PROVIDER=local`,
`paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều) — đây là số liệu nhóm dùng để kết luận. Cột cuối là điểm
với `mock` để đối chiếu; phân tích chênh lệch ở **mục 3.5**.

| Chiến lược (thành viên) | Số chunk | Dài TB | doc-hit@3 | **evidence-hit@3** | evid@1 | grounded | **Điểm /10 (local)** | Điểm (mock) | Điểm mạnh | Điểm yếu |
|-----------|----------|--------|-----------|--------------------|--------|----------|----------|-------|-----------|----------|
| `fixed_size` **(TV1)** 500/50 | 131 | 485 | 5/5 | 4/5 | **3/5** | 2/5 | 6 | 0 | Overlap cho thông tin ở ranh giới 2 cơ hội lọt top-k; evid@1 cao | Cắt ngang bảng và giữa câu; Q2 "đúng tài liệu sai mục" |
| **`by_sentences` (TV2)** 3 câu | **179** | **319** | **5/5** | **5/5** | **3/5** | **3/5** | **8** | 0 | **Chunk nhỏ ⇒ tín hiệu đậm đặc, không bị pha loãng; duy nhất đạt evid@3 = 5/5** | Chunk vụn, dễ mất ngữ cảnh bao quanh; phụ thuộc dấu câu |
| `recursive` **(TV3)** 500 | 158 | 362 | 4/5 | 3/5 | 2/5 | 3/5 | 5 | **2** | Tôn trọng ranh giới đoạn/câu theo thứ tự ưu tiên | Không biết khái niệm "mục"; **doc@3 thấp nhất (4/5)** |
| **`by_heading` (TV4)** | **115** | **497** | 5/5 | 4/5 | 2/5 | 2/5 | 5 | 1 | Giữ trọn điều kiện + ngoại lệ trong một chunk; ít chunk nhất (tiết kiệm 36% token so với `by_sentences`) | **Chunk dài ⇒ pha loãng tín hiệu**: đúng tài liệu nhưng chunk chứa đáp án tụt xuống hạng 2–3 |

**Cột `grounded`** đo tiêu chí *Grounding* của rubric: câu trả lời của `KnowledgeBaseAgent` có thật sự mang
bằng chứng lấy từ context đã retrieve hay không. Để phép đo này trung thực, `bench.py` dùng một **LLM giả lập
kiểu trích xuất** (`extractive_llm`) chỉ được phép trả lại câu lấy nguyên văn từ phần NGỮ CẢNH của prompt —
nếu retrieval không đưa được câu chứa đáp án vào context thì agent **không thể** trả lời đúng, đúng bản chất
của RAG. Nhờ vậy `grounded` bám sát `evidence-hit@3` thay vì bị thổi phồng bởi một mô hình biết "đoán" đáp án
từ kiến thức sẵn có.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **`by_sentences` (8/10)** — và kết quả này đi **ngược dự đoán ban đầu của nhóm**, nên đáng giải thích kỹ.
>
> Nhóm đã dự đoán `by_heading` thắng, với lập luận: chính sách viết theo điều khoản, cắt theo heading thì giữ
> được *quy tắc + điều kiện + ngoại lệ* trong một chunk. Lập luận đó **đúng về mặt cấu trúc nhưng bỏ sót cơ
> chế xếp hạng**. Cosine similarity so sánh vector *trung bình hoá* của cả chunk. Chunk `by_heading` dài
> TB 497 ký tự và thường chứa nhiều ý; câu chứa đáp án bị **pha loãng** giữa các câu khác cùng mục. Chunk
> `by_sentences` chỉ 319 ký tự, tín hiệu đậm đặc hơn, nên chunk chứa đáp án dễ nổi lên top-3.
>
> Số liệu xác nhận: `by_sentences` đạt **evidence-hit@3 = 5/5** — chiến lược **duy nhất** đưa được bằng chứng
> vào top-3 ở *cả năm* query. `by_heading` được 4/5 và **evid@1 chỉ 2/5**: nó tìm đúng tài liệu ở cả 5 query
> (doc@3 = 5/5, ngang `by_sentences`) nhưng chunk chứa đáp án thường xếp hạng 2–3 chứ không phải hạng 1.
> Đây chính xác là biểu hiện của pha loãng tín hiệu, không phải của ranh giới chunk sai.
>
> **Vậy `by_heading` có vô dụng không? Không** — và đây là chỗ hai cách đo nói hai chuyện khác nhau:
> - Nó **tiết kiệm nhất**: 115 chunk so với 179, tức ít hơn **36% token** phải nhúng và lưu trữ cho cùng
>   lượng nội dung. Với corpus lớn, đây là khác biệt chi phí thật.
> - Nó **giữ ngữ cảnh tốt nhất cho người đọc**: khi chunk lọt top-k, người dùng thấy trọn cả mục kèm ngoại lệ,
>   thay vì 3 câu rời rạc.
>
> **Kết luận có điều kiện của nhóm:** nếu tối ưu *độ chính xác top-3 thuần tuý* thì chọn `by_sentences`. Nếu
> tối ưu *chi phí và khả năng đọc hiểu của câu trả lời* thì `by_heading`, nhưng phải bù bằng **top-k lớn hơn**
> (k=5 thay vì 3) để hấp thụ việc chunk đáp án hay xếp hạng 2–3. Hướng tốt nhất là **kết hợp**: cắt theo
> heading để giữ ranh giới ngữ nghĩa, rồi cắt tiếp mục dài thành đơn vị nhỏ hơn nhưng **gắn lại tiêu đề mục**
> — đúng cơ chế `MarkdownHeadingChunker` đã làm cho mục quá dài, chỉ cần hạ `chunk_size` từ 1000 xuống ~350.
>
> Một điểm yếu của `by_heading` **không phụ thuộc embedder**: nó phụ thuộc **chất lượng heading của nguồn**.
> Corpus này có heading Markdown sạch nên chunker hoạt động; trên bộ `data/data-canhan/` (HTML bị duỗi thành
> text phẳng) cùng chunker chỉ cho 57 chunk TB 861 ký tự — gần như không cắt được gì.

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

Số liệu dưới đây chạy với **embedding local** (xem mục 3.5 để đối chiếu với mock):

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk chứa **bằng chứng** trong top-3? | Agent trả lời đúng? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------------------|---------|
| 1 | Thời hạn gửi yêu cầu | **cả 4 đều FULL 2/2đ** | ✓ ở cả 4, đều **hạng 1** | ✓ ở cả 4 | Query dễ nhất: từ khoá "thực phẩm tươi sống" hiếm và đặc trưng |
| 2 | Hoàn tiền thẻ tín dụng | `by_sentences`, `by_heading` (1đ) | ✓ 2/4 — `fixed_size` và `recursive` **MISS** | ✗ ở cả 4 | Đáp án nằm **trong một dòng bảng**; xem FC2 |
| 3 | Hình thức gửi hàng hoàn | **`by_sentences` (2đ — FULL)** | ✓ 3/4 — `recursive` chỉ có ở hạng 2 | ✓ ở `by_sentences` | Query không filter; `by_heading` bị `return-refund-policy` chiếm 2 slot đầu |
| 4 | Thời hạn khiếu nại của người bán | **`fixed_size`, `by_sentences`, `recursive` (2đ)** | ✓ ở cả 4 | ✓ ở cả 4 | Nhờ metadata filter — score cao nhất toàn bộ benchmark (0.90) |
| 5 | Ai được trả hàng COM | `fixed_size`, `by_sentences` (1đ) | ✓ 2/4 — `recursive` và `by_heading` **MISS** | ✗ ở cả 4 | Bằng chứng ("Kim Cương", "hạng Vàng") nằm rải ở 3 tài liệu khác nhau |

**Một bài học về chính cách chấm:** lần chạy đầu, Q4 bị chấm 1đ vì chuỗi bằng chứng khai báo là
`"2 ngày kể từ khi Shopee"`, trong khi corpus diễn đạt cùng mốc đó theo hai cách — văn xuôi dùng
*"2 ngày kể từ khi Shopee gửi thông báo"*, còn bảng tóm tắt dùng *"Trong vòng 2 ngày"*. Agent đã trích đúng
dòng bảng và **trả lời đúng nội dung**, nhưng bị chấm là thiếu chỉ vì khác câu chữ. Sau khi khai báo cả hai
biến thể, Q4 đạt **FULL 2/2đ**. Điều này cho thấy chấm bằng chuỗi cứng vẫn có thể **chấm oan**: nó chặt hơn
doc_id nhưng phải bao được mọi cách diễn đạt của cùng một dữ kiện trong corpus.

**Chênh lệch giữa hai cách chấm — phát hiện đáng giá nhất của buổi lab:**

| Chiến lược | doc-hit@3 (chấm theo doc_id) | **evidence-hit@3 (chấm theo chunk)** | Chênh lệch |
|---|---|---|---|
| `fixed_size` | 5/5 | **4/5** | −1 |
| `by_sentences` | 5/5 | **5/5** | **0** |
| `recursive` | 4/5 | **3/5** | −1 |
| `by_heading` | **5/5** | **4/5** | −1 |

Với embedding local, khoảng cách thu hẹp còn 0–1 — nhưng **không biến mất**, và nó vẫn đủ để đảo thứ hạng:
`by_heading` có doc@3 = 5/5 ngang `by_sentences`, nhưng thua ở evid@3 (4/5 so với 5/5) và thua đậm ở evid@1
(2/5 so với 3/5). **Chấm theo doc_id sẽ kết luận hai chiến lược này ngang nhau; chấm theo chunk cho thấy
chúng không ngang.**

Với mock, khoảng cách này lớn hơn nhiều: `recursive` được **4/5** theo doc_id nhưng chỉ **1/5** theo bằng
chứng — **thổi phồng gấp 4 lần**, với 9/20 lượt chạy rơi vào "đúng tài liệu nhưng sai mục". Bài học rút ra
không phải "doc_id luôn sai gấp 4 lần", mà là: **mức độ thổi phồng tỷ lệ nghịch với chất lượng embedder**.
Embedder càng yếu, chấm theo doc_id càng dối. Vì không biết trước embedder mạnh hay yếu, **luôn phải chấm ở
mức chunk**.

> **Điểm score cao là tín hiệu xếp hạng, không phải bằng chứng rằng nội dung đúng.** Q4 với `by_heading`
> minh họa trực tiếp — kể cả khi dùng embedding thật: chunk hạng 1 là "### 4. Mốc thời gian Người bán có thể
> khiếu nại" (score **0.8705**) **không chứa** mốc 2 ngày; chunk chứa đáp án xếp **hạng 2** với score thấp
> hơn (0.8687). Chênh lệch chỉ 0.0018 — nhỏ đến mức thứ tự giữa chúng gần như ngẫu nhiên.

### Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?

Chạy `python bench.py --chunker by_heading --ablation` — A/B trên cả 3 query có filter:

| Query | Không filter (top-3) | Có filter (top-3) | Kết quả |
|---|---|---|---|
| Q1 (buyer) | `return-refund-policy`**(both)**, `seller-return-process`**(seller)**, `buyer-return-eligibility` → **2đ** | `buyer-return-eligibility` ×2, `buyer-refund-timeline` → **2đ** | Đổi kết quả, không đổi điểm |
| Q2 (buyer) | `buyer-refund-timeline` ×3 → 1đ | `buyer-refund-timeline` ×3 → 1đ | **HAI KẾT QUẢ GIỐNG HỆT NHAU** |
| Q4 (seller) | `seller-return-process`, **`buyer-refund-timeline`**, `seller-refund-appeal` → **1đ** | `seller-return-process` ×2, `seller-refund-appeal` → **1đ** | Đổi kết quả, không đổi điểm |

**Kết luận trung thực — và nó khác hẳn kết luận khi chạy mock:** với embedding ngữ nghĩa thật, metadata filter
**không cải thiện điểm ở bất kỳ query nào trong ba**. Đây là kết quả nhóm không mong đợi nhưng phải ghi đúng.

Ba tình huống khác nhau, cần phân biệt:

1. **Q2 — filter hoàn toàn không có tác dụng.** Top-3 **giống hệt nhau** từng chunk một, có filter hay không.
   Lý do: embedding đã tự xếp cả 3 slot vào đúng `buyer-refund-timeline` rồi. Filter chỉ loại bỏ những chunk
   *vốn dĩ đã không lọt top-3*. Đây là trường hợp filter là **chi phí thuần tuý** — tốn một vòng duyệt
   metadata mà không đổi gì.
2. **Q1 và Q4 — filter đổi thành phần top-3 nhưng không đổi điểm.** Ở Q4, không lọc thì slot 2 bị
   `buyer-refund-timeline` chiếm; lọc xong slot đó thành `seller-return-process`. Kết quả **sạch hơn về vai**
   (3/3 seller thay vì 2/3) nhưng chunk chứa bằng chứng vẫn ở đúng vị trí cũ, nên điểm không đổi.
3. **Giá trị thật của filter không nằm ở điểm số mà ở việc chặn câu trả lời sai vai.** Ở Q1 không lọc, hạng 1
   là `return-refund-policy` (role `both`) và hạng 2 là `seller-return-process` — tức hệ thống đưa **quy trình
   của người bán** vào ngữ cảnh để trả lời câu hỏi của **người mua**. Điểm vẫn 2đ vì bằng chứng tình cờ nằm ở
   hạng 3, nhưng nếu agent trích nhầm hạng 2 thì câu trả lời sai vai hoàn toàn. **Metric evidence-hit không
   bắt được rủi ro này** — đó là giới hạn của chính cách chấm nhóm đang dùng.

Với mock thì ngược lại: Q4 được filter cải thiện **0 → 1đ**, vì mock xếp hạng gần như ngẫu nhiên nên việc thu
hẹp không gian tìm kiếm giúp ích rõ rệt. **Embedder càng yếu, metadata filter càng có giá trị bù đắp.** Nói
cách khác, filter là *lưới an toàn cho xếp hạng kém*, không phải công cụ tăng điểm khi xếp hạng đã tốt.

Ranh giới vẫn giữ nguyên ở cả hai backend: **filter sửa được nhiễu chéo vai, không sửa được xếp hạng kém
trong cùng vai.**

**Chi phí của filter — đánh đổi precision lấy recall:** **31/115 chunk (27%)** của corpus mang
`customer_role: both` (toàn bộ `return-refund-policy`). Vì `search_with_filter` so khớp chính xác từng cặp
key/value (`src/store.py:107`), giá trị `"both"` **không** khớp `"buyer"` lẫn `"seller"` — nên hơn một phần tư
kho tri thức bị vô hiệu hoá ở **mọi** filter theo vai, kể cả khi nội dung của nó đúng cho vai đang hỏi. Cụ
thể: Điều 5 "Quyền của Người Bán" (`return-refund-policy`) nêu đúng mốc **02 ngày lịch** mà Q4 cần, nhưng bị
`filter=seller` loại mất. Đây không phải ca lẻ mà là **hệ quả có hệ thống của việc gắn tag ở mức file thay vì
mức chunk**.

### Ba failure case có bằng chứng

Toàn bộ số liệu dưới đây lấy từ lần chạy **embedding local** — tức là các lỗi này **vẫn còn** kể cả khi đã
thay mock bằng mô hình ngữ nghĩa thật, nên chúng là lỗi của *thiết kế chunk và metadata*, không phải của
embedder.

**FC1 — Q4: chunk đúng chủ đề nhưng không chứa số liệu lại thắng chunk có đáp án** *(cosine đo độ giống chủ
đề, không đo mật độ thông tin trả lời được)*

- **Query:** "Khi Shopee quyết định hoàn tiền ngay…, bên bán có bao lâu để khiếu nại?"
- **Bằng chứng từ top-k** (`by_heading`, filter seller, embedding local):

  | Hạng | Chunk | Score | Có bằng chứng? |
  |---|---|---|---|
  | 1 | `seller-return-process` — "### 4. Mốc thời gian Người bán có thể khiếu nại" | **0.8705** | ✗ |
  | 2 | `seller-refund-appeal` — "### Thời hạn khiếu nại" | 0.8687 | **✓ chứa "trong vòng 2 ngày"** |
  | 3 | `seller-return-process` — "Shopee có thể quyết định hoàn tiền ngay…" | 0.8461 | **✓** |

- **Nguyên nhân:** chunk hạng 1 có **tiêu đề** trùng gần như từng chữ với query ("mốc thời gian", "khiếu
  nại") nên cosine cao nhất, nhưng phần thân của nó chỉ dẫn chiếu sang mục khác chứ không nêu con số. Khoảng
  cách score giữa hạng 1 và hạng 2 chỉ **0.0018** — nhỏ hơn cả sai số làm tròn, tức thứ tự giữa chúng là
  ngẫu nhiên. Điều này **không** được cải thiện bởi embedding tốt hơn: vấn đề là chunk hạng 1 *thật sự* nói
  về chủ đề đó, chỉ là không chứa dữ kiện.
- **Thay đổi đề xuất:** với câu hỏi dạng "bao lâu", thêm bước **rerank ưu tiên chunk chứa mẫu số + đơn vị
  thời gian** (regex `\d+\s*(ngày|giờ|tháng)`). Đây là loại lỗi mà *chỉ* embedding không sửa được — cần tín
  hiệu từ vựng bổ sung.

**FC2 — Q2: đáp án nằm trong một dòng bảng, bị pha loãng ở mọi chiến lược**

- **Query:** "Thanh toán bằng thẻ tín dụng/ghi nợ… tiền về đâu và mất bao lâu?" — gold là **một dòng** trong
  Bảng 1 của `buyer-refund-timeline`, chứa "7–14 ngày làm việc".
- **Bằng chứng:** đây là query **khó nhất** của bộ — không chiến lược nào đạt FULL. `fixed_size` và
  `recursive` **MISS hoàn toàn** (0đ) dù cả 3 slot top-3 đều đúng tài liệu `buyer-refund-timeline`: chúng lấy
  trúng các mảnh khác của tài liệu (đoạn nói về hoàn 100% tiền hàng, đoạn nói về khiếu nại của người bán)
  chứ không phải dòng bảng cần tìm. `by_sentences` và `by_heading` được 1đ nhờ bằng chứng lọt hạng 3 và
  hạng 1 tương ứng.
- **Nguyên nhân:** bảng 9 dòng liệt kê 9 phương thức thanh toán, mỗi dòng một mốc thời gian khác nhau. Khi cả
  bảng nằm trong một chunk, vector trung bình hoá đại diện cho *"bảng thời gian hoàn tiền nói chung"*, và
  tín hiệu riêng của dòng "thẻ tín dụng" bị pha loãng giữa 8 dòng còn lại. Khi bảng bị cắt (như `fixed_size`),
  dòng cần tìm chỉ có **một cơ hội** lọt top-k vì overlap 50 ký tự không đủ phủ một hàng bảng.
- **Thay đổi đề xuất:** với nội dung dạng bảng, chunk **theo hàng** và **lặp lại dòng tiêu đề bảng** lên mỗi
  hàng (`| Phương thức | Gửi qua | Thời gian |` + hàng dữ liệu). Đây là mở rộng tự nhiên của TV4 và là việc
  nhóm sẽ làm đầu tiên nếu có thêm thời gian.

**FC3 — Q3: query không filter bị tài liệu `role: both` chiếm hai slot đầu**

- **Query:** "Người mua có những hình thức gửi hàng hoàn nào? Hình thức nào miễn phí?" — cố ý **không** đặt
  filter để làm đối chứng.
- **Bằng chứng** (`by_heading`, embedding local): hạng 1 = `return-refund-policy` (0.6355, role `both`),
  hạng 2 = `return-refund-policy` (0.6216, `both`), hạng 3 = `buyer-return-shipping` (0.6159) — **gold, có
  bằng chứng, nhưng bị đẩy xuống cuối**. Chỉ được 1đ thay vì 2đ. Với `by_sentences` thì gold lên hạng 1 và
  đạt FULL 2đ.
- **Nguyên nhân:** `return-refund-policy` là văn bản chính sách gốc dài nhất (13.483 ký tự), dùng ngôn ngữ
  pháp lý bao quát ("Người Mua đồng ý rằng…", "phạm vi áp dụng…") nên **giống mọi query một cách chung
  chung**. Nó không trả lời câu hỏi nào cụ thể nhưng luôn đạt score khá. Đây là hiện tượng *hub document* —
  tài liệu tổng quát chiếm chỗ của tài liệu chuyên biệt.
- **Thay đổi đề xuất:** query kiểu này đáng lẽ nên có `metadata_filter={"customer_role": "buyer"}` — và đáng
  chú ý là filter đó sẽ loại luôn `return-refund-policy` vì nó mang `both`, tức **vô tình sửa đúng lỗi này**.
  Nhóm giữ nó không filter **có chủ đích** để chứng minh: khi corpus có một tài liệu tổng quát, **không lọc
  là một lựa chọn tồi**, kể cả khi câu hỏi đã nêu rõ "Người mua". Về lâu dài nên suy ra filter từ chính câu
  hỏi thay vì bắt người dùng chỉ định.

### 3.5. Mock vs Local — vì sao phải chọn embedder TRƯỚC khi đo

Nhóm chạy toàn bộ benchmark hai lần, **chỉ đổi biến môi trường `EMBEDDING_PROVIDER`**, giữ nguyên corpus,
5 query, cách chấm và `top_k=3`:

| Chiến lược | Điểm (mock) | **Điểm (local)** | doc@3 mock → local | evid@3 mock → local |
|---|---|---|---|---|
| `fixed_size` | 0/10 | **6/10** | 3/5 → **5/5** | 0/5 → **4/5** |
| `by_sentences` | 0/10 | **8/10** | 2/5 → **5/5** | 0/5 → **5/5** |
| `recursive` | **2/10** | 5/10 | 4/5 → 4/5 | 1/5 → 3/5 |
| `by_heading` | 1/10 | 5/10 | 2/5 → **5/5** | 1/5 → 4/5 |

**Ba điều bảng này cho thấy:**

1. **Thứ hạng bị đảo hoàn toàn.** Với mock, `recursive` đứng đầu (2/10) và `by_sentences` đứng chót (0/10).
   Với local, `by_sentences` đứng đầu (8/10) và `recursive` đứng chót (5/10) — **đảo ngược chính xác**. Nếu
   nhóm chỉ chạy mock rồi kết luận "recursive tốt nhất", kết luận đó sẽ **sai hoàn toàn**.
2. **Mock không chỉ *ồn ào hơn*, nó *thiên lệch có hệ thống*.** `recursive` là chiến lược duy nhất không
   được cải thiện về doc@3 (4/5 → 4/5). Lý do: điểm mock của nó cao là do **may mắn về độ dài chunk** chứ
   không phải chất lượng ranh giới — và may mắn đó không chuyển thành lợi thế khi có ngữ nghĩa thật.
3. **Kết luận nào sống sót qua cả hai lần chạy thì mới đáng tin.** Có ba kết luận như vậy, và nhóm coi đây
   là phần giá trị nhất của báo cáo:
   - Chấm theo doc_id luôn thổi phồng so với chấm theo chunk (mức độ thay đổi, chiều hướng thì không).
   - Score cao ≠ nội dung đúng (FC1 đúng ở cả mock lẫn local).
   - 27% corpus mang `role: both` bị loại ở mọi filter theo vai (thuộc về metadata, hoàn toàn độc lập
     với embedder).

> **Bài học phương pháp:** embedder **không phải** một tham số điều chỉnh sau cùng — nó là **nền của mọi
> phép đo**. Đổi embedder không làm điểm "tốt lên đều" mà **sắp xếp lại toàn bộ thứ hạng**. Vì vậy quy trình
> đúng là: chọn embedder gần nhất với môi trường thật → mới benchmark chiến lược chunk. Làm ngược lại thì
> mọi bảng so sánh đều có nguy cơ vô nghĩa.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Demo trực tiếp — ứng dụng web

Nhóm viết `app.py` — một giao diện web tối giản dùng `http.server` của thư viện chuẩn (**không thêm phụ
thuộc nào**) để demo trực tiếp thay vì đọc log terminal.

```bash
# Bước 1 (một lần): cài mô hình nhúng local
python -m pip install -r requirements-local.txt

# Bước 2: chạy web
python app.py            # mở http://127.0.0.1:8000
```

**Demo được điều gì:**

| Thành phần trên giao diện | Minh hoạ cho luận điểm nào |
|---|---|
| Ô chọn **chiến lược chunk** (4 lựa chọn) | Đổi chunker và xem top-k đổi **ngay tại chỗ** — trực quan hơn bảng số |
| Ô chọn **`customer_role`** (buyer / seller / không lọc) | A/B metadata filter trực tiếp: gõ Q1 rồi bật/tắt filter để thấy chunk seller biến mất |
| **5 nút query nhanh** ứng với 5 câu hỏi khoá | Không phải gõ lại query dài khi demo trước lớp |
| Mỗi chunk hiện **score + doc_id + role + nhãn "có bằng chứng"** | Cho thấy trực tiếp hiện tượng **score cao ≠ có bằng chứng** (FC1) |
| Khung **câu trả lời của agent** kèm ngữ cảnh đánh số | Truy vết nguồn: câu trả lời trích từ chunk nào |

**Kịch bản demo 3 phút nhóm sẽ trình bày:**
1. Gõ **Q4** với chunker `by_heading`, không lọc → chỉ ra slot bị `buyer-refund-timeline` chiếm (sai vai).
2. Bật `customer_role = seller` → cả 3 slot thành seller, nhưng **điểm không đổi** → đúng kết luận mục 3.
3. Vẫn Q4, chỉ vào chunk hạng 1 (score 0.8705) **không** có nhãn "có bằng chứng", còn hạng 2 (0.8687) thì
   có → **FC1 nhìn thấy được bằng mắt**.
4. Đổi chunker sang `by_sentences` → bằng chứng nhảy lên hạng 1 → minh hoạ vì sao `by_sentences` thắng.

### Những phân tích (insights) hay nhất nhóm sẽ trình bày

1. **Đổi embedder đảo ngược hoàn toàn bảng xếp hạng.** Với mock, `recursive` nhất và `by_sentences` chót.
   Với local, đúng hai chiến lược đó hoán đổi vị trí (5/10 và 8/10). Cùng corpus, cùng query, cùng cách chấm
   — chỉ đổi một biến môi trường. **Embedder là nền của phép đo, không phải tham số tinh chỉnh cuối.**
2. **Chấm theo doc_id thổi phồng kết quả, và mức thổi phồng tỷ lệ nghịch với chất lượng embedder.** Với mock,
   `recursive` được 4/5 theo doc_id nhưng 1/5 theo bằng chứng — **gấp 4 lần**. Với local, khoảng cách thu hẹp
   còn 0–1 nhưng **vẫn đủ đảo thứ hạng** giữa `by_heading` và `by_sentences` (cùng doc@3 = 5/5, khác evid@3).
   Vì không biết trước embedder mạnh hay yếu, **luôn phải chấm ở mức chunk**.
3. **Score cao ≠ nội dung đúng — kể cả với embedding thật.** Ở Q4, chunk hạng 1 (0.8705) có tiêu đề trùng gần
   như từng chữ với query nhưng **không chứa con số nào**; chunk chứa đáp án xếp hạng 2 (0.8687). Chênh lệch
   0.0018 — thứ tự giữa chúng là ngẫu nhiên. Loại lỗi này embedding tốt hơn **không sửa được**, phải rerank
   bằng tín hiệu từ vựng.
4. **Chunk dài giữ ngữ cảnh tốt nhưng pha loãng tín hiệu tìm kiếm.** `by_heading` đạt doc@3 = 5/5 (tìm đúng
   tài liệu ở mọi query) nhưng evid@1 chỉ 2/5 — chunk chứa đáp án hay xếp hạng 2–3. Đây là **đánh đổi thật**
   giữa khả năng đọc hiểu của câu trả lời và độ chính xác xếp hạng, không phải lỗi của chunker.
5. **Metadata filter là lưới an toàn cho xếp hạng kém, không phải công cụ tăng điểm.** Với mock, filter cải
   thiện Q4 từ 0 → 1đ. Với local, filter **không tăng điểm ở bất kỳ query nào** trong ba, và ở Q2 cho kết
   quả **giống hệt nhau** từng chunk. Nhưng nó vẫn có giá trị: ở Q1 không lọc, hạng 1–2 là chunk `both` và
   `seller` cho một câu hỏi của người mua — **rủi ro trả lời sai vai mà metric evidence-hit không bắt được**.
6. **Chi phí của filter: 27% corpus bị vô hiệu hoá.** 31/115 chunk mang `role: both`; vì `search_with_filter`
   so khớp chính xác, `"both"` không khớp `"buyer"` lẫn `"seller"` — hơn một phần tư kho tri thức bị loại ở
   **mọi** filter theo vai, kể cả khi nội dung đúng cho vai đang hỏi.

**Bài học rút ra khi so sánh trong nhóm:**
> Nhóm bắt đầu với giả thuyết "cắt theo heading là tốt nhất cho văn bản chính sách" — nghe rất hợp lý, và
> **sai** khi đo bằng embedding thật. Cái sai không nằm ở lập luận về cấu trúc (heading *đúng là* giữ được
> quy tắc + ngoại lệ cạnh nhau) mà ở chỗ bỏ qua **cơ chế xếp hạng**: cosine so sánh vector trung bình hoá,
> nên chunk càng dài thì tín hiệu của câu chứa đáp án càng loãng. Bài học là **một lập luận đúng về dữ liệu
> vẫn có thể cho kết luận sai về retrieval**, nếu quên rằng retrieval có cơ chế riêng của nó. Chỉ có chạy
> benchmark thật mới phát hiện được — và phải chạy trên embedder thật.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> **Một:** cài embedding local **ngay từ đầu** thay vì để cuối. Toàn bộ vòng phân tích đầu tiên chạy trên
> mock đã cho kết luận ngược, phải làm lại. **Hai:** gắn `customer_role` ở **mức chunk** thay vì mức file.
> `return-refund-policy` có Điều 5 rõ ràng dành cho người bán và Điều 6 dành cho người mua, nhưng cả file
> phải mang một nhãn `both` duy nhất — mất 27% corpus mỗi lần lọc. **Ba:** xử lý bảng riêng (chunk theo hàng,
> lặp tiêu đề cột), vì Q2 có đáp án nằm trong một dòng bảng và **không chiến lược nào đạt điểm tối đa** ở
> query đó. **Bốn:** thử `by_heading` với `chunk_size` nhỏ hơn (~350 thay vì 1000) để lấy cả hai: ranh giới
> ngữ nghĩa của heading *và* mật độ tín hiệu của chunk ngắn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 | 8 tài liệu, hai phía buyer/seller có chủ đích, metadata đủ 5 trường + 3 tài liệu có ngày hiệu lực thật; đã loại nguồn Lazada vì bị chặn đăng nhập thay vì cố lách |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 | **4 thành viên, 4 chiến lược khác nhau** trên cùng corpus + cùng 5 query nên đối chứng công bằng; TV4 custom có 2 tinh chỉnh được giải thích bằng lý do cụ thể; so sánh trên baseline + benchmark **với 2 backend nhúng**. Kết luận có điều kiện (khi nào chọn `by_sentences`, khi nào `by_heading`) thay vì xếp hạng đơn giản |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 | Với embedding local: **4/5 query có bằng chứng trong top-3** ở chiến lược tốt nhất (`by_sentences` đạt 5/5, điểm 8/10). Phương pháp chấm đầy đủ: mức chunk + A/B filter + 3 failure case có bằng chứng top-k + đối chứng mock/local. Trừ điểm vì Q2 (đáp án trong bảng) không chiến lược nào đạt tối đa |
| Thuyết trình (Demo) | 5 / 5 | 6 insight có số liệu hậu thuẫn, trong đó phát hiện chính (đổi embedder đảo ngược xếp hạng) đi ngược giả thuyết ban đầu; **có app web `app.py` chạy được** kèm kịch bản demo 3 phút bám sát các luận điểm |
| **Tổng phần nhóm** | **36 / 40** | |
