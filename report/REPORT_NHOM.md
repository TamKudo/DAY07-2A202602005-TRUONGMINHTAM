# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** E2 — lớp D303 K4  
**Thành viên:** Trần Văn Toàn (2A202601218), Phạm Hải Yến (2A202601152), Trần Hoàng Khôi (2A202601778), Trương Minh Tâm (2A202602005), Trần Minh Hiển (2A202601812)  
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân nộp riêng trong `REPORT_CANHAN.md`. Thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng.

**Phạm vi cụ thể nhóm tập trung:**
> Quy trình **Trả hàng/Hoàn tiền trên Shopee**, thu thập song song phía Người mua (`help.shopee.vn`) và Người bán (`banhang.shopee.vn/edu`), cộng một văn bản chính sách gốc áp dụng cho cả hai. Cùng một đơn hoàn nhưng hai bộ quy tắc khác nhau theo vai — đúng điều kiện để kiểm chứng giá trị của `metadata_filter`.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|--------------------|----------------------|----------|-----------------|
| 1 | Những quy định chung về Trả hàng/Hoàn tiền | https://help.shopee.vn/portal/4/article/188931-[Tr%E1%BA%A3-h%C3%A0ng/Ho%C3%A0n-ti%E1%BB%81n]-Nh%E1%BB%AFng-quy-%C4%91%E1%BB%8Bnh-chung-v%E1%BB%81-Tr%E1%BA%A3-h%C3%A0ng/Ho%C3%A0n-ti%E1%BB%81n-c%E1%BB%A7a-Shopee | 2026-08-03 / not-stated | 6.205 | `buyer`, return-eligibility |
| 2 | Thời gian nhận tiền hoàn và cách kiểm tra | https://help.shopee.vn/portal/4/article/189473-[Tr%E1%BA%A3-h%C3%A0ng/-Ho%C3%A0n-ti%E1%BB%81n]-Th%E1%BB%9Di-gian-nh%E1%BA%ADn-ti%E1%BB%81n-ho%C3%A0n-v%C3%A0-c%C3%A1ch-ki%E1%BB%83m-tra-ti%E1%BB%81n-ho%C3%A0n | 2026-08-03 / not-stated | 3.690 | `buyer`, refund-timeline |
| 3 | Quy trình Shopee xử lý yêu cầu THHT | https://help.shopee.vn/portal/4/article/190242-[Tr%E1%BA%A3-h%C3%A0ng/-Ho%C3%A0n-ti%E1%BB%81n]-Quy-tr%C3%ACnh-Shopee-x%E1%BB%AD-l%C3%BD-y%C3%AAu-c%E1%BA%A7u-Tr%E1%BA%A3-h%C3%A0ng/-Ho%C3%A0n-ti%E1%BB%81n | 2026-08-03 / not-stated | 8.595 | `buyer`, return-process |
| 4 | Phương thức gửi hàng hoàn trả và phí | https://help.shopee.vn/portal/4/article/189477-[Tr%E1%BA%A3-h%C3%A0ng/-Ho%C3%A0n-ti%E1%BB%81n]-C%C3%A1c-ph%C6%B0%C6%A1ng-th%E1%BB%A9c-g%E1%BB%ADi-h%C3%A0ng-ho%C3%A0n-tr%E1%BA%A3-v%C3%A0-ph%C3%AD-ho%C3%A0n-tr%E1%BA%A3 | 2026-08-03 / not-stated | 5.488 | `buyer`, return-shipping |
| 5 | Quy trình THHT dành cho Người bán | https://banhang.shopee.vn/edu/article/563 | 2026-08-03 / not-stated | 7.467 | `seller`, seller-response |
| 6 | Hướng dẫn Người bán khiếu nại THHT | https://banhang.shopee.vn/edu/article/3647 | 2026-08-03 / **2025-11-03** | 4.625 | `seller`, seller-appeal |
| 7 | Mẹo cung cấp bằng chứng khiếu nại | https://banhang.shopee.vn/edu/article/25057 | 2026-08-03 / **2025-06-02** | 7.846 | `seller`, return-evidence |
| 8 | Chính sách Trả hàng và Hoàn tiền | https://help.shopee.vn/portal/4/article/77251-CH%C3%8DNH-S%C3%81CH-TR%E1%BA%A2-H%C3%80NG-V%C3%80-HO%C3%80N-TI%E1%BB%80N | 2026-08-03 / **2026-03-11** | 13.483 | `both`, general-policy |

