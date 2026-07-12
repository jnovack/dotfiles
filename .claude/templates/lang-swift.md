---
id: lang-swift
scope: project
requires: [testing-philosophy]
order: 66
---

## swift

Covers macOS and iOS application development. Shared rules first; platform
divergences (lifecycle, windowing, entitlements) live in their own subsections.
Keep core logic platform-agnostic so those subsections stay small.

### Toolchain and language mode

- Target the Swift 6 language mode (`swiftLanguageMode(.v6)` /
  `SWIFT_VERSION = 6`) with strict concurrency checking set to `complete` for
  all new targets. For existing projects, respect the configured mode — do not
  flip a Swift 5 target to 6 without explicit instruction; that is a migration,
  not a side effect.
- Respect the project's minimum deployment targets. Do not raise them to use a
  newer API without calling it out — use `if #available` at the boundary
  instead.
- Never hand-edit `project.pbxproj`. Make target/build-setting changes through
  Xcode, or through the project generator (XcodeGen, Tuist) if the repo uses
  one. Keeping logic in SPM packages (see Project Structure) is the primary
  defense against project-file churn.

### Formatting

- All Swift code must be `swift-format`-clean before committing. Run
  `swift format lint --recursive .` — any output is a failure. If the repo has
  a `.swift-format` config, it is authoritative.
- If the repo uses SwiftLint (`.swiftlint.yml` present), a clean `swiftlint`
  run is also required. Do not add SwiftLint to a repo that doesn't have it.
- Trailing commas in multiline collections; one declaration per line; `let`
  before `var` in property lists only when it reads naturally — do not
  hand-sort against the formatter.

### Idioms

- Value types first: `struct` by default, `class` only for identity, reference
  semantics, or framework requirements (`@Observable` models, AppKit/UIKit
  subclasses).
- `let` by default. `var` only when mutation is required.
- Never force-unwrap (`!`) or force-try (`try!`) in application code. Use
  `guard let`/`if let` with early exit. The only acceptable force-unwraps are
  compile-time-guaranteed resources (e.g. a bundled asset) — and each one gets
  a comment stating the guarantee.
- Do not use `try?` to swallow errors that matter. If failure is genuinely
  ignorable, say why in a comment.
- Prefer protocol conformance over inheritance. Prefer extensions to group
  conformances (`extension Foo: Codable { ... }`).
- Access control is deliberate: `private` by default inside a target, explicit
  `public` only at package boundaries. No `open` unless subclassing across
  modules is a designed extension point.

### Error handling

- Define domain errors as `enum ... : Error` with associated values; conform to
  `LocalizedError` when the message reaches the user.
- Use typed throws (`throws(ParseError)`) when the error set is closed and
  callers benefit from exhaustive handling; plain `throws` otherwise.
- Errors cross layer boundaries wrapped with context, not swallowed. The UI
  layer decides presentation; the core layer never calls `fatalError` for
  recoverable conditions.
- `fatalError`/`precondition` are for programmer errors only (impossible
  states), never for I/O, network, or user-input failures.

### Concurrency

- `async`/`await` exclusively. No completion handlers, no `DispatchQueue`, no
  semaphores in new code. Wrap legacy callback APIs with
  `withCheckedThrowingContinuation` at the boundary — resume exactly once.
- UI state is `@MainActor`. Annotate the type, not individual members, when the
  whole type is UI-facing.
- Shared mutable state lives in an `actor`. Do not reach for locks; if a lock
  is truly required (tight hot path), use `Mutex`/`OSAllocatedUnfairLock` and
  keep the critical section free of `await`.
- Prefer structured concurrency (`async let`, `TaskGroup`) over unstructured
  `Task { }`. Every unstructured `Task` must have an owner responsible for its
  lifetime — in SwiftUI use `.task { }`/`.task(id:)` so cancellation is
  automatic.
- Honor cancellation: long loops check `Task.isCancelled` or call
  `Task.checkCancellation()`.
- `@unchecked Sendable` requires a comment proving the invariant that makes it
  safe. Treat it as a code smell, not an escape hatch. Never silence a
  concurrency diagnostic with `@preconcurrency` unless the module is genuinely
  a pre-Swift-6 dependency.

### UI framework

- SwiftUI first, on both platforms. Drop to AppKit/UIKit only when SwiftUI
  cannot do the job, via `NSViewRepresentable`/`UIViewRepresentable` — keep the
  representable a thin adapter, logic stays in Swift(UI)-land.
- Use the Observation framework (`@Observable`) for new model objects — not
  `ObservableObject`/`@Published`. Match the existing pattern in older code.
- Views are cheap value types: no side effects in `body`, no business logic in
  views. Views render state and forward intent to a model.
- Dependency injection flows through the SwiftUI `Environment`
  (`@Environment`, custom `EnvironmentKey`/`@Entry`) — no singletons for
  anything a test would want to substitute.
- Every user-facing string goes through String Catalogs (`Localizable.xcstrings`)
  — no hardcoded literals in views. Use `LocalizedStringKey` semantics; format
  values with `Text(_:format:)`, dates/numbers with `FormatStyle`, never
  string interpolation.
