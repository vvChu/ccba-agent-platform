Tôi sẽ đối chiếu kế hoạch Issue #446 với ADR-0060 Mục 6, seam contracts và code catalog hiện có trước khi phản biện các điểm mù.Kế hoạch Issue #446 đi đúng hướng của ADR-0060 Mục 6 (snapshot bất biến, probe nằm ngoài tiến trình chính, `binding.mode`, fail-closed khi mất snapshot). Sáu điểm dưới đây cần khóa vào kế hoạch trước khi viết code. Phần còn lại là lỗ hổng kiểm thử.

Biên lai trong kế hoạch khớp byte hiện tại của `seam-contracts.yaml`: `9a22f6d37e90b3069a30dfd0e35d4254e32e80db1647c01fcbc7125916afda64` (1 938 byte). Hash này đổi ngay khi thêm `binding`. `catalog.yaml` hiện 46 295 byte.

## 1. Con trỏ `current`: chọn một tệp văn bản, không làm alias thư mục

`os.replace` chỉ hoán đổi nguyên tử khi đích là file. Thư mục đích không rỗng thì Linux trả `ENOTEMPTY`, Windows trả `ERROR_ALREADY_EXISTS`. Alias thư mục tên `current` không có cửa sổ hoán đổi an toàn.

| Biểu diễn | POSIX | Windows | Kết luận |
|---|---|---|---|
| Symlink `current` → `<sha>/` | `rename(2)` thay đúng inode symlink, reader đang mở thư mục cũ giữ inode cũ | `os.symlink` cần SeCreateSymbolicLinkPrivilege hoặc Developer Mode (WinError 1314). `MoveFileEx` không thay directory symlink đang bị giữ handle | Đúng trên máy dev Linux, gãy trên Spoke Windows và trên `shutil.copytree` / OneDrive |
| Thư mục thật tên `current` | Không replace được khi bên trong còn file | Cùng thất bại, cộng lock thư mục | Loại |
| File thường `current` chứa đúng một token `<sha>` | `os.replace` file→file là nguyên tử | `MoveFileEx(MOVEFILE_REPLACE_EXISTING)` nguyên tử với file | Biểu diễn duy nhất nên ghi vào kế hoạch |

ADR đang ghi “văn bản/symlink”. Kế hoạch cần chốt một biểu diễn, nếu không Linux sẽ thành symlink và Windows thành file, reader phải đoán.

Giao thức ghi:

1. `snapshot_id = sha256(seam_bytes + b"\n" + catalog_bytes)`. Khóa thư mục chỉ bằng hash của `seam-contracts.yaml` sẽ ghi đè `catalog.yaml` khi skill đổi mà hợp đồng không đổi. Hai file này lệch nhau thường xuyên vì `catalog.yaml` được `yaml.safe_dump` lại từ frontmatter.
2. Ghi vào `snapshots/<snapshot_id>/` trên cùng filesystem với `current`. Temp nằm trong chính thư mục `snapshots/`. `os.replace` xuyên filesystem thành copy và mất tính nguyên tử (`EXDEV`).
3. Bộ ba `seam-contracts.yaml`, `catalog.yaml`, `.catalog_provenance.json` ghi bằng temp file rồi `os.replace` từng file. `fsync` từng file và `fsync` thư mục trước khi đổi con trỏ. Cấm gọi `CatalogMerger.atomic_write`: hàm đó `yaml.dump` dict và phá byte gốc. Chỉ mượn vòng retry `PermissionError`.
4. Thư mục `<snapshot_id>/` đã tồn tại và hash khớp thì bỏ qua ghi, chỉ đổi con trỏ. Hash lệch thì dừng publish. Snapshot content-addressed là bất biến.
5. Ghi token vào `snapshots/.current.<pid>.tmp` rồi `os.replace` lên `snapshots/current`. Retry `PermissionError` (WinError 32 và WinError 5). Thất bại thì giữ con trỏ cũ.
6. Đọc xong `current` thì đóng handle ngay. Trên POSIX, reader giữ inode cũ nên không cần lock. Trên Windows, handle đọc không kèm `FILE_SHARE_DELETE` làm `os.replace` thất bại. Câu “reader không cần lock” chỉ đúng sau khi handle đã đóng.
7. Token chỉ được là một thành phần `^[0-9a-f]{64}$`. `lstat` bắt buộc thấy regular file. Symlink, đường dẫn tuyệt đối, `..`, và thư mục nằm ngoài `snapshots/` đều là snapshot hỏng.
8. Giữ đúng hai id: id trong `current` và id ngay trước đó. Xóa id thứ ba chỉ sau khi đọc lại `current`. Reader gặp `FileNotFoundError` thì đọc lại con trỏ một lần.

