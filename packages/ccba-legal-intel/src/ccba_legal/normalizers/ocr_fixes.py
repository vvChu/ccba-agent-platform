"""OCR text fix utilities for Vietnamese legal documents.

Fixes character spacing, common OCR typos, stuck Vietnamese words,
and syllable boundary detection for scanned PDFs.
"""

import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# OCR Spacing Normalization (for scanned PDFs with char-separated text)
# ---------------------------------------------------------------------------

# Vietnamese characters that may appear space-separated in broken OCR
_VN_CHARS = r"[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴa-zđàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]"

# Pattern: single Vietnamese char + 1-3 spaces + single Vietnamese char (repeated)
_SPACED_CHAR_RE = re.compile(rf"({_VN_CHARS})\s{{1,3}}(?={_VN_CHARS}(?:\s{{1,3}}{_VN_CHARS}))")


def normalize_ocr_spacing(text: str) -> str:
    """Fix character-separated Vietnamese text from scanned PDFs.

    Detects lines where Vietnamese characters are separated by excessive spaces
    (e.g. 'B Ộ  XÂY D Ự NG' → 'BỘ XÂY DỰNG') and collapses them.

    Also strips OCR noise characters (box-drawing, geometric shapes, etc.)
    that are never valid in Vietnamese legal text.

    Only applies to lines where >30% of tokens are single characters,
    to avoid collapsing normal spaced text.
    """
    if not text:
        return text

    # Strip OCR noise characters — box drawing, geometric shapes, scan artifacts
    # These are never valid in Vietnamese legal/technical text
    text = re.sub(r"[▯◻⬜█▶◀▲▼♦♣♠♥←→↑↓│┤┐└┘┌├─┼┴┬┌╔╗╚╝║═╬╣╠╩╦▒░▓■□●○◇◆★☆✓✗✘☐☑☒]", "", text)
    # Strip isolated underscores/tildes that are scan noise (not in URLs or code)
    text = re.sub(r"(?<!\w)[_~]{3,}(?!\w)", "", text)
    # Collapse resulting multi-spaces
    text = re.sub(r"  +", " ", text)

    lines = text.split("\n")
    fixed_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            fixed_lines.append(line)
            continue

        # Count short tokens (1-2 chars) that are Vietnamese letters
        tokens = stripped.split()
        if len(tokens) < 3:
            fixed_lines.append(line)
            continue

        short_vn_tokens = sum(1 for t in tokens if len(t) <= 3 and re.match(rf"^{_VN_CHARS}+$", t))
        ratio = short_vn_tokens / len(tokens)

        if ratio > 0.20:
            result = []
            i = 0
            while i < len(tokens):
                if len(tokens[i]) <= 2 and re.match(rf"^{_VN_CHARS}+$", tokens[i]):
                    run = [tokens[i]]
                    j = i + 1
                    while (
                        j < len(tokens)
                        and len(tokens[j]) <= 3
                        and re.match(rf"^{_VN_CHARS}+$", tokens[j])
                    ):
                        run.append(tokens[j])
                        j += 1
                    result.append("".join(run))
                    i = j
                else:
                    result.append(tokens[i])
                    i += 1

            fixed_line = " ".join(result)
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


# ---------------------------------------------------------------------------
# OCR Typo Correction
# ---------------------------------------------------------------------------

_OCR_TYPO_MAP = [
    ("NGHÈ", "NGHỀ"),
    ("Nghè", "Nghề"),
    ("nghè", "nghề"),
    ("Tỳ lệ", "Tỷ lệ"),
    ("tỳ lệ", "tỷ lệ"),
    ("hổ sơ", "hồ sơ"),
    ("Hổ sơ", "Hồ sơ"),
    ("bố sung", "bổ sung"),
    ("Bố sung", "Bổ sung"),
    ("tính,", "tỉnh,"),
    ("tính.", "tỉnh."),
    ("họp đồng", "hợp đồng"),
    ("Họp đồng", "Hợp đồng"),
    ("trưởng họp", "trường hợp"),
    ("Trưởng họp", "Trường hợp"),
    ("trực thuộc trung ượng", "trực thuộc trung ương"),
]


def fix_common_ocr_typos(text: str) -> str:
    """Fix frequent Vietnamese OCR misrecognitions."""
    if not text:
        return text
    for wrong, correct in _OCR_TYPO_MAP:
        if wrong in text:
            text = text.replace(wrong, correct)
    return text