**Tổng:** 8 tài liệu (~57k ký tự thân bài), phân bố **4 buyer · 3 seller · 1 both**. Corpus lưu kèm `sources.csv`.

**Vì sao cấu trúc corpus ảnh hưởng retrieval:**
- Cân bằng buyer/seller có chủ đích — nếu lệch một phía thì A/B metadata filter ở câu 4 không có ý nghĩa.
- Độ dài lệch mạnh: tài liệu timeline ngắn (~3.7k) còn policy dài (~13.5k, ~23% corpus) và mang nhãn `both`, nên vừa quan trọng vừa dễ bị filter loại.
- Nhiều nội dung dạng **bảng Markdown** (thời gian hoàn theo phương thức thanh toán, hạn chế sản phẩm…) — không strategy nào hiểu “cắt theo hàng bảng”, và đây là lý do câu 2 khó với mọi người.

Nhóm ban đầu nhắm vài trang Lazada nhưng bị redirect sang xác thực; theo hướng dẫn thu thập dữ liệu, nhóm **đổi nguồn** thay vì cố vượt. Chỉ **3/8** tài liệu công bố ngày hiệu lực rõ; phần còn lại ghi `not-stated` (không lấy ngày crawl thay phiên bản).

**Danh sách kiểm tra quản trị dữ liệu:**
- [x] Corpus chỉ chứa nguồn công khai; không có dữ liệu cá nhân / đăng nhập / tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated`).

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất? |
|-----------------|------|---------------|--------------------------------|
| `customer_role` | enum | `buyer` / `seller` / `both` | Lọc theo vai; tránh lẫn quy tắc buyer với seller trên cùng chủ đề hoàn tiền. |
| `category` | string | `refund-timeline`, `seller-appeal` | Thu hẹp theo loại thông tin khi corpus mở rộng. |
| `doc_id` | slug | `seller-refund-appeal` | Gom chunk theo tài liệu cha; truy vết nguồn / `delete_document()`. |
| `document_version` | date/string | `2026-03-11`, `not-stated` | Phân biệt phiên bản chính sách khi có mâu thuẫn theo thời gian. |
| `source_url` | URL | URL đầy đủ ở bảng trên | Người đọc tự mở nguồn để kiểm chứng. |
| `retrieved_at` | date | `2026-08-03` | Ngày nhóm lấy tài liệu (khác ngày hiệu lực). |
| `title`, `language` | string | tiếng Việt / tiêu đề gốc | Hiển thị và dự phòng corpus song ngữ. |

**Sau khi benchmark:** chỉ `customer_role` thực sự được dùng để lọc. `category` gần như một-một với `doc_id` trên bộ 8 file nên chưa mang thêm precision. `doc_id` quan trọng để chấm và truy vết, nhưng **chấm chỉ bằng doc_id dễ thổi phồng** (đúng tài liệu nhưng sai mục) — vì vậy nhóm chuyển sang chấm bằng chuỗi bằng chứng trong chunk.

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy comparator trên toàn corpus (body đã bỏ front matter), embedder local `paraphrase-multilingual-MiniLM-L12-v2`:

| Chiến lược | Số chunk | Độ dài TB | Giữ được ngữ cảnh không? |
|------------|----------|-----------|--------------------------|
| FixedSize (500, overlap 50) | 131 | 485 | Trung bình — overlap giúp biên chunk, nhưng dễ cắt giữa câu/bảng |
| Sentence (3 câu) | 179 | 319 | Tốt ở mức câu; dễ mất ngữ cảnh cả mục |
| Recursive (500) | 158 | 362 | Khá — ưu tiên đoạn rồi câu; chưa gắn “điều khoản” |
| Heading (custom) | 115 | 497 | Tốt nhất theo cấu trúc mục; chunk dài hơn → dễ pha loãng tín hiệu |

Heading cho **ít chunk nhất nhưng dài nhất**; Sentence ngược lại. Đây là trade-off chính nhóm đo trong phần so sánh: giữ ngữ cảnh điều khoản thì chunk dài, còn muốn tín hiệu tìm kiếm sắc thì chunk phải ngắn hơn.

### Chiến lược của từng thành viên

**Trần Văn Toàn — FixedSizeChunker (500, overlap 50)**  
- **Loại:** FixedSize  
- **Mô tả & lý do:** Làm baseline “cắt mù”: không dùng heading hay câu, chỉ cửa sổ ký tự. `chunk_size=500` gần độ dài một mục trung bình trong corpus; `overlap=50` để câu nằm ở biên vẫn xuất hiện trong ít nhất một chunk — đây là điểm khác biệt quan trọng so với ba strategy còn lại (không overlap).  
- **Kết quả:** **6/10** (local), evid@1 khá cao. Overlap giúp thông tin ở ranh giới có hai cơ hội lọt top-k; đó cũng là lý do Fixed cứu được một số câu mà Recursive/Heading miss. Điểm yếu rõ ở câu 2: đúng tài liệu timeline nhưng không bắt được đúng dòng bảng vì cửa sổ cắt ngang hàng.

**Phạm Hải Yến — SentenceChunker (3 câu)**  
- **Loại:** Sentence  
- **Mô tả & lý do:** Tôn trọng ranh giới câu; 3 câu/chunk đủ ngắn để tín hiệu cosine ít bị pha loãng. Cách này hợp với câu hỏi số liệu/điều kiện ngắn trong FAQ chính sách, nơi đáp án thường nằm trong 1–2 câu đặc trưng (“24 giờ”, “7–14 ngày làm việc”).  
- **Kết quả:** **8/10**, evid@3 = 5/5 — duy nhất đưa bằng chứng vào top-3 ở cả năm câu trên lần chạy nhóm. Điểm yếu: nhiều chunk nhất (~179); văn bản liệt kê dễ bị cắt vụn và tốn thêm chi phí embed/lưu trữ so với Heading.

**Trần Hoàng Khôi — RecursiveChunker (500)**  
- **Loại:** Recursive  
- **Mô tả & lý do:** Thử separator theo thứ tự `\n\n → \n → . ` rồi mới cắt cứng — hướng “thoả hiệp” phổ biến (giống nhiều pipeline mặc định) khi chưa biết trước cấu trúc tài liệu. Kỳ vọng: vừa giữ đoạn văn, vừa không cắt giữa câu.  
- **Kết quả:** **5/10**. Tôn trọng đoạn/câu nhưng không hiểu “mục điều khoản”, nên vừa dễ tách điều kiện khỏi ngoại lệ, vừa không có overlap để bù. Đáng chú ý: với **mock** embedder, recursive từng đứng cao trong nhóm; khi chuyển local thì tụt hạng — minh họa rõ không nên chọn strategy dựa trên mock.

**Trương Minh Tâm — MarkdownHeadingChunker (custom)**  
- **Loại:** Custom (heading)  
- **Mô tả & lý do:** Chính sách viết theo điều khoản có `##`/`###`. Cắt theo heading để giữ quy tắc + điều kiện + ngoại lệ trong một chunk — đúng giả thuyết ban đầu của nhóm (“heading phải thắng”). Hai tinh chỉnh bắt buộc: gộp mục quá ngắn (heading cha chỉ có tiêu đề); mục quá dài cắt tiếp bằng recursive nhưng **gắn lại tiêu đề** lên từng mảnh để không mất ngữ cảnh.  
- **Code snippet:**
```python
class MarkdownHeadingChunker:
    def chunk(self, text: str) -> list[str]:
        sections = self._split_sections(text)          # [(heading, body)]
        merged = self._merge_short_sections(sections)  # gộp mục quá ngắn
        chunks = []
        for heading, body in merged:
            block = f"{heading}\n{body}".strip()
            if len(block) <= self.chunk_size:
                chunks.append(block)
            else:
                for i, piece in enumerate(RecursiveChunker(chunk_size=self.chunk_size).chunk(body)):
                    chunks.append(f"{heading}\n{piece}".strip() if heading and i else piece.strip())
        return [c for c in chunks if c]
```
- **Kết quả:** **5/10**. Doc@3 = 5/5 (tìm đúng tài liệu rất tốt, ngang Sentence) nhưng evid@1 chỉ 2/5: chunk chứa đáp án thường xếp hạng 2–3. Nguyên nhân không phải cắt sai ranh giới, mà là **pha loãng tín hiệu** khi cosine trung bình hoá chunk dài (~497 ký tự).

