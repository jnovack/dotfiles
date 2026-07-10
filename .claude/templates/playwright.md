
<!-- playwright.md -->
## Playwright Testing

### Structure

- One page object file per page or major section: `pages/HomePage.js`, `pages/ContactPage.js`.
- One spec file per page or user journey: `tests/home.spec.js`, `tests/contact.spec.js`.
- All selectors live in the page object. Tests contain zero raw CSS/XPath strings.
- Each `test()` must be able to run in isolation. Do not share state between tests
  via module-level variables.
- Failing tests must fail loudly — no `try/catch` blocks that swallow assertion
  failures.

### What to assert

- **JS health**: listen for `page.on('pageerror', ...)` — any uncaught JS error
  is a test failure.
- **Network requests**: use `page.waitForResponse(urlOrPredicate)` to assert
  XHR/fetch calls complete with a 2xx status. Assert on response status, not DOM
  side-effects alone.
- **Modals / interactive elements**: `expect(locator).toBeVisible()` after trigger;
  `expect(locator).toBeHidden()` after dismiss.
- **Dynamic content**: use `waitForSelector` or
  `expect(locator).toBeVisible({ timeout })` never `page.waitForTimeout()`.

### Minimum coverage

Every new page under test must include a "page loads without JS errors" test.

### Running

```bash
npx playwright test                                         # all tests
npx playwright test tests/home.spec.js                     # single spec
BASE_URL=https://staging.example.com npx playwright test   # against another env
npx playwright show-report                                  # open HTML report
```
