#!/usr/bin/env bash
# Scaffolds a standard Android (Kotlin) project layout in the current directory.
# Usage: init-android-project.sh <application-name> [package-id] [kiosk|app]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES="${SCRIPT_DIR}/templates"

# ── Args ──────────────────────────────────────────────────────────────────────
APPLICATION="${1:-}"
PACKAGE="${2:-}"
ARCHITECTURE="${3:-kiosk}"

if [[ -z "$APPLICATION" ]]; then
    echo "Usage: $0 <application-name> [package-id] [kiosk|app]" >&2
    echo "  e.g.  $0 parking-app com.parxcasino.parkingapp kiosk" >&2
    echo "  kiosk (default): plain Activity, classic View system — single-screen kiosk devices" >&2
    echo "  app: ComponentActivity + Jetpack Compose — multi-screen apps with navigation/state" >&2
    echo "  see CLAUDE.md's 'Architecture: kiosk vs. app' section for which shape fits" >&2
    exit 1
fi

case "$ARCHITECTURE" in
    kiosk|app) ;;
    *)
        echo "Unknown architecture '${ARCHITECTURE}' — expected 'kiosk' or 'app'" >&2
        exit 1
        ;;
esac

SLUG="$(echo "$APPLICATION" | tr -cd '[:alnum:]' | tr '[:upper:]' '[:lower:]')"
if [[ -z "$PACKAGE" ]]; then
    PACKAGE="com.example.${SLUG}"
    echo "No package-id given, defaulting to ${PACKAGE} — change applicationId/namespace later if needed."
fi
PACKAGE_PATH="$(echo "$PACKAGE" | tr '.' '/')"

# PascalCase for the Theme name (meal-ticket -> MealTicket), Title Case for the
# launcher label (meal-ticket -> Meal Ticket).
THEME_NAME="$(echo "$APPLICATION" | awk -F'[-_ ]+' '{out=""; for (i=1;i<=NF;i++) out = out toupper(substr($i,1,1)) substr($i,2); print out}')"
APP_LABEL="$(echo "$APPLICATION" | awk -F'[-_ ]+' '{out=""; for (i=1;i<=NF;i++) out = out (i>1?" ":"") toupper(substr($i,1,1)) substr($i,2); print out}')"

# ── Versions ──────────────────────────────────────────────────────────────────
# Defaults below are current stable as of 2026-07-21 (see CLAUDE.md's
# Toolchain section for how to re-verify: Gradle's version endpoint, the AGP
# release notes, kotlinlang.org/docs/releases.html). Do not let this drift —
# re-check and bump all three together next time this script is touched,
# rather than trusting these numbers from memory. Override via env vars to
# scaffold against a different target without editing the script.
COMPILE_SDK="${COMPILE_SDK:-36}"
MIN_SDK="${MIN_SDK:-26}"
TARGET_SDK="${TARGET_SDK:-36}"
BUILD_TOOLS_VERSION="${BUILD_TOOLS_VERSION:-36.0.0}"
AGP_VERSION="${AGP_VERSION:-9.2.1}"
KOTLIN_VERSION="${KOTLIN_VERSION:-2.3.20}"
GRADLE_VERSION="${GRADLE_VERSION:-9.6.1}"
COMPOSE_BOM_VERSION="${COMPOSE_BOM_VERSION:-2026.06.01}"

echo "Scaffolding Android project: ${APPLICATION} (package=${PACKAGE}, architecture=${ARCHITECTURE}, compileSdk=${COMPILE_SDK})"

SED_EXPR="s|{{APPLICATION}}|${APPLICATION}|g; s|{{PACKAGE_PATH}}|${PACKAGE_PATH}|g; s|{{PACKAGE}}|${PACKAGE}|g; s|{{THEME_NAME}}|${THEME_NAME}|g; s|{{APP_LABEL}}|${APP_LABEL}|g; s|{{COMPILE_SDK}}|${COMPILE_SDK}|g; s|{{MIN_SDK}}|${MIN_SDK}|g; s|{{TARGET_SDK}}|${TARGET_SDK}|g; s|{{BUILD_TOOLS_VERSION}}|${BUILD_TOOLS_VERSION}|g; s|{{AGP_VERSION}}|${AGP_VERSION}|g; s|{{KOTLIN_VERSION}}|${KOTLIN_VERSION}|g; s|{{GRADLE_VERSION}}|${GRADLE_VERSION}|g; s|{{COMPOSE_BOM_VERSION}}|${COMPOSE_BOM_VERSION}|g"

