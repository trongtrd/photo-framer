# Photo Framer

Add floating-photo shadows or gallery frames without regenerating your photographs.

Photo Framer is a Python renderer and an English–Vietnamese agent skill. It runs locally with Python 3.10+ and Pillow 10.1–12.x. No API key, remote image service, or image-generation model is required.

## Styles

| Code | Style | Default choices |
| --- | --- | --- |
| A | Floating photo: light background and soft shadow | `2-2-1`: medium margin, medium shadow, white background |
| B | Gallery: rigid frame, white mat, inner and outer shadows | `1-2-1`: black frame, medium mat, gray background |

The skill shows an A/B comparison for an unspecified request. Explicit requests such as “A default” or “B, 1-3-1” run without repeating the menu. See [the bilingual menus](skills/photo-framer/references/menus.md).

## Run the renderer

Install the dependencies in your preferred Python environment:

```sh
python -m pip install -r skills/photo-framer/scripts/requirements.txt
```

Use `python3` or `py` if that is how your environment exposes Python.

```sh
# Reduced comparison using the first photo
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --preview --out-dir "output"

# Full-resolution PNGs, with frames added outside the photos
python skills/photo-framer/scripts/frame_photo.py "landscape.jpg" "portrait.jpg" --style A --choices 2-2-1 --out-dir "output"

# Gallery plus an additional lightweight sRGB JPEG
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style B --choices 1-3-1 --share --out-dir "output"
```

For a caption, supply its exact text and a Unicode font file available on your machine:

```sh
python skills/photo-framer/scripts/frame_photo.py "photo.jpg" --style B --caption "Hà Nội — mùa thu." --font "/path/to/unicode-font.ttf" --out-dir "output"
```

Check that the chosen font includes the required Vietnamese glyphs. No font is bundled. Filesystems must support hard links for the renderer's atomic, no-overwrite final save. Errors are returned per input as JSON; always inspect every item.

## Use as an agent skill

The installable skill is in [`skills/photo-framer/`](skills/photo-framer/). Follow your host's skill-import mechanism, or place this complete directory in its supported personal-skills location. The host must be able to read image files and execute Python; a GitHub URL alone does not install the skill or make every chat session capable of running it.

Example requests:

- “Frame these photos.”
- “Use A default for both photos.”
- “Use B, 1-3-1 and include lightweight copies for sharing.”
- “Use A for the first photo and B for the second.”

## Preservation and boundaries

- JPEG and 8-bit PNG inputs; at most 30 million pixels per input and 60 million pixels per framed output. Smaller PNG bit depths remain supported when decoded by Pillow. Animated images are rejected.
- PNG bit depth is inspected before decoding. All 16-bit PNG color types are rejected rather than silently reduced to 8-bit.
- Full-size final PNGs keep the RGB photo region's decoded pixel values, after EXIF orientation, and retain valid source RGB ICC profiles. Frames and shadows stay outside the photo.
- Grayscale/CMYK with suitable profiles are converted to sRGB. Unprofiled CMYK is rejected; unprofiled RGB is treated as sRGB.
- Transparent content is composited onto white paper. Alpha and grayscale transparency keys are captured before ICC conversion. Alpha is not retained in the opaque final image.
- Crop requires explicit user approval. The script never edits the input file.
- Preview and share JPEGs are reduced/lossy; share images have a longest edge of at most 2048 pixels. They are not pixel-identical archival copies.
- EXIF/GPS are excluded from presentation outputs. Captions are optional, one line, up to 200 characters, and must fit outside the photo.

## Regression tests

```sh
python skills/photo-framer/scripts/test_frame_photo.py
```

The tests generate synthetic images and an original grayscale ICC profile. They require only Python and Pillow; no personal photographs, downloaded profiles, NumPy, or machine-specific font paths are needed.

The suite covers all four 16-bit PNG color types, disguised extensions, preview rejection, mixed batches, profiled grayscale alpha and transparency keys with both styles, ordinary alpha modes, RGB/ICC preservation, EXIF orientation, no-overwrite behavior and Vietnamese filenames with legacy Windows output encodings. JSON escapes preserve the exact Unicode paths when parsed. It fails on the pre-fix renderer and passes on the fixed version.

Local validation used Linux, Python 3.12.14 and Pillow 12.3.0. The included GitHub Actions workflow is configured for additional operating systems and the minimum supported Pillow version; those jobs are not claimed to have passed until GitHub runs them.

## Remaining review items

This patch fixes two image-handling defects, not every item in the independent review:

- Input PNG decoding does not reject every structurally damaged PNG that still decodes.
- A syntactically valid ICC profile with the wrong color space for its pixels needs stricter validation.
- If the PNG succeeds but an additional share export fails, the current JSON error omits the completed PNG path.
- A/B labels inside previews are English; conversation menus are English–Vietnamese. The mixed-style interaction instructions could be more explicit about only asking for missing settings.

## Tiếng Việt

**Photo Framer** thêm khung bằng xử lý ảnh xác định, không dùng AI vẽ lại ảnh.

- **A — Ảnh nổi:** mặc định `2-2-1` = khoảng trắng vừa, bóng mềm vừa, nền trắng.
- **B — Gallery:** mặc định `1-2-1` = khung đen, bo giấy trắng vừa, nền xám.
- Yêu cầu chung được xem trước A/B; đã nói rõ mã hoặc “mặc định” thì chạy thẳng.
- Có thể xử lý nhiều ảnh và tách phong cách theo từng ảnh. Ảnh đã có viền phải được hỏi cách xử lý trước; không tự cắt ảnh hoặc chữ ký sát mép.
- PNG cuối giữ kích thước và pixel RGB sau giải mã/chuẩn hóa EXIF; các trường hợp chuyển màu, ghép trong suốt lên trắng, crop được duyệt và JPEG chia sẻ có giới hạn riêng như phần trên.
- Hai lỗi đã sửa: PNG 16-bit được chặn trước giải mã; ảnh xám có ICC giữ đúng alpha/transparency key trước chuyển màu.

Cần Python 3.10+ và Pillow 10.1–12.x; các lệnh ở trên chạy từ thư mục gốc repository. Khi dùng skill trong ứng dụng AI, ứng dụng phải có quyền truy cập ảnh và chạy mã. Việc cài skill tùy thuộc ứng dụng; chỉ gửi URL GitHub không bảo đảm cài đặt.

Để chia sẻ, thêm `--share`; để thêm chữ tiếng Việt, truyền `--caption` và đường dẫn `--font` có đủ dấu. Ảnh gốc không bị ghi đè; dữ liệu ảnh không tự được tải lên dịch vụ bên ngoài.

## License

MIT; see [LICENSE](LICENSE). The code and synthetic test data in this repository are covered by this license. No user photographs or third-party ICC profile files are included.
