---
id: lang-android
scope: project
requires: [testing-philosophy]
order: 68
---

## android

Covers Kotlin/Android development for internally-distributed, MDM-managed
apps (enterprise kiosks and internal tools shipped outside the Play Store).
Sections describe what this org's existing Android codebase actually does —
where a heavier architecture is genuinely warranted for a new project, that's
called out separately rather than silently assumed.

### Toolchain

- JDK 17 is the stable baseline (re-check against AGP's stated minimum on a
  major AGP bump). Kotlin, Android Gradle Plugin, and Gradle track current
  stable — do not carry a version forward from training-data memory or an
  older project; verify the actual current release first, the same rule as
  GitHub Actions versions above:
  - Gradle: `curl -s https://services.gradle.org/versions/current`
  - AGP: check `developer.android.com/build/releases/agp-<major>-<minor>-0-release-notes`
    for the latest, and its stated supported API level
  - Kotlin: `https://kotlinlang.org/docs/releases.html`
  Bump all three together and re-check compatibility — do not let one drift
  ahead of the others. `init-android-project.sh`'s pinned defaults are
  overridable via env vars for this reason; refresh them the same way
  whenever they're next touched, since the script itself doesn't fetch live.
- `compileSdk`/`targetSdk` track the API level the current stable AGP
  supports; `minSdk` 26 is a fixed org/business decision, not a toolchain
  version, and moves independently. Respect whatever an existing project
  already has; raising min/target SDK is a deliberate, called-out change
  (e.g. an ADR in `docs/decisions/`), not a side effect of scaffolding a new
  one or bumping AGP.
- SDK location is `/opt/homebrew/share/android-commandlinetools` on dev
  machines (`sdk.dir` in `local.properties`, gitignored;
  `local.properties.example` is the checked-in template). `JAVA_HOME` is
  pinned to `/opt/homebrew/opt/openjdk@17` in the Makefile rather than relying
  on whatever JDK is default on the machine.
- Never hand-edit `gradlew`/`gradlew.bat`/`gradle/wrapper/*` — regenerate with
  `gradle wrapper --gradle-version <version>`.
- New projects: scaffold with `code/android/src/init-android-project.sh
  <application-name> [package-id] [kiosk|app]` (dotfiles repo) rather than
  hand-writing the Gradle files, manifest, and Makefile — it reproduces this
  toolchain exactly and covers both shapes described below (`kiosk`: plain
  `Activity` + XML layout; `app`: `ComponentActivity` + Jetpack Compose,
  default `kiosk` if omitted). See that script's templates before deviating
  from any file it generates.

### Formatting

- No formatter/linter is wired into CI yet (no `ktlint`/`detekt` config in the
  reference project). If you add one to a project, wire it into CI in the
  same change — don't add a formatter nobody runs.
- Until then: match the surrounding file's brace style, 4-space indent, and
  trailing-comma conventions. `./gradlew lint` (Android Lint) is always
  available and should stay clean.

### Architecture: kiosk vs. app

The reference project (a badge-scan kiosk) is a deliberately minimal
single-`Activity` app: plain `Activity` (not `AppCompatActivity` or
`ComponentActivity`), classic View system (XML layouts, `findViewById`), no
Jetpack Compose, no `ViewModel`/`LiveData`, no Room, no DI framework. That's a
considered choice for a single-screen device that boots straight into one
task — not an oversight to "modernize" reflexively.

- Keep a project in this lean shape when it is genuinely single-screen/kiosk
  in nature: one `Activity`, no back-stack navigation, no persisted
  multi-entity state.
- Default to modern Jetpack for anything else — multi-screen navigation,
  shared/persisted state, or a testable presentation layer: Jetpack Compose
  for UI, `ViewModel` + `StateFlow` for state, Kotlin Coroutines for
  concurrency (see below), Room for local persistence. Don't retrofit the
  kiosk's minimalism onto a project that has outgrown it.

### Concurrency

- The reference project uses `kotlin.concurrent.thread` for background work
  and a single `Handler(Looper.getMainLooper())` to post results back to the
  main thread — no coroutines. This is accepted for its scope (a handful of
  fire-and-forget network calls with no cancellation needs), not a pattern to
  default to.
- For any project with more than incidental background work, use Kotlin
  Coroutines: `viewModelScope`/`lifecycleScope` + `Dispatchers.IO` for
  network/disk, structured concurrency instead of ad-hoc `thread {}` calls.
  Reach for this once you need cancellation, multiple concurrent calls, or
  anything a raw `Handler` callback chain makes awkward to reason about.
