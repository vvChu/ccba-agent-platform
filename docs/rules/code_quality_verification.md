# CCBA Code Quality Verification & SDLC Loop

> **Tài liệu Tham chiếu Quy chuẩn Kiểm thử & Thẩm định (Layer 2 — SSOT)**  
> Áp dụng cho quy trình kiểm thử, thẩm định chất lượng, vòng lặp SDLC và điều tra thực nghiệm trên CCBA Platform.  
> Đối với quy chuẩn kiến trúc và lập trình mã nguồn, xem [`docs/rules/code_quality_standards.md`](code_quality_standards.md).

## 🧭 Bảng Điều Hướng Nhanh (Verification Navigation Index)

| Nhóm Quy Chuẩn (Category) | Các Mục Quy Chuẩn (Sections) |
| :--- | :--- |
| **I. Vòng Lặp SDLC & Cổng Kỹ Năng** | [3. SDLC Implementation Loop](#3-sdlc-implementation-loop) · [4. Cognitive Skills Quality & Invariant Gates](#4-cognitive-skills-quality--invariant-gates-layer-2) |
| **II. Kiểm Thử Thực Chất & Bất Biến** | [9. Pre-Evaluation Fast-Fail & CI Parity](#9-pre-evaluation-working-tree-fast-fail--ci-parity-cho-tác-tử-tự-hóa-auto-tuner-guardrails) · [10. Test Integrity & Anti-Potemkin](#10-test-integrity--anti-potemkin-invariant-kiểm-thử-thực-chất--chống-test-giả-lập) · [12. Standards-to-Code Enforcement](#12-standards-to-code-enforcement-invariant-kỷ-luật-đồng-bộ-giữa-quy-chuẩn-văn-bản--mã-nguồn-thực-thi) · [13. Temporal Invariance & Collinear Sort](#13-temporal-invariance--collinear-multi-key-sort-testing-kiểm-thử-bất-biến-thời-gian--chống-bẫy-cùng-chiều) |
| **III. Kiểm Chuẩn Tài Liệu & Điều Tra Sâu** | [14. Document Validation Arity & Drift Cleanliness](#14-document-validation-arity--drift-cleanliness-gate-cổng-kiểm-chuẩn-tài-liệu--vệ-sinh-kiến-trúc) · [17. Hypothesis-Driven Forensic & Ambiguity Resolution](#17-hypothesis-driven-forensic--ambiguity-resolution-figure-it-out-discipline) |
| **IV. Kiến Trúc & Tiêu Chuẩn Lập Trình** | Xem tài liệu bổ trợ: [`code_quality_standards.md`](code_quality_standards.md) (Mục 1, 2, 5, 6, 7, 8, 11, 15, 16) |

---

## 3. SDLC Implementation Loop
Khi triển khai mã nguồn dựa trên đặc tả (Spec):
1. **TDD (Test-Driven Development)**: Viết unit tests trước tại các điểm khớp nối công khai (seams).
2. **Continuous Validation**: Chạy kiểm tra kiểu (`mypy`) và chạy test suite liên tục.
3. **Review before Merge**: Chạy `/ccba-code-review` để quét code smells trước khi tạo PR.
4. **Merge Danger Triage**: Mọi PR và Kế hoạch Thực thi (`implementation_plan.md`) bắt buộc tự phân loại mức độ nguy hiểm: Khả năng đảo ngược (**One-way door** vs **Two-way door**) và Bán kính ảnh hưởng (**Localized** vs **Package-wide** vs **Monorepo-wide** vs **Spoke-affecting**) để tối ưu hóa thời gian review của con người.

---

## 4. Cognitive Skills Quality & Invariant Gates (Layer 2)
- Mọi Agent Skill thuộc hệ sinh thái CCBA phải tuân thủ Khung Quyết Định Hai Giai Đoạn (ADR-0057).
- Kỹ năng có nhiều chế độ hoạt động (multi-mode) bắt buộc phải xây dựng Tiêu chí hoàn thành động kiểm chứng đầy đủ từng mode, không để xảy ra tình trạng thiên lệch luồng mặc định gây hoàn thành non.
- Tuân thủ nguyên tắc Single Source of Truth trong các tài liệu tham chiếu vệ tinh (`references/*.md`, `MODES.md`), tuyệt đối không nhân bản các cảnh báo ràng buộc cờ.
- **Recompilation & Asset Synchronization Gate (HUB-ADR-0047, HUB-ADR-0058):**
  Khi tạo mới, chỉnh sửa nội dung hoặc bump version bất kỳ tệp `SKILL.md` nào, Agent **BẮT BUỘC** phải kích hoạt chuỗi 3 lệnh tái biên dịch và đồng bộ hóa tài sản nền tảng:
  1. `python scripts/governance/compile_catalog.py` (Cập nhật catalog SSOT `catalog.yaml`).
  2. `python scripts/governance/compile_skills_docs.py --write` (Đồng bộ Web Docs Portal, Markdown docs, và llms.txt).
  3. `python scripts/sync_hub_adr_matrix.py` (Đồng bộ Living Traceability Matrix nếu kỹ năng có viện dẫn hoặc điều chỉnh phạm vi ADR).

---

## 9. Pre-Evaluation Working Tree Fast-Fail & CI Parity cho Tác Tử Tự Hóa (Auto-Tuner Guardrails)
Khi thiết kế các pipeline tự động tối ưu hóa mã nguồn hoặc kỹ năng (như Nightly Auto-Tuner, GitRatchetOptimizer):
1. **Chặn Lỗi Trước Khi Đánh Giá (Pre-Evaluation Working Tree Fast-Fail):**
   - Mọi đột biến nội dung (mutation) sau khi áp dụng vào working tree BẮT BUỘC phải vượt qua kiểm tra vệ sinh tĩnh (`LinkAuditor`, syntax parser) **TRƯỚC KHI** kích hoạt hàm đánh giá tốn kém (`evaluate_content` / gọi LLM).
   - Bộ lọc kiểm tra tĩnh phải bao quát toàn diện: liên kết Markdown hỏng (`links`), ký hiệu mã giả định (`code_refs`), và biến môi trường chưa đăng ký (`env_vars`).
   - Nếu phát hiện vi phạm, hệ thống phải ROLLBACK ngay lập tức tệp trên đĩa về `best_content`, hủy bỏ iteration và không tiêu tốn bất kỳ token LLM đánh giá nào.
2. **Chỉ Dẫn Đột Biến An Toàn (Safe Heuristic Directives):**
   - Trong các mutator thao tác đơn tệp (single-file mutators như `tuner.py`), gợi ý cấu trúc tuyệt đối KHÔNG được chèn đường dẫn tương đối tĩnh giả định (ví dụ: `references/guide.md`) nếu tệp chưa hiện diện trên đĩa. Chỉ được dẫn link tới các tệp hiện hữu hoặc hướng dẫn qua mục lục text thuần.
3. **Tuyệt Đối Khớp Nối Công Cụ Kiểm Tra (True CI Parity):**
   - Các cổng Pre-PR Gate của Daemon và lệnh kiểm định cục bộ (`ccba_harness verify-patch --preset skill`) bắt buộc phải đồng bộ 100% với các bước kiểm tra của CI trên GitHub Actions (bao gồm cả `scripts/validate_docs.py . --src scripts,packages --changed`), đảm bảo mã tự động sinh ra luôn xanh 100% khi mở Pull Request.

---

## 10. Test Integrity & Anti-Potemkin Invariant (Kiểm Thử Thực Chất & Chống Test Giả Lập)
Khi viết unit tests cho các cơ chế kiểm định phòng vệ (Guardrails, Linters, Deletion Guards, Diff Auditors):
1. **Bắt buộc kích hoạt vi phạm thực tế (Trigger Before Pardon):**
   - Bài test kiểm tra ngoại lệ tha bổng (ví dụ: cờ `[DEPRECATED]` hoặc whitelist bypass) **BẮT BUỘC PHẢI THỰC SỰ XÓA BỎ** hoặc làm sai lệch đối tượng kiểm chuẩn trong văn bản đề xuất.
   - Nghiêm cấm giữ nguyên cấu trúc gốc trong văn bản đề xuất khiến tập hợp vi phạm rỗng (`missing_patterns == set()`), tạo ra các bài test Potemkin giả lập luôn pass mà mã nguồn kiểm tra ngoại lệ bên dưới chưa từng được thực thi.
2. **Kiểm chứng độc lập nhánh phủ định (Dual Assertion):**
   - Mọi test suite cho guardrail phải đi kèm cặp kiểm thử đối ứng:
     - Trường hợp không có thẻ ngoại lệ $\rightarrow$ Phải bắt lỗi thành công (`assert len(violations) > 0`).
     - Trường hợp có thẻ ngoại lệ hợp lệ $\rightarrow$ Phải tha bổng thành công (`assert len(violations) == 0`).
3. **Bao phủ toàn diện các ký tự phân cách (Separator Coverage):**
   - Bộ test cho parser/regex ranh giới bắt buộc phải kiểm thử độc lập cả 3 họ phân cách: phân cấp số thập phân (`.1`), hậu tố gạch nối (`-bis`, `-sub`), và gạch chéo (`/2`).
4. **Phép thử hai biến đổi hành vi (Two-Edit Behavioral Test Litmus — Pstack v0.15.25 & COND-03):**
   - **Hành vi quan sát được (Observable Behavior)** được định nghĩa gắn kết trực tiếp với các bất biến tiêu chuẩn tại Mục 12: bao gồm giá trị trả về, giới hạn quy chuẩn/tiêu chuẩn, lỗi chuẩn hóa mà caller phân nhánh xử lý, trạng thái đọc lại được qua giao diện công khai, và hiệu ứng phụ (side-effects) lên hệ thống ngoài.
   - Mọi bài unit/integration test phải vượt qua đồng thời 2 phép biến đổi giả định:
     - **Phá vỡ hành vi (Break the behavior):** Giả sử làm sai lệch kết quả trả về, vi phạm ngưỡng tiêu chuẩn (Mục 12), bỏ qua một side-effect hoặc gọi trùng lặp $\rightarrow$ nếu bài test vẫn PASS, bài test đó vô giá trị (thường do assertion quá lỏng như `is not None`, hoặc tự tính expected value bằng chính hàm đang test). Bắt buộc viết lại hoặc xóa bỏ.
     - **Thay đổi cấu trúc nội bộ (Change the internals):** Giữ nguyên 100% hành vi quan sát được và tính tuân thủ quy chuẩn nhưng đổi tên hàm helper nội bộ hoặc thứ tự gọi private $\rightarrow$ nếu bài test FAIL, bài test đang bị ghim cứng vào implementation thay vì contract.

---

## 12. Standards-to-Code Enforcement Invariant (Kỷ Luật Đồng Bộ Giữa Quy Chuẩn Văn Bản & Mã Nguồn Thực Thi)
- Khi ban hành hoặc nâng cấp bất kỳ quy chuẩn kỹ thuật nào trong `docs/rules/*.md` (ví dụ: mở rộng regex ranh giới từ `(?!\.\d)` sang `(?![.\-\/][\w\d])`):
- Agent **BẮT BUỘC** phải:
  1. Mở ngay patch tương ứng trong mã nguồn tham chiếu chuẩn (`packages/ccba-harness` hoặc core packages).
  2. Bổ sung các unit test cases kiểm chứng trực tiếp từng trường hợp biên mới quy định vào bộ test suite chính thức (tuân thủ Mục 10.3 Separator Coverage).
- Nghiêm cấm tuyên bố tính năng đã hoàn thiện trong báo cáo nghiệm thu (`walkthrough.md`) nếu quy chuẩn mới chỉ nằm trên văn bản tài liệu mà mã nguồn chạy thực tế chưa được áp dụng.

---

## 13. Temporal Invariance & Collinear Multi-Key Sort Testing (Kiểm Thử Bất Biến Thời Gian & Chống Bẫy Cùng Chiều)
Khi xây dựng các bài unit test có yếu tố thời gian hoặc kiểm thử độ ưu tiên giữa nhiều tiêu chí sắp xếp:
1. **Bất biến thời gian tương đối (Temporal Invariance):**
   - Tuyệt đối KHÔNG hardcode chuỗi ngày tĩnh (`"YYYY-MM-DD"`) trong các test case kiểm tra cơ chế cooldown, TTL, sliding window, hoặc phân loại theo thời gian thực thi gần nhất.
   - Luôn sử dụng hàm sinh ngày động tương đối dựa trên `datetime.date.today()` hoặc `datetime.datetime.now(datetime.timezone.utc)` (ví dụ: `older_date = today - timedelta(days=2)`, `newer_date = today - timedelta(days=1)`).
   - Đảm bảo tính bất biến toán học: Khoảng cách giữa các ngày kiểm thử và `cutoff_date` luôn giữ nguyên giá trị logic bất kể bài test được thực thi vào ngày nào trong tương lai.
2. **Chống bẫy kiểm thử cùng chiều (Collinear Multi-Key Sort Trap):**
   - Khi một hàm sắp xếp sử dụng khóa phức hợp (ví dụ: `(date, mtime)`), nếu fixture ghi tệp mới hơn sau tệp cũ hơn, thứ tự filesystem `st_mtime` và thứ tự ngày parsed sẽ cùng chiều ($mtime_{new} > mtime_{old}$ đồng thời $date_{new} > date_{old}$). Điều này tạo ra một "bài test pass ảo": ngay cả khi logic sắp xếp theo `date` hỏng hoàn toàn, test vẫn pass nhờ `st_mtime`.
   - **Quy chuẩn bắt buộc:** Khi kiểm thử thứ tự ưu tiên của khóa chính (`date`), fixture phải cố tình tạo ra xung đột với khóa phụ: thiết lập `os.utime` sao cho tệp có ngày mới hơn lại mang `mtime` cũ hơn (ví dụ lùi lại 3600s). Chỉ khi đó bài test mới thực sự chứng minh được khóa chính có độ ưu tiên cao hơn khóa phụ.

---

## 14. Document Validation Arity & Drift Cleanliness Gate (Cổng Kiểm Chuẩn Tài Liệu & Vệ Sinh Kiến Trúc)

Khi chạy kiểm định tài liệu hoặc chuẩn bị báo cáo nghiệm thu:

1. **Single-Arity CLI Constraint:** `scripts/validate_docs.py` chỉ nhận duy nhất 1 tham số vị trí mục tiêu `[docs_dir]`. TUYỆT ĐỐI CẤM truyền đồng thời nhiều thư mục dạng `validate_docs.py dirA dirB` (gây lỗi `unrecognized arguments`, Exit Code 2). BẮT BUỘC chạy tuần tự qua toán tử `&&` hoặc truyền thư mục cha bao trùm (ví dụ: `docs` hoặc `.`).
2. **Untracked Core Drift Isolation:** Động cơ `DriftAuditor` quét cả tệp không theo dõi (`status == "??"`) trong các thư mục cốt lõi (`packages/`, `scripts/`, `.agents/skills/`, `.agents/workflows/`, và `pyproject.toml`). Mọi tệp rác hoặc script tạm (ngoại trừ các tệp nằm trong `tests/` hoặc `scripts/tests/`) chưa đăng ký trong tài liệu kiến trúc (`README.md`, `PLATFORM.md`) sẽ kích hoạt lỗi chặn cứng `Structural drift detected` (Exit Code 1). BẮT BUỘC stash hoặc dọn sạch tệp untracked trước khi chạy validation, hoặc đặt tệp thử nghiệm trong `scripts/tests/`.
3. **Verbatim Reproducible Commands:** Mọi lệnh kiểm định trong `walkthrough.md`, `task.md` và PR body BẮT BUỘC ghi toàn văn đường dẫn tệp cụ thể, TUYỆT ĐỐI CẤM dùng dấu ba chấm `...` rút gọn đối số `--target` trong `ccba-harness verify-patch` (gây lỗi gãy kiểm thử `Artifact not found` hoặc `File does not exist`, Exit Code 1).

---

## 17. Hypothesis-Driven Forensic & Ambiguity Resolution (Figure-It-Out Discipline)

Quy chuẩn xử lý bài toán kỹ thuật phức tạp, di chuyển kiến trúc quy mô lớn, hoặc chẩn đoán các lỗi ẩn không rõ nguyên nhân (ambiguous anomalies):

1. **Completion Predicate & Non-Goals (Xác Lập Điều Kiện Tiên Quyết):**
   - Trước khi sửa bất kỳ dòng mã nào, Agent bắt buộc phải tuyên bố bằng văn bản:
     - **Completion Predicate:** Tiêu chí hoàn thành cụ thể, đo lường được bằng lệnh thực thi tự động (exit code 0, benchmark vượt ngưỡng, test pass).
     - **Non-Goals:** Những hạng mục nằm ngoài phạm vi tác vụ nhằm chống trượt mục tiêu (scope creep) và tối ưu hóa ngân sách token.
2. **4-Part Uncertainty Partitioning (Phân Tách Vùng Mù 4 Nhóm):**
   - Khi đối mặt với sự mơ hồ, Agent bắt buộc chia tách bài toán thành 4 nhóm độc lập:
     - **Factual Questions (Câu hỏi sự thật):** Tìm kiếm câu trả lời bằng công cụ nội tại (`grep`, `view_file`, AST parsing, git log). TUYỆT ĐỐI CẤM hỏi con người những gì máy tính và mã nguồn có thể tự trả lời.
     - **Empirical Forks (Nhánh giả thuyết thực nghiệm):** Khi có $\ge 2$ hướng giải quyết khả thi, bắt buộc tạo spike/prototype độc lập hoặc bài test nhỏ để đo đạc định lượng thay vì suy diễn lý thuyết. **Giới hạn ngắt mạch (COND-02):** Mỗi nhánh thực nghiệm chỉ được thử-sai tối đa 3 lần (*Max 3 Empirical Iterations*); nếu vượt quá 3 lần mà chưa hội tụ kết quả, bắt buộc dừng lại để nâng cấp thành thảo luận kiến trúc (ADR).
     - **Product Preferences (Sở thích sản phẩm):** Chỉ phỏng vấn người dùng khi liên quan trực tiếp đến trải nghiệm người dùng cuối hoặc quy định kinh doanh nghiệp vụ. **Ứng xử khi chạy headless/CI (COND-03):** Nếu không có người dùng tương tác trực tiếp, Agent tự động chọn phương án bảo thủ nhất (*least-privilege*), duy trì tính tương thích ngược tối đa và ghi nhận rõ lý do trong PR description.
     - **Irreversible Decisions (Quyết định một chiều - One-way door):** Thay đổi schema dữ liệu, xóa API công khai, thay đổi giao thức nền tảng bắt buộc phải lập bản đề xuất kiến trúc (ADR) và có sign-off chính thức trước khi commit.
3. **Falsifiable Hypotheses & Minimal Reproducer Codification (Tái Lập & Khắc Sâu Bài Test - COND-04):**
   - Mọi giả định nguyên nhân lỗi bắt buộc phải phát biểu dưới dạng giả thuyết có thể bác bỏ (Falsifiable Hypothesis).
   - Thiết lập kịch bản tái lập lỗi nhỏ nhất (Minimal Reproducer) và chứng minh lỗi xuất hiện TRƯỚC KHI viết mã sửa lỗi.
   - **Bắt buộc lưu vết thường trực (Reproducer Codification):** Mọi Minimal Reproducer sau khi chứng minh và sửa lỗi thành công BẮT BUỘC phải được chuẩn hóa thành test case chính thức trong `tests/` hoặc bài kiểm tra trong `harness/`, tuyệt đối không xóa bỏ dưới dạng script rác tạm thời.
4. **Runtime Evidence over Proxy Assumptions (Bằng Chứng Thực Tế Thay Vì Giả Định Ảo):**
   - Tuyệt đối CẤM kết luận "code nhìn có vẻ đúng" hoặc "lý thuyết đã khớp". Mọi nghiệm thu bắt buộc phải kèm theo bằng chứng runtime thực tế (kết quả chạy lệnh, stdout/stderr, mã thoát 0 từ `ccba-harness verify-patch`).
5. **Post-Forensic Cheap Always-On Signal (Tín Hiệu Giám Sát Thường Trực Sau Điều Tra Sâu — Pstack v0.15.22 & COND-03):**
   - Khi một ca chẩn đoán lỗi đòi hỏi phải đào sâu qua nhiều tầng dữ liệu mới tìm ra dữ kiện quyết định (*deciding fact*), sau khi khắc phục nguyên nhân gốc, Agent bắt buộc phải bổ sung hoặc đề xuất một **tín hiệu giám sát rẻ, luôn bật (cheap always-on signal)** — như một trường dữ liệu trong structured log, một kiểm tra bất biến (invariant assertion) nhẹ mang mã định danh điều khoản/quy chuẩn liên quan (theo Mục 12), hoặc một chỉ báo trong readiness probe — để nếu lỗi tương tự tái diễn, nguyên nhân sẽ lộ diện ngay ở cái nhìn đầu tiên mà không làm suy giảm hiệu năng hệ thống.
