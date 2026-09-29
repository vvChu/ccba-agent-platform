Phản biện đối kháng cho Issue #439. Kế hoạch đi đúng bốn điều kiện bảo lưu và thứ tự A rồi B rồi C không có vòng phụ thuộc. Chưa nên mở PR-A cho đến khi sửa các điểm dưới đây. Chúng nằm trong mã Hub hiện tại, không chỉ trong văn bản chuẩn.

## Phê duyệt

- Chỉ mục card và lệnh `find-seam` theo `in` / `out` / `hardware` là đúng Điều khoản 4.1.
- Linter bám AST sẵn có trong `check_dependency_contracts.py` (dải dòng `lineno`–`end_lineno`) là đúng chỗ để gắn marker. Không viết scanner regex mới trên toàn file.
- Allowlist vai trò cho `check_spoke_cleanliness.py` là đúng Điều khoản 4.5. Ngân sách 15 file đang đếm mọi `scripts/*.py` ngoài `ALLOWLIST_SCRIPTS` và tiền tố `check_`.
- PR-C đứng sau PR-A. Hiến pháp chỉ được ra lệnh `find-seam --in/--out` khi cờ đó đã có trên `main`.
- Giữ GPI (ADR-0057) nguyên vai trò. Thang \(U\) chỉ chấm lựa chọn thiết kế. Hai thước này không thay nhau.
- Complexity \(\ge 15\) và SLOC \(> 80\) ở lại review. Không đưa vào CI trong PR-B. `tuner.py`, `daemon.py`, `scorers/domain.py` sẽ làm đỏ cổng ngay.

## Chặn PR-A

**1. Card mẫu trỏ symbol không tồn tại.** `ConversionPipeline` nằm ở `mdconverter` (`packages/mdconverter/src/mdconverter/__init__.py`, `__version__ = 2.3.0`). Không có module `ccba_markdown` và không có lệnh `python -m ccba_markdown health`. `import_path` của card markdown phải là `mdconverter:ConversionPipeline`. Test PR-A phải đối soát từng `import_path` với `__all__` của package. Bỏ `version` và `health_check` bịa. `health_check` để trống cho đến khi có argv cấu trúc. `find-seam` không thực thi chuỗi shell đó.

**2. Ngữ nghĩa khớp card phải là "card đáp ứng được truy vấn".** `--in pdf --out markdown` phải khớp card `in: [pdf, docx]`, `out: [markdown]`. So sánh bằng tập sẽ làm ví dụ trong chuẩn v2.0 trả `NO_MATCH`. Quy tắc:

- Mỗi giá trị `--in` thuộc `capability.in`. Card được nhận thêm đầu vào.
- Mỗi giá trị `--out` thuộc `capability.out`.
- Bỏ `--hardware` thì không lọc. `--hardware dgx_spark` khớp card có `dgx_spark` hoặc `any`. Card chỉ có `dgx_spark` không khớp `linux_cuda`.
- Nhiều card khớp thì JSON trả cả danh sách, sắp theo `seam_id`, exit 0. Không chọn thầm một card.

**3. Từ khóa không được biến thành biên lai card.** Chế độ hybrid trong kế hoạch trả mô tả catalog khi trúng từ. Điều khoản 4.1 cấm điều đó. Positional `keyword` giữ optional để lệnh cũ không gãy, nhưng kết quả chỉ là `KEYWORD_HINT`. Không có card capability thì trạng thái vẫn là `NO_MATCH`, kèm hash. Hash là SHA-256 của đúng byte file `seam-contracts.yaml` đã đọc.

Exit code: `0` khi có card, `2` khi `NO_MATCH`, `1` khi sai cú pháp. `--json` in một object `{status, index_sha256, cards}`. `--check` đang được nêu mà chưa định nghĩa. Bỏ khỏi PR-A hoặc định nghĩa thành "exit 2 khi NO_MATCH".

**4. `forbidden_substitute_imports` chỉ chứa tên module AST nhìn thấy.** `fitz`, `pymupdf`, `docx`, `openpyxl`. Bỏ token `direct_pymupdf_in_spoke` và `direct_openai_in_spoke`. Chúng không bao giờ khớp `import`.

Thêm `implementation_packages`, chép từ `RAW_BYPASS_RESTRICTIONS` đang chạy:

| Module | Package được phép import |
| :--- | :--- |
| `docx` | `ccba_ooxml`, `ccba_legal`, `mdconverter` |
| `openpyxl` | `ccba_ooxml` |
| `fitz`, `pymupdf` | `ccba_pdf_prep` |

Không đưa `litellm` hay `openai` vào đợt card đầu. `ccba_ai/client.py` và `fallback.py` import `openai`. Cấm chúng trước khi có `implementation_packages: [ccba_ai]` sẽ làm đỏ CI ở PR-B.

Schema skill khác package: `kind: skill` có `command` và `skill_path`, không có `import_path`. PR-A cần ít nhất hai card skill cùng một từ khóa, nếu không test "disambiguation" không kiểm tra gì.

## Chặn PR-B

