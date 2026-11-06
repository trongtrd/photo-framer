# Menus / Lựa chọn

The short display names map to the same existing codes: Shadow / Ảnh nổi (A),
Gallery / Khung gallery (B), Specs / Thông số (C), Specs + Text / Thông số + chữ riêng (D),
Color / Viền màu (E), Film / Viền phim (F), Paper / Giấy xé (G), Canvas / Khung tỷ lệ (H).
Use names and appearance descriptions when helping someone choose. The detailed
menus below retain their previous names and frozen choice codes for compatibility.

Use the user's language. Preserve codes: A floating photo, B gallery frame, C print/spec card, D spec card with custom right-side text, E Color Echo, F Film Edge, G Deckled Paper, H Minimal Mat. Default style A; default settings **A, 2-2-1**, **B, 1-2-1**, **C/D/E/F/G, 2-1-1**, **H, 1-1-1**.

## Tiếng Việt

**Chọn phong cách:** A — Ảnh nổi (mặc định); B — Khung gallery; C — Thẻ thông số; D — Thẻ thông số có chữ riêng; E — Color Echo / Viền đồng sắc; F — Film Edge / Viền phim; G — Deckled Paper / Giấy mỹ thuật mép xé; H — Minimal Mat / Khung tối giản.

### A — Ảnh nổi
<!-- generated:menu-vi-A -->
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Khoảng trắng | Hẹp | **Vừa — mặc định** | Rộng |
| Bóng đổ | Nhẹ | **Mềm vừa — mặc định** | Rõ |
| Nền | **Trắng — mặc định** | Trắng ngà | Xám rất nhạt |
<!-- /generated:menu-vi-A -->

Trả lời theo thứ tự **khoảng trắng–bóng–nền**, ví dụ `2-2-1`, hoặc `mặc định`.
"Mềm vừa" là mức bóng đã tăng và được duyệt, không phải bóng mờ của bản thử đầu.

### B — Khung gallery
<!-- generated:menu-vi-B -->
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Màu khung | **Đen — mặc định** | Trắng | Xám than |
| Bo giấy trắng | Hẹp | **Vừa — mặc định** | Rộng |
| Nền ngoài khung | **Xám — mặc định** | Trắng | Trắng ngà |
<!-- /generated:menu-vi-B -->

Trả lời theo thứ tự **khung–bo giấy–nền**, ví dụ `1-3-1`, hoặc `mặc định`.
Bóng trong/ngoài và độ dày khung phối sẵn; bo giấy luôn trắng ở v0.1.

### C — Thẻ thông số (print/spec card)
<!-- generated:menu-vi-C -->
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Viền | Hẹp | **Vừa — mặc định** | Rộng |
| Nền | **Trắng — mặc định** | Trắng ngà | Xám rất nhạt |
| Chữ | **Máy + ống kính + thông số — mặc định** | Chỉ máy + ống kính | Không chữ |
<!-- /generated:menu-vi-C -->

Trả lời theo thứ tự **viền–nền–chữ**, ví dụ `2-1-1`, hoặc `mặc định`.
Thông số đọc tự động từ EXIF/XMP của ảnh, không tự bịa; logo hãng gắn theo máy chụp,
hãng chưa có logo thì dùng chữ đậm. Mã máy quen thuộc hiện bằng tên thương mại
(`ILCE-7C` → `α7C`), không lặp lại tên hãng đã có trên logo. Ảnh mất metadata (ví dụ scan phim) có thể tự nhập máy, ống kính,
ISO, khẩu, tốc, tiêu cự; nếu không, sẽ được hỏi trước khi bỏ chữ.

### D — Thẻ thông số có chữ riêng
<!-- generated:menu-vi-D -->
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Viền | Hẹp | **Vừa — mặc định** | Rộng |
| Nền | **Trắng — mặc định** | Trắng ngà | Xám rất nhạt |
| Thông tin bên trái | **Máy + ống kính + thông số — mặc định** | Chỉ máy + ống kính | Không thông tin |
<!-- /generated:menu-vi-D -->

Trả lời theo thứ tự **viền–nền–thông tin bên trái**, ví dụ `2-1-1`, hoặc `mặc định`.
Đọc EXIF/XMP như C, thay logo bằng chữ bạn cung cấp ở góc dưới bên phải.
Chữ bên phải dùng cùng font, cỡ, độ đậm và màu với dòng máy/ống kính;
vẫn hiện khi chọn 3 ở hàng cuối. Không tự thu nhỏ hoặc cắt chữ cho vừa.

Nếu chưa có nội dung, hỏi: **Bạn muốn điền chữ gì ở góc dưới bên phải?**
Có thể điền địa điểm, tên người chụp, thời gian hoặc kết hợp; dùng nguyên văn,
không suy đoán từ metadata. Ví dụ: `Berlin, Germany | October 2022`.
Nếu đã cung cấp nội dung, không hỏi lại.

