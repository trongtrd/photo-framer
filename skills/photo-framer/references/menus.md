# Menus / Lựa chọn

Use the user's language. Preserve codes: A floating photo, B gallery frame, C print/spec card, D spec card with custom right-side text, E Color Echo, F Film Edge, G Deckled Paper. Default style A; default settings **A, 2-2-1**, **B, 1-2-1**, **C/D/E/F/G, 2-1-1**.

## Tiếng Việt

**Chọn phong cách:** A — Ảnh nổi (mặc định); B — Khung gallery; C — Thẻ thông số; D — Thẻ thông số có chữ riêng; E — Color Echo / Viền đồng sắc; F — Film Edge / Viền phim; G — Deckled Paper / Giấy mỹ thuật mép xé.

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

### E — Color Echo / Viền đồng sắc
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Độ rộng viền | Hẹp | **Vừa — mặc định** | Rộng |
| Sắc độ màu tự chọn | **Dịu — mặc định** | Tự nhiên | Sáng |
| Đường viền trong | **Mảnh — mặc định** | Không có | Vừa |

Trả lời theo thứ tự **độ rộng–sắc độ tự chọn–viền trong**, mặc định `2-1-1`.
Mặc định, Python tự chọn một màu cho mỗi ảnh; chạy cả lô mà không hỏi lại từng
ảnh và không tạo ba phương án màu. Chỉ tạo bản xem trước khi được yêu cầu.
Nếu muốn một màu chung cho cả bộ, cung cấp màu một lần: `--frame-color "#ad896c"`.
Màu chung được dùng nguyên giá trị, không chịu tùy chọn sắc độ ở hàng thứ hai.
Ảnh gần trắng đen dùng màu trung tính dự phòng; pixel vùng ảnh được giữ nguyên.

### F — Film Edge / Viền phim
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Độ rộng viền | Hẹp | **Vừa — mặc định** | Rộng |
| Nền viền | **Than — mặc định** | Đen | Nâu đậm |
| Lỗ phim hai bên | **Tiêu chuẩn — mặc định** | Thưa | Dày |

Trả lời theo thứ tự **độ rộng–nền viền–lỗ phim**, mặc định `2-1-1`.
Hai cụm chữ đều do người dùng nhập. Nếu chưa đủ thông tin, hỏi cùng lúc:
**Bạn muốn ghi gì ở góc dưới trái và góc dưới phải? Có thể để trống từng bên.**
Giữ phần đã cung cấp; chỉ để trống khi người dùng chủ động chọn như vậy.
Ví dụ: trái `Berlin, Germany`, phải `October 2022`. Không tự điền số ảnh,
nhãn hãng phim, thời gian từ metadata hoặc chữ từ bản phác thảo.
Chữ hai bên dùng cùng font và cỡ; không tự cắt, viết hoa hoặc thu nhỏ cho vừa.

### G — Deckled Paper / Giấy mỹ thuật mép xé
| Tùy chỉnh | 1 | 2 | 3 |
|---|---|---|---|
| Khoảng giấy quanh ảnh | Hẹp | **Vừa — mặc định** | Rộng |
| Màu giấy | **Trắng ấm — mặc định** | Trắng sáng | Ngà |
| Mép xé | **Nhẹ — mặc định** | Vừa | Rõ |

Trả lời theo thứ tự **khoảng giấy–màu giấy–mép xé**, mặc định `2-1-1`.
Vân giấy và bóng nhẹ chỉ nằm ngoài vùng ảnh hình chữ nhật. Mép xé là mép
ngoài của tờ giấy; ảnh không bị xé, đổi màu hay thêm hạt. Mẫu được tạo bằng
Python, không gọi AI cho từng ảnh. Chạy cùng thiết lập cho cả lô; mặc định
không có chữ hoặc logo. Có thể yêu cầu thêm chữ riêng trên khoảng giấy.

## English

**Choose style:** A — Floating photo (default); B — Gallery frame; C — Print / spec card; D — Custom spec card; E — Color Echo; F — Film Edge; G — Deckled Paper.

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

### E — Color Echo
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Border width | Narrow | **Medium — default** | Wide |
| Auto color tone | **Muted — default** | Natural | Light |
| Inner edge | **Thin — default** | None | Medium |

Reply in **width–auto tone–inner edge** order, default `2-1-1`.
Python selects one color per photo and processes the whole batch without
per-image questions or three color variants. Generate previews only on request.
For a shared color, supply `--frame-color "#ad896c"` once for the batch; that
exact color bypasses auto analysis and ignores the auto-tone row.
Near-neutral images use a neutral fallback. Photo pixels stay unchanged.

### F — Film Edge
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Border width | Narrow | **Medium — default** | Wide |
| Border background | **Charcoal — default** | Black | Dark brown |
| Side sprockets | **Standard — default** | Sparse | Dense |

Reply in **width–background–sprockets** order, default `2-1-1`.
Both corner texts are user-supplied. Ask for any missing choices together:
**What would you like at the bottom left and bottom right? Either corner may be left blank.**
Keep supplied fields; a blank must be explicitly chosen. Example: left
`Berlin, Germany`, right `October 2022`. Never auto-fill a frame number,
film brand, capture date or mockup wording. The fields share font and size;
never truncate, uppercase or shrink them to fit.

### G — Deckled Paper
| Setting | 1 | 2 | 3 |
|---|---|---|---|
| Paper margin | Narrow | **Medium — default** | Wide |
| Paper tone | **Warm white — default** | Bright white | Ivory |
| Torn edges | **Subtle — default** | Medium | Rough |

Reply in **margin–paper tone–torn edges** order, default `2-1-1`.
Paper texture and a soft shadow stay outside the rectangular photo. The torn
silhouette belongs to the paper's outer edge; the photo is never torn, recolored
or grained. Python creates the pattern without per-photo AI calls. Reuse the
settings across a batch. No text or logo is added by default; a caption on the
paper may be requested separately.