render() { # <template-name> <dest-path>
    if [[ ! -f "$2" ]]; then
        sed -e "$SED_EXPR" "${TEMPLATES}/$1" > "$2"
        echo "  [create] $2"
    fi
}

# ── Directory layout ──────────────────────────────────────────────────────────
mkdir -p \
    "app/src/main/kotlin/${PACKAGE_PATH}" \
    "app/src/main/res/drawable" \
    "app/src/main/res/mipmap-anydpi-v26" \
    "app/src/main/res/values" \
    "docs/decisions" \
    ".github/workflows"

if [[ "$ARCHITECTURE" == "kiosk" ]]; then
    mkdir -p "app/src/main/res/layout"
fi

# ── Root project files ─────────────────────────────────────────────────────────
# AGP 9+ has Kotlin support built in — the root build file only needs a
# separate Kotlin-family plugin (versioned) when the Compose compiler plugin
# is in play, which is why this branches by architecture.
render "Makefile" "Makefile"
render "settings.gradle.kts" "settings.gradle.kts"
if [[ "$ARCHITECTURE" == "app" ]]; then
    render "build.gradle.kts.compose" "build.gradle.kts"
else
    render "build.gradle.kts" "build.gradle.kts"
fi
render "gradle.properties" "gradle.properties"
render "gitignore" ".gitignore"
render "local.properties.example" "local.properties.example"

# ── App module ─────────────────────────────────────────────────────────────────
# kiosk: plain Activity + XML layout. app: ComponentActivity + Compose. See
# CLAUDE.md's "Architecture: kiosk vs. app" for which shape fits a new project.
if [[ "$ARCHITECTURE" == "app" ]]; then
    render "app-build.gradle.kts.compose" "app/build.gradle.kts"
    render "MainActivity.kt.compose.tmpl" "app/src/main/kotlin/${PACKAGE_PATH}/MainActivity.kt"
    mkdir -p "app/src/main/kotlin/${PACKAGE_PATH}/ui/theme"
    render "Theme.kt.tmpl" "app/src/main/kotlin/${PACKAGE_PATH}/ui/theme/Theme.kt"
else
    render "app-build.gradle.kts" "app/build.gradle.kts"
    render "MainActivity.kt.tmpl" "app/src/main/kotlin/${PACKAGE_PATH}/MainActivity.kt"
    render "activity_main.xml" "app/src/main/res/layout/activity_main.xml"
fi
render "AndroidManifest.xml" "app/src/main/AndroidManifest.xml"
render "strings.xml" "app/src/main/res/values/strings.xml"
render "themes.xml" "app/src/main/res/values/themes.xml"
render "ic_launcher_background.xml" "app/src/main/res/drawable/ic_launcher_background.xml"
render "ic_launcher_foreground.xml" "app/src/main/res/drawable/ic_launcher_foreground.xml"
render "ic_launcher.xml" "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml"
render "ic_launcher_round.xml" "app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml"

# ── GitHub workflow: release.yml ──────────────────────────────────────────────
render "release.yml" ".github/workflows/release.yml"

# ── Gradle wrapper ─────────────────────────────────────────────────────────────
if [[ ! -f gradlew ]]; then
    if command -v gradle >/dev/null 2>&1; then
        gradle wrapper --gradle-version "${GRADLE_VERSION}"
        echo "  [create] gradlew, gradlew.bat, gradle/wrapper/"
    else
        echo "  [skip]   gradlew — 'gradle' not on PATH; run 'gradle wrapper --gradle-version ${GRADLE_VERSION}' or open the project in Android Studio once to generate it"
    fi
fi

echo ""
echo "Done. Next steps:"
echo "  1. cp local.properties.example local.properties (adjust sdk.dir if needed)"
echo "  2. Review namespace/applicationId (${PACKAGE}) and SDK versions in app/build.gradle.kts"
echo "  3. Run 'make build' to verify the toolchain"