### E — Color Echo / Viền đồng sắc
<!-- generated:menu-vi-E -->
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Độ rộng viền | Hẹp | **Vừa — mặc định** | Rộng |
| Sắc độ màu tự chọn | **Dịu — mặc định** | Tự nhiên | Sáng |
| Đường viền trong | **Mảnh — mặc định** | Không có | Vừa |
<!-- /generated:menu-vi-E -->

Trả lời theo thứ tự **độ rộng–sắc độ tự chọn–viền trong**, mặc định `2-1-1`.
Mặc định, Python tự chọn một màu cho mỗi ảnh; chạy cả lô mà không hỏi lại từng
ảnh và không tạo ba phương án màu. Chỉ tạo bản xem trước khi được yêu cầu.
Nếu muốn một màu chung cho cả bộ, cung cấp màu một lần: `--frame-color "#ad896c"`.
Màu chung được dùng nguyên giá trị, không chịu tùy chọn sắc độ ở hàng thứ hai.
Ảnh gần trắng đen dùng màu trung tính dự phòng; pixel vùng ảnh được giữ nguyên.

### F — Film Edge / Viền phim
<!-- generated:menu-vi-F -->
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Độ rộng viền | Hẹp | **Vừa — mặc định** | Rộng |
| Nền viền | **Than — mặc định** | Đen | Nâu đậm |
| Lỗ phim hai bên | **Tiêu chuẩn — mặc định** | Thưa | Dày |
<!-- /generated:menu-vi-F -->

Trả lời theo thứ tự **độ rộng–nền viền–lỗ phim**, mặc định `2-1-1`.
Hai cụm chữ đều do người dùng nhập. Nếu chưa đủ thông tin, hỏi cùng lúc:
**Bạn muốn ghi gì ở góc dưới trái và góc dưới phải? Có thể để trống từng bên.**
Giữ phần đã cung cấp; chỉ để trống khi người dùng chủ động chọn như vậy.
Ví dụ: trái `Berlin, Germany`, phải `October 2022`. Không tự điền số ảnh,
nhãn hãng phim, thời gian từ metadata hoặc chữ từ bản phác thảo.
Chữ hai bên dùng cùng font và cỡ; không tự cắt, viết hoa hoặc thu nhỏ cho vừa.

### G — Deckled Paper / Giấy mỹ thuật mép xé
<!-- generated:menu-vi-G -->
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Khoảng giấy quanh ảnh | Hẹp | **Vừa — mặc định** | Rộng |
| Màu giấy | **Trắng ấm — mặc định** | Trắng sáng | Ngà |
| Mép xé | **Nhẹ — mặc định** | Vừa | Rõ |
<!-- /generated:menu-vi-G -->

Trả lời theo thứ tự **khoảng giấy–màu giấy–mép xé**, mặc định `2-1-1`.
Vân giấy và bóng nhẹ chỉ nằm ngoài vùng ảnh hình chữ nhật. Mép xé là mép
ngoài của tờ giấy; ảnh không bị xé, đổi màu hay thêm hạt. Mẫu được tạo bằng
Python, không gọi AI cho từng ảnh. Chạy cùng thiết lập cho cả lô; mặc định
không có chữ hoặc logo. Có thể yêu cầu thêm chữ riêng trên khoảng giấy.

### H — Minimal Mat / Khung tối giản
<!-- generated:menu-vi-H -->
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Tỷ lệ khung | **4:5 dọc — mặc định** | 1:1 vuông | Theo ảnh gốc, viền mỏng |
| Nền | **Trắng — mặc định** | Xám ấm nhạt | Trắng ngà |
| Viền đen sát ảnh (keyline) | **Mảnh — mặc định** | Không có | Dày |
<!-- /generated:menu-vi-H -->

Trả lời theo thứ tự **tỷ lệ–nền–viền đen**, mặc định `1-1-1`.
Với 4:5 và 1:1, ảnh ngang hay dọc đều dùng chung một khung cố định: ảnh được
đặt vừa vào khung, căn giữa, không cắt và không thu nhỏ. 4:5 là khổ dọc lớn nhất
hiển thị trọn trong feed Instagram/Facebook, hợp màn hình điện thoại. Lựa chọn 3
chỉ thêm viền mỏng đều quanh ảnh theo đúng tỷ lệ ảnh. Mặc định không có chữ.
Bản chia sẻ JPEG của 4:5 và 1:1 có đúng kích thước 1080×1350 và 1080×1080.
Ngoài menu: `--ratio 3:4` hoặc `--ratio 9:16` (story, reels; bản chia sẻ 1080×1440,
1080×1920) và `--background blur` để dùng chính ảnh làm nền mờ, tối nhẹ, thay màu nền.
Nhãn gallery: `--title` (Inter SemiBold như D) và `--subtitle` (chữ xám nhỏ) căn giữa dưới ảnh,
dùng nguyên văn chữ bạn cung cấp; ảnh dịch lên để chừa chỗ.

