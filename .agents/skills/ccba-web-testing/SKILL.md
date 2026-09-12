---
name: ccba-web-testing
description: Web testing with Playwright, Vitest, k6. E2E, load, visual, and a11y
  testing. Use for test automation, flakiness, Core Web Vitals, and cross-browser.
user-invocable: true
command: /ccba-web-testing
when_to_use: Invoke for browser, visual, load, or accessibility tests.
category: dev-tools
gpi:
  s: 4.0
  k: 3.0
  a: 1.0
  p: 1.0
keywords:
- Playwright
- Vitest
- k6
- e2e
- load-testing
license: Apache-2.0
argument-hint: '[test-type] [target]'
metadata:
  author: claudekit
  version: 3.0.0
disable-model-invocation: true
bundle: _software
tier: kernel
triggers:
- Playwright
- Vitest
- k6
- e2e
- load-testing
- ccba-web-testing
- playwright
- UI test
- e2e test
- browser automation
- vitest
---
# Web Testing Skill

Comprehensive web testing: unit, integration, E2E, load, security, visual regression, accessibility.

## Quick Start

```bash
npx vitest run                    # Unit tests
npx playwright test               # E2E tests
npx playwright test --ui          # E2E with UI
k6 run load-test.js               # Load tests
npx @axe-core/cli https://example.com  # Accessibility
npx lighthouse https://example.com     # Performance
```

## Testing Strategy (Choose Your Model)

| Model | Structure | Best For |
|-------|-----------|----------|
| Pyramid | Unit 70% > Integration 20% > E2E 10% | Monoliths |
| Trophy | Integration-heavy | Modern SPAs |
| Honeycomb | Contract-centric | Microservices |

→ `./references/testing-pyramid-strategy.md`

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/testing-pyramid-strategy.md` | Chiến lược phân bổ tỷ trọng kiểm thử: Kim tự tháp, Trophy, Honeycomb |
| `references/unit-integration-testing.md` | Kiểm thử đơn vị và tích hợp với Vitest, mock data và AAA pattern |
| `references/e2e-testing-playwright.md` | Kiểm thử E2E toàn diện với Playwright: fixtures, sharding, selectors |
| `references/playwright-component-testing.md` | Mô hình kiểm thử component trực tiếp bằng Playwright Component Testing |
| `references/component-testing.md` | Kiểm thử component cho các framework React, Vue, Angular |
| `references/test-data-management.md` | Quản lý dữ liệu kiểm thử: Factories, fixtures, synthetic data seeding |
| `references/database-testing.md` | Kiểm thử cơ sở dữ liệu với Testcontainers và transaction rollback |
| `references/ci-cd-testing-workflows.md` | Tích hợp kiểm thử vào pipeline CI/CD GitHub Actions và sharding song song |
| `references/contract-testing.md` | Kiểm thử giao ước (Contract Testing) với Pact và MSW mocks |
| `references/cross-browser-checklist.md` | Ma trận và checklist kiểm thử tương thích đa trình duyệt và thiết bị |
| `references/mobile-gesture-testing.md` | Kiểm thử thao tác cảm ứng di động: touch, swipe, pinch, orientation |
| `references/interactive-testing-patterns.md` | Mẫu kiểm thử tương tác người dùng phức tạp (drag-and-drop, canvas, modal) |
| `references/shadow-dom-testing.md` | Kỹ thuật kiểm thử các Web Components có Shadow DOM và slot elements |
| `references/performance-core-web-vitals.md` | Đo lường và tối ưu Core Web Vitals (LCP, CLS, INP) qua Lighthouse CI |
| `references/visual-regression.md` | Kiểm thử hồi quy giao diện qua so sánh ảnh chụp màn hình (pixel diffing) |
| `references/test-flakiness-mitigation.md` | Chiến lược phát hiện, cô lập và giảm thiểu test chập chờn (flaky tests) |
| `references/accessibility-testing.md` | Hướng dẫn kiểm thử khả năng truy cập (a11y) theo chuẩn WCAG và axe-core |
| `references/security-testing-overview.md` | Tổng quan kiểm thử bảo mật ứng dụng web theo chuẩn OWASP Top 10 |
| `references/security-checklists.md` | Danh mục kiểm tra an toàn web: Auth, headers, CSRF, input validation |
| `references/vulnerability-payloads.md` | Tập mẫu dữ liệu payload kiểm tra lỗ hổng XSS, SQLi, SSRF, Command Injection |
| `references/api-testing.md` | Kiểm thử API REST và GraphQL bằng Supertest và HTTP assertions |
| `references/load-testing-k6.md` | Kiểm thử tải và stress testing với k6 scenarios và metrics |
| `references/functional-testing-checklist.md` | Danh mục kiểm thử chức năng chi tiết cho web application |
| `references/pre-release-checklist.md` | Danh mục kiểm định toàn diện trước khi phát hành sản phẩm (Pre-Release Gate) |

## Scripts

### Initialize Playwright Project
```bash
node ./scripts/init-playwright.js [--ct] [--dir <path>]
```
Creates best-practice Playwright setup: config, fixtures, example tests.

### Analyze Test Results
```bash
node ./scripts/analyze-test-results.js \
  --playwright test-results/results.json \
  --vitest coverage/vitest.json \
  --output markdown
```
Parses Playwright/Vitest/JUnit results into unified summary.

## CI/CD Integration

```yaml
jobs:
  test:
    steps:
      - run: npm run test:unit      # Gate 1: Fast fail
      - run: npm run test:e2e       # Gate 2: After unit pass
      - run: npm run test:a11y      # Accessibility
      - run: npx lhci autorun       # Performance
```