**Trần Minh Hiển — RecursiveChunker (300)**  
- **Loại:** Recursive (tinh chỉnh tham số)  
- **Mô tả & lý do:** Cùng thuật toán với Recursive 500 của Khôi, chỉ giảm `chunk_size` để kiểm giả thuyết “chunk ngắn hơn → tín hiệu đậm hơn” mà không đổi separator. Đây là phép A/B sạch nhất trong nhóm: nếu điểm tăng thì nguyên nhân gần như chắc chắn nằm ở độ dài chunk, không phải ở logic cắt mới.  
- **Code snippet:**
```python
chunker = RecursiveChunker(chunk_size=300)
```
- **Kết quả:** **5/10** trên đối chứng local (`data/shopee-return-refund`, 323 chunk, TB ~194). Hơn Recursive 500 **một điểm** trên cùng lần chạy (cứu thêm câu 3 vào top-3), nhưng vẫn miss câu 2 (dòng bảng) và câu 5 (điều kiện rải nhiều tài liệu). Kết luận: tinh chỉnh size có ích, nhưng chưa đủ để bắt Sentence nếu không tôn trọng ranh giới câu.

### So Sánh Giữa Các Thành Viên

Số liệu chính lấy từ lần chạy nhóm với embedding local. Khi đối chứng lại trên corpus `data/shopee-return-refund`, điểm tuyệt đối có thể lệch ±1 nhưng **thứ hạng giữ nguyên hướng** (Sentence vẫn nhất; Recursive 300 ≥ Recursive 500).

