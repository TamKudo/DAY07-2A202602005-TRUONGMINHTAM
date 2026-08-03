# Bộ 5 Benchmark Query + Gold Answer — **BẢN ĐẦU (v1), ĐÃ THAY THẾ**

> ⚠️ **Đây không phải bộ query đang dùng.** Tài liệu này ghi lại bộ query **bản đầu**, xây trên corpus v1
> (`data/data-canhan/`, 7 file crawl HTML bị duỗi thành text phẳng). Các `doc_id` ở đây
> (`quan-ly-don-tra-hang-hoan-tien`, `chinh-sach-tra-hang-hoan-tien`…) **không còn tồn tại** trong corpus
> hiện tại.
>
> **Bộ 5 query chính thức của nhóm** — chạy trên `data/data-nhom/` — nằm ở **`REPORT_NHOM.md` mục 3**, và là
> bộ được khai báo trong `bench.py` (hằng `QUERIES`). Giữ file này để đối chứng quá trình: nó cho thấy bộ
> query đã được viết lại thế nào sau khi nhóm đổi sang corpus có heading Markdown sạch, đặc biệt là Q2 (viết
> lại thành câu hỏi trung lập vai) và việc bổ sung **chuỗi bằng chứng** cho từng query.

Corpus (v1): `data/data-canhan/` (7 tài liệu, nguồn Shopee Trung tâm trợ giúp, thu thập 2026-08-03).
Mọi gold answer dưới đây đều trích được từ corpus — không dùng kiến thức ngoài. Cột "Nguồn" ghi `doc_id:dòng`
theo file `.md` đã làm sạch để đối chiếu khi chấm retrieval.

Quy ước đánh giá: một lần retrieval được tính là **hit** nếu chunk trả về chứa được nội dung ở cột "Câu chốt".

---

## Q1 — Người mua được hoàn tiền trong bao lâu sau khi gửi trả hàng?

- **metadata_filter**: `{"customer_role": "buyer"}`
- **Tài liệu vàng**: `thoi-gian-nhan-tien-hoan`
- **Nguồn**: `thoi-gian-nhan-tien-hoan.md:16`, bảng ở `:22-95`, lưu ý ở `:101`

**Gold answer:** Thời gian hoàn tiền phụ thuộc vào phương thức thanh toán, tính từ khi Shopee chấp nhận
hoàn tiền: Ví ShopeePay **24 giờ** (với điều kiện ví vẫn hoạt động bình thường); tài khoản ngân hàng mặc
định liên kết với Shopee **2 ngày làm việc** (tùy ngân hàng); tài khoản ngân hàng ban đầu qua ứng dụng ngân
hàng **7 ngày làm việc**; thẻ nội địa Napas **2–5 ngày làm việc**; thẻ tín dụng/ghi nợ, Apple Pay và Google
Pay **7–14 ngày làm việc** (tùy ngân hàng); SPayLater hoàn về mục Giao dịch trong **24 giờ**. Nếu Người bán
khiếu nại trong quá trình xử lý, Shopee xem xét và thông báo kết quả cuối cùng trong **3–5 ngày làm việc**.

**Câu chốt (bắt buộc có trong chunk để tính hit):** dải thời gian theo phương thức thanh toán (24 giờ /
2 ngày làm việc / 7 ngày làm việc / 2–5 ngày / 7–14 ngày).

**Bẫy thường gặp:** chunk chỉ lấy được tiêu đề bảng mà mất phần giá trị thời gian — bảng HTML bị duỗi thành
các dòng rời, nên chunker cắt quá nhỏ sẽ tách "Ví ShopeePay" khỏi "24 giờ".

---

## Q2 — Khi hàng hoàn trả bị thất lạc hoặc hư hỏng trên đường về, ai chịu trách nhiệm và cần làm gì?

- **metadata_filter**: `{"customer_role": "seller"}` / `{"customer_role": "buyer"}`  ← **query bắt buộc theo K4_VARIANT.md**
- **Loại câu hỏi:** quy trình + trách nhiệm (**query ẩn danh** — không nêu vai trong câu hỏi)
- **Tài liệu vàng (seller)**: `quan-ly-don-tra-hang-hoan-tien`, `quan-ly-don-giao-khong-thanh-cong`
- **Tài liệu vàng (buyer)**: `quy-trinh-xu-ly-yeu-cau-tra-hang`, `chinh-sach-tra-hang-hoan-tien`

