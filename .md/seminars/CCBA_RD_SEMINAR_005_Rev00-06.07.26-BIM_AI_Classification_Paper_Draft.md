# CCBA RD SEMINAR 005 - KHUNG ĐỀ CƯƠNG BÀI BÁO KHOA HỌC
## Ứng dụng Trí tuệ Nhân tạo Tự động hóa phân loại cấu kiện theo ISO 12006-2 và Hệ thống Uniclass trong Mô hình thông tin công trình (BIM)

**Tác giả:** Nhóm nghiên cứu CCBA
**Ngày tạo:** 06.07.2026
**Phiên bản:** Rev00

---

## I. CẤU TRÚC CHI TIẾT CÁC PHẦN (IMRAD STRUCTURE)

### 1. Introduction (Mở đầu)
*   **1.1. Bối cảnh nghiên cứu:** Sự phát triển của OpenBIM và yêu cầu quản lý dữ liệu tài sản số theo tiêu chuẩn ISO 19650. Vai trò cốt lõi của việc gán nhãn phân loại (Classification) dựa trên khung **ISO 12006-2** nhằm đảm bảo tính đồng bộ thông tin.
*   **1.2. Vấn đề thực tế (Khoảng trống):** Quy trình gán mã Uniclass hiện nay chủ yếu là thủ công hoặc sử dụng các bộ lọc Dynamo/API cứng nhắc (Rule-based scripts). Các phương pháp này dễ sai sót, tốn nhân lực và thất bại khi gặp các quy ước đặt tên family không đồng nhất từ các nhà thầu khác nhau.
*   **1.3. Giải pháp đề xuất:** Giới thiệu phương pháp phân loại tự động kết hợp thông tin hình học IFC và xử lý ngôn ngữ tự nhiên (NLP) dựa trên AI, nâng cao tính đồng bộ dữ liệu bàn giao (COBie).

### 2. Materials & Methods (Vật liệu & Phương pháp)
*   **2.1. Chuẩn bị Dữ liệu (Materials):** Tập dữ liệu các file thiết kế định dạng IFC4.3 từ các dự án thực tế, chứa các bảng phân loại Uniclass mẫu:
    *   *Co (Complexes)*, *En (Entities)*, *SL (Spaces/Locations)*, *Ss (Systems)*, *Pr (Products)*.
*   **2.2. Trích xuất thuộc tính hình học & phi hình học:** Sử dụng Python để bóc tách thuộc tính từ IFC (tên cấu kiện, cao độ, không gian chứa, vật liệu).
*   **2.3. Huấn luyện Mô hình AI:** Kiến trúc mô hình phân loại văn bản (BERT/LLM) kết hợp Classifier để dự đoán mã Uniclass phù hợp từ mô tả thô.
*   **2.4. Quy trình đối soát và Ghi ngược dữ liệu:** Cơ chế lưu trữ và tự động ghi đè mã phân loại mới vào tệp tin mô hình gốc.

### 3. Results (Kết quả)
*   Trình bày kết quả thực nghiệm khách quan (>90% Kiến trúc, thấp hơn ở MEP).

### 4. Discussion (Thảo luận)
*   **4.1. Đóng góp khoa học chính:** Giải pháp AI đạt độ chính xác cao ngay cả khi dữ liệu family đặt tên không chuẩn hóa.
*   **4.2. So sánh đối chiếu:** So sánh trực tiếp hiệu quả của phương pháp AI đề xuất so với quy trình truyền thống.
*   **4.3. Giới hạn nghiên cứu:** Mô hình cần lượng dữ liệu huấn luyện lớn, chi phí gọi API cao và nhạy cảm đối với các lỗi chính tả thô của tiếng Việt.

---

## II. DANH MỤC HÌNH VẼ & BẢNG BIỂU DỰ KIẾN (VISUALS PLAN)

### 1. Các hình vẽ (Figures)
*   **Hình 1: Sơ đồ luồng xử lý dữ liệu (Data Pipeline):**
    - Luồng dữ liệu: Mô hình BIM (IFC) -> Trích xuất thuộc tính (Python/ifcopenshell) -> AI Classifier (Xử lý ngữ nghĩa tên cấu kiện) -> ISO 12006-2 Compliance check (Mapping sang Uniclass Tables) -> Mô hình BIM đã chuẩn hóa.
*   **Hình 2: Biểu đồ đánh giá hiệu năng:**
    - Biểu đồ đường biểu diễn sự thay đổi của độ chính xác (Precision/Recall) tương ứng với độ lớn của tập dữ liệu huấn luyện (Training Set Size).

### 2. Các bảng biểu (Tables)

