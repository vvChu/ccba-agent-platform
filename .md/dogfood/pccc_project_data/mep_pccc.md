# BẢN VẼ HỆ THỐNG CƠ ĐIỆN PCCC (MEP - TRÍCH XUẤT THÔNG SỐ)
**DỰ ÁN: CCBA HORIZON TOWER - BỘ MÔN MEP PCCC**

---

## 1. HỆ THỐNG CẤP NƯỚC & TRẠM BƠM CHỮA CHÁY
- **Vị trí trạm bơm:** Tầng hầm B2, cốt $-6.800\text{ m}$.
- **Thông số bể nước ngầm PCCC trên bản vẽ MEP-FS-01:**
  - Kích thước phủ bì bể: $12.0\text{ m} \times 7.0\text{ m} \times 5.0\text{ m}$.
  - Mực nước hữu dụng thực tế: $12.0 \times 7.0 \times 5.0 = 420\text{ m}^3$.
  - *Xung đột thông số (M-01):* Dung tích hữu dụng trên bản vẽ MEP chỉ đạt **420 m³**, trong khi Thuyết minh thiết kế kỹ thuật yêu cầu tính toán tối thiểu là **450 m³** (Thiếu hụt $30\text{ m}^3$ nước dự trữ).
- **Thông số tổ hợp bơm chữa cháy trên bản vẽ MEP-FS-02:**
  - Bơm điện chính (EP-01): Nhãn thiết bị ghi $Q = 120\text{ l/s}$, Cột áp **H = 90 m** (Khác với Thuyết minh tính toán là **H = 95 m** $\rightarrow$ *Xung đột M-02*).
  - Bơm diesel dự phòng (DP-01): $Q = 120\text{ l/s}$, Cột áp $H = 95\text{ m}$.
  - Bơm bù áp (JP-01): $Q = 5\text{ l/s}$, Cột áp $H = 105\text{ m}$.
  - Đường ống hút và ống đẩy: Đường kính ống hút DN250, ống đẩy DN200 thép mạ kẽm tráng kẽm nhúng nóng SCH40.

---

## 2. HỆ THỐNG CHỮA CHÁY TỰ ĐỘNG SPRINKLER & MÀN NGĂN DRENCHER
- Mạng lưới đường ống phân phối:
  - Tầng hầm: Đường ống khô đi trần lộ, đầu phun hướng lên Upright nhiệt độ tác động $68^\circ\text{C}$.
  - Tầng điển hình văn phòng: Đầu phun hướng xuống Pendent loại giấu trần thẩm mỹ có nắp chụp bảo vệ.
- Cụm van kiểm tra báo động (Alarm Valve):
  - Mỗi tầng bố trí 01 cụm van kiểm tra kèm công tắc dòng chảy (Flow Switch) và van giám sát tín hiệu mở (Tamper Switch) kết nối về tủ trung tâm báo cháy.

---

## 3. HỆ THỐNG BÁO CHÁY TỰ ĐỘNG & CHIẾU SÁNG SỰ CỐ
- Bố trí đầu báo cháy (Bản vẽ MEP-FA-03):
  - Đầu báo khói địa chỉ thông minh bố trí tại các sảnh tầng, hành lang, phòng văn phòng mở.
  - Đầu báo nhiệt địa chỉ bố trí tại phòng máy biến áp, máy phát điện và phòng rác.
- *Xung đột kỹ thuật phát hiện (M-03):*
  - Tại trục 4-5 hành lang tầng 3, đầu báo khói mã số FA-SD-0312 bố trí cách miệng gió hồi máy lạnh chỉ $400\text{ mm}$ ($0.4\text{ m}$). Theo Mục 6.13 TCVN 5738:2021, đầu báo khói phải cách miệng thổi hoặc hút gió điều hòa không khí tối thiểu **1.0 m** để tránh luồng không khí thổi loãng khói gây trễ báo cháy.
- Chiếu sáng sự cố và chỉ dẫn thoát nạn (Emergency & Exit Lights):
  - Sử dụng đèn LED tích hợp pin sạc dự phòng duy trì chiếu sáng tối thiểu 2 giờ khi mất điện nguồn.
  - *Xung đột kỹ thuật phát hiện (M-04):* Tuyến cáp cấp nguồn cho đèn thoát nạn Exit buồng thang ST-01 sử dụng cáp đồng bọc PVC thường (Cu/PVC/PVC) thay vì cáp chậm cháy/chống cháy (FR - Fire Resistant) theo quy định của QCVN 06:2022/BXD.