`source_url` trong provenance để giá trị `hub-fs` hoặc URL control plane. Cấm ghi `CCBA_HUB_PATH` tuyệt đối vào JSON. `.agents/*` và `.agents/**/*.json` đã ignore cache, nhưng scanner đường dẫn máy vẫn quét file nếu bản sao lọt vào repo.

Định danh Hub vẫn an toàn với layout này: `HubDiscoverer._is_valid_hub` chỉ nhận `.agents/skills/platform-loader/catalog.yaml`. Snapshot phẳng trong `.agents/cache/...` không thoả đường đó. Test cần khóa điều kiện này.

`CCBA_HUB_PATH` treo là lỗ hổng cùng lớp với `getaddrinfo`. Tailscale hoặc NFS chết thì `Path.exists()` trong tiến trình cha kẹt ở kernel, `SIGKILL` của probe không chạm tới. Bước 1 của thứ tự phân giải phải nằm trong chính subprocess bị trần 1.5s. Subprocess chết thì rơi xuống `current` và `freshness: unverified`. `Path.exists()` trên env này không được chạy ở tiến trình CLI.

Env trỏ tới đường dẫn không phải Hub (thiếu `catalog.yaml` đúng chỗ) thì bỏ qua và dùng snapshot nếu có. Chỉ ném `CatalogSnapshotMissing` khi cả Hub hợp lệ lẫn `current` đều không có. `HUB_PATH` giữ thứ tự sau `CCBA_HUB_PATH`, cùng quy ước với `HubDiscoverer`.

Hub hợp lệ luôn thắng, kể cả khi snapshot mới hơn. Câu “bỏ qua snapshot cũ hơn” trong Test 6 đang đổi thứ tự ADR thành so mtime.

## 2. `Popen` + `SIGKILL`: zombie có, và `p.kill()` không giết cả cây

`p.kill()` không thu hoạch (reap) tiến trình. Trên Linux tiến trình thành zombie (`Z`) cho tới `waitpid`. `Popen.__del__` chỉ dọn khi GC chạy, nên CLI sống lâu sẽ tích zombie theo mỗi lần probe. Sau `kill` phải `wait()` hoặc `communicate()` lần hai để rút pipe và reap.

`start_new_session=True` cộng `p.kill()` vẫn chỉ giết process leader. `os.kill` không gửi theo nhóm. Cháu (shell, `curl`) giữ đầu ghi của pipe thì `communicate()` treo tiếp. Cách giết:

- Linux: `os.killpg(os.getpgid(p.pid), signal.SIGKILL)`, bắt `ProcessLookupError`, rồi `p.wait()`.
- Windows: không có `signal.SIGKILL` (`AttributeError`). `p.kill()` là `TerminateProcess`. Probe phải là Python trực tiếp trong process con, `shell=False`. `TerminateProcess` không giết cháu, nên cấm `shell=True` và cấm `cmd /c`.

Trần 1.5s tính cả thời gian khởi động interpreter. Process con chỉ được làm HTTP và in một dòng kết quả. Import `compile_catalog` trong process đó dễ nuốt hết ngân sách và mọi probe thành `unverified`.