H also supports `--ratio 16:9` for a fixed landscape canvas (share 1920×1080).
Blur works with every ratio: square blur is `--ratio 1:1 --background blur`;
landscape blur is `--ratio 16:9 --background blur`. The menu codes keep their meaning.

## English

**Choose style:** A — Floating photo (default); B — Gallery frame; C — Print / spec card; D — Custom spec card; E — Color Echo; F — Film Edge; G — Deckled Paper; H — Minimal Mat.

### A — Floating photo
<!-- generated:menu-en-A -->
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Margin | Narrow | **Medium — default** | Wide |
| Shadow | Light | **Soft medium — default** | Strong |
| Background | **White — default** | Ivory | Light gray |
<!-- /generated:menu-en-A -->

Reply in **margin–shadow–background** order, e.g. `2-2-1`, or `default`.

### B — Gallery frame
<!-- generated:menu-en-B -->
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Frame color | **Black — default** | White | Charcoal |
| White mat | Narrow | **Medium — default** | Wide |
| Outer background | **Gray — default** | White | Ivory |
<!-- /generated:menu-en-B -->

Reply in **frame–mat–background** order, e.g. `1-3-1`, or `default`.
Frame thickness and shadows are coordinated; mat remains white in v0.1.

### C — Print / spec card
<!-- generated:menu-en-C -->
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Margin | Narrow | **Medium — default** | Wide |
| Background | **White — default** | Ivory | Light gray |
| Caption | **Camera + lens + exposure — default** | Camera + lens only | No text |
<!-- /generated:menu-en-C -->

Reply in **margin–background–caption** order, e.g. `2-1-1`, or `default`.
Specs come from the photo's EXIF/XMP and are never invented; the brand logo follows
the camera body, with a bold text wordmark for brands without a bundled logo.
Known camera codes show their product name (`ILCE-7C` → `α7C`), never repeating
the brand the logo shows. Files without
metadata (e.g. film scans) can take typed camera, lens and exposure values;
otherwise they are flagged before text is skipped.

### D — Custom spec card
<!-- generated:menu-en-D -->
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Margin | Narrow | **Medium — default** | Wide |
| Background | **White — default** | Ivory | Light gray |
| Left-side details | **Camera + lens + exposure — default** | Camera + lens only | No details |
<!-- /generated:menu-en-D -->

Reply in **margin–background–left-side details** order, e.g. `2-1-1`, or `default`.
Capture details come from EXIF/XMP as in C. Your text replaces the logo at the
bottom right, using the same font, size, weight and color as the gear line.
The right-side text remains visible with option 3. It is never shrunk or truncated.

If the wording is missing, ask: **What exact text would you like at the bottom right?**
It can be a location, photographer name, date, or combination; preserve it verbatim
and never infer it from metadata. Example: `Berlin, Germany | October 2022`.
Do not ask again when the wording has already been supplied.

### E — Color Echo
<!-- generated:menu-en-E -->
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Border width | Narrow | **Medium — default** | Wide |
| Auto color tone | **Muted — default** | Natural | Light |
| Inner edge | **Thin — default** | None | Medium |
<!-- /generated:menu-en-E -->

Reply in **width–auto tone–inner edge** order, default `2-1-1`.
Python selects one color per photo and processes the whole batch without
per-image questions or three color variants. Generate previews only on request.
For a shared color, supply `--frame-color "#ad896c"` once for the batch; that
exact color bypasses auto analysis and ignores the auto-tone row.
Near-neutral images use a neutral fallback. Photo pixels stay unchanged.

### F — Film Edge
<!-- generated:menu-en-F -->
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Border width | Narrow | **Medium — default** | Wide |
| Border background | **Charcoal — default** | Black | Dark brown |
| Side sprockets | **Standard — default** | Sparse | Dense |
<!-- /generated:menu-en-F -->

Reply in **width–background–sprockets** order, default `2-1-1`.
Both corner texts are user-supplied. Ask for any missing choices together:
**What would you like at the bottom left and bottom right? Either corner may be left blank.**
Keep supplied fields; a blank must be explicitly chosen. Example: left
`Berlin, Germany`, right `October 2022`. Never auto-fill a frame number,
film brand, capture date or mockup wording. The fields share font and size;
never truncate, uppercase or shrink them to fit.

