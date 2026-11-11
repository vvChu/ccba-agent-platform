# Performance & Core Web Vitals Testing

## Core Web Vitals (2024 Targets)

| Metric | Target | Description |
|--------|--------|-------------|
| LCP | < 2.5s | Largest Contentful Paint |
| CLS | < 0.1 | Cumulative Layout Shift |
| INP | < 200ms | Interaction to Next Paint (replaced FID) |

## Lighthouse CI Setup

```json
// lighthouserc.json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000", "http://localhost:3000/dashboard"],
      "numberOfRuns": 3
    },
    "assert": {
      "preset": "lighthouse:recommended",
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "largest-contentful-paint": ["warn", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "interactive": ["warn", { "maxNumericValue": 3800 }]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

## GitHub Actions Integration

```yaml
performance:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: npm ci && npm run build
    - run: npm install -g @lhci/cli
    - run: lhci autorun
      env:
        LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_TOKEN }}
```

## Playwright Performance Test

```typescript
test('measure Core Web Vitals', async ({ page }) => {
  await page.goto('/');

  const metrics = await page.evaluate(() => {
    return new Promise((resolve) => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lcp = entries.find(e => e.entryType === 'largest-contentful-paint');
        resolve({ lcp: lcp?.startTime });
      }).observe({ type: 'largest-contentful-paint', buffered: true });
    });
  });

  expect(metrics.lcp).toBeLessThan(2500);
});
```

## INP Measurement

```typescript
test('interaction responsiveness', async ({ page }) => {
  await page.goto('/');

  const inp = await page.evaluate(() => {
    return new Promise((resolve) => {
      let maxINP = 0;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          maxINP = Math.max(maxINP, entry.duration);
        }
        resolve(maxINP);
      }).observe({ type: 'event', buffered: true, durationThreshold: 16 });

      // Trigger interactions
      document.querySelector('button')?.click();
      setTimeout(() => resolve(maxINP), 1000);
    });
  });

  expect(inp).toBeLessThan(200);
});
```

## Quick Commands

```bash
npx lighthouse https://example.com --output=json
npx @lhci/cli autorun
npx bundlesize                    # Bundle size check
npx webpack-bundle-analyzer stats.json
```

## Optimization Checklist

### LCP
- [ ] Lazy load below-fold images
- [ ] Preload critical resources (`<link rel="preload">`)
- [ ] Use CDN for static assets
- [ ] Optimize server response time

### CLS
- [ ] Set explicit width/height on images
- [ ] Reserve space for dynamic content
- [ ] Use `font-display: swap` or `optional`
- [ ] Avoid inserting content above existing

### INP
- [ ] Break long JavaScript tasks (<50ms)
- [ ] Use `requestIdleCallback` for non-critical work
- [ ] Implement code splitting
- [ ] Debounce rapid user interactions

---

## Lighthouse 13+ Shared Performance Insights & 5-Pillar Web Quality Audit

> **Upstream Attribution:** Chuyển thể từ `addyosmani/web-quality-skills` (`skills/web-quality-audit`, commit `afa8da94`, MIT License).

### 1. Chuyển Dịch Sang Lighthouse 13+ Shared Performance Insights
- Từ **Lighthouse 13+**, danh mục Performance sử dụng bộ **Performance Insights** dùng chung trực tiếp với bảng DevTools Performance (thay thế các mã audit rời rạc cũ vốn dễ báo động giả hoặc khuyến nghị quá tay). Không ép khôi phục các audit ID đã bị loại bỏ.
- **Định tuyến công cụ đo lường trực tiếp (Chrome DevTools MCP Routing):**
  - **Performance & Core Web Vitals:** Thu trace trực tiếp bằng `performance_start_trace` rồi phân tích nút thắt qua `performance_analyze_insight` (kèm dữ liệu người dùng thực CrUX p75/28 ngày nếu có).
  - **Accessibility, SEO, Best Practices & Agentic Browsing:** Chạy `lighthouse_audit` (lưu ý `lighthouse_audit` của DevTools MCP chủ đích tách riêng khỏi Performance). Chế độ `navigation` tải lại trang từ đầu; bắt buộc chọn chế độ **`snapshot`** khi cần bảo toàn trạng thái phiên đăng nhập hoặc giao diện tương tác dở dang của người dùng.
  - **Cây trợ năng & tương tác thực tế:** Đối chứng bằng `take_snapshot` và `evaluate_script` có trọng tâm.

### 2. Khung Kiểm Toán Chất Lượng Web 5 Trụ Cột Dựa Trên Bằng Chứng (5-Pillar Audit)
Không coi điểm tổng hợp đơn lẻ là bằng chứng chất lượng; luôn tách bạch **bằng chứng đo lường runtime** với **giả thuyết đọc từ mã nguồn tĩnh**:

1. **Performance:** LCP `< 2.5s`, INP `< 200ms`, CLS `< 0.1`, tối ưu tài nguyên WebP/AVIF, tách bundle JS và `font-display: swap`.
2. **Accessibility (POUR):** Đủ văn bản thay thế (`alt`), tương phản màu WCAG AA (`>= 4.5:1`), điều hướng bàn phím trọn vẹn không kẹt focus, có `Skip to main content`, thuộc tính `<html lang="...">` và vai trò ARIA chuẩn xác.
3. **SEO:** `/robots.txt` không chặn tài nguyên kết xuất, `sitemap.xml` chuẩn, canonical tự tham chiếu, tiêu đề/mô tả đặc thù từng trang và JSON-LD khớp nội dung hiển thị (chi tiết xem tại `.agents/skills/ccba-design/references/seo-and-agentic-discoverability.md`).
4. **Best Practices:** HTTPS toàn trình + HSTS + CSP chống XSS, không lộ source maps trên production, không dùng API trình duyệt lỗi thời (`document.write`, XHR đồng bộ), console sạch lỗi.
5. **Agentic Browsing:** Đánh giá khả năng trợ lý tự động hiểu cây trợ năng ngữ nghĩa, biểu mẫu có nhãn rõ ràng, tích hợp WebMCP (chỉ khi ứng dụng thực sự có tác vụ hữu ích cần phơi bày) và tệp `/llms.txt` tùy chọn. Tuyệt đối không đồng nhất điểm Agentic Browsing với thứ hạng tìm kiếm hay cam kết trích dẫn của sản phẩm AI.

### 3. Phân Bậc Mức Độ Nghiêm Trọng & Chuẩn Đầu Ra Báo Cáo
- **Critical** (lỗ hổng bảo mật, gãy luồng hoàn toàn $\rightarrow$ sửa ngay) · **High** (trượt Core Web Vitals, rào cản truy cập lớn $\rightarrow$ sửa trước khi phát hành) · **Medium** (cơ hội tối ưu hiệu năng/SEO $\rightarrow$ sửa trong sprint) · **Low** (tinh chỉnh nhỏ).
- Mọi báo cáo kiểm toán phải lập bảng **Evidence** (`Signal | Scope/Conditions | Result | Source`), liệt kê vấn đề kèm vị trí `file:line`, chạy lại đúng phép đo sau khi sửa và ghi nhận minh bạch những hạng mục vẫn chờ dữ liệu thực địa (field validation).