# ---------------------------------------------------------------------------
# Stuck Vietnamese Word Fix (OCR word-joining)
# ---------------------------------------------------------------------------

# NOTE: This list is intentionally large — it is a domain-specific dictionary
# built from corpus analysis of QCVN/TCVN/BGTVT legal documents.
# Each entry is a known OCR merge pattern discovered through audit.
# Longer patterns MUST come before shorter ones to avoid partial matching.
_STUCK_WORD_FIXES = [
    ("hồsơ", "hồ sơ"),
    ("Hồsơ", "Hồ sơ"),
    ("vàcó", "và có"),
    ("vàxử", "và xử"),
    ("vàcác", "và các"),
    ("vàvị", "và vị"),
    ("vàrà", "và rà"),
    ("sựcố", "sự cố"),
    ("cơsở", "cơ sở"),
    ("Cơsở", "Cơ sở"),
    ("chiếutới", "chiếu tới"),
    ("đođộ", "đo độ"),
    ("Ápkế", "Áp kế"),
    ("épôm", "ép ôm"),
    ("éprô", "ép rô"),
    ("Xảáp", "Xả áp"),
    ("thểhiện", "thể hiện"),
    ("quảlý", "quả lý"),
    ("nhàở", "nhà ở"),
    ("trờicó", "trời có"),
    ("cóthểcó", "có thể có"),
    ("cóthểđạt", "có thể đạt"),
    ("cóthểđược", "có thể được"),
    ("cóthểsử", "có thể sử"),
    ("cóthểđo", "có thể đo"),
    ("cóthể", "có thể"),
    ("làmột", "là một"),
    ("Làmột", "Là một"),
    ("đốivới", "đối với"),
    ("Đốivới", "Đối với"),
    ("nhưsau", "như sau"),
    ("vàvà", "và và"),
    ("làgiá", "là giá"),
    ("cóphải", "có phải"),
    ("phảiđược", "phải được"),
    ("cóthêm", "có thêm"),
    ("vàcóthể", "và có thể"),
    ("hoặclà", "hoặc là"),
    ("khôngđược", "không được"),
    ("màcác", "mà các"),
    ("trênmột", "trên một"),
    ("theocác", "theo các"),
    ("dướiđây", "dưới đây"),
    ("sauđây", "sau đây"),
    ("trongmột", "trong một"),
    ("mộtsố", "một số"),
    ("đãcóhạ", "đã có hạ"),
    ("đãcóphương", "đã có phương"),
    ("đãcó", "đã có"),
    ("mởra", "mở ra"),
    ("kểtừ", "kể từ"),
    ("sốvà", "số và"),
    ("dựán", "dự án"),
    ("Dựán", "Dự án"),
    ("sởdữ", "sở dữ"),
    ("lývàrà", "lý và rà"),
    ("lývà", "lý và"),
    ("ánđã", "án đã"),
    ("đánh sốvà", "đánh số và"),
    ("quản lývàrà", "quản lý và rà"),
    ("quản lývà", "quản lý và"),
    ("Xửlý", "Xử lý"),
    ("xửlý", "xử lý"),
    ("đầu tưdự", "đầu tư dự"),
    ("phương ánđã", "phương án đã"),
    ("thiết kếđã", "thiết kế đã"),
    # QCVN 122-125 corpus
    ("vàbảovệmôi", "và bảo vệ môi"),
    ("cógắnđộng", "có gắn động"),
    ("vềxeô", "về xe ô"),
    ("vềxe", "về xe"),
    ("vềyêu", "về yêu"),
    ("vềkỹ", "về kỹ"),
    ("vềkiểm", "về kiểm"),
    ("vềthiết", "về thiết"),
    ("vềan", "về an"),
    ("vềđèn", "về đèn"),
    ("vềkhung", "về khung"),
    ("vàbảo", "và bảo"),
    ("vàsự", "và sự"),
    ("vàmôi", "và môi"),
    ("vàphụ", "và phụ"),
    ("từngữ", "từ ngữ"),
    ("cơgiới", "cơ giới"),
    ("sốcho", "số cho"),
    ("cókhả", "có khả"),
    ("códấu", "có dấu"),
    ("cógiá", "có giá"),
    ("cómàu", "có màu"),
    ("cógắn", "có gắn"),
    ("dovà", "do và"),
    ("dokhi", "do khi"),
    ("bằngcách", "bằng cách"),
    ("đểcố", "để cố"),
    ("đểkiểm", "để kiểm"),
    ("đểđảm", "để đảm"),
    ("Sựlàm", "Sự làm"),
    ("Códấu", "Có dấu"),
    ("Cógắn", "Có gắn"),
    ("theoquy", "theo quy"),
    ("theotiêu", "theo tiêu"),
    ("tạiphụ", "tại phụ"),
    ("tạibảng", "tại bảng"),
    ("khiđo", "khi đo"),
    ("khicó", "khi có"),
    ("đểkiểm", "để kiểm"),
    ("đểcó", "để có"),
    ("đểnâng", "để nâng"),
    ("đểtạo", "để tạo"),
    ("đểmở", "để mở"),
    ("cócác", "có các"),
    ("cónhiều", "có nhiều"),
    ("cótác", "có tác"),
    ("cókhả", "có khả"),
    ("cónăng", "có năng"),
    ("cótính", "có tính"),
    ("códiện", "có điện"),
    ("vệmôi", "vệ môi"),
    ("vớicác", "với các"),
    ("vớimức", "với mức"),
    ("vớitài", "với tài"),
    ("vớicông", "với công"),
    ("sốcủa", "số của"),
    ("sốnày", "số này"),
    ("sốtối", "số tối"),
    ("sốcho", "số cho"),
    ("bằngcách", "bằng cách"),
    ("nhỏnhất", "nhỏ nhất"),
    ("lớnnhất", "lớn nhất"),
    ("ănkhớp", "ăn khớp"),
    ("phảicó", "phải có"),
    ("phảinằm", "phải nằm"),
    ("khôngnhỏ", "không nhỏ"),
    ("khônglớn", "không lớn"),
    ("khôngcó", "không có"),
    ("khôngmở", "không mở"),
    ("khôngquá", "không quá"),
    ("tốiđa", "tối đa"),
    ("Tốiđa", "Tối đa"),
    ("mỗitrục", "mỗi trục"),
    ("đốivớixe", "đối với xe"),
    ("đốivới", "đối với"),
    ("xecó", "xe có"),
    ("xekhác", "xe khác"),
    ("xephải", "xe phải"),
    ("xeđang", "xe đang"),
    ("xekhi", "xe khi"),
    ("xetrong", "xe trong"),
    ("xemáy", "xe máy"),
    ("xecơ", "xe cơ"),
    ("docọ", "do cọ"),
    ("donhà", "do nhà"),
    ("conlăn", "con lăn"),
    ("kếcủa", "kế của"),
    ("kếnêu", "kế nêu"),
    ("mểtan", "mể tan"),
    ("quaycó", "quay có"),
    ("nhakhi", "nha khi"),
    ("khicần", "khi cần"),
    ("khikéo", "khi kéo"),
    ("khimở", "khi mở"),
    ("khitải", "khi tải"),
    ("mứcảnh", "mức ảnh"),
    ("mứccho", "mức cho"),
    # QCVN 21 maritime
    ("vàổn", "và ổn"),
    ("vàtàu", "và tàu"),
    ("vàmạn", "và mạn"),
    ("vàmột", "và một"),
    ("vàkét", "và két"),
    ("vàcửa", "và cửa"),
    ("vàmặt", "và mặt"),
    ("vàkín", "và kín"),
    ("vànắp", "và nắp"),
    ("vàtính", "và tính"),
    ("vàkết", "và kết"),
    ("vàtất", "và tất"),
    ("vàtư", "và tư"),
    ("vàcó", "và có"),
    ("củacác", "của các"),
    ("củatàu", "của tàu"),
    ("củatất", "của tất"),
    ("củađường", "của đường"),
    ("từmặt", "từ mặt"),
    ("từcác", "từ các"),
    ("từmạn", "từ mạn"),
    ("từmép", "từ mép"),
    ("từđường", "từ đường"),
    ("cáctàu", "các tàu"),
    ("cáckết", "các kết"),
    ("cáckét", "các két"),
    ("đếncác", "đến các"),
    ("đếnmặt", "đến mặt"),
    ("vớitàu", "với tàu"),
    ("chotàu", "cho tàu"),
    ("viáp", "vi áp"),
    ("tàucó", "tàu có"),
    ("tàuphải", "tàu phải"),
    ("tàukhi", "tàu khi"),
    ("tàutrong", "tàu trong"),
    ("tàuở", "tàu ở"),
    ("tàuvà", "tàu và"),
    ("mạnkhô", "mạn khô"),
    ("mạncó", "mạn có"),
    ("bềmặt", "bề mặt"),
    ("vịtrí", "vị trí"),
    # BGTVT Thông tư corpus
    ("camáynày", "ca máy này"),
    ("camáycủa", "ca máy của"),
    ("camáy", "ca máy"),
    ("sốnội", "số nội"),
    ("kýkết", "ký kết"),
    ("nhucầu", "nhu cầu"),
    ("quảlý", "quả lý"),
    ("đầutư", "đầu tư"),
    ("Đầutư", "Đầu tư"),
    ("cơcấu", "cơ cấu"),
    ("Cơcấu", "Cơ cấu"),
    ("kỹthuật", "kỹ thuật"),
    ("kinh tếkỹ", "kinh tế kỹ"),
    ("nhiệm vụcủa", "nhiệm vụ của"),
    ("hiệu lựcthi", "hiệu lực thi"),
    ("Thông tưnày", "Thông tư này"),
    ("phương ánđã", "phương án đã"),
    ("thiết kếđã", "thiết kế đã"),
    ("đảmbảo", "đảm bảo"),
    ("giámSát", "giám sát"),
    ("banAn", "ban An"),
    # Geographic place names
    ("baCửa", "ba Cửa"),
    ("baLác", "ba Lác"),
    ("baLầu", "ba Lầu"),
    ("baMom", "ba Mom"),
    ("baVàm", "ba Vàm"),
    ("baNúi", "ba Núi"),
    ("baNậm", "ba Nậm"),
    ("baMũi", "ba Mũi"),
    ("baGia", "ba Gia"),
    ("baĐụn", "ba Đụn"),
    ("baBến", "ba Bến"),
    ("laoÔng", "lao Ông"),
    ("hònMột", "hòn Một"),
    ("hònĐứa", "hòn Đứa"),
    ("đếnĐập", "đến Đập"),
    ("đếnCẩm", "đến Cẩm"),
    ("đậpDầu", "đập Dầu"),
    # TT-08/29 patterns
    ("vàcấp", "và cấp"),
    ("vàcập", "và cập"),
    ("vàcá", "và cá"),
    ("vàchịu", "và chịu"),
    ("vàcông", "và công"),
    ("vàkhông", "và không"),
    ("vàtổ", "và tổ"),
    ("vàtrang", "và trang"),
    ("vàmã", "và mã"),
    ("vàcác", "và các"),
    ("vàcòn", "và còn"),
    ("củamỗi", "của mỗi"),
    ("củamoay", "của moay"),
    ("củanhà", "của nhà"),
    ("củaPhụ", "của Phụ"),
    ("củapháp", "của pháp"),
    ("đểcấp", "để cấp"),
    ("đểcòn", "để còn"),
    ("đểcác", "để các"),
    ("đểnhận", "để nhận"),
    ("đểnhà", "để nhà"),
    ("đểnâng", "để nâng"),
    ("sốkỹ", "số kỹ"),
    ("sốcó", "số có"),
    ("sốmàu", "số màu"),
    ("sốnền", "số nền"),
    ("sốnhỏ", "số nhỏ"),
    ("sốkhung", "số khung"),
    ("sốcách", "số cách"),
    ("ởchế", "ở chế"),
    ("ởcác", "ở các"),
    ("ởmức", "ở mức"),
    ("ởmột", "ở một"),
    ("vớimặt", "với mặt"),
    ("vớinhà", "với nhà"),
    ("vớikhối", "với khối"),
    ("trongcác", "trong các"),
    ("trongkhu", "trong khu"),
    ("trongkhoảng", "trong khoảng"),
    ("trongtrường", "trong trường"),
    ("chocác", "cho các"),
    ("chokhách", "cho khách"),
    ("chomỗi", "cho mỗi"),
    ("chongười", "cho người"),
    ("tạicác", "tại các"),
    ("tạimỗi", "tại mỗi"),
    ("tạicảng", "tại cảng"),
    ("từcác", "từ các"),
    ("tàubaycó", "tàu bay có"),
    ("tàubaymà", "tàu bay mà"),
    ("tàubayphải", "tàu bay phải"),
    ("tàubaytại", "tàu bay tại"),
    ("đỗtàu", "đỗ tàu"),
    ("đỗtàubay", "đỗ tàu bay"),
    ("cấpcứu", "cấp cứu"),
    ("kýcủa", "ký của"),
    ("antoàn", "an toàn"),
    ("ôtôc", "ô tô c"),
    ("xeôtô", "xe ô tô"),
    ("xeô tô", "xe ô tô"),
    ("sơnkẻ", "sơn kẻ"),
    ("vankẻ", "van kẻ"),
    ("càngnhỏ", "càng nhỏ"),
    ("cảngnhỏ", "cảng nhỏ"),
    ("kẻtín", "kẻ tín"),
    ("mấtan", "mất an"),
    ("cơnkẹt", "cơn kẹt"),
    ("phankhông", "phan không"),
    ("mátàu", "má tàu"),
    ("nàycó", "này có"),
    ("hànhcủa", "hành của"),
    ("cầncó", "cần có"),
    ("cầntắt", "cần tắt"),
    # --- BIM template patterns (from 2026-03 audit) ---
    ("đáp ứngcácmục", "đáp ứng các mục"),
    ("đáp ứngcác", "đáp ứng các"),
    ("Yêucầu", "Yêu cầu"),
    ("yêucầu", "yêu cầu"),
    ("đểc hỉ", "để chỉ"),
    ("Đểcó", "Để có"),
    ("đểcó", "để có"),
    ("sơđồ", "sơ đồ"),
    ("Sơđồ", "Sơ đồ"),
    ("sơbộ", "sơ bộ"),
    ("Sơbộ", "Sơ bộ"),
    ("mãmàu", "mã màu"),
    ("Kýtự", "Ký tự"),
    ("Tấtcả", "Tất cả"),
    ("tấtcả", "tất cả"),
    ("Cácmốc", "Các mốc"),
    ("cácmốc", "các mốc"),
    ("cácmức", "các mức"),
    ("cáccấu", "các cấu"),
    ("cácbộ", "các bộ"),
    ("cáctài", "các tài"),
    ("đơnvị", "đơn vị"),
    ("Đơnvị", "Đơn vị"),
    ("đặtra", "đặt ra"),
    ("đặttên", "đặt tên"),
    ("chomột", "cho một"),
    ("cómột", "có một"),
    ("vàmô", "và mô"),
    ("BIMcủa", "BIM của"),
    ("BIMdự", "BIM dự"),
    ("BIMcho", "BIM cho"),
    ("nhiệmvụ", "nhiệm vụ"),
    ("lànơi", "là nơi"),
    ("phốihợp", "phối hợp"),
    ("quymô", "quy mô"),
    ("Quytắc", "Quy tắc"),
    ("lưutrữ", "lưu trữ"),
    ("bộmôn", "bộ môn"),
    ("Bộmôn", "Bộ môn"),
    ("Mứcđộ", "Mức độ"),
    ("mứcđộ", "mức độ"),
    ("cụthể", "cụ thể"),
    ("ởmỗi", "ở mỗi"),
    ("sẽtùy", "sẽ tùy"),
    ("sẽđược", "sẽ được"),
    ("bởicác", "bởi các"),
    ("yêu cầucủa", "yêu cầu của"),
    ("Làkế", "Là kế"),
    ("tấtcảcác", "tất cả các"),
    ("loạibỏ", "loại bỏ"),
    ("vụứng", "vụ ứng"),
    ("đồtổ", "đồ tổ"),
    ("độmốc", "độ mốc"),
    ("sốcấu", "số cấu"),
    ("vịcó", "vị có"),
    ("Môtả", "Mô tả"),
    ("bảnvẽ", "bản vẽ"),
    ("chia sẻmô", "chia sẻ mô"),
    ("chia sẻcác", "chia sẻ các"),
    ("lậpkế", "lập kế"),
    ("bêncập", "bên cập"),
    ("quycách", "quy cách"),
    ("thôngtin", "thông tin"),
    ("dữliệu", "dữ liệu"),
    ("quảnlý", "quản lý"),
    ("hệthống", "hệ thống"),
    ("côngtrình", "công trình"),
    ("xâydựng", "xây dựng"),
    ("thiếtkế", "thiết kế"),
    ("thicông", "thi công"),
    ("báocáo", "báo cáo"),
    ("phạmvi", "phạm vi"),
    ("tiêuchuẩn", "tiêu chuẩn"),
    ("chấtlượng", "chất lượng"),
    ("thựchiện", "thực hiện"),
    ("kếhoạch", "kế hoạch"),
    ("côngviệc", "công việc"),
    ("nộidung", "nội dung"),
    ("mụctiêu", "mục tiêu"),
    ("quytrình", "quy trình"),
    ("giảipháp", "giải pháp"),
    # --- Luật Đất Đai QH15 patterns (from 2026-03 audit) ---
    ("lýcó", "lý có"),
    ("bốcác", "bố các"),
    ("cơtác", "cơ tác"),
    ("bịô", "bị ô"),
    ("làcá", "là cá"),
    ("màcó", "mà có"),
    ("đấtcòn", "đất còn"),
    ("đócho", "đó cho"),
    ("tưcó", "tư có"),
    ("từmục", "từ mục"),
    ("lývà", "lý và"),
    ("đaicủa", "đai của"),
    ("hữutài", "hữu tài"),
    ("đaiquy", "đai quy"),
    ("mànay", "mà nay"),
    ("tốcáo", "tố cáo"),
    ("làchủ", "là chủ"),
    ("cóquyền", "có quyền"),
    ("lýnhà", "lý nhà"),
    ("đấtkhông", "đất không"),
    ("đấtphải", "đất phải"),
    ("đấtcủa", "đất của"),
    ("đấttại", "đất tại"),
    ("đấttheo", "đất theo"),
    ("đấtcho", "đất cho"),
    ("đấtdo", "đất do"),
    ("đấtcó", "đất có"),
    ("đấtmà", "đất mà"),
    ("quyềnvà", "quyền và"),
    ("quyềnsử", "quyền sử"),
    ("dụngđất", "dụng đất"),
    ("dụngvào", "dụng vào"),
    ("luậtnày", "luật này"),
    ("Luậtnày", "Luật này"),
    ("nghĩavụ", "nghĩa vụ"),
    ("tráchnhiệm", "trách nhiệm"),
    ("thẩmquyền", "thẩm quyền"),
    ("hiệnquyền", "hiện quyền"),
    ("hànhchính", "hành chính"),
    ("chínhcấp", "chính cấp"),
    ("nướccó", "nước có"),
    ("nướcthực", "nước thực"),
    ("lậptheo", "lập theo"),
    ("bồithường", "bồi thường"),
    ("đượccơ", "được cơ"),
    ("đượcNhà", "được Nhà"),
    ("đượcgiao", "được giao"),
    ("đượccho", "được cho"),
    ("đượccấp", "được cấp"),
    ("đượcthực", "được thực"),
    ("cóhiệu", "có hiệu"),
    ("cóthẩm", "có thẩm"),
    ("cầnthiết", "cần thiết"),
    ("thuêđất", "thuê đất"),
    ("nhậnchuyển", "nhận chuyển"),
    ("ánbất", "án bất"),
    ("ánhoặc", "án hoặc"),
    ("sảnnhưng", "sản nhưng"),
    # Stuck words from uppercase section headings
    ("SỐĐIỀU", "SỐ ĐIỀU"),
    ("ĐIỀUCỦA", "ĐIỀU CỦA"),
    ("CỦACÁC", "CỦA CÁC"),
    ("VỤCỦA", "VỤ CỦA"),
    ("vụcủa", "vụ của"),
    ("VỤCỦATỔ", "VỤ CỦA TỔ"),
    ("vụcủatổ", "vụ của tổ"),
    # Stuck words from Điều 243 (amendment references)
    ("báoxu", "báo xu"),
    ("vàmục", "và mục"),
    ("kỳkế", "kỳ kế"),
    ("hộicủa", "hội của"),
    ("vàkế", "và kế"),
    ("thứtự", "thứ tự"),
    ("IIvề", "II về"),
    ("dịchvụ", "dịch vụ"),
    ("sởytế", "sở y tế"),
    ("hóaxã", "hóa xã"),
    ("mànay", "mà nay"),
    ("dựánmà", "dự án mà"),
    ("dựánhoặc", "dự án hoặc"),
    ("sảngắn", "sản gắn"),
    ("hữutài", "hữu tài"),
    ("đaicủa", "đai của"),
    ("đaitheo", "đai theo"),
    ("tốcáo", "tố cáo"),
    ("cấpxã", "cấp xã"),
]


