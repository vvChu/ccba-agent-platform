#!/usr/bin/env bash
# ==============================================================================
# Script: setup_ccba_devs_acls.sh
# Purpose: Cấu hình POSIX ACLs và phân quyền đa người dùng chuẩn cho CCBA Devs
# Target: Ubuntu 22.04 LTS (NVIDIA DGX Spark)
# Framework: CCBA 4-Hubs × Federated Spokes (#366)
# Author: Worker 2 - OS Topology Specialist
# ==============================================================================

set -euo pipefail

# Màu hiển thị console
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}  CCBA OS Topology Hardening & POSIX ACLs Deployment Tool           ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# 1. Kiểm tra quyền root/sudo
if [[ "$EUID" -ne 0 ]]; then
    echo -e "${RED}[LỖI] Script này bắt buộc phải chạy dưới quyền sudo hoặc root.${NC}"
    echo "Ví dụ: sudo ./setup_ccba_devs_acls.sh"
    exit 1
fi

TARGET_USER="vvc"
TARGET_HOME="/home/${TARGET_USER}"
COLLAB_GROUP="ccba-devs"
MEMBER_USERS=("vvc" "tta" "tat" "mtt")
TARGET_DIRS=("${TARGET_HOME}/Codebase" "${TARGET_HOME}/ccba" "${TARGET_HOME}/VvC_Notes")
PRIVATE_DIRS=("${TARGET_HOME}/.ssh" "${TARGET_HOME}/.gemini" "${TARGET_HOME}/.config" "${TARGET_HOME}/.claude")

# 2. Kiểm tra các tiện ích ACL cần thiết
echo -e "\n${YELLOW}--- Bước 1: Kiểm tra các gói công cụ hệ thống ---${NC}"
if ! command -v setfacl &> /dev/null || ! command -v getfacl &> /dev/null; then
    echo -e "${YELLOW}[!] Đang cài đặt gói 'acl'...${NC}"
    apt-get update -qq && apt-get install -y -qq acl
    echo -e "${GREEN}[✓] Gói 'acl' đã được cài đặt thành công.${NC}"
else
    echo -e "${GREEN}[✓] Tiện ích 'setfacl' và 'getfacl' đã sẵn sàng.${NC}"
fi

# 3. Tạo nhóm ccba-devs và thêm thành viên
echo -e "\n${YELLOW}--- Bước 2: Khởi tạo nhóm và gán thành viên ---${NC}"
if getent group "${COLLAB_GROUP}" > /dev/null 2>&1; then
    echo -e "${BLUE}[i] Nhóm '${COLLAB_GROUP}' đã tồn tại.${NC}"
else
    groupadd "${COLLAB_GROUP}"
    echo -e "${GREEN}[✓] Đã tạo mới nhóm '${COLLAB_GROUP}'.${NC}"
fi

for user in "${MEMBER_USERS[@]}"; do
    if id -u "${user}" > /dev/null 2>&1; then
        usermod -a -G "${COLLAB_GROUP}" "${user}"
        echo -e "${GREEN}[✓] Đã thêm người dùng '${user}' vào nhóm '${COLLAB_GROUP}'.${NC}"
    else
        echo -e "${RED}[CẢNH BÁO] Người dùng '${user}' không tồn tại trên hệ thống. Bỏ qua.${NC}"
    fi
done

# 4. Thiết lập Traversal Pin-Hole trên /home/vvc
echo -e "\n${YELLOW}--- Bước 3: Cấu hình Pin-Hole Traversal trên ${TARGET_HOME} ---${NC}"
# Đảm bảo mode cơ bản là 0750 (User: rwx, Group: r-x, Other: ---)
chmod 750 "${TARGET_HOME}"
# Cấp quyền --x DUY NHẤT cho nhóm ccba-devs trên /home/vvc
setfacl -m "g:${COLLAB_GROUP}:--x" "${TARGET_HOME}"
echo -e "${GREEN}[✓] Đã áp dụng 'g:${COLLAB_GROUP}:--x' trên ${TARGET_HOME}.${NC}"
echo -e "    -> Nhóm '${COLLAB_GROUP}' chỉ có thể xuyên qua để vào thư mục được phân quyền."
echo -e "    -> Người dùng ngoài nhóm bị chặn hoàn toàn bởi other::---."