### G — Deckled Paper
<!-- generated:menu-en-G -->
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Paper margin | Narrow | **Medium — default** | Wide |
| Paper tone | **Warm white — default** | Bright white | Ivory |
| Torn edges | **Subtle — default** | Medium | Rough |
<!-- /generated:menu-en-G -->

Reply in **margin–paper tone–torn edges** order, default `2-1-1`.
Paper texture and a soft shadow stay outside the rectangular photo. The torn
silhouette belongs to the paper's outer edge; the photo is never torn, recolored
or grained. Python creates the pattern without per-photo AI calls. Reuse the
settings across a batch. No text or logo is added by default; a caption on the
paper may be requested separately.

### H — Minimal Mat
<!-- generated:menu-en-H -->
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Canvas ratio | **4:5 portrait — default** | 1:1 square | Follow photo, thin border |
| Mat | **White — default** | Warm light gray | Ivory |
| Black keyline | **Thin — default** | None | Thick |
<!-- /generated:menu-en-H -->

Reply in **ratio–mat–keyline** order, default `1-1-1`.
With 4:5 and 1:1, landscape and portrait photos share one fixed canvas: the
photo is fitted, centered, never cropped or scaled. 4:5 is the tallest ratio
shown uncropped in Instagram/Facebook feeds, best on phone screens. Option 3
adds only a thin even border in the photo's own ratio. No text by default.
Share JPEGs for 4:5 and 1:1 are exactly 1080×1350 and 1080×1080.
Beyond the menu: `--ratio 3:4` or `--ratio 9:16` (stories, reels; share copies
1080×1440, 1080×1920) and `--background blur` for a softly blurred, slightly
darkened copy of the photo instead of the mat color. Gallery label: `--title`
(Inter SemiBold, as in D) and `--subtitle` (small gray Inter), centered below the photo,
verbatim; the photo moves up to make room.

## Named options / Tùy chọn có tên

Since v0.12, `--title`/`--subtitle` are supported on A/B/G/H; labels are separate
from `--caption` and `--signature`. A/B/G grow only the lower margin as needed.
C/D accept opt-in `--capture-sidecar` for per-image `<input filename>.json`;
explicit capture flags override JSON, which overrides EXIF/XMP. See the C/D
style reference for the six allowed fields. All styles share a 24 MP complete
output cap; oversized results require a smaller source copy, with no silent resize.

Choice codes never change meaning; additional features use named flags. Your own PNG signature or logo (`--signature`) goes in the margin below the photo for A, B, E and G. ✓ accepted, `required` must be supplied (F accepts an explicit empty string for a blank corner), — rejected with an error.

Mã 3 số không bao giờ đổi nghĩa; tính năng bổ sung dùng cờ có tên. Chữ ký/logo PNG của bạn (`--signature`) đặt ở lề dưới ảnh với A, B, E, G. ✓ dùng được, `required` bắt buộc (F chấp nhận chuỗi rỗng để chủ động để trống một góc), — báo lỗi.

<!-- generated:option-matrix -->
| Flag | A | B | C | D | E | F | G | H |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `--left-text` | — | — | — | — | — | required | — | — |
| `--frame-color` | — | — | — | — | ✓ | — | — | — |
| `--right-text` | — | — | — | required | — | required | — | — |
| `--caption` | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| `--font` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `--camera` | — | — | ✓ | ✓ | — | — | — | — |
| `--lens` | — | — | ✓ | ✓ | — | — | — | — |
| `--iso` | — | — | ✓ | ✓ | — | — | — | — |
| `--aperture` | — | — | ✓ | ✓ | — | — | — | — |
| `--shutter` | — | — | ✓ | ✓ | — | — | — | — |
| `--focal` | — | — | ✓ | ✓ | — | — | — | — |
| `--raw-model` | — | — | ✓ | ✓ | — | — | — | — |
| `--capture-sidecar` | — | — | ✓ | ✓ | — | — | — | — |
| `--ratio` | — | — | — | — | — | — | — | ✓ |
| `--background` | — | — | — | — | — | — | — | ✓ |
| `--blur-tone` | — | — | — | — | — | — | — | ✓ |
| `--title` | ✓ | ✓ | — | — | — | — | ✓ | ✓ |
| `--subtitle` | ✓ | ✓ | — | — | — | — | ✓ | ✓ |
| `--signature` | ✓ | ✓ | — | — | ✓ | — | ✓ | — |
| `--signature-position` | ✓ | ✓ | — | — | ✓ | — | ✓ | — |
| `--signature-width` | ✓ | ✓ | — | — | ✓ | — | ✓ | — |
| `--signature-opacity` | ✓ | ✓ | — | — | ✓ | — | ✓ | — |
| `--share` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `--crop` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `--metadata` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
<!-- /generated:option-matrix -->