Đây là query **cùng chủ đề, cùng từ vựng, khác đáp án**: cả hai vai đều có nội dung về hàng hoàn trả bị thất
lạc/hư hỏng, nhưng việc phải làm hoàn toàn khác nhau. Câu hỏi cố tình không nêu "người mua" hay "người bán",
nên **chỉ `metadata_filter` mới quyết định được đáp án nào là đúng** — đó là điều query này dùng để chứng minh.

### Gold answer A — nhánh `customer_role: seller`

- **Nguồn**: `quan-ly-don-tra-hang-hoan-tien.md:52`, `:64`, `:76-84`;
  `quan-ly-don-giao-khong-thanh-cong.md:44`, `:46`, `:50`

Người bán chọn **Thêm chi phí** và nhập số tiền ứng với giá vốn hàng hoàn khi hàng thất lạc hoặc không còn
nguyên vẹn. Người bán **không thực sự mất chi phí**: khi hàng hoàn bị thất lạc, hệ thống tự hiển thị khoản
**Đền bù** từ Shopee tại cột Đền bù. Nếu hàng hoàn **bị hư hỏng**, Người bán cần nhanh chóng **liên hệ CSKH**
để được hỗ trợ và khiếu nại kịp thời. Thời hạn phản hồi: nếu hệ thống ghi nhận đã trả hàng thành công nhưng
shop chưa nhận được hàng hoặc hàng gặp vấn đề, phải phản hồi **trong vòng 2 ngày** kể từ ngày hệ thống cập
nhật. Nên **quay video mở hàng** để có bằng chứng xác thực.

**Câu chốt A:** "Thêm chi phí" + khoản đền bù từ Shopee, hoặc mốc phản hồi 2 ngày, hoặc liên hệ CSKH.

### Gold answer B — nhánh `customer_role: buyer`

- **Nguồn**: `chinh-sach-tra-hang-hoan-tien.md:132`;
  `quy-trinh-xu-ly-yeu-cau-tra-hang.md:252`, `:273`, `:275`, `:277`

Người mua chịu trách nhiệm **phòng ngừa từ khâu gửi trả**: phải đóng gói Sản Phẩm Hoàn Trả theo quy định
Chính Sách Vận Chuyển, gửi kèm **toàn bộ phụ kiện, hóa đơn GTGT, tem phiếu bảo hành**, và Sản Phẩm phải
**nguyên vẹn như khi nhận hàng**; **bắt buộc quay video và/hoặc chụp ảnh** Sản Phẩm ngay khi nhận và **trong
lúc đóng gói** hàng hoàn trả để làm bằng chứng đối chiếu về sau. Nếu hàng bị Shopee trả ngược lại (không đáp
ứng tiêu chí mục 4), lưu ý **Shopee không hỗ trợ đồng kiểm** với đơn hoàn về người mua, nên khi nhận lại phải
kiểm tra kỹ ngoại quan kiện hàng và **quay video toàn bộ quá trình mở hàng**; nếu sản phẩm nhận về có vấn đề
hoặc ĐVVC cập nhật sai trạng thái thì **liên hệ ngay CSKH Shopee**.

**Câu chốt B:** quay video lúc đóng gói/mở hàng + đóng gói nguyên vẹn kèm phụ kiện + không có đồng kiểm.

### Đối chiếu hai đáp án

| | Nhánh `seller` | Nhánh `buyer` |
|---|---|---|
| Vai trò | Bên **nhận** hàng hoàn về | Bên **gửi** hàng hoàn đi |
| Việc phải làm | Thêm chi phí → nhận đền bù từ Shopee | Đóng gói đúng quy định + quay video làm bằng chứng |
| Mốc thời gian | Phản hồi trong **2 ngày** | Không có mốc — yêu cầu về **bằng chứng** |
| Kênh xử lý | Kênh Quản Lý Shop (kế toán, nhập kho) | Ứng dụng Shopee (theo dõi vận đơn, CSKH) |

