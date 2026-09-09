# 🎨 Hướng Dẫn: Mẫu Thử Giao Diện (UI Prototype)

Mẫu thử giao diện là việc tạo ra **một vài phương án thiết kế giao diện (UI variants) khác biệt rõ rệt** trên cùng một route, cho phép người dùng chuyển đổi qua lại nhanh chóng thông qua một thanh điều khiển nổi (floating switcher) ở dưới màn hình để chọn ra phương án tốt nhất và xóa bỏ các phương án còn lại.

---

## 📅 Trường hợp áp dụng
- *"Trang này trông nên như thế nào?"*
- *"Tôi muốn xem một vài phương án bố cục cho trang Dashboard trước khi code thật."*
- *"Hãy thử một bố cục khác cho màn hình thiết lập."*
- Tránh việc mất cả ngày để phân vân giữa các mockup mơ hồ trong đầu mà không được trải nghiệm thực tế.

---

## 🛠️ Quy trình thực hiện

### 1. Chọn cấu trúc tích hợp (Sub-shapes)
Mẫu thử giao diện nên được đặt trong ngữ cảnh thực tế của ứng dụng (chung header, sidebar, dữ liệu thật). Có 2 cách đặt mẫu thử:
- **Phương án A (Ưu tiên): Tích hợp trực tiếp vào trang hiện tại**
  Sử dụng khi trang đã tồn tại. Render các phương án khác nhau trên cùng một route, phân biệt bằng tham số URL `?variant=A` hoặc `?variant=B`. Các phần fetching dữ liệu và xác thực giữ nguyên, chỉ thay đổi phần render giao diện.
- **Phương án B (Lựa chọn cuối): Tạo trang độc lập tạm thời**
  Chỉ dùng khi tính năng mới hoàn toàn chưa có trang chủ quản. Tạo một route tạm thời (ví dụ `/prototype/new-feature`) tuân thủ cấu trúc định tuyến của dự án. Đặt tên file/route chứa chữ `prototype` rõ ràng.

### 2. Thiết kế các phương án khác biệt rõ rệt (Radical Variants)
Tạo ra tối đa **3 - 5 phương án** (nhiều hơn sẽ gây loãng):
- Các phương án phải **khác biệt về cấu trúc** (layout, thông tin phân cấp, luồng thao tác chính) chứ không chỉ khác nhau về màu sắc hay chữ nghĩa.
- Export các component riêng biệt, ví dụ: `VariantA`, `VariantB`, `VariantC`.

### 3. Tích hợp Switcher điều khiển
Tạo một cơ chế định tuyến mỏng trên route:
```tsx
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <VariantA {...data} />}
    {variant === 'B' && <VariantB {...data} />}
    {variant === 'C' && <VariantC {...data} />}
    <PrototypeSwitcher variants={['A','B','C']} current={variant} />
  </>
);
```

### 4. Xây dựng thanh điều khiển nổi (Floating Switcher)
Thiết kế một thanh pill bar nhỏ, cố định ở góc dưới chính giữa màn hình (fixed-position bottom-center):
- Gồm: Nút mũi tên Trái (cycle back), Tên variant hiện tại (ví dụ: `B — Sidebar layout`), Nút mũi tên Phải (cycle forward).
- Hành vi: 
  - Click mũi tên sẽ thay đổi tham số `?variant=` trên URL (dùng router của framework để thay đổi trực tiếp mà không reload trang).
  - Cho phép dùng phím mũi tên `←` và `→` trên bàn phím để chuyển đổi nhanh (chú ý không bắt sự kiện này khi người dùng đang focus vào input/textarea).
  - Ẩn thanh switcher này trong môi trường sản xuất (gate trên `process.env.NODE_ENV !== 'production'`) để tránh lỡ tay merge lên production.

### 5. Thu hoạch và dọn dẹp
Khi người dùng đã lựa chọn được phương án ưng ý (hoặc kết hợp các phần tốt nhất của các phương án):
- Ghi nhận quyết định thiết kế vào file `NOTES.md` trong thư mục `.md/knowledge/issues/[feature_name]/prototypes/`.
- Thực hiện dọn dẹp:
  - Nếu là Phương án A: Xóa bỏ các variant thua cuộc và thanh switcher; tích hợp variant chiến thắng vào trang chính.
  - Nếu là Phương án B: Chuyển variant chiến thắng thành route chính thức, xóa bỏ route prototype tạm và thanh switcher.
  - Viết lại code chuẩn chỉ, viết tests và xử lý lỗi đầy đủ khi fold code vào dự án thực tế.

---

## 🚫 Các lỗi cần tránh (Anti-patterns)
- **Các phương án chỉ khác nhau về màu sắc hoặc copy.** Đó là tinh chỉnh, không phải prototype cấu trúc.
- **Dùng chung quá nhiều code UI giữa các phương án.** Việc chia sẻ Header là bình thường, nhưng chia sẻ chung Layout sẽ làm mất đi tính khác biệt của các variant.
- **Tích hợp mutation thật.** Prototype giao diện nên là read-only, nếu cần click hoạt động hãy dùng mock mutations.
