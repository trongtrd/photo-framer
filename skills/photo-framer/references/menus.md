# Menus / Lựa chọn

Use the user's language. Preserve codes: A floating photo, B gallery frame, C print/spec card. Default style A; default settings **A, 2-2-1**, **B, 1-2-1** or **C, 2-1-1**.

## Tiếng Việt

**Chọn phong cách:** A — Ảnh nổi (mặc định); B — Khung gallery; C — Thẻ thông số.

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

## English

**Choose style:** A — Floating photo (default); B — Gallery frame; C — Print / spec card.

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