| Thành viên | Chiến lược | Điểm (/10, local) | Điểm mạnh | Điểm yếu |
|------------|------------|-------------------|-----------|----------|
| Phạm Hải Yến | Sentence 3 câu | **8** | Tín hiệu đậm; evid@3 đủ 5/5 | Nhiều chunk; dễ mất ngữ cảnh mục |
| Trần Văn Toàn | Fixed 500/50 | 6 | Overlap cứu biên chunk | Cắt bảng/câu |
| Trần Hoàng Khôi | Recursive 500 | 5 | Tôn trọng đoạn/câu | Không gắn “mục”; dễ miss bằng chứng |
| Trương Minh Tâm | Heading custom | 5 | Ít chunk; giữ điều khoản trọn | Chunk dài → đáp án tụt hạng |
| Trần Minh Hiển | Recursive 300 | 5 | A/B sạch với Recursive 500; mịn hơn | Vẫn miss Q2/Q5; kém Sentence |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **Sentence (Phạm Hải Yến, 8/10)** tốt nhất nếu mục tiêu là độ chính xác top-3 thuần túy. Cosine so sánh vector trung bình của cả chunk, nên chunk ngắn làm câu chứa đáp án “nổi” hơn. Heading của Tâm đúng về cấu trúc tài liệu (giữ quy tắc + ngoại lệ) và tiết kiệm token (~36% ít chunk hơn Sentence), nhưng thường đẩy bằng chứng xuống hạng 2–3 — nên chỉ hợp khi chấp nhận tăng `top_k` hoặc cắt thêm mục dài. Recursive 300 của Hiển xác nhận giả thuyết độ dài: cùng recursive, size nhỏ hơn thì tốt hơn một chút, nhưng chưa đủ để bắt Sentence nếu không cắt theo câu.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-----------------|---------------------------------|---------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu THHT sau khi giao thành công? Thực phẩm tươi sống/đông lạnh có khác không? | Hầu hết **15 ngày**; thực phẩm tươi sống/đông lạnh: **24 giờ** (trừ chưa nhận hàng). | `buyer-return-eligibility` mục 1.2; `return-refund-policy` Điều 3.2 |
| 2 | Thanh toán thẻ tín dụng/ghi nợ: tiền hoàn về đâu, mất bao lâu? | Về **đúng thẻ đã dùng**; **7–14 ngày làm việc**. | `buyer-refund-timeline` Bảng 1 |
| 3 | Sau khi được chấp nhận THHT, có những hình thức gửi hàng hoàn nào? Hình thức nào miễn phí? | Lấy hàng tại nhà (miễn phí), bưu cục (miễn phí), tự sắp xếp (hỗ trợ phí theo chính sách). | `buyer-return-shipping` mục 1.1 |
| 4 | *(Seller + filter)* Khi Shopee hoàn tiền ngay, Người bán khiếu nại trong bao lâu? Shopee xử lý bao lâu? | Khiếu nại **2 ngày**; Shopee xem xét **3–5 ngày làm việc**. | `seller-refund-appeal`; `seller-return-process` B.1 |
| 5 | Ai được trả hàng vì đổi ý (COM)? Có hạn chế sản phẩm nào không? | Từ 24/11/2025: hạng **Kim Cương/Vàng** hoặc **Shopee VIP**; không áp dụng danh sách hạn chế / Shopee Mart. | `buyer-return-eligibility` 1.3; policy Điều 4 |