Hai cột khác nhau ở *nội dung đáp án*, không chỉ ở mức độ chi tiết — đây là bằng chứng cho thấy filter đang
thay đổi câu trả lời chứ không chỉ lọc bớt nhiễu.

### Hai phát hiện tách bạch về metadata filter

**(1) Filter là điều kiện cần để trả lời đúng.** Từ khóa "thất lạc / hư hỏng / hoàn trả" xuất hiện ở 4/7 tài
liệu. Đo thực tế (chunker `recursive`, mock embeddings), top-3 **không filter** cho ra
`chinh-sach(both)`, `quy-trinh-xu-ly(buyer)`, `quy-dinh-chung(buyer)` — **không một chunk seller nào**. Bật
`metadata_filter={"customer_role":"seller"}` mới ra đúng `quan-ly-don-tra-hang-hoan-tien` ×2 +
`quan-ly-don-giao-khong-thanh-cong`. Nếu hỏi theo vai người bán mà không filter, agent sẽ trả lời bằng quy
trình dành cho người mua — sai tình huống, dù mọi chunk đều "liên quan" về mặt từ khóa.

**(2) Filter có false negative — và đây là quy luật, không phải ca lẻ.** Mục **"5. QUYỀN CỦA NGƯỜI BÁN"**
(`chinh-sach-tra-hang-hoan-tien.md:128`) nói đúng tình huống "Sản Phẩm Hoàn Trả bị hư hỏng, mất mát trong quá
trình hoàn trả" và nêu hạn phản hồi **02 ngày lịch** cho Người Bán — nội dung seller thực chất, nhưng nằm
trong file gắn `customer_role: both`, nên `filter=seller` **loại mất nó**.

Điều đáng nói là **hiện tượng này đối xứng ở cả hai nhánh**, không riêng seller. Gold answer B (buyer) cũng
trích `chinh-sach-tra-hang-hoan-tien.md:132` — cùng file `both` đó. Vì `search_with_filter` so khớp chính xác
từng cặp key/value (`record["metadata"].get(key) == value`, `src/store.py:107`), giá trị `"both"` **không**
khớp `"buyer"` lẫn `"seller"`. Đo thực tế xác nhận: với cùng câu Q2, `filter=seller` trả về 5 kết quả toàn
role `seller`, `filter=buyer` trả về 5 kết quả toàn role `buyer` — **không nhánh nào có chunk `both` lọt qua**.

Quy mô của vấn đề: **60/129 chunk (47%) của corpus mang `customer_role: both`**. Nghĩa là gần một nửa kho tri
thức bị vô hiệu hoá mỗi khi bật filter theo vai — kể cả khi nội dung của nó đúng cho vai đang hỏi. Đây không
phải một ca lẻ mà là **hệ quả có hệ thống của việc gắn tag ở mức file thay vì mức chunk**: metadata filter
tăng precision nhưng giảm recall, và mức giảm tỷ lệ thuận với lượng tài liệu "dùng chung".

May mắn là ở cả hai nhánh, chunk `both` bị mất đều chỉ là nguồn **bổ trợ/trùng lặp**, không phải nguồn duy
nhất: nhánh seller còn `quan-ly-don-tra-hang-hoan-tien.md:64`, `:76-84` (role `seller` thuần) giữ đủ hạn 2
ngày và khoản đền bù; nhánh buyer còn `quy-trinh-xu-ly-yeu-cau-tra-hang.md:252`, `:273`, `:275`, `:277`
(role `buyer` thuần) giữ đủ yêu cầu quay video và cảnh báo không đồng kiểm — đo thực tế cho thấy
`quy-trinh-xu-ly-yeu-cau-tra-hang` **có** trong top-10 của `filter=buyer`. Vì vậy đáp án cuối ở cả hai nhánh
vẫn đúng và đủ, và Q2 giữ nguyên giá trị là phép thử "chỉ đúng khi có filter".