`communicate(timeout=1.5)` khi hết giờ không tự giết process. Bắt `TimeoutExpired`, giết cả nhóm, rồi `communicate()` lần nữa.

Ghi mốc debounce trên cả thành công lẫn timeout, nếu không máy mất mạng trả 1.5s cho mỗi lần `find-seam` và mất SLA dưới 2ms. File trạng thái nằm ngoài thư mục `<sha>/` (ví dụ `.agents/cache/hub-catalog/probe-state.json`). Ghi giờ probe vào provenance sẽ đổi byte snapshot. Dùng Unix time bền qua lần chạy lại. `time.monotonic()` không so được sau khi process thoát. Đồng hồ nhảy lùi thì probe một lần.

Không có `CCBA_CATALOG_URL` thì không mở socket và không suy ra `:8090`. Kết quả là `unverified`.

HEAD không đủ để phân biệt `fresh` và `stale`. GitHub Raw trả ETag yếu, không phải SHA-256 của body. Process con phải GET body (46 KB là đủ trong 1.5s khi DNS đã thông) hoặc GET một sidecar `*.sha256` vài chục byte, rồi hash. Issue này chỉ phát hiện lệch hash. Tải và `publish_snapshot` là việc của issue sau. `stale` không được sửa snapshot trong `find-seam`.

`corrupt` thắng mọi trạng thái mạng. Timeout trên file lệch hash vẫn là exit 1.

Khi nguồn là filesystem Hub, `fresh` có nghĩa “khớp remote”, mà probe chưa chạy. Thêm `source: hub_fs | snapshot`. Hub vừa đọc xong, chưa probe, để `freshness: unverified`.

## 3. `binding` không chạm AST hiện tại. Hash không nằm trong `compile_catalog.py`

`validate_seam_exports` đọc `packages/*/AGENTS.md`. `validate_seam_contracts` kiểm tra `seam_id`, `kind`, `capability.in/out`, symbol package, đường dẫn skill. Khóa lạ bị bỏ qua. Thêm `binding` không làm `--check` đỏ, và cũng không làm catalog lệch, vì `compile_catalog_dict` không đọc `seam-contracts.yaml`. Không chạy `compile_catalog.py --write` cho thay đổi này.

Câu “cập nhật SHA-256 tương ứng trong `compile_catalog.py`” không có chỗ để sửa. `load_seam_contracts` hash `read_bytes()` lúc đọc. Không có hằng số. Biên lai `9a22f6d3…` hết hiệu lực ngay sau khi sửa YAML. Test hiện chỉ kiểm độ dài 64 và bằng byte trên đĩa, nên chúng không gãy vì hash mới.

Việc cần thêm vào `validate_seam_contracts`, nếu không `binding` chỉ là chú thích:

- `binding.mode` thuộc `{local_import, remote_mcp, skill}`.
- `kind: package` đi với `local_import` hoặc `remote_mcp`. `kind: skill` đi với `skill`.
- `remote_mcp` bắt buộc có khóa khai báo endpoint qua tên biến môi trường. Cấm IP, cấm cổng `:8090`, cấm `:8004` viết cứng trong code. Năm card hiện tại không có `remote_mcp`. Card đó chỉ xuất hiện trong fixture của Test 5.
- Snapshot cũ thiếu `binding` vẫn đọc được: package suy ra `local_import`, skill suy ra `skill`. `--check` trên Hub mới thì bắt buộc có field. Hai chính sách này viết tách nhau. “Tương thích ngược” nằm ở reader, không phải ở chỗ nới validator của file Hub.

Sửa `seam-contracts.yaml` bằng tay, LF, không BOM. Cấm round-trip `yaml.safe_dump`. Comment và thứ tự khóa nằm trong hash. Sau khi lưu file, hash lại bằng `sha256sum` trên byte đĩa.