def fix_stuck_vietnamese_words(text: str) -> str:
    """Fix common Vietnamese words stuck together by OCR (no space between)."""
    if not text:
        return text
    for wrong, correct in _STUCK_WORD_FIXES:
        if wrong in text:
            text = text.replace(wrong, correct)
    return text


# ---------------------------------------------------------------------------
# Generic Stuck Word Detection (regex-based)
# ---------------------------------------------------------------------------

_VN_DIACRITIC_LOWER = r"[àáảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]"
_VN_UPPER_START = r"[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ]"

_STUCK_GENERIC_RE = re.compile(rf"({_VN_DIACRITIC_LOWER})({_VN_UPPER_START})")


def fix_generic_stuck_words(text: str) -> str:
    """Insert space between Vietnamese words stuck together by OCR (diacritic+uppercase)."""
    if not text:
        return text
    return _STUCK_GENERIC_RE.sub(r"\1 \2", text)


# ---------------------------------------------------------------------------
# Vietnamese Syllable Boundary Detection
# ---------------------------------------------------------------------------

_VN_DIAC_VOWELS = r"[àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]"
_VN_VOWELS_ALL = r"[aăâeêioôơuưyàáảãạắằẳẵặấầẩẫậèéẻẽẹếềểễệìíỉĩịòóỏõọốồổỗộớờởỡợùúủũụứừửữựỳýỷỹỵ]"

