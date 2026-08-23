# ADR 0046: Personal Sandbox Spoke Lifecycle, Registry TTL, and CCBA Charter 2026 Alignment

## Context
As the CCBA Agent Platform scales across all technical personnel, individual engineers, researchers, and project managers require dedicated local workspaces to experiment with AI prompts, develop automation scripts, and execute assigned Phiáº¿u Giao Viá»‡c (PGV) tasks without endangering official project production repositories. However:
1. Unlimited, unmonitored personal spoke creation risks Registry Bloat and orphaned metadata in Hub's `spoke_registry.yaml`.
2. Uncontrolled output generation in personal sandboxes risks accidental distribution of unverified draft reports as certified CCBA deliverables.
3. Organizational roles and functional departments in workspace contexts must strictly mirror the authentic *Quy cháº¿ Tá»• chá»©c vÃ  Hoáº¡t Ä‘á»™ng CCBA 2026* (5 Functional Departments, 11 Accountability Seats, 5-Level QC Gate, and GWC Capacity Framework).

## Decision
We formally establish the **Personal Sandbox Spoke Specification (`specialized_extension` / `personal_sandbox`)**, the **Tiered Registry TTL Protocol**, the **Sandbox Watermarking & QC Level Cap**, and the **3-Step Deliverable Promotion & PGV Handover Pipeline**.