`load_seam_contracts` hôm nay nuốt mọi exception và trả `{}, ""`. File gzip hoặc YAML gãy vì thế thành `NO_MATCH` với hash rỗng, không thành `corrupt`. Client mới so `sha256(read_bytes())` với `seam_contracts_sha256` và `catalog_sha256`. Lệch hash, thiếu file, hay parse gãy đều là `CorruptSnapshotError`, JSON `status: corrupt`, exit 1. So hash sau `yaml.dump` sẽ biến Test 4 thành `MATCH` vì YAML vẫn cùng nghĩa.

`CCBA_CATALOG_URL` là mặt phẳng catalog. Health của `remote_mcp` là mặt phẳng khác (`:8004` / `:8008` trên Spark). Timeout GitHub Raw không được chặn MCP đang sống, và HEAD catalog thành công không được coi là MCP khỏe. `freshness` chỉ mô tả snapshot. `invoke` chỉ xét health của đúng seam, cũng trong subprocess có trần giết.

Quarantine không tự bật. Marker hợp lệ cần `until` và URL issue GitHub. CLI không tạo `adapters/quarantine/`, không mở issue, không chèn import thay thế. Receipt chỉ đưa `reason: health_timeout` để agent lập marker sau.

Exit code đang thiếu một trạng thái. ADR-0061: `0` là `MATCH` (được dùng làm biên lai), `2` là `NO_MATCH` (agent sẽ đi viết công cụ mới), `1` là lỗi cú pháp. Seam `remote_mcp` chết mà trả `MATCH` thì agent gọi dịch vụ chết. Trả `NO_MATCH` thì agent viết script thay thế, đúng việc ADR-0061 cấm. Khóa trong kế hoạch:

- Card `local_import` và `skill` vẫn `MATCH`, exit 0, khi mạng chết.
- Chỉ khi mọi card khớp đều `remote_mcp` và health chết: `status: BLOCKED`, exit 3, kèm `{"invoke":"blocked","reason":"health_timeout","seam_id":"..."}`.
- `corrupt` giữ exit 1 và không bao giờ là `MATCH`.

Exit 3 chưa có trong ADR. Ghi vào kế hoạch trước khi code để CLI và test không mỗi nơi một mã.

`find-seam` hôm nay truyền `hub_root=_ROOT_DIR` (`Path(__file__).parents[1]`), không phải CWD và không phải `CCBA_HUB_PATH`. Chạy test trong repo Hub thì file hợp đồng luôn có, client không bao giờ được gọi. `check_dependency_contracts.load_seam_bypass_restrictions` còn hẹp hơn: chỉ mở `<project_root>/seam-contracts.yaml`. Thiếu file, YAML hỏng, hoặc không có `forbidden_substitute_imports` thì `except: pass` và rơi vào `RAW_BYPASS_RESTRICTIONS` với `seam_id` dạng `<mod>_legacy`. Sửa CLI mà không sửa hàm này thì Test 2 xanh trong unit test và Spoke vẫn đi raw bypass.

Cả `find-seam` và `load_seam_bypass_restrictions` phải dùng chung một hàm phân giải. Snapshot hỏng thì linter dừng, không fallback.

## 4. Sáu test chưa khóa các biên mà CI sẽ bỏ qua

`pyproject.toml` có `addopts = -m 'not stress and not slow'`. Đánh dấu `stress` hoặc `slow` thì `verify-patch` bỏ qua đúng bài cần chặn merge. Dùng marker `adversarial` (đã đăng ký) hoặc không marker. `testpaths` đã gồm `tests/`, nên `tests/spoke/` được thu thập.

Mỗi bài cần thêm các ca sau.