Chúng tôi **giữ nguyên corpus** thay vì tách file để gắn role "sạch" hơn, vì chính ca này là bằng chứng thật
về ranh giới của metadata filter. Ba hướng khắc phục nếu làm tiếp, theo thứ tự ưu tiên:
1. Gắn `customer_role` ở **mức chunk** (theo mục/điều khoản) thay vì mức file — mục 5 và mục 7 của
   `chinh-sach` rõ ràng là seller, mục 6 là buyer.
2. Cho `both` **luôn lọt qua** mọi filter vai (sửa điều kiện thành `value in (record_value, "both")`) — rẻ và
   nhanh, nhưng kéo lại nhiễu mà filter vốn sinh ra để loại.
3. Dùng filter làm **tín hiệu xếp hạng** (boost) thay vì điều kiện loại cứng — giữ được cả precision lẫn
   recall, nhưng phức tạp hơn và vượt phạm vi lab này.

---

## Q3 — Những voucher/mã giảm giá nào không được hoàn lại khi trả hàng?

- **metadata_filter**: không (kiểm tra retrieval thuần ngữ nghĩa)
- **Tài liệu vàng**: `quy-dinh-chung-tra-hang-hoan-tien`
- **Nguồn**: `quy-dinh-chung-tra-hang-hoan-tien.md:216`, `:218`, `:186`, `:210`, `:220`

**Gold answer:** Không được hoàn lại trong **bất kỳ trường hợp nào**: Voucher Shopee Live, Video Voucher,
Voucher Người dùng mới Shopee, Voucher Người dùng mới Shopee Pay, Voucher Người dùng mới SPayLater — nếu
voucher **đã hết hiệu lực hoặc hết lượt sử dụng**. Shop Voucher (mã do Người bán phát hành) và **Mã miễn phí
vận chuyển** cũng không được hoàn lại trong bất cứ trường hợp nào (có thể liên hệ Người bán để được hỗ trợ).
Ngoài ra, mã giảm giá **không được hoàn** khi khiếu nại chỉ trên một/một vài sản phẩm, và khi Hoàn tiền ngay
với lý do khác "Chưa nhận được hàng" hoặc "Hàng rỗng". Khi được hoàn, mã trả lại trong vòng **48 giờ**
(không kể Thứ 7, Chủ nhật và ngày lễ).

**Câu chốt:** danh sách voucher không hoàn + Shop Voucher/Mã miễn phí vận chuyển.

**Bẫy thường gặp:** câu trả lời nằm rải ở cả bảng điều kiện (`:146-212`) lẫn phần Lưu ý (`:214-224`).
Chunk theo heading giữ được cả cụm; chunk cố định 300 ký tự dễ trả về nửa bảng, thiếu vế "không hoàn".

---

## Q4 — Người bán xử lý đơn giao không thành công như thế nào trên Kênh Quản Lý Shop?

- **metadata_filter**: `{"customer_role": "seller"}`
- **Tài liệu vàng**: `quan-ly-don-giao-khong-thanh-cong`
- **Nguồn**: `quan-ly-don-giao-khong-thanh-cong.md:20`, `:28`, `:34-48`, `:82-98`

**Gold answer:** Hệ thống **tự động ghi nhận** các đơn Shopee giao không thành công; Người bán vào mục
**Giao Không Thành Công** trong tính năng Đơn hàng, chọn **Trạng thái hoàn** để lọc. Có hai tình huống xử lý:
(1) hàng trả về thành công và nguyên vẹn → chọn **Nhập lại vào kho**, hoặc **Đồng ý nhập kho trực tiếp** rồi
Xác nhận để nhập nhanh không cần phiếu nhập; (2) hàng thất lạc hoặc không còn nguyên vẹn → chọn **Thêm chi
phí**, nhập vào cột **Chi phí khác**; nếu thất lạc, khoản đền bù từ Shopee tự hiển thị ở cột Đền bù; nếu hư
hỏng thì liên hệ CSKH. Về kế toán: khi nhập lại kho, hệ thống tự giảm trừ tương ứng Doanh thu, Giá vốn hàng
bán và Lợi nhuận gộp (xem tại Nhật Ký Giao Dịch); chi phí thất thoát được ghi nhận dưới dạng chi phí khác ở
mục Kết Quả Kinh Doanh.