- No hardcoded frame sizes for layout. Use layout containers, `Spacer`,
  and let Dynamic Type work — test at accessibility text sizes.

### Project structure

The app target is wiring only — the `App` struct, scene declarations, and
platform glue. Everything else lives in local SPM packages inside the repo:

```text
{repo}/
├── {App}.xcodeproj            # or Package.swift-driven workspace
├── {App}/                     # app target: @main, scenes, entitlements, assets
│   ├── {App}App.swift
│   ├── Assets.xcassets
│   └── {App}.entitlements
├── Packages/
│   ├── {App}Core/             # platform-agnostic: models, services, logic
│   │   ├── Package.swift
│   │   ├── Sources/{App}Core/
│   │   └── Tests/{App}CoreTests/
│   └── {App}UI/               # shared SwiftUI views and view models
│       ├── Package.swift
│       ├── Sources/{App}UI/
│       └── Tests/{App}UITests/
├── docs/                      # user-facing documentation
└── scripts/                   # build/CI helpers
```

- Core packages must not import SwiftUI, AppKit, or UIKit. If a core type
  needs a platform check, the design is wrong — invert it so the platform
  layer injects the difference.
- `#if os(macOS)` / `#if os(iOS)` is allowed only in the UI package and app
  targets, and only at the smallest possible scope (a modifier, a single
  view) — never wrapping whole files of logic.
- Multiplatform projects use a single multiplatform target where possible,
  not parallel per-OS targets, unless the products genuinely diverge.

### Platform: iOS

- Respect the scene lifecycle. Persist state on `scenePhase` transitions to
  `.background` — iOS can kill the process at any time afterward.
- Background work goes through `BGTaskScheduler` (registered identifiers in
  `Info.plist`), not detached tasks that die with the app.
- Layout must survive Dynamic Type, both orientations where supported, and
  compact/regular size classes. Do not design against a single simulator.
- Every capability prompt needs its purpose string (`NSCameraUsageDescription`,
  etc.) — missing strings are a crash at first use, not a warning.

### Platform: macOS

- App Sandbox stays on. Add entitlements one at a time, each justified —
  never `com.apple.security.files.all` when a security-scoped bookmark from an
  `NSOpenPanel`/`.fileImporter` selection will do. Start/stop security-scoped
  resource access in balanced pairs.
- Provide the expected desktop affordances: a real menu bar via `Commands`,
  keyboard shortcuts for primary actions, a `Settings` scene instead of an
  ad-hoc preferences window.
- Support multiple windows/tabs where the document model allows; use
  `WindowGroup`/`DocumentGroup` scenes rather than manual `NSWindow` juggling.
- Test resizing: macOS windows are user-sized; layouts that only work at one
  size are bugs.

### Persistence

- SwiftData for new persistence needs; respect existing Core Data stacks and
  do not migrate between them as a side effect.
- Small preferences go in `UserDefaults` (via `@AppStorage` in UI); anything
  secret goes in the Keychain — never `UserDefaults`, never a plist.

### Logging

- Use `os.Logger` with `subsystem` = bundle identifier and a per-area
  `category`. No `print()` or `NSLog` in committed code.
- Interpolate values with appropriate privacy: `\(value, privacy: .public)`
  only for values that are genuinely not user data — the default private is
  correct for identifiers, paths, and content.

### Dependencies

- SPM only. No CocoaPods or Carthage in new projects.
- Do not add a package without calling it out explicitly. Prefer Apple
  frameworks — the platform SDK covers most needs.
- Pin with `from:` version requirements and commit `Package.resolved`. Never
  depend on `branch:` or `revision:` outside short-lived experiments.

### Testing

- Swift Testing (`@Test`, `#expect`, `#require`) for all new unit tests.
  XCTest remains for UI tests (`XCUIApplication`) and existing suites — do not
  mix frameworks within one file.
- Parameterized tests (`@Test(arguments:)`) are the table-driven idiom — use
  them wherever cases share a shape.
- Core-package tests run with `swift test` and no simulator — this is the main
  payoff of the package structure; keep it true by keeping platform imports
  out of core.
- Mock at protocol boundaries defined in the core package. Never mock types
  you don't own — wrap them behind a protocol first.
- UI tests are for critical user journeys only, and only when asked. Do not
  add brittle tests that depend on timing guesses, pixel layout, or incidental
  accessibility-identifier structure.

### Validation

```bash
swift format lint --recursive .   # formatting — any output is a failure
swift build --package-path Packages/{App}Core
swift test --package-path Packages/{App}Core
xcodebuild -scheme {App} -destination 'platform=macOS' build test
xcodebuild -scheme {App} -destination 'platform=iOS Simulator,name=iPhone 16' build test
```

- Package-level `swift test` is the fast inner loop; `xcodebuild test` against
  both destinations is required before claiming a multiplatform change works.
- Treat new warnings as failures — do not commit code that adds to the warning
  count, especially concurrency diagnostics.
