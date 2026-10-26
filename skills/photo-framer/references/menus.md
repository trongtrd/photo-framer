# Menus / Lựa chọn

Use the user's language. Preserve codes: A floating photo, B gallery frame, C print/spec card, D spec card with custom right-side text. Default style A; default settings **A, 2-2-1**, **B, 1-2-1**, **C, 2-1-1** or **D, 2-1-1**.

## Tiếng Việt

**Chọn phong cách:** A — Ảnh nổi (mặc định); B — Khung gallery; C — Thẻ thông số; D — Thẻ thông số có chữ riêng.

### A — Ảnh nổi
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Khoảng trắng | Hẹp | **Vừa — mặc định** | Rộng |
| Bóng đổ | Nhẹ | **Mềm vừa — mặc định** | Rõ |
| Nền | **Trắng — mặc định** | Trắng ngà | Xám rất nhạt |

Trả lời theo thứ tự **khoảng trắng–bóng–nền**, ví dụ `2-2-1`, hoặc `mặc định`.
"Mềm vừa" là mức bóng đã tăng và được duyệt, không phải bóng mờ của bản thử đầu.

### B — Khung gallery
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Màu khung | **Đen — mặc định** | Trắng | Xám than |
| Bo giấy trắng | Hẹp | **Vừa — mặc định** | Rộng |
| Nền ngoài khung | **Xám — mặc định** | Trắng | Trắng ngà |

Trả lời theo thứ tự **khung–bo giấy–nền**, ví dụ `1-3-1`, hoặc `mặc định`.
Bóng trong/ngoài và độ dày khung phối sẵn; bo giấy luôn trắng ở v0.1.

### C — Thẻ thông số (print/spec card)
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Viền | Hẹp | **Vừa — mặc định** | Rộng |
| Nền | **Trắng — mặc định** | Trắng ngà | Xám rất nhạt |
| Chữ | **Máy + ống kính + thông số — mặc định** | Chỉ máy + ống kính | Không chữ |

Trả lời theo thứ tự **viền–nền–chữ**, ví dụ `2-1-1`, hoặc `mặc định`.
Thông số đọc tự động từ EXIF/XMP của ảnh, không tự bịa; logo hãng gắn theo máy chụp,
hãng chưa có logo thì dùng chữ đậm. Ảnh mất metadata sẽ được hỏi trước khi bỏ chữ.

### D — Thẻ thông số có chữ riêng
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Viền | Hẹp | **Vừa — mặc định** | Rộng |
| Nền | **Trắng — mặc định** | Trắng ngà | Xám rất nhạt |
| Thông tin bên trái | **Máy + ống kính + thông số — mặc định** | Chỉ máy + ống kính | Không thông tin |

Trả lời theo thứ tự **viền–nền–thông tin bên trái**, ví dụ `2-1-1`, hoặc `mặc định`.
Đọc EXIF/XMP như C, thay logo bằng chữ bạn cung cấp ở góc dưới bên phải.
Chữ bên phải dùng cùng font, cỡ, độ đậm và màu với dòng máy/ống kính;
vẫn hiện khi chọn 3 ở hàng cuối. Không tự thu nhỏ hoặc cắt chữ cho vừa.

Nếu chưa có nội dung, hỏi: **Bạn muốn điền chữ gì ở góc dưới bên phải?**
Có thể điền địa điểm, tên người chụp, thời gian hoặc kết hợp; dùng nguyên văn,
không suy đoán từ metadata. Ví dụ: `Berlin, Germany | October 2022`.
Nếu đã cung cấp nội dung, không hỏi lại.

## English

**Choose style:** A — Floating photo (default); B — Gallery frame; C — Print / spec card; D — Custom spec card.

### A — Floating photo
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Margin | Narrow | **Medium — default** | Wide |
| Shadow | Light | **Soft medium — default** | Strong |
| Background | **White — default** | Ivory | Light gray |

Reply in **margin–shadow–background** order, e.g. `2-2-1`, or `default`.

### B — Gallery frame
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Frame color | **Black — default** | White | Charcoal |
| White mat | Narrow | **Medium — default** | Wide |
| Outer background | **Gray — default** | White | Ivory |

Reply in **frame–mat–background** order, e.g. `1-3-1`, or `default`.
Frame thickness and shadows are coordinated; mat remains white in v0.1.

### C — Print / spec card
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Margin | Narrow | **Medium — default** | Wide |
| Background | **White — default** | Ivory | Light gray |
| Caption | **Camera + lens + exposure — default** | Camera + lens only | No text |

Reply in **margin–background–caption** order, e.g. `2-1-1`, or `default`.
Specs come from the photo's EXIF/XMP and are never invented; the brand logo follows
the camera body, with a bold text wordmark for brands without a bundled logo.
Files without metadata are flagged before text is skipped.

### D — Custom spec card
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Margin | Narrow | **Medium — default** | Wide |
| Background | **White — default** | Ivory | Light gray |
| Left-side details | **Camera + lens + exposure — default** | Camera + lens only | No details |

Reply in **margin–background–left-side details** order, e.g. `2-1-1`, or `default`.
Capture details come from EXIF/XMP as in C. Your text replaces the logo at the
bottom right, using the same font, size, weight and color as the gear line.
The right-side text remains visible with option 3. It is never shrunk or truncated.

If the wording is missing, ask: **What exact text would you like at the bottom right?**
It can be a location, photographer name, date, or combination; preserve it verbatim
and never infer it from metadata. Example: `Berlin, Germany | October 2022`.
Do not ask again when the wording has already been supplied.