**Câu chốt:** hai nhánh xử lý "Nhập lại vào kho" và "Thêm chi phí".

**Bẫy thường gặp:** trùng nhiều thuật ngữ với `quan-ly-don-tra-hang-hoan-tien` (cùng `customer_role: seller`,
cùng nói "Thêm chi phí", "nhập kho") — metadata filter **không** tách được hai file này, phải dựa vào chất
lượng embedding. Đây là ví dụ cho thấy giới hạn của metadata filter.

---

## Q5 — Người mua có bắt buộc phải gửi trả hàng để được hoàn tiền không?

- **metadata_filter**: `{"customer_role": "buyer"}`
- **Tài liệu vàng**: `quy-trinh-xu-ly-yeu-cau-tra-hang`
- **Nguồn**: `quy-trinh-xu-ly-yeu-cau-tra-hang.md:48`, `:50`, `:52`;
  đối chiếu `quy-dinh-chung-tra-hang-hoan-tien.md:156`

**Gold answer:** **Không bắt buộc trong mọi trường hợp.** Khi yêu cầu Trả hàng/Hoàn tiền được chấp nhận,
Shopee quyết định 1 trong 2 phương án tùy tính chất sản phẩm hoặc đơn hàng: (1) **Hoàn Tiền Ngay** — người
mua nhận tiền hoàn **mà không cần trả hàng**; (2) **Trả hàng & Hoàn tiền** — người mua phải chọn hình thức
trả hàng và hoàn tất gửi trả về kho Shopee/Người bán **trong vòng 6 ngày** kể từ thời điểm nhận được thông
báo gửi trả hàng từ Shopee.

**Câu chốt:** phân biệt hai phương án + mốc 6 ngày của phương án Trả hàng & Hoàn tiền.

**Bẫy thường gặp:** câu hỏi dạng có/không, dễ bị trả lời cụt "có" nếu chunk chỉ bắt được phương án (2).
Chunk phải giữ được cả hai nhánh ở `:48-52` mới trả lời đúng.

---

## Tổng hợp — bộ 5 query đã khóa

| Query | Loại câu hỏi | metadata_filter | Tài liệu vàng | Vai trò trong benchmark |
|---|---|---|---|---|
| Q1 | **Số liệu** (thời hạn) | `customer_role=buyer` | thoi-gian-nhan-tien-hoan | Kiểm tra giữ bảng số liệu khi chunk |
| Q2 | **Quy trình + trách nhiệm** | `seller` / `buyer` | quan-ly-don-* / quy-trinh-xu-ly | **Query ẩn danh — phép thử chính của filter** |
| Q3 | **Liệt kê + ngoại lệ** | không | quy-dinh-chung-tra-hang-hoan-tien | Baseline retrieval thuần ngữ nghĩa |
| Q4 | **Quy trình thao tác** | `customer_role=seller` | quan-ly-don-giao-khong-thanh-cong | Giới hạn filter (2 doc cùng role) |
| Q5 | **Điều kiện** (có/không) | `customer_role=buyer` | quy-trinh-xu-ly-yeu-cau-tra-hang | Câu hỏi có/không, cần giữ đủ 2 nhánh |

**Độ phủ loại câu hỏi:** số liệu (Q1) · điều kiện (Q5) · quy trình (Q2, Q4) · liệt kê (Q3) · ngoại lệ (Q3 —
"không hoàn lại trong bất kỳ trường hợp nào"). Q2 phủ thêm *trách nhiệm/vai trò*, loại câu hỏi chỉ trả lời
được khi biết ngữ cảnh người hỏi là ai.

**Đáp ứng `K4_VARIANT.md`:** Q2 và Q4 dùng `metadata_filter={"customer_role": "seller"}`, Q1/Q5 dùng `buyer`,
Q2 chạy được cả hai nhánh; toàn bộ gold answer trích từ corpus nhóm, không dùng nguồn ngoài.

**Trạng thái:** bộ query **đã khóa** — mọi kết quả `bench.py` chạy sau đều dựa trên đúng 5 câu hỏi này.