_VN_MULTI_NF = r"(?:gh|gi|kh|ph|th|tr|qu)"
_VN_SINGLE_NF = r"[bdđghlqrsvxy]"
_VN_NEVER_FINAL = rf"(?:{_VN_MULTI_NF}|{_VN_SINGLE_NF})"
_VN_FINAL_CONS = r"(?:ng|nh|ch|[ckmntpk])"

_VN_SYLB_P1 = re.compile(rf"({_VN_DIAC_VOWELS})({_VN_NEVER_FINAL})(?={_VN_VOWELS_ALL})")
_VN_SYLB_P2 = re.compile(
    rf"({_VN_DIAC_VOWELS}{_VN_FINAL_CONS})({_VN_NEVER_FINAL})(?={_VN_VOWELS_ALL})"
)
_VN_SYLB_P3 = re.compile(rf"([aeio]|u(?!y)|(?<!u)y)({_VN_NEVER_FINAL})(?={_VN_DIAC_VOWELS})")
_VN_SYLB_P4 = re.compile(
    rf"([aeio]|u(?!y)|(?<!u)y)({_VN_FINAL_CONS})({_VN_NEVER_FINAL})(?={_VN_VOWELS_ALL})"
)

_UY_REJOIN_RE = re.compile(
    r"\b(thu|ngu|chu|tu|khu|hu|xu|bu|lu|phu|tru|du|su|vu|mu|cu|nu|ru)"
    r"\s+(yền|yên|yến|yện|yệt|yết|yể|yễ|yệ|yếu|yểu|yều)\b",
    re.IGNORECASE,
)
_UY_REJOIN_RE2 = re.compile(
    r"\b(quy|huy|tuy|chuy|nguy|khuy|xuy|buy|luy|duy|suy|ruy|muy|truy|phuy)"
    r"\s+(ền|ên|ến|ện|ệt|ết|ể|ễ|ệ|ếu|ểu|ều|ếp|ến)\b",
    re.IGNORECASE,
)


def _rejoin_uy_compounds(text: str) -> str:
    """Rejoin Vietnamese uy-compound words that were incorrectly split."""
    if not text:
        return text
    text = _UY_REJOIN_RE.sub(r"\1\2", text)
    text = _UY_REJOIN_RE2.sub(r"\1\2", text)
    return text


def fix_vietnamese_syllable_boundaries(text: str) -> str:
    """Insert spaces at Vietnamese syllable boundaries detected by regex.

    Applied iteratively (max 5 passes) to resolve chains like
    'tựtrảvềvịtrí' → 'tự trả về vị trí'.
    """
    if not text or len(text) < 3:
        return text

    for _ in range(5):
        prev = text
        text = _VN_SYLB_P1.sub(r"\1 \2", text)
        text = _VN_SYLB_P2.sub(r"\1 \2", text)
        text = _VN_SYLB_P3.sub(r"\1 \2", text)
        text = _VN_SYLB_P4.sub(r"\1 \2\3", text)
        if text == prev:
            break

    text = _rejoin_uy_compounds(text)
    return text
