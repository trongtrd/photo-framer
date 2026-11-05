<p align="center">
  <a href="#examples">
    <img src="docs/images/photo-framer-header.png" alt="Photo Framer: frame your photos and keep the original. A — Floating, B — Gallery, C — Spec card. Thêm khung ảnh, giữ nguyên file gốc." width="100%">
  </a>
</p>

# Photo Framer

**Your photo, eight ways to frame it.** Ask your AI assistant to add a frame, then save the finished PNG. The original file stays untouched.

**Một bức ảnh, tám phong cách khung.** Yêu cầu trợ lý AI thêm khung rồi tải PNG thành phẩm. File gốc được giữ nguyên.

[English: get started](#use-in-an-ai-app) · [Tiếng Việt: bắt đầu](#tiếng-việt) · [Choose A–H / Chọn phong cách](#choose-a-style) · [Before & after / Trước & sau](#examples) · [Python](#python-and-maintenance)

<picture>
  <source media="(max-width: 600px)" srcset="docs/images/photo-framer-workflow-mobile.svg">
  <img src="docs/images/photo-framer-workflow.svg" alt="Install the skill → attach photos → choose A–H → save the framed PNG. Cài skill → đính kèm ảnh → chọn A–H → tải PNG có khung." width="100%">
</picture>

## Use in an AI app

Your AI app needs support for **installed skills, image file access and Python execution**. Photo Framer processes your photos with Python, without an image-generation model or API key.

### Get started

1. Download this repository and install the complete [`skills/photo-framer/`](skills/photo-framer/) folder using your app's supported skill installation method. Keep all files in that folder together.
2. Open a chat where Photo Framer is available and attach your JPEG or PNG photos.
3. Ask for help choosing a style:

> Use Photo Framer to frame these photos. Help me choose a style from A to H.

You will see a comparison using the first photo. Pick a style in your own words; the assistant asks for any settings or text it needs. Already know your style? Say **“Use Photo Framer, G default, for all photos.”** to run directly.

You receive a full-resolution PNG. Ask for a **lightweight JPEG** if you also want a sharing copy. [See the styles](#choose-a-style) or [jump to the photos](#examples).

<details>
<summary>Installation and supported files</summary>

Installation depends on the app. A GitHub link alone does not install the skill or enable Python in a chat. Keep the whole skill folder together, including its scripts, references, fonts and logos. To run it on your own computer, use the [Python instructions](#python-and-maintenance).

Use JPEG or 8-bit PNG. Frames are added outside the photo; previews and sharing JPEGs may be reduced. Existing borders are checked before processing, and cropping requires your approval. See [technical limits](#technical-notes) for size, color and transparency handling.

</details>

## Tiếng Việt

### Bắt đầu trong ứng dụng AI

Ứng dụng AI cần hỗ trợ **cài skill, đọc file ảnh và chạy Python**. Photo Framer xử lý ảnh bằng Python, không dùng AI vẽ lại và không cần API key.

1. Tải mã nguồn của dự án này và cài toàn bộ thư mục [`skills/photo-framer/`](skills/photo-framer/) theo cách cài skill mà ứng dụng hỗ trợ. Giữ đầy đủ các file đi kèm.
2. Mở cuộc trò chuyện có thể dùng Photo Framer, rồi đính kèm ảnh JPEG hoặc PNG.
3. Gửi yêu cầu để được hỗ trợ chọn phong cách:

> Dùng Photo Framer thêm khung cho các ảnh này. Giúp tôi chọn phong cách từ A đến H.

Trợ lý dùng ảnh đầu tiên để tạo bản so sánh. Bạn chọn bằng lời; trợ lý sẽ hỏi thêm tùy chỉnh hoặc nội dung chữ khi cần. Nếu đã biết phong cách muốn dùng, yêu cầu thẳng: **“Dùng Photo Framer, G mặc định, cho toàn bộ ảnh.”**

Bạn nhận được PNG đầy đủ độ phân giải. Nếu cần bản chia sẻ, hãy yêu cầu thêm **JPEG nhẹ**. [Chọn phong cách](#choose-a-style) hoặc [xem ảnh trước và sau](#examples).

<details>
<summary>Cách cài và loại ảnh hỗ trợ</summary>

Cách cài phụ thuộc vào ứng dụng. Chỉ gửi đường dẫn GitHub chưa đủ để cài skill hoặc cho phép chat chạy Python. Giữ nguyên cả thư mục skill, gồm mã xử lý, tài liệu, font và logo. Nếu muốn tự chạy trên máy tính, xem [hướng dẫn Python](#python-and-maintenance).

Dùng JPEG hoặc PNG 8-bit. Khung được thêm bên ngoài ảnh; bản xem trước và JPEG chia sẻ có thể giảm kích thước. Ảnh có sẵn viền sẽ được hỏi cách xử lý; chỉ cắt khi bạn đồng ý. Xem [giới hạn kỹ thuật](#technical-notes) về kích thước, màu và ảnh trong suốt.

</details>

<a id="choose-a-style"></a>

## Choose a style / Chọn phong cách

Click a style to see its full-size example below. / Bấm vào phong cách để xem ảnh minh họa lớn bên dưới.

<!-- generated:styles -->
| Style / Phong cách | Look / Hình thức | Default / Mặc định |
| --- | --- | :---: |
| [**A · Floating / Ảnh nổi**](#style-a) | Soft shadow on a light background<br>Bóng mềm trên nền sáng | `2-2-1` |
| [**B · Gallery**](#style-b) | Black frame and white mat<br>Khung đen, bo giấy trắng | `1-2-1` |
| [**C · Spec card / Thẻ thông số**](#style-c) | Camera details and brand logo<br>Thông số chụp và logo hãng | `2-1-1` |
| [**D · Custom spec card / Thẻ có chữ riêng**](#style-d) | Camera details + your text at bottom right<br>Thông số chụp + chữ của bạn bên phải | `2-1-1` |
| [**E · Color Echo / Viền đồng sắc**](#style-e) | A border color drawn from each photo<br>Màu viền được chọn từ từng ảnh | `2-1-1` |
| [**F · Film Edge / Viền phim**](#style-f) | Side sprockets + two custom text fields<br>Lỗ phim hai bên + hai cụm chữ riêng | `2-1-1` |
| [**G · Deckled Paper / Giấy mép xé**](#style-g) | Textured warm-white paper with torn edges<br>Giấy trắng ấm, vân nhẹ và mép xé | `2-1-1` |
| [**H · Minimal Mat / Khung tối giản**](#style-h) | Fixed 4:5, 1:1, 3:4 or 9:16 canvas for any photo, or a thin border; black keyline; plain or blurred background<br>Khung cố định 4:5, 1:1, 3:4 hoặc 9:16 cho mọi ảnh, hoặc viền mỏng; viền đen; nền trơn hoặc nền mờ từ ảnh | `1-1-1` |
<!-- /generated:styles -->

Say **“A default”** or **“A mặc định”**; you do not need to remember the codes. If you only say “use defaults,” A is used unless another style is already chosen. For other settings, use your own words or the [English–Vietnamese menus](skills/photo-framer/references/menus.md).

Chỉ cần nói **“A mặc định”**, không cần nhớ mã số. Nếu chỉ nói “dùng mặc định”, skill dùng A, trừ khi đã chọn phong cách khác. Muốn tùy chỉnh thêm, hãy mô tả bằng lời hoặc dùng [menu tiếng Việt](skills/photo-framer/references/menus.md#tiếng-việt).

The first comparison shows A/B/C/E/F/G/H; D joins once you supply its text. F's preview corners stay blank until you choose their wording. / Bản so sánh đầu gồm A/B/C/E/F/G/H; D được thêm khi có nội dung chữ. Hai góc của F để trống trong bản xem trước cho đến khi bạn chọn chữ.

<details>
<summary>Custom text: D, F and captions / Chữ riêng: D, F và chú thích</summary>

**D — One custom field / Một cụm chữ:**

> Use Photo Framer, D default, with “Berlin, Germany | October 2022” at the bottom right.

> Dùng Photo Framer, D mặc định, điền “Berlin, Germany | October 2022” vào góc dưới bên phải.

Your text replaces the logo and matches the camera/lens line's font, size, weight and color. The assistant asks if the wording is missing. / Chữ của bạn thay logo, dùng cùng font, cỡ, độ đậm và màu với dòng máy/ống kính. Nếu chưa có nội dung, trợ lý sẽ hỏi.

**F — Two independent fields / Hai cụm chữ độc lập:**

> Use Photo Framer, F default. Bottom left: “Berlin, Germany”. Bottom right: “October 2022”.

> Dùng Photo Framer, F mặc định. Góc dưới trái: “Berlin, Germany”. Góc dưới phải: “October 2022”.

The assistant asks for missing corner choices together. Either or both may be intentionally blank. Both fields share font and size. / Trợ lý hỏi cùng lúc các ô còn thiếu. Bạn có thể chủ động để trống một hoặc cả hai bên. Hai cụm chữ dùng cùng font và cỡ.

D/F preserve your case, accents and punctuation. Text is never inferred from dates, GPS, filenames or the demo. Long text is flagged for shorter wording, never shrunk or truncated. / D/F giữ nguyên cách viết, dấu và dấu câu. Không suy đoán chữ từ thời gian, GPS, tên file hay ảnh mẫu. Chữ quá dài sẽ được đề nghị rút gọn, không tự thu nhỏ hoặc cắt bớt.

For a separate caption on A–E, G or H, supply exact wording and a font with the required characters. D/F fields use bundled fonts with Vietnamese support. / Với chú thích riêng trên A–E, G hoặc H, cung cấp nguyên văn và font có đủ ký tự. Các ô D/F dùng font đi kèm, hỗ trợ dấu tiếng Việt.

</details>

<details>
<summary>Batch framing and more requests / Xử lý cả bộ ảnh và yêu cầu khác</summary>

| What you want / Nhu cầu | Example request / Yêu cầu mẫu |
| --- | --- |
| Auto border colors / Tự chọn màu viền | “Use Photo Framer, E default, for all photos. No previews needed.”<br>“Dùng Photo Framer, E mặc định, cho toàn bộ ảnh. Không cần xem trước.” |
| One shared color / Một màu chung | “Use Photo Framer, E, with border color #ad896c for the whole batch.”<br>“Dùng Photo Framer, E, với màu viền #ad896c cho cả bộ.” |
| Phone-ready 4:5 / Khung dọc 4:5 cho điện thoại | “Use Photo Framer, H default, for all photos, with share copies.”<br>“Dùng Photo Framer, H mặc định, cho toàn bộ ảnh, thêm bản chia sẻ.” |
| Square grid / Khung vuông | “Use Photo Framer, H, 2-2-2.” (1:1, warm gray, no keyline)<br>“Dùng Photo Framer, H, 2-2-2.” (1:1, nền xám ấm, không viền đen) |
| Paper borders / Viền giấy | “Use Photo Framer, G default, for all photos.”<br>“Dùng Photo Framer, G mặc định, cho toàn bộ ảnh.” |
| Different styles / Chọn riêng từng ảnh | “Use Photo Framer, A for the first photo and B for the second.”<br>“Dùng Photo Framer, A cho ảnh thứ nhất, B cho ảnh thứ hai.” |
| Settings and a share copy / Tùy chỉnh và bản chia sẻ | “Use Photo Framer, B, 1-3-1, with lightweight JPEG copies.”<br>“Dùng Photo Framer, B, 1-3-1, thêm bản JPEG nhẹ.” |
| A caption / Thêm chú thích | “Use Photo Framer, B default, with the caption ‘Hà Nội — mùa thu.’”<br>“Dùng Photo Framer, B mặc định, thêm chữ ‘Hà Nội — mùa thu.’” |

**E** selects one color per photo locally, without candidate variants or per-image questions. Near-neutral photos use a warm neutral fallback. Supply one shared color to bypass selection. **G** creates its paper pattern locally and reuses your margin, tone and edge settings across the batch. Neither needs per-photo AI generation; the full-resolution photo region is preserved.

**E** tự chọn một màu cho mỗi ảnh, không tạo nhiều phương án hay hỏi lại từng ảnh. Ảnh gần trắng đen dùng màu trung tính dự phòng; cung cấp một màu chung để bỏ qua bước chọn màu. **G** tạo mẫu giấy tại chỗ và dùng cùng độ rộng, màu giấy, mức mép xé cho cả bộ. Cả hai không cần AI tạo từng ảnh; vùng ảnh đầy đủ độ phân giải được giữ nguyên.

</details>

<a id="examples"></a>

## Before & after / Trước & sau

One real photograph, eight styles at their default settings. D/F use supplied wording; E selects its border color automatically. Click an image to enlarge it.

Cùng một ảnh thật, tám phong cách ở chế độ mặc định. D/F dùng nội dung được cung cấp cho ví dụ; E tự chọn màu viền. Bấm vào ảnh để xem lớn hơn.

| Before & after / Trước & sau |
| :---: |
| **BEFORE — Original / Ảnh nguồn** · No frame / Chưa thêm khung<br>![Before: a person walking through a sunlit colonnade, without a frame](docs/images/demo-source-final.jpg) |
| <a id="style-a"></a>**AFTER A — Floating / Ảnh nổi** · Default / Mặc định `2-2-1`<br>![After A: the same photograph with a white surround and soft shadow](docs/images/demo-after-a-final.jpg) |
| <a id="style-b"></a>**AFTER B — Gallery** · Default / Mặc định `1-2-1`<br>![After B: the same photograph with a black frame, white mat and gray background](docs/images/demo-after-b-final.jpg) |
| <a id="style-c"></a>**AFTER C — Spec card / Thẻ thông số** · Default / Mặc định `2-1-1`<br>![After C: the same photograph with a flat white border, camera and exposure information read from EXIF, and the SONY logo](docs/images/demo-after-c-final.jpg) |
| <a id="style-d"></a>**AFTER D — Custom spec card / Thẻ thông số có chữ riêng** · Default / Mặc định `2-1-1`<br>![After D: the same photograph with capture details on the left and the supplied Berlin, Germany and October 2022 text at the bottom right](docs/images/demo-after-d-final.jpg) |
| <a id="style-e"></a>**AFTER E — Color Echo / Viền đồng sắc** · Default / Mặc định `2-1-1`<br>![After E: the same photograph with an automatically selected muted brown border and a thin dark inner edge](docs/images/demo-after-e-final.jpg) |
| <a id="style-f"></a>**AFTER F — Film Edge / Viền phim** · Default / Mặc định `2-1-1`<br>![After F: the same photograph with a charcoal film border, side sprockets, Berlin Germany at the bottom left and October 2022 at the bottom right](docs/images/demo-after-f-final.jpg) |
| <a id="style-g"></a>**AFTER G — Deckled Paper / Giấy mỹ thuật mép xé** · Default / Mặc định `2-1-1`<br>![After G: the same rectangular photograph on warm-white textured paper with subtly torn outer edges and a soft shadow](docs/images/demo-after-g-final.jpg) |
| <a id="style-h"></a>**AFTER H — Minimal Mat / Khung tối giản** · Default / Mặc định `1-1-1`<br>![After H: the same landscape photograph centered on a fixed 4:5 white portrait canvas with a thin black keyline](docs/images/demo-after-h-final.jpg) |

C reads the camera details from this photo and selects the SONY logo. D keeps those details and replaces the logo with the supplied text: `Berlin, Germany | October 2022`.

C tự đọc thông số từ ảnh và chọn logo SONY. D giữ thông tin chụp, thay logo bằng chữ được cung cấp: `Berlin, Germany | October 2022`.

F uses `Berlin, Germany` on the left and `October 2022` on the right. Both are supplied text, not inferred metadata.

F dùng `Berlin, Germany` bên trái và `October 2022` bên phải. Cả hai là chữ được cung cấp, không suy đoán từ metadata.

C/D read capture details from EXIF/XMP and never invent missing values. Known camera codes are shown by their product names (`ILCE-7C` → `α7C` beside the SONY logo in C, `Sony α7C` in D), and C never repeats the brand its logo already shows (`Canon EOS R5` → `EOS R5`). Without metadata, such as film scans, you can type the camera, lens and exposure yourself, or C can use your caption or a blank band; D keeps your text on the right. / C/D đọc EXIF/XMP, không tự bịa thông tin thiếu. Mã máy quen thuộc được hiển thị bằng tên thương mại (`ILCE-7C` → `α7C` cạnh logo SONY ở C, `Sony α7C` ở D); C không lặp lại tên hãng đã có trên logo (`Canon EOS R5` → `EOS R5`). Khi mất metadata, ví dụ ảnh scan phim, bạn có thể tự nhập máy, ống kính và thông số chụp, hoặc C dùng chữ bạn cung cấp hay dải không chữ; D vẫn giữ chữ của bạn bên phải.

### Portrait photos in style H / Ảnh dọc với style H

A second real photograph, a 1000 × 1500 (2:3) portrait, shows how H fits portrait photos without cropping or scaling: on the fixed 4:5 and 1:1 canvases the spare space goes to the sides, while the top and bottom keep the minimum margin.

Ảnh thật thứ hai, khổ dọc 1000 × 1500 (2:3), minh họa cách H đặt ảnh dọc mà không cắt hay thu nhỏ: với khung cố định 4:5 và 1:1, phần dư nằm hai bên, trên và dưới giữ lề tối thiểu.

| Original / Ảnh gốc | H `1-1-1` · 4:5 | H `2-2-2` · 1:1 | H `3-1-2` · thin border / viền mỏng |
| :---: | :---: | :---: | :---: |
| ![Portrait source: Prague rooftops and the Lesser Town Bridge Tower seen from above](docs/images/demo-portrait-source.jpg) | ![The full portrait photo centered on a white 4:5 canvas with a thin black keyline](docs/images/demo-portrait-h-4x5.jpg) | ![The full portrait photo centered on a warm light gray 1:1 canvas without a keyline](docs/images/demo-portrait-h-1x1.jpg) | ![The full portrait photo with a thin even white border and a thick black keyline](docs/images/demo-portrait-h-thin.jpg) |

### 9:16 and blurred background / Khung 9:16 và nền mờ

`--ratio` adds 3:4 and 9:16 canvases (stories, reels, phone wallpapers) beside the menu's 4:5, 1:1 and thin border. `--background blur` fills the canvas with a softly blurred, slightly darkened copy of the same photo instead of a flat mat; the photo itself stays sharp, whole and uncropped, with its keyline. Share copies are exactly 1080×1440 (3:4) or 1080×1920 (9:16).

`--ratio` thêm khung 3:4 và 9:16 (story, reels, hình nền điện thoại) bên cạnh 4:5, 1:1 và viền mỏng trong menu. `--background blur` dùng chính bức ảnh, làm mờ và tối nhẹ, để phủ nền thay cho màu trơn; ảnh chính vẫn nét, nguyên vẹn, không bị cắt và giữ viền đen. Bản chia sẻ có đúng kích thước 1080×1440 (3:4) hoặc 1080×1920 (9:16).

> Use Photo Framer, H default, 9:16 with a blurred background.
>
> Dùng Photo Framer, H mặc định, khung 9:16 nền mờ.

| Landscape / Ảnh ngang · H `--ratio 9:16 --background blur` | Portrait / Ảnh dọc · H `--ratio 9:16 --background blur` |
| :---: | :---: |
| ![The full landscape colonnade photo centered on a 9:16 canvas filled with a dark, softly blurred copy of itself, thin black keyline](docs/images/demo-after-h-9x16-blur.jpg) | ![The full Prague portrait photo centered on a 9:16 canvas filled with a softly blurred copy of itself, thin black keyline](docs/images/demo-portrait-h-9x16-blur.jpg) |

### Gallery label and signature / Nhãn gallery và chữ ký

Since v0.12, A, B and G also accept `--title` and `--subtitle`, using the same Inter faces and inks as H. The title is centered under the photo; the lower background (A), white mat and frame (B), or paper (G) grows only as needed, with the photo's size and position unchanged. Choose a gallery label, a caption, or a signature separately: a centered label cannot be combined with `--caption` or `--signature`. H continues to reject signatures.

The existing portrait and wording from the H example are reused below to compare the new layouts:

| A · Gallery label | B · Gallery label | G · Gallery label |
| :---: | :---: | :---: |
| ![Praha gallery label beneath the intact photo in style A](docs/images/demo-portrait-a-label.jpg) | ![Praha gallery label beneath the intact photo in style B](docs/images/demo-portrait-b-label.jpg) | ![Praha gallery label beneath the intact photo on deckled paper](docs/images/demo-portrait-g-label.jpg) |

H can add a gallery label below the photo: `--title` and an optional `--subtitle` in the same typeface as the spec cards: Inter SemiBold near-black for the title (like D's camera line and custom text) and smaller gray Inter Regular for the subtitle (like the exposure line), with full Vietnamese support. The photo moves up to make room on fixed canvases; on the thin border the canvas grows. The wording is always yours, used verbatim. A, B, E and G can also place your own transparent PNG signature or logo with `--signature`, in the margin below the photo (bottom-right by default, or bottom-center/bottom-left), sized by `--signature-width` and faded with `--signature-opacity`. Nothing is ever drawn over the photo: if text or a signature does not fit, or two items would overlap, the renderer asks for shorter wording, a smaller signature or another position.

H có thể thêm nhãn gallery dưới ảnh: `--title` và `--subtitle` tùy chọn dùng cùng kiểu chữ với thẻ thông số: tiêu đề Inter SemiBold màu gần đen (như dòng máy và chữ riêng của D), phụ đề Inter Regular xám, nhỏ hơn (như dòng thông số), đủ dấu tiếng Việt. Với khung cố định, ảnh dịch lên để chừa chỗ; với viền mỏng, khung cao thêm. Nội dung chữ luôn do bạn cung cấp, giữ nguyên văn. A, B, E và G còn có thể đặt chữ ký hoặc logo PNG nền trong suốt của bạn bằng `--signature`, ở lề dưới ảnh (mặc định góc phải, hoặc giữa/trái), chỉnh cỡ bằng `--signature-width` và độ mờ bằng `--signature-opacity`. Không bao giờ vẽ đè lên ảnh: nếu chữ hoặc chữ ký không vừa, hay hai thành phần chồng nhau, renderer sẽ đề nghị rút gọn chữ, thu nhỏ chữ ký hoặc đổi vị trí.

> Use Photo Framer, H 2-1-1, with the title “Praha” and the subtitle “Prague · Czech Republic”.
>
> Dùng Photo Framer, H 2-1-1, tiêu đề “Praha”, phụ đề “Prague · Czech Republic”.

| H `2-1-1` · `--title` · `--subtitle` |
| :---: |
| ![The full Prague portrait photo on a white 1:1 canvas, moved up, with the centered title Praha and the gray subtitle Prague · Czech Republic below it](docs/images/demo-portrait-h-1x1-label.jpg) |

The example's wording was written for this README; it names the place in the photo.

[↑ Choose another style / Chọn phong cách khác](#choose-a-style)

## Python and maintenance

Run Photo Framer directly, check its technical limits, or reproduce the README examples using the instructions below. The skill bundles a Python renderer that runs locally with Python 3.10+ and Pillow 10.1–12.x.

Phần này dành cho người tự chạy bằng Python hoặc bảo trì project. Các lệnh được chạy từ thư mục gốc của repository, sau bước cài thư viện bên dưới.

### Install and run locally

Download or clone this repository, then open a terminal in its root folder. Install the dependencies first:

```sh
python -m pip install -r skills/photo-framer/scripts/requirements.txt
```

This installs Pillow for image processing and `defusedxml` for reading XMP capture metadata. / Lệnh này cài Pillow để xử lý ảnh và `defusedxml` để đọc thông tin chụp từ XMP.

Use `python3` or `py` instead of `python` if that is how your environment exposes Python. Then run:

```sh
# Reduced A/B/C/E/F/G/H comparison using the first photo
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --preview --out-dir "output"

# Full-resolution PNGs, with frames added outside the photos
python skills/photo-framer/scripts/frame_photo.py "landscape.jpg" "portrait.jpg" --style A --choices 2-2-1 --out-dir "output"

# Gallery plus an additional lightweight sRGB JPEG
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style B --choices 1-3-1 --share --out-dir "output"

# Spec card with capture information and the camera brand mark
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style C --out-dir "output"

# Custom spec card: same gear-line font, with your text replacing the brand mark
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style D --right-text "Berlin, Germany | October 2022" --out-dir "output"

# Color Echo: one automatic color per photo, processed together without previews
python skills/photo-framer/scripts/frame_photo.py "photo-1.jpg" "photo-2.jpg" --style E --out-dir "output"

# Color Echo: one exact shared sRGB color, skipping automatic color analysis
python skills/photo-framer/scripts/frame_photo.py "photo-1.jpg" "photo-2.jpg" --style E --frame-color "#ad896c" --out-dir "output"

# Film Edge: two independently supplied corner texts
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style F --left-text "Berlin, Germany" --right-text "October 2022" --out-dir "output"

# Film Edge with intentionally blank corners
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style F --left-text= --right-text= --out-dir "output"

# Deckled Paper: warm-white paper, subtle torn edges and a soft shadow
python skills/photo-framer/scripts/frame_photo.py "photo-1.jpg" "photo-2.jpg" --style G --out-dir "output"

# Minimal Mat: landscape and portrait share one 4:5 canvas; share copies are exactly 1080x1350
python skills/photo-framer/scripts/frame_photo.py "landscape.jpg" "portrait.jpg" --style H --choices 1-1-1 --share --out-dir "output"

# Minimal Mat on a 9:16 story canvas with a blurred background; share copies are exactly 1080x1920
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style H --ratio 9:16 --background blur --share --out-dir "output"

# Film scan without EXIF: type the capture details (C/D); typed values are shown as given
python skills/photo-framer/scripts/frame_photo.py "scan.jpg" --style C --camera "Pentax 67" --lens "SMC Takumar 105mm F2.4" --iso 400 --aperture 2.4 --shutter 1/125 --focal 105 --out-dir "output"

# Per-image capture details for a batch: scan.jpg.json and next.jpg.json
python skills/photo-framer/scripts/frame_photo.py "scan.jpg" "next.jpg" --style C --capture-sidecar --out-dir "output"

# Gallery label below the photo (A, B, G, H)
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style H --choices 2-1-1 --title "Hồ Hoàn Kiếm" --subtitle "Hà Nội · Tháng 10, 2022" --out-dir "output"

# Your own PNG signature at the bottom right (A, B, E, G)
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style A --signature "my-signature.png" --signature-width 0.1 --out-dir "output"

# Remove all EXIF, including GPS location, from the outputs
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style A --metadata strip --out-dir "output"
```

To include D in the comparison, add `--right-text "your exact text"` to `--preview`. F's preview corners stay blank until both text fields are supplied; these preview blanks are not a choice of blank final corners. Add both `--left-text` and `--right-text` to preview F with your wording. An empty F right field omits D, which requires nonempty text. E's `--frame-color` accepts an opaque sRGB hex code or a supported English color name; it overrides the auto-tone choice. Selected colors are recorded as sRGB hex in the JSON notes.

For custom text, supply the exact caption; it is set in the bundled Inter, like every other text in Photo Framer:

```sh
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style B --caption "Hà Nội — mùa thu." --out-dir "output"
```

Text supplied with `--caption` must fit on one line, contain at most 200 characters, and stay outside the photo. It uses the bundled Inter Regular, the spec cards' typeface (C uses Inter SemiBold, as its caption replaces the camera line); `--font` with another font file overrides it, and then Vietnamese glyphs should be checked. C/D's automatic spec band can contain two lines and uses the bundled Inter Regular and SemiBold fonts. D requires `--right-text`, also one line of at most 200 characters, and uses the gear line's SemiBold face and size without requiring `--font`. A font override applies to both sides. If the text and capture details cannot fit together, the renderer reports an error.

F requires both `--left-text` and `--right-text`, including explicit empty values for blank corners. Each accepts one line of at most 200 characters. Both use bundled Inter SemiBold in warm white; `--font` overrides both. The renderer rejects texts that overlap or do not fit; it does not shrink, wrap, uppercase or truncate them. F uses these two fields instead of `--caption`.

Which named flags each style accepts (✓), requires, or rejects (—). Choice codes never change meaning; new features arrive as named flags. / Cờ có tên mà từng phong cách nhận (✓), bắt buộc (required) hoặc báo lỗi (—). Mã 3 số không đổi nghĩa; tính năng mới dùng cờ có tên.

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

For Vietnamese captions, pass `--caption` as above; the bundled Inter covers Vietnamese. Add `--share` for a sharing copy. / Để thêm chữ tiếng Việt, dùng `--caption` như ví dụ; font Inter đi kèm đủ dấu tiếng Việt. Thêm `--share` để xuất bản chia sẻ.

Filesystems must support hard links for the renderer's atomic, no-overwrite final save. Existing output filenames receive numeric suffixes. The CLI returns JSON per input; inspect every item and report successes and errors separately.

#### Per-image capture sidecars (C/D)

`--capture-sidecar` opts into a UTF-8 JSON sibling for each image, named with its complete filename: `scan.jpg.json` for `scan.jpg`, or `scan.png.json` for `scan.png`. Nothing is read automatically without the flag. The object accepts only `camera`, `lens`, `iso`, `aperture`, `shutter` and `focal`; partial objects are allowed. For example:

```json
{
  "camera": "Pentax 67",
  "lens": "SMC Takumar 105mm F2.4",
  "iso": 400,
  "aperture": "f/2.4",
  "shutter": "1/125",
  "focal": "105mm"
}
```

Explicit capture flags override that image's JSON, which overrides EXIF/XMP, field by field. A missing sibling uses the existing capture values and is reported in the JSON notes. A malformed file, duplicate or unknown field, invalid value, or file over 16 KiB fails that image while the remaining batch continues. Typed camera text never chooses a logo. Sidecar values affect the displayed spec band only: they are not written into source or output EXIF. A preview reads only the first image's sidecar.

Try the synthetic example without a personal photograph:

```sh
python skills/photo-framer/scripts/frame_photo.py docs/examples/scan.png --style C --capture-sidecar --share --out-dir output/sidecar-example
```

![Synthetic scan with the capture details from its JSON sibling](docs/images/demo-sidecar-c.jpg)

#### Maintaining the renderer / Bảo trì

The renderer is the `skills/photo-framer/scripts/photoframer/` package (one module per style in `styles/`, shared drawing in `components/`); `frame_photo.py` is its CLI entry point. Release notes are in [CHANGELOG.md](CHANGELOG.md). / Renderer nằm trong package `photoframer/`, mỗi phong cách một module; lịch sử phiên bản ở [CHANGELOG.md](CHANGELOG.md).

```sh
# Regression tests (all of skills/photo-framer/scripts/tests/; add -k NAME to filter)
python skills/photo-framer/scripts/test_frame_photo.py

# Regenerate the style, menu and flag tables from the style registry (CI runs --check)
python tools/gen_docs.py

# Prove a refactor leaves every output byte unchanged against a git revision
python tools/golden.py compare --base main
# (add --ignore-icc-dates when --base is older than v0.11.1)
```

<a id="technical-notes"></a>

### Technical limits and preservation

<details>
<summary>Formats, pixels, color and metadata / Định dạng, pixel, màu và metadata</summary>

- **Inputs and memory:** JPEG and 8-bit PNG, up to 30 million encoded pixels per input and **24 million pixels for the complete framed output in every style**, including H. The usable source size is smaller and depends on the chosen frame: H 9:16 around a landscape can exceed three times the source pixel count. Layout is checked before a full-size canvas is allocated (JPEGs are checked before decoding); an oversized result reports the expected canvas dimensions and a suitable smaller source size. The renderer never silently resizes. Export a smaller copy or explicitly authorize the assistant to resize a separate copy first; the original stays untouched. The 24 MP cap limits pixel buffers, not compressed file size in MB, and is not an absolute RAM guarantee. Smaller PNG bit depths remain supported when decoded by Pillow. Animated images are rejected.
- **16-bit PNG:** encoded bit depth is inspected before decoding. All 16-bit PNG color types are rejected rather than silently reduced to 8-bit.
- **RGB preservation:** full-size final PNGs keep the prepared photo region's dimensions and decoded RGB pixel values after EXIF orientation, and retain valid source RGB ICC profiles. The frame increases the overall output dimensions; frames and shadows stay outside the photo.
- **Color conversion:** grayscale/CMYK with suitable profiles are converted to sRGB. Unprofiled CMYK is rejected; unprofiled RGB is treated as sRGB.
- **Reproducible output:** the sRGB profile embedded in previews, share copies and unprofiled photos is the committed file [`assets/profiles/srgb.icc`](skills/photo-framer/assets/profiles/README.md) (LittleCMS's built-in sRGB with a fixed creation date), so running the same command again, on any day, writes byte-identical files on the same Pillow build.
- **Transparency:** transparent content is composited onto white paper, so the output is opaque. Alpha and grayscale transparency keys are captured before ICC conversion. Original alpha is not retained.
- **Cropping:** requires explicit user approval. The script never edits the input file, and the skill asks how to handle existing borders before proceeding.
- **Previews and sharing:** JPEG previews and sharing copies are reduced/lossy, with sharing copies limited to a longest edge of 2048 pixels. They are not pixel-identical archival copies; preview/share versions convert to sRGB.
- **Styles C/D:** Make, Model, LensModel, ISO, aperture, shutter speed and focal length are read from EXIF first; embedded XMP, such as a Lightroom export's capture data, fills missing fields; values typed with `--camera`, `--lens`, `--iso`, `--aperture`, `--shutter` and `--focal` win field by field. The exposure line is omitted unless all four exposure values exist. No values are invented. Camera codes listed in [`assets/cameras.json`](skills/photo-framer/assets/cameras.json) are shown by product name (C omits the brand beside its brand mark); `--raw-model` shows the EXIF code. Typed camera text is shown verbatim and never selects a brand mark. D uses exact user text on the right with the same typography as the gear line; it rejects overflow instead of shrinking, truncating or hiding left-side details.
- **Brand marks (C):** selected from the camera body and pasted without recoloring or distortion. Sources are documented in [`assets/logos/`](skills/photo-framer/assets/logos/). Brands without a bundled logo use a bold text wordmark. D draws no logo or wordmark.
- **Output metadata:** by default the final PNG and the share JPEG keep the source EXIF, including GPS location. Orientation is reset to 1 because the pixels are already rotated, pixel dimensions are updated, and the embedded thumbnail, maker notes and XMP (including edit history) are dropped. `--metadata strip` writes no EXIF. Previews never carry metadata. / Mặc định PNG cuối và JPEG chia sẻ giữ EXIF của ảnh gốc, kể cả vị trí GPS; hướng xoay đặt lại 1, cập nhật kích thước, bỏ ảnh thu nhỏ, maker notes và XMP. Dùng `--metadata strip` để không ghi EXIF.
- **Style E:** one deterministic sRGB color is selected from a sample no larger than 96×96, favoring colors near the edges and midtones. Near-neutral or unusable samples fall back to warm neutral #e8e4dc. Default tone is muted; natural and light variants are optional settings. `--frame-color` bypasses this selection and applies one exact color across the batch. E converts only its decorative colors into the source RGB ICC profile; photo pixels and ICC bytes stay unchanged. No per-image AI color analysis or candidate variants are needed.
- **Style F:** sprockets and both corner texts stay outside the rectangular photo region. Charcoal, black and dark-brown backgrounds are available, with standard, sparse or dense sprockets. Both custom fields preserve the supplied wording; no metadata, counter, film brand or photo effect is generated. F converts its decorative sRGB colors into the source RGB profile while retaining photo pixels and ICC bytes.
- **Gallery label and signature (v0.11–v0.12):** `--title` (Inter SemiBold, as D's camera line, 5% of the photo's short edge) and `--subtitle` (Inter Regular, as the exposure line, 2.6%) are centered below the photo in A/B/G/H; dark ink on light backgrounds and light ink on dark blurred backgrounds. A/B/G grow the lower margin as needed without moving the photo; H retains its centered photo/label block. `--signature` takes a PNG up to 4096 px, keeps its transparency, converts its colors like other decorations and places it in the margin below the photo of A, B, E or G, aligned to the photo edges. H takes no signature: a corner mark beside its centered label looks unbalanced. Each item claims its own box; leaving the margin or overlapping another item is an error. `--caption` keeps its previous behavior. A gallery label cannot be combined with a caption or signature.
- **Style H:** 4:5 and 1:1 canvases have exact ratios; any photo is fitted and centered, never scaled or cropped, with a minimum margin of 3.6% (4:5) or 2.4% (1:1) of the canvas width. Option 3 adds a thin even border (1.5% of the photo's short edge) in the photo's own ratio. Mats are white, warm light gray or ivory; the black keyline is thin, absent or thick and sits outside the photo. `--ratio` also offers 3:4 and 9:16 (minimum margin 4.0% and 5.0% of the canvas width) and overrides the first menu row. `--background blur` replaces the mat with a blurred copy of the photo scaled to cover the canvas (blurred on a copy of at most 384 px, then enlarged; `--blur-tone` dark by default, neutral or light), drawn only outside the photo. Because the full-resolution photo is kept, the canvas grows with it; H shares the 24 MP complete output cap; large source photos need a smaller, explicitly authorized copy before framing. Share copies are exactly 1080×1350 (4:5), 1080×1080 (1:1), 1080×1440 (3:4) or 1080×1920 (9:16).
- **Style G:** paper grain, torn edges and a soft shadow stay outside the rectangular photo. Choose narrow/medium/wide margins, warm-white/bright-white/ivory paper and subtle/medium/rough edges. A fixed procedural pattern and a reusable 256×256 texture tile support batches without AI calls or external texture files. Decorative colors convert into the source RGB profile; photo pixels and ICC bytes remain unchanged. No caption or logo is added by default.

Ở PNG cuối, vùng ảnh đã được chuẩn bị giữ nguyên kích thước và pixel RGB sau giải mã/chuẩn hóa hướng xoay EXIF. Khung được thêm bên ngoài nên kích thước toàn bộ ảnh đầu ra tăng lên. Các trường hợp chuyển màu, ghép nội dung trong suốt lên trắng, cắt ảnh đã được duyệt và JPEG chia sẻ có giới hạn riêng như mô tả trên.

The renderer has no remote image service, analytics, or automatic public upload. See [the rendering presets](skills/photo-framer/references/presets.md) for geometry and shadow settings.

</details>

### Reproduce the README examples

<details>
<summary>Source details and reproduction commands / Ảnh nguồn và lệnh tái tạo</summary>

Complete [the dependency installation](#install-and-run-locally) first. Run the commands from the repository root, using an empty `output/demo` directory for the filenames shown. Reruns preserve existing outputs by adding numeric suffixes.

Cài thư viện theo phần trên trước khi chạy. Dùng thư mục `output/demo` chưa có ảnh đầu ra để nhận đúng tên file bên dưới; chạy lại sẽ thêm hậu tố số để giữ các file đã có.

```sh
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style A --choices 2-2-1 --share --out-dir output/demo
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style B --choices 1-2-1 --share --out-dir output/demo
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style C --choices 2-1-1 --share --out-dir output/demo
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style D --choices 2-1-1 --right-text "Berlin, Germany | October 2022" --share --out-dir output/demo
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style E --choices 2-1-1 --share --out-dir output/demo
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style F --choices 2-1-1 --left-text "Berlin, Germany" --right-text "October 2022" --share --out-dir output/demo
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style G --choices 2-1-1 --share --out-dir output/demo
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style H --choices 1-1-1 --share --out-dir output/demo
```

Each command creates `demo-source-final_<STYLE>.png` and `demo-source-final_<STYLE>_share.jpg` in `output/demo`.

The portrait H examples use separate folders because all three settings share the `_H` filename:

```sh
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-portrait-source.jpg --style H --choices 1-1-1 --share --out-dir output/demo-portrait/4x5
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-portrait-source.jpg --style H --choices 2-2-2 --share --out-dir output/demo-portrait/1x1
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-portrait-source.jpg --style H --choices 3-1-2 --share --out-dir output/demo-portrait/thin
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-portrait-source.jpg --style H --ratio 9:16 --background blur --share --out-dir output/demo-portrait/9x16-blur
python skills/photo-framer/scripts/frame_photo.py docs/images/demo-source-final.jpg --style H --ratio 9:16 --background blur --share --out-dir output/demo-h-9x16-blur
```

The portrait source is a real photograph supplied by the project owner, at 1000 × 1500 pixels, without EXIF/XMP/GPS metadata. Copy each `output/demo-portrait/<name>/demo-portrait-source_H_share.jpg` to `docs/images/demo-portrait-h-<name>.jpg`. The gallery-label example comes from `python skills/photo-framer/scripts/frame_photo.py docs/images/demo-portrait-source.jpg --style H --choices 2-1-1 --title "Praha" --subtitle "Prague · Czech Republic" --share --out-dir output/demo-portrait/label` (copy `demo-portrait-source_H_share.jpg` to `docs/images/demo-portrait-h-1x1-label.jpg`). The two blurred 9:16 examples come from `output/demo-portrait/9x16-blur/` and `output/demo-h-9x16-blur/` (`demo-source-final_H_share.jpg` → `docs/images/demo-after-h-9x16-blur.jpg`).

The source is a real photograph supplied by the project owner, at 2048 × 1365 pixels. It retains EXIF/XMP (no GPS) for reproduction; since v0.9 re-rendered examples carry that EXIF by default (C and D were re-rendered for v0.9). EXIF supplies `ILCE-7C | FE 85mm F1.8` and `ISO 100  f/8  1/200s  85mm`, shown as `α7C` in C and `Sony α7C` in D; the camera make selects the SONY logo. EXIF takes priority over XMP. No capture values were added or invented.

E's automatic color for this source is sRGB `#a98e84`, with inner edge `#181c24`. It comes from the local selection algorithm, not an AI-generated mockup.

The embedded AFTER files are lightweight sRGB JPEG share copies; the full-resolution PNG outputs retain the source photo region's decoded RGB pixels and ICC profile. GitHub scales images to the available width, so the photo appears smaller inside a larger framed canvas.

After rendering, run this Python snippet from the repository root to update the documentation copies. It leaves the source photograph untouched.

Sau khi render, chạy đoạn Python này từ thư mục gốc để cập nhật ảnh minh họa. Ảnh nguồn được giữ nguyên.

```python
from pathlib import Path
import shutil

rendered = Path("output/demo")
images = Path("docs/images")
for style in "ABCDEFGH":
    shutil.copyfile(
        rendered / f"demo-source-final_{style}_share.jpg",
        images / f"demo-after-{style.lower()}-final.jpg",
    )
```

</details>

### Regression tests

<details>
<summary>Run tests and view recorded validation / Chạy kiểm thử và xem kết quả đã ghi nhận</summary>

After installing dependencies, run:

```sh
python skills/photo-framer/scripts/test_frame_photo.py
```

The entry point runs every module in [`skills/photo-framer/scripts/tests/`](skills/photo-framer/scripts/tests/), split by area: input files and color handling, C/D spec cards, E/F/G, H, labels and signatures, metadata, and the style registry. Run one area with `python -m unittest tests.test_metadata` from the `scripts` folder, or filter by name with `-k`.

The tests generate synthetic images and an original grayscale ICC profile. They use Python and the dependencies in `requirements.txt` (Pillow and defusedxml); no personal photographs, downloaded profiles, NumPy, or machine-specific font paths are needed. GitHub Actions installs that same requirements file while testing each Pillow version in its matrix.

The suite covers all four 16-bit PNG color types, disguised extensions, preview rejection, mixed batches, profiled grayscale alpha and transparency keys with every style, ordinary alpha modes, RGB/ICC preservation, EXIF orientation, no-overwrite behavior and Vietnamese filenames with legacy Windows output encodings. Style C covers EXIF/XMP captions, blank bands, caption modes, logo pasting and wordmark fallback. D covers custom-text validation, matching gear-line typography, Vietnamese text, missing metadata, left-side modes, overflow errors, mixed batches and comparisons with supplied wording. E covers deterministic selection, edge weighting, bounded sampling, neutral fallback, fixed-color batches, invalid colors, border options and pixel preservation. F adds explicit corner choices, blank fields, Vietnamese text, mirrored sprockets, layout variants, overflow rejection, mixed batches and previews. G adds repeatable paper texture and torn edges, shadows, all 27 preset combinations on landscape/portrait/tiny photos, optional Vietnamese captions and mixed batches. H covers exact 4:5/1:1 ratios, centering and minimum margins for landscape/portrait/square/tiny photos, keylines and mats, thin-border mode, exact share sizes, the output limit and mixed batches. The bundled sRGB profile is checked against the profile LittleCMS builds, and outputs rendered a second apart are compared byte for byte. JSON escapes preserve the exact Unicode paths when parsed.

Recorded local validation used Linux, Python 3.12.14 and Pillow 12.3.0 for v0.1, and Windows, Python 3.12 and Pillow 12.3.0 for v0.2. The historical GitHub Actions [v0.1 regression run 37142845990](https://github.com/trongtrd/photo-framer/actions/runs/37142845990) passed four matrix jobs: macOS/Python 3.12/Pillow 12.x, Windows/Python 3.12/Pillow 12.x, Ubuntu/Python 3.10/Pillow 10.1.0, and Ubuntu/Python 3.12/Pillow 12.x.

</details>

## License

MIT; see [LICENSE](LICENSE). The code and synthetic test data in this repository are covered by this license. The README examples use real photographs supplied by the project owner in [`docs/images/demo-source-final.jpg`](docs/images/demo-source-final.jpg) and [`docs/images/demo-portrait-source.jpg`](docs/images/demo-portrait-source.jpg). The bundled camera brand marks are public-domain files from Wikimedia Commons (sources and terms in [`skills/photo-framer/assets/logos/README.md`](skills/photo-framer/assets/logos/README.md)); the trademarks belong to their owners and the marks are only displayed, unmodified, next to photographs taken with that equipment.