# 5. Cấp quyền truy cập và kế thừa trên các thư mục dự án
echo -e "\n${YELLOW}--- Bước 4: Thiết lập POSIX ACLs trên các Hub dự án ---${NC}"
for dir in "${TARGET_DIRS[@]}"; do
    if [[ -d "${dir}" ]]; then
        echo -e "${BLUE}[*] Đang xử lý: ${dir}${NC}"
        # 1. Cấp quyền rwX cho toàn bộ cây thư mục hiện hữu
        setfacl -R -m "g:${COLLAB_GROUP}:rwX" "${dir}"
        # 2. Cấp default inheritance rwX cho toàn bộ tệp/thư mục tạo mới sau này
        setfacl -R -d -m "g:${COLLAB_GROUP}:rwX" "${dir}"
        echo -e "${GREEN}[✓] Hoàn tất ACL active & default trên ${dir}.${NC}"
    else
        echo -e "${RED}[!] Thư mục ${dir} không tồn tại. Bỏ qua.${NC}"
    fi
done

# 6. Thắt chặt phòng thủ các thư mục cá nhân nhạy cảm
echo -e "\n${YELLOW}--- Bước 5: Thắt chặt an ninh các thư mục nhạy cảm (chmod 700) ---${NC}"
for pdir in "${PRIVATE_DIRS[@]}"; do
    if [[ -d "${pdir}" ]]; then
        echo -e "${BLUE}[*] Đang khoá chặt: ${pdir}${NC}"
        chmod 700 "${pdir}"
        # Xoá toàn bộ ACL mở rộng nếu có để đảm bảo chỉ owner mới có quyền
        setfacl -b "${pdir}" 2>/dev/null || true
        echo -e "${GREEN}[✓] Đã cô lập quyền riêng tư mode 0700 cho ${pdir}.${NC}"
    fi
done

# Chuẩn hoá thêm các tệp SSH quan trọng bên trong ~/.ssh
if [[ -d "${TARGET_HOME}/.ssh" ]]; then
    [[ -f "${TARGET_HOME}/.ssh/id_ed25519" ]] && chmod 600 "${TARGET_HOME}/.ssh/id_ed25519"
    [[ -f "${TARGET_HOME}/.ssh/config" ]] && chmod 600 "${TARGET_HOME}/.ssh/config"
    [[ -f "${TARGET_HOME}/.ssh/authorized_keys" ]] && chmod 600 "${TARGET_HOME}/.ssh/authorized_keys"
    [[ -f "${TARGET_HOME}/.ssh/id_ed25519.pub" ]] && chmod 644 "${TARGET_HOME}/.ssh/id_ed25519.pub"
    echo -e "${GREEN}[✓] Đã chuẩn hoá quyền tập tin trong ${TARGET_HOME}/.ssh.${NC}"
fi

# 7. Cấu hình umask 0002 toàn cục cho thành viên nhóm ccba-devs
echo -e "\n${YELLOW}--- Bước 6: Cấu hình umask 0002 tự động ---${NC}"
UMASK_PROFILE="/etc/profile.d/ccba-umask.sh"
cat << 'EOF' > "${UMASK_PROFILE}"
# /etc/profile.d/ccba-umask.sh
# Tự động gán umask 0002 cho thành viên nhóm ccba-devs để duy trì quyền ghi nhóm
if id -nG 2>/dev/null | grep -qw "ccba-devs"; then
    umask 0002
fi
EOF
chmod 644 "${UMASK_PROFILE}"
echo -e "${GREEN}[✓] Đã tạo ${UMASK_PROFILE}.${NC}"

# 8. Kiểm chứng tự động (Verification & Audit)
echo -e "\n${YELLOW}--- Bước 7: Kiểm chứng kết quả phân quyền (Verification) ---${NC}"
echo -e "${BLUE}>> getfacl ${TARGET_HOME}:${NC}"
getfacl -c "${TARGET_HOME}"

echo -e "\n${BLUE}>> getfacl ${TARGET_HOME}/ccba:${NC}"
getfacl -c "${TARGET_HOME}/ccba" | head -n 12

echo -e "\n${BLUE}>> Quyền các thư mục nhạy cảm:${NC}"
ls -ld "${PRIVATE_DIRS[@]}"

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}  TRIỂN KHAI PHÂN QUYỀN CCBA-DEVS HOÀN TẤT THÀNH CÔNG!              ${NC}"
echo -e "${GREEN}====================================================================${NC}"
echo -e "${YELLOW}[LƯU Ý QUAN TRỌNG ĐỐI VỚI LẬP TRÌNH VIÊN]:${NC}"
echo "Để áp dụng nhóm mới ngay trong phiên bash hiện tại mà không cần logout:"
echo "  $ newgrp ccba-devs"
echo "Kiểm tra nhóm hiệu lực:"
echo "  $ id"