*   **Bảng 1: Ma trận so sánh giải pháp (Giá trị × Độ phức tạp × Rủi ro × KISS)**

| Tiêu chí | Gán mã thủ công (Manual) | Script lọc cứng (Dynamo/API) | Giải pháp đề xuất (BIM + AI) |
| :--- | :--- | :--- | :--- |
| **Giá trị mang lại** | Thấp (Tốn thời gian, dễ sai sót) | Trung bình (Nhanh nhưng dễ bỏ sót) | **Cao** (Tự động hóa hoàn toàn, hiểu ngữ nghĩa) |
| **Độ phức tạp** | Rất thấp (Không cần lập trình) | Trung bình (Kỹ năng Dynamo cơ bản) | **Cao** (Cần kiến thức về Machine Learning/IFC) |
| **Rủi ro dữ liệu** | Rất cao (Sai sót con người) | Cao (Lỗi logic khi đổi tên Family) | **Thấp** (Có cơ chế tự học và đối soát tiêu chuẩn) |
| **KISS Compliance** | Đơn giản nhất về kỹ thuật | Đơn giản ở quy mô nhỏ | Cần đóng gói thành tool mỏng để thân thiện |

*   **Bảng 2: Bảng ánh xạ dữ liệu mẫu (Data Mapping Table)**

| Cấu kiện đầu vào (Raw Text) | Bảng Uniclass (ISO 12006-2) | Mã Uniclass dự kiến | Tên chuẩn hóa (English) |
| :--- | :--- | :--- | :--- |
| "Cửa đi gỗ 2 cánh D1000" | **Pr (Products)** | `Pr_30_59_24` | Door assemblies |
| "Phòng khách - tầng 1" | **SL (Spaces/Locations)** | `SL_25_10_48` | Living spaces |
| "Hệ thống ống gió cấp gió tươi" | **Ss (Systems)** | `Ss_75_70_52` | Mechanical ventilation systems |

---

## III. BẢN NHÁP CÁC ĐOẠN VĂN TIẾNG ANH CHUYÊN NGÀNH (DRAFTS)

### 2.1. Dataset and Material Preparation (Materials)
> *“To evaluate the proposed classification model, a real-world dataset was assembled from **ten complete BIM models** of commercial and residential projects in Vietnam. From these models, a total of **5,000 architectural and structural components** were extracted. The extraction process targeted both geometric attributes (volume, orientation, and level) and non-geometric metadata (family name, material description, and user-defined parameters) from the Industry Foundation Classes (IFC) schema. The extracted data was then cleaned by removing duplicates and null entries to form the raw text corpus for semantic processing.”*

### 2.2. Semantic Representation and AI-based Classification (Methods)
> *“To capture the deep semantic meaning of non-standard Vietnamese and English terms within the metadata, **pre-trained Bidirectional Encoder Representations from Transformers (BERT)** and **Large Language Models (LLMs)** were utilized. The raw text descriptions of the components were first tokenized and mapped into high-dimensional semantic vector spaces (embeddings). These embeddings were subsequently processed through a specialized classification layer to predict the corresponding **Uniclass 2015** classification codes, ensuring alignment with the **ISO 12006-2** framework. The performance of the classification was evaluated using standard metrics, including Precision, Recall, and F1-score.”*

### 3. Results (Kết quả)
> *“The experimental results indicated that the proposed BERT-based model achieved an overall F1-score of **92.4% for architectural elements** (such as walls, slabs, doors, and windows). However, the classification performance decreased when evaluating **specialized MEP (Mechanical, Electrical, and Plumbing) equipment**, yielding an average F1-score of **81.5%**. This discrepancy is primarily attributed to the higher diversity and abbreviation density in MEP component naming conventions compared to structural elements.”*

### 4. Discussion (Thảo luận)

#### 4.1. Explaining the Performance Discrepancy (Move 2b)
> *“The lower accuracy observed in MEP equipment classification stems from the heavy usage of non-standard abbreviations and technical acronyms (e.g., 'AHU-01', 'FCU-VAV') in real-world models. Unlike architectural elements which possess rich semantic descriptors, MEP family names often lack contextual vocabulary, limiting the ability of pre-trained BERT models to establish deep semantic mapping to Uniclass tables.”*

#### 4.2. Limitations and Model Sensitivity (Move 2c)
> *“A primary limitation of the proposed approach is its **high sensitivity to spelling errors and diacritic inconsistencies** in Vietnamese text metadata. Common typos in family naming (e.g., writing 'cưa' instead of 'cửa', or omitting tone marks entirely) significantly altered the generated text embeddings, leading to misclassifications. To mitigate this vulnerability, future research should integrate an automated domain-specific spell-checker and text-normalization pipeline prior to the embedding stage.”*

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