Độ phủ: số liệu (1–2), liệt kê (3), quy trình + thời hạn seller (4), điều kiện/ngoại lệ (5). Câu 4 bắt buộc dùng metadata filter theo yêu cầu K4.

### Cách chấm: mức chunk, không chỉ doc_id

Nếu chỉ kiểm “top-3 có đúng `doc_id` không”, một strategy có thể chiếm cả ba slot bằng đúng tài liệu nhưng **không chunk nào chứa câu trả lời**. Vì vậy mỗi câu khai báo chuỗi bằng chứng phải xuất hiện trong nội dung chunk (ví dụ câu 1: “24 giờ” / “thực phẩm tươi sống”; câu 2: “7–14 ngày làm việc”; câu 4: “2 ngày” / “3–5 ngày làm việc”).

### Tổng hợp chất lượng truy xuất của nhóm

Theo `docs/SCORING.md`: 2đ nếu bằng chứng hạng 1 + trả lời đúng; 1đ nếu có trong top-3 nhưng không hạng 1 / thiếu chi tiết; 0đ nếu không có trong top-3.

| # | Câu hỏi | Chiến lược tốt nhất | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|---------------------|----------------------------------|---------|
| 1 | Thời hạn gửi yêu cầu | Hầu hết strategy FULL | Có | Từ khoá “thực phẩm tươi sống” đặc trưng, dễ nổi |
| 2 | Hoàn tiền thẻ | Sentence / Heading (thường 1đ) | Một phần | Đáp án nằm **một dòng bảng** — Fixed/Recursive hay MISS |
| 3 | Hình thức gửi hàng hoàn | Sentence (2đ) | Có | Recursive 300 của Hiển được 1đ trên đối chứng |
| 4 | Khiếu nại người bán | Fixed / Sentence / Recursive | Có (khi filter `seller`) | Filter làm top-3 sạch vai; score retrieval thường rất cao |
| 5 | Trả hàng COM | Fixed / Sentence (1đ) | Một phần | Bằng chứng rải nhiều tài liệu; Heading/Recursive dễ MISS |

