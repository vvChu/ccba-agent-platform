# Vietnamese Legal Documents

Special handling for Vietnamese legal document formatting.

## Supported Document Types

- **Quy chế** (Regulations)
- **Nghị định** (Decrees)
- **Thông tư** (Circulars)
- **Quyết định** (Decisions)

## Legal Structure Detection

mdconvert automatically detects Vietnamese legal documents by looking for patterns:

- `Điều X` (Article X)
- `Chương I, II, III...` (Chapter)
- `Mục X` (Section)
- `Khoản X` (Clause)
- `Điểm a, b, c...` (Point)

## VN Legal Lint Rules

| Rule | Description | Example |
|------|-------------|---------|
| VN001 | Merged list items | `a) Item b) Item` should be on separate lines |
| VN002 | Numbering reset | Many `1.` without `2.` suggests reset issue |
| VN003 | Điều spacing | Missing blank line before `### Điều` headers |
| VN004 | Điểm format | `- a)` should be just `a)` |

## Post-Processing Rules

The VN Legal Processor applies these fixes:

1. **Remove bullets from intro phrases**: `- Đối với...` → `Đối với...`
2. **Fix definition lists**: Convert inline definitions to proper format
3. **Bold header spacing**: Ensure blank line after `**N. Header**`
4. **Normalize list markers**: Convert `*` and `+` to `-`
5. **Trailing newline**: Ensure single newline at EOF

## Usage

```bash
# Validate VN legal docs
mdconvert validate ./legal-docs/

# Lint with auto-fix
mdconvert lint ./legal-docs/ --fix

# VN-only checks
mdconvert lint ./legal-docs/ --vn-only
```