### 1. Personal Sandbox Taxonomy & CCBA Charter 2026 Schema
Personal sandboxes are classified under Archetype `specialized_extension` with `sub_type: "personal_sandbox"`. Their `.md/workspace_context.yaml` strictly maps to CCBA Charter 2026:
- The 5 Functional Departments + Ban GiÃ¡m Ä‘á»‘c (`department`): `PHONG_TONG_HOP`, `PHONG_RD_HTQT`, `PHONG_BIM_THIET_KE`, `PHONG_BIM_DU_AN`, `PHLNG_TV_KD_HCM`, `BAN_GIAM_DOC`.
- The 11 Accountability Seats (`seat_role`): `GIAM_DOC`, `PHO_GIAM_DOC`, `CO_VAN_PHAP_LY_QA`, `TRUONG_PHONG_TONG_HOP`, `PHU_TRACH_KE_TOAN`, `TRUONG_PHONG_RD_HTQT`, `IDOP_LEAD`, `TRUONG_PHONG_BIM_THIET_KE`, `TRUONG_PHONG_BIM_DU_AN`, `CHU_TRI_HOP_DONG_PM`, `CHU_TRI_BO_MON`, `KY_SU_THUC_THI`‚‹HKS]™[PÈ]]Üš^˜][Ûˆ
X×ÙÛÝ™\›˜[˜ÙX
NˆU‘SÌWÕPÒ’PÐSÐÒPÒØÈU‘SÍWÑ’SSÐT“ÕS
1$xnà]HLÊK‚‹HQÔÈ\ÚÈ[YÜ˜][Ûˆ
YÜÝ\ÚÜØ
NˆX\ÈXÝ]™HÝ—ØÛÙX][\ÈÚ]X^Ì	HY˜[˜ÙH[Z]
X^ØY˜[˜ÙWÜ˜]NˆÌ\ˆ1$xnà]HMÊK‚‚ˆÈÈÈ‹ˆY\™Y™YÚ\ÝžH™YÚ\Ý˜][Ûˆ	ˆŒQ^HÝÙY\‹HX‰ÜÈÜÚÙWÜ™YÚ\ÝžKžX[[›YÜÈØ[™›Þ\ÈÚ]\×ÜØ[™›ÞˆYX[™ÝÛ™\—Ù[XZ[‚‹HÙ[˜[˜]ÚÞ[˜ÜÈ
Þ[˜×ÜÜÚÙKœHKX[
H]]ÛX]XØ[H^ÛYH\œÛÛ˜[Ø[™›Þ\È[›\ÜÈ^XÚ]H\™Ù]Y

Z[˜ÛYK\Ø[™›Þ\Ø
K‚‹HØ[™›Þ\È[˜XÝ]™H›ÜˆˆŒ^\È\™HX\šÙYS’PÕU‘WÔÐS‘“Ö[™ØY™[HÝÙ\\š[™È™YÚ\ÝžHXZ[[˜[˜ÙK‚‚ˆÈÈÈËˆØ[™›ÞØ]\›X\šÚ[™È	ˆPÈ]™[Ø\‹H[ØÝ[Y[ËØ[Ý[][ÛœË[™]Y]™\ÜÈÙ[™\˜]Y[œÚYHHØ[™›Þ]]ÛX]XØ[H[˜ÛYHHX[™]ÜžHXY\‹Ù›ÛÝ\Ž‚ˆÐÐÐHÐS‘“ÖS‘TÈ¸n¨“ˆ8n¨“ÈQÒpâ“ˆÐUH“ÒH¸næHÒPH0àU0à’Ò0ãS’8n«×X‚‹HØ[™›ÞÜ\˜][ÛœÈ\™HØ\Y]
”TH]™[H
XÚšXØ[ÚXÚÊJ‹ˆ\™XÝX›\Ú[™ÈÈÙ™šXÚX[Ú\™TÚ[ÙQØÝ[Y[Ø\ÈÝšXÝH›ØÚÙYžHQÔœšYÙXÚ[ˆØ[™›ÞÛ[ÙNˆYX‚‚ˆÈÈÈˆËTÝ\[]™\˜X›H›Û[Ý[Ûˆ	ˆØH[YÜ˜][Û‚‚ŒKˆ
ŠÛX[œÙH	ˆ˜[Y]JŠŽˆønîHñ¬Ú8n¨^HÚxnàÛH˜Høn©\K8náÈ8nä[™È8nìH1$xnæ[™ÈønèH8nèÞH0è[ˆÐÐHÐS‘“ÖQ•ÚH1$xn¨]Úxnª[‹‚Œ‹ˆ
Š•\™Ù][™Ù\Ý[ÛŠŠŽˆ8nëÈxnáÝH1$pìÛ™ÈðìÚH1$q¬8nèØÈÚ^xnàÛˆ8n¬Û™ÈØ[™ÈÜÚÙH8nìH0à[ˆ1$pëXÚ
[]™\žWÜ›Ú™XÝ
Høn­ØÈ1$xnª^H0ê›ˆXˆ]XHØØØ˜K\›ÜÜÙK]ËZX˜‚ŒËˆ
Š”ÕˆÚYÛ‹[Ù™ˆÝYÚ[™ÊŠŽˆQÔœšYÙX8nìH1$xnæ[™È1$pà[šðìÚH0í™È[ˆxn¯ÝHÚX[ÈšxnáØÈ
›Ø\ÜÚYÛ›Y[Ø
H1$xnàÈÚxnª[ˆ¸nâÈH^xnáÝ± Û™ÈÝxn©]8n©Û™ÈË‚‚ˆÈÈÛÛœÙ\]Y[˜Ù\Â‹HÜÚ]]™Nˆ8nìHÈðè[™È8n¨[È°è8nëH™ÚxnáÛH[ˆðèˆxn©]8nìXÈÚÈ0èššpê›ˆÐÐK‚‹HÜÚ]]™Nˆpè›ˆ8néÈL	H]^HÚ8n¯ÈÐÐHŒ‹špêpêH¸néÞ¹’Æž¸wR6’Î¸v6‚n¹¶’fž¸vâ”%5Bà¢Ò÷6—F—fS¢Œ:&âI¸¶æ‚,:æ‚Þª6‚vžºöL:’>ª6âN»:â6Œ:Öæ‚FŽº–2l:,ª6âæŒ:FŽºÒæv†ž¸vÒ<:æŒ:&âà