**Hai failure pattern nhóm quan sát được:**
1. **Đúng chủ đề, sai dữ liệu:** chunk có tiêu đề trùng query (ví dụ “mốc thời gian khiếu nại”) đứng hạng 1 nhưng thân chunk không chứa con số; chunk có “2 ngày” đứng hạng 2 với score chỉ thấp hơn rất ít (~0.002). Embedding tốt hơn **không sửa** kiểu lỗi này — cần tín hiệu từ vựng/rerank bổ sung.  
2. **Đúng tài liệu, sai mục:** đặc biệt câu 2 — top-3 toàn `buyer-refund-timeline` nhưng không có dòng “7–14 ngày làm việc”. Bảng nhiều hàng bị trung bình hoá thành “bảng thời gian hoàn tiền nói chung”, nên tín hiệu riêng của dòng thẻ tín dụng bị pha loãng.

**Mock vs local (tóm tắt):** cùng corpus/cùng câu, mock có thể xếp Recursive cao và Sentence thấp; local thì đảo lại. Vì vậy nhóm chỉ dùng số liệu local để kết luận strategy. Ba kết luận sống sót qua cả hai backend: (1) chấm doc_id thổi phồng hơn chấm chunk, (2) score cao ≠ nội dung đúng, (3) filter `both` luôn làm mất một phần corpus bất kể embedder.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có ích rõ nhất ở **câu 4**. Không lọc, top-k dễ lẫn chunk buyer vào ngữ cảnh khiếu nại seller; có filter `customer_role=seller` thì top-3 sạch vai hơn. Với local embedder, filter không phải lúc nào cũng tăng điểm số (vì ranking đã khá tốt, thậm chí câu 2 top-3 gần như không đổi), nhưng giảm rủi ro agent trả lời sai vai — rủi ro mà metric evidence-hit không bắt hết. Chi phí đi kèm: file `role=both` (~1/4 chunk) bị loại hoàn toàn khi filter theo buyer/seller vì khớp metadata chính xác. Nếu làm lại, nên gắn role ở mức chunk (ví dụ Điều dành cho Người bán trong policy), không gắn cả file.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Embedder là nền của phép đo:** mock và local có thể đảo thứ hạng (recursive từng “thắng” trên mock rồi tụt khi có ngữ nghĩa thật).  
2. **Chấm theo doc_id dễ thổi phồng;** phải chấm bằng chứng trong chunk. Score cao ≠ có đáp án.  
3. **Chunk ngắn vs chunk theo heading là đánh đổi thật:** Sentence thắng precision; Heading thắng ngữ cảnh đọc và chi phí lưu trữ.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng corpus và cùng 5 câu, chỉ khác cách cắt đã lệch khoảng 3 điểm (8 vs 5). Giả thuyết “heading tốt nhất cho văn bản chính sách” nghe rất hợp lý về cấu trúc, nhưng đo thật thì Sentence thắng vì cosine trung bình hoá cả chunk — chunk dài làm đáp án bị pha loãng. Recursive 300 của Hiển cho thấy chỉ cần tinh chỉnh size trong cùng họ recursive cũng đủ đổi điểm, dù chưa đủ để bắt Sentence.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu?**
> Cài local embedding ngay từ đầu thay vì kết luận trên mock; gắn `customer_role` ở mức chunk thay vì cả file `both`; xử lý bảng theo hàng (lặp tiêu đề cột) vì câu hoàn tiền thẻ chưa ai đạt điểm tối đa; thử heading với `chunk_size` nhỏ hơn để giữ ranh giới mục mà vẫn giữ mật độ tín hiệu.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **36 / 40** |