**5. Điều kiện bảo lưu 2 chưa khép.** Issue yêu cầu fail khi Seam đã xanh mà file quarantine vẫn được import, cộng half-open mỗi lần deploy. Kế hoạch chỉ có `until`, `reason` và đường dẫn. `health_check` lại bị cấm chạy trong `find-seam`. Hai yêu cầu này đang mâu thuẫn. PR-B làm hết hạn, lý do, đường dẫn, và package chủ. Half-open và "Seam đã xanh" ghi trong ADR-0061 là việc theo sau, chưa đánh dấu xong điều kiện 2.

**6. Marker mới làm gãy marker cũ.** `# ccba:allow-raw-bypass` đang nằm trên import thật, không nằm trong `adapters/quarantine/`:

- `scripts/ccba_platform_cli.py` (`docx`, `fitz`, `pymupdf`)
- `ccba_legal/formula_harvester.py`, `ccba_legal/provenance.py`
- `ccba_qc_core/pipeline.py`, `ccba_qc_core/discovery.py`
- `mdconverter` (`analyze_pdfs.py`, `core/gemini.py`)

`ccba_legal` và `mdconverter` được phép import `docx` theo bảng trên, nhưng không được phép import `fitz`. Nếu PR-B đổi marker mà không di trú các dòng này, CI Hub đỏ ngay. Cùng PR-B: package chủ đi qua `implementation_packages`. Mọi chỗ khác hoặc chuyển sang import Seam, hoặc chuyển vào `adapters/quarantine/<seam_id>.py` với marker còn hạn. Chạy dry-run và dán số vi phạm vào mô tả PR trước khi bật mặc định.

**7. Khe hở của chính marker.**

- Gắn marker vào span AST của câu `import` / `from`, như visitor hiện tại. Một comment ở đầu file, trong docstring, hoặc trong chuỗi không miễn trừ import.
- `seam_id` phải là id có trong chỉ mục. Dùng id đó làm tên file chỉ sau khi tra card. Từ chối `..` và dấu phân cách đường dẫn.
- Import trong file quarantine phải là tập con của `forbidden_substitute_imports` của đúng card đó. Một marker `legal_markdown.v1` không được mở cửa cho `fitz` của card PDF.
- `reason` chỉ nhận `hardware_mismatch`, `seam_regression`, `health_timeout`, `version_conflict`.
- `issue` chỉ nhận `https://github.com/vvChu/ccba-agent-platform/issues/<số>`.
- `until` so với ngày UTC của runner. Ghi múi giờ trong ADR để khỏi lệch một ngày với +07.
- Điều khoản 4.5 cho phép "có marker hoặc có import Seam". Nhánh OR là cửa sau: file import `fitz` rồi import thêm symbol Seam cho có. ADR-0061 bỏ nhánh OR. Chỉ package chủ hoặc quarantine còn hạn mới hợp lệ.

Âm tính đã biết, ghi vào ADR: client HTTP tự viết tới gateway không có tên trong `forbidden_substitute_imports` thì AST không thấy. Không săn bằng regex trên thân hàm.

**8. Chẩn đoán cleanliness trong kế hoạch lệch mã.** `EPHEMERAL_PREFIXES` gồm `fix_`, `audit_`, `patch_`, `debug_`, `tmp_`, không có `daemon`. Daemon bị tính vào ngân sách 15 file. Chúng không bị gắn nhãn ephemeral chỉ vì tên. Allowlist vai trò phải thắng tiền tố: `audit_memory.py` nằm trong `audits` thì không bị đề nghị archive. Phạm vi PR-B là `scripts/*.py` ở gốc Spoke. `scripts/cron/*.sh` và cây `services/` không nằm trong linter hiện tại. Đừng ghi nhận Điều khoản E.3 là xong cho các đường đó.

## Trình tự PR

Không có phụ thuộc vòng. A cung cấp YAML. B đọc YAML. C sửa hiến pháp sau khi CLI đã ở `main`.

Tách PR-B thành hai PR. Linter import và cleanliness là hai seam, hai bộ test, hai cách làm đỏ CI. Gộp chúng vượt quá một lần review có chủ đích.

PR-C còn thiếu file đang giữ trần "2 subagent" và công thức tích:

- `.agents/skills/ccba-code-review/SKILL.md` (tối đa 2 sub-agent)
- `.agents/skills/ccba-issue-tree/SKILL.md` và `references/tree_templates.md`
- `skills_compiled.md` chỉ đổi bằng cổng biên dịch lại, không sửa tay

Điều khoản 4.3 (spike 7 ngày, `.md/scratch/spikes/`) không thuộc bốn bảo lưu. Ghi trong ADR là review guideline, chưa phải CI.

`verify-patch --preset full` đúng cho PR cuối. PR-A và PR-B dùng preset hẹp hơn (`code` cộng đúng file test mới) để khỏi biến một PR hợp đồng thành một vòng full monorepo.

## Việc sửa trong kế hoạch trước khi mở PR-A

1. Đổi card markdown sang `mdconverter:ConversionPipeline`. Bỏ version và health command bịa. Thêm `implementation_packages` như bảng trên.
2. Viết ngữ nghĩa khớp, exit code, hash byte thô, và quy tắc `KEYWORD_HINT` không phải `MATCH`.
3. Ghi PR-B sẽ di trú `# ccba:allow-raw-bypass` và chưa bật half-open.
4. Tách cleanliness khỏi PR linter.
5. Trong ADR, giữ GPI, bỏ nhánh OR của 4.5, và ghi âm tính HTTP client.