- Whichever model is in use, every background unit of work has a clear owner
  for its lifetime — an unstructured `thread {}` that outlives the screen that
  started it is a bug.

### Error handling

- Network/parsing failures degrade to a typed result (e.g. an `ALLOWED` /
  `DENIED` / `ERROR` enum) and a logged warning — they do not crash the app.
  Log through a single consistent tag per app (`Log.w("AppName", "what
  failed", e)`), not ad-hoc tags per call site.
- Enrichment calls that only affect display (e.g. fetching a name/photo after
  a decision is already recorded) degrade to `null` on failure rather than
  failing the whole flow — the recorded decision is the thing that matters.
- Validate untrusted input (scanned/swiped/typed) against a strict format
  before it reaches a network call — reject anything that doesn't look like
  the expected shape instead of forwarding noise to the server.

### Networking

- Prefer OkHttp/Retrofit for a new REST/JSON client — don't hand-roll HTTP
  framing unless the protocol genuinely requires it.
- The reference project hand-frames gRPC-Web over `HttpURLConnection`
  because the ingress in front of the target service strips HTTP/2 trailers
  (native gRPC fails: "server closed the stream without sending trailers")
  and `grpc-java` has no gRPC-Web transport. If you hit that exact failure
  mode against another gRPC-Web-only backend, that hand-framing approach
  (manual varint-encoded protobuf, 5-byte gRPC-Web frame header) is the
  established solution — don't rediscover it from scratch.
- Set explicit `connectTimeout`/`readTimeout` on any raw `HttpURLConnection`
  use (5s/10s in the reference project) — the platform default is effectively
  unbounded.

### Secrets and configuration

- Never compile a real secret (auth key, API token) into `BuildConfig` for a
  release build. A string constant in an APK is trivially recoverable
  regardless of obfuscation.
- Pattern: `local.properties` (gitignored) → `BuildConfig` fields, gated to
  `BuildConfig.DEBUG` builds only. The release `buildTypes` block explicitly
  overrides those fields back to `""` so a release build can never
  accidentally compile in a real value even if a dev's `local.properties` has
  one.
- Real runtime values for an MDM-managed app are delivered via Android
  Enterprise **Managed App Configuration**, not compiled in:
  1. Declare accepted keys in `res/xml/app_restrictions.xml`, referenced from
     `AndroidManifest.xml` via an `android.content.APP_RESTRICTIONS`
     meta-data entry.
  2. Read them at runtime with `RestrictionsManager` /
     `getSystemService(RESTRICTIONS_SERVICE)`.
  3. Register a `BroadcastReceiver` for
     `Intent.ACTION_APPLICATION_RESTRICTIONS_CHANGED` and re-resolve the
     values when it fires, so a rotated key or repointed URL takes effect
     without an app relaunch.
  4. Fall back to the `local.properties`-sourced `BuildConfig` field only
     when `BuildConfig.DEBUG` is true, and to `""` otherwise — an
     unconfigured release build should fail closed (surfaced as a normal
     connection error), not fall back to a stale or wrong value.
- Restriction key names are case-sensitive and must match the schema exactly
  — a mismatch fails silently (the value just never arrives) rather than
  erroring, so treat the key string as an exact contract, not a label.

### Network security

- Pin any enterprise root CA the app must trust via
  `res/xml/network_security_config.xml` (`trust-anchors` with `src="system"`
  plus a `@raw/<ca>` certificate), referenced from the manifest's
  `android:networkSecurityConfig`. Set `cleartextTrafficPermitted="false"` at
  the base config and keep it that way — do not add a cleartext exception or
  flip `usesCleartextTraffic` to work around a connection issue; fix the
  actual TLS/CA problem instead.
- Request only the permissions the app actually uses. `INTERNET` alone
  covers the reference project — anything else (camera, storage, location)
  needs its own justification and, for dangerous permissions, runtime
  request handling.

### Distribution

- Internal-only apps default to **Enterprise App (in-house) distribution**
  through the org's MDM (an `.apk` uploaded directly to the MDM's app
  repository) rather than Managed Google Play or the public Play Store —
  this avoids a dependency on a Google Play Developer account or Google's
  review pipeline for something that never needs public distribution.
- Enterprise-distributed release builds are **unsigned** on purpose (there's
  no store requiring a signature). Do not add a signing config unless the
  distribution model actually changes to something that requires one.