**Test 1.** Assert tường `elapsed < 2.5s` (pytest `timeout = 30` chỉ bắt treo thô). Sau khi giết, `p.poll()` khác `None`, không còn process `Z`, và cháu `sleep` cũng chết. Lần gọi thứ hai trong 15 phút không `Popen`. Timeout vẫn ghi probe-state. Listener ở `:8090` không nhận connection khi URL trống. Process con khỏe trên localhost phải còn trả `fresh` trong 1.5s, nếu không trần này chỉ được chứng minh bằng ca treo. Snapshot lệch hash trong lúc DNS treo vẫn exit 1.

**Test 2.** Chạy trong `tmp_path`, xóa `CCBA_HUB_PATH` và `HUB_PATH`. Gọi cả client lẫn `load_seam_bypass_restrictions`. Kết quả cấm chứa `seam_id` kết thúc bằng `_legacy`. Thêm env rỗng, env trỏ file, env trỏ cây chỉ có cache, `current` rỗng, token `..`, symlink ra ngoài cache. `CatalogSnapshotMissing` chỉ khi không có Hub và không có con trỏ hợp lệ.

**Test 3.** Năm process ghi năm payload khác nhau, reader đọc trong lúc ghi. Mỗi lần mở qua `current` phải có hash file bằng provenance cùng thư mục. Parse được YAML là chưa đủ. Mock `os.replace` ném `PermissionError` hai lần rồi thành công, để Linux CI phủ vòng WinError 32. Giết publisher sau khi ghi thư mục và trước khi đổi con trỏ: `current` cũ còn nguyên. Temp file cùng thư mục với `current`.

**Test 4.** Ba đột biến tách bạch: đổi một byte, `yaml.safe_dump` round-trip (cùng nghĩa, khác byte), gzip. Cả ba ra `corrupt`, exit 1. Thêm ca chỉ hỏng `catalog.yaml` trong khi seam vẫn khớp. Ca provenance bị sửa cho khớp file hỏng nằm ngoài mối đe doạ: kiểm tra này bắt hỏng tay và ghi dở, không phải chữ ký chống kẻ sửa cả thư mục cache.

**Test 5.** Fixture `remote_mcp`, không đưa card đó vào `seam-contracts.yaml` của Hub. Cùng lúc assert `legal_markdown.v1` vẫn `MATCH` và exit 0. JSON là object `invoke` / `reason` / `seam_id`, không phải một câu ghép. Catalog timeout không được tự nó làm `BLOCKED`. CLI không tạo file dưới `adapters/quarantine/`.

**Test 6.** Hub hợp lệ thắng snapshot mới hơn. Hash receipt lấy từ byte Hub, không từ provenance của cache. Env Hub không hợp lệ thì dùng snapshot và không ném lỗi. Chọn Hub không được ghi `hub_path` tuyệt đối vào `workspace_context.yaml`.

## Việc cần sửa trong kế hoạch

1. Chốt file con trỏ, `snapshot_id` ghép hai body, thư mục bất biến, temp cùng ổ, token 64 hex, retry WinError 32 sau khi reader đã đóng handle.
2. Mọi `stat`/`open` của `CCBA_HUB_PATH` nằm trong subprocess trần 1.5s. Hub hợp lệ luôn thắng snapshot.
3. Probe: `shell=False`, giết theo process group, `wait` sau kill, debounce ghi cả khi timeout, không URL thì không socket, GET hoặc sidecar để có SHA-256. `probe-state.json` nằm ngoài `<sha>/`.
4. `status: corrupt` exit 1. `status: BLOCKED` exit 3 khi mọi card khớp đều là `remote_mcp` chết. Card local vẫn `MATCH`.
5. Một hàm phân giải dùng chung cho `find-seam` và `load_seam_bypass_restrictions`. Cấm fallback `RAW_BYPASS_RESTRICTIONS` khi snapshot thiếu hoặc hỏng.
6. Validator enum `binding.mode` cộng ràng buộc `kind`. Hash lấy từ `read_bytes()` sau khi sửa tay. Không `--write` catalog vì field này.

Sau khi sáu mục đó nằm trong plan, bộ test mới có chỗ để thất bại đúng việc cần chặn.