- CI (`v*.*.*` tag → GitHub Release with the unsigned APK attached) installs
  the Android SDK with plain shell (`curl` the command-line tools zip,
  checksum-verify, `sdkmanager --licenses` then install `platform-tools` +
  the matching `platforms;android-<compileSdk>` and `build-tools`) instead of
  a third-party `setup-android` action — needed when the org's Actions policy
  only allows GitHub-owned/verified-marketplace actions. Keep
  `CMDLINE_TOOLS_VERSION`/`CMDLINE_TOOLS_SHA256` pinned and re-verify both
  together against developer.android.com whenever you bump the version —
  Google doesn't publish a separate checksum file to check against later.
  Use `actions/setup-java` for the JDK.

### Kiosk device behavior

Applies to single-purpose scan/kiosk devices; skip for a normal handheld app.

- Set `WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON` whenever the app is
  foregrounded. A sleeping screen eats the first keystrokes of an external
  keyboard-wedge scan while the device wakes, so the input arrives truncated.
- A USB/Bluetooth keyboard-wedge scanner (badge reader, barcode scanner)
  types its payload as keystrokes terminated by Enter — accumulate it in
  `dispatchKeyEvent`, not a focused `EditText`, so it works regardless of
  what's on screen, and emit the buffered string on `KEYCODE_ENTER` /
  `KEYCODE_NUMPAD_ENTER`.
- Debounce repeat scans with a cooldown window, and **re-arm the cooldown on
  every scan attempt, not just accepted ones** — otherwise a reader picking
  up continuous noise (e.g. held against another device) leaks one real
  lookup through each time the cooldown from the last rejected scan expires.

### Project structure

```text
{repo}/
├── app/
│   ├── build.gradle.kts        # namespace/applicationId, SDK versions, deps
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── kotlin/{package/path}/   # ui/theme/ too for the `app` (Compose) shape
│       └── res/
│           ├── layout/               # kiosk shape only — `app` has no XML layouts
│           ├── values/
│           └── xml/             # app_restrictions.xml, network_security_config.xml
├── docs/                        # admin/ops hand-off docs, ADRs
├── .github/workflows/           # release.yml (tag -> unsigned APK on GitHub Release)
├── .local/screenshots/          # `make screenshot` output (gitignored)
├── Makefile                     # build/install/launch/adb wireless/screenshot targets
├── local.properties(.example)   # sdk.dir + debug-only secrets; real file gitignored
├── settings.gradle.kts
└── build.gradle.kts
```

### Dependencies

- Minimal footprint by default — `androidx.core-ktx` and whatever the chosen
  architecture needs (Compose, Coroutines, Room), nothing speculative.
- Do not add a dependency (HTTP client, DI framework, image loader) without
  calling it out explicitly. Prefer AndroidX + Kotlin stdlib first.

### Testing

The reference project currently has no automated tests — call that out
plainly rather than implying coverage that doesn't exist. For new logic:

- Pure-logic pieces with no Android framework dependency (parsing, filtering,
  protocol framing, input buffering/validation) are the first candidates for
  plain JUnit unit tests — they need no emulator/Robolectric.
- Add Robolectric or AndroidX Test (`androidx.test.ext:junit`,
  `espresso-core`) only once a project has logic that genuinely depends on
  Android framework classes (`Context`, views, lifecycle) — don't reach for
  instrumented tests to cover what a plain JUnit test already can.
- What's worth testing at all is governed by the Testing Philosophy section;
  this just maps it onto where Android-specific test types apply.

### Dev workflow

- `make help` lists available targets. The standard set: `build`/`install`
  (assemble/install the debug APK), `launch`, `deploy` (install + launch),
  `devices`, `uninstall`, `logcat`, `clean`, `screenshot` (pulls a PNG into
  `.local/screenshots/`), and wireless ADB `pair`/`connect`.
- Wireless ADB workflow: `make pair ADDR=<ip:port>` using the address and
  6-digit code from the phone's "Pair device with pairing code" screen
  (one-time per device), then `make connect ADDR=<ip:port>` using the
  phone's persistent wireless-debugging address for every session after —
  that address is not stable enough to hardcode a default for, so `connect`
  requires it explicitly rather than falling back to a stale value.

### Validation

```bash
./gradlew :app:assembleDebug
./gradlew :app:lint
./gradlew test                # once unit tests exist
```
