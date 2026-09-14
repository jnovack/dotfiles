SDK            := /opt/homebrew/share/android-commandlinetools
ADB            := $(SDK)/platform-tools/adb
JAVA_HOME      := /opt/homebrew/opt/openjdk@17
GRADLEW        := JAVA_HOME=$(JAVA_HOME) ./gradlew
PACKAGE        := {{PACKAGE}}
SCREENSHOT_DIR := .local/screenshots

.PHONY: help build install launch deploy devices uninstall logcat clean pair connect screenshot

help: ## Show available targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

build: ## Build the debug APK
	$(GRADLEW) :app:assembleDebug

install: ## Build and install the debug APK on the connected phone
	$(GRADLEW) :app:installDebug

launch: ## Launch the app on the phone
	$(ADB) shell monkey -p $(PACKAGE) -c android.intent.category.LAUNCHER 1

deploy: install launch ## Install and launch in one step

devices: ## List connected ADB devices
	$(ADB) devices -l

pair: ## Pair a phone for wireless ADB (make pair ADDR=<ip:port from the phone's "Pair device with pairing code" screen>; then enter the 6-digit code when prompted)
	@test -n "$(ADDR)" || { echo "Usage: make pair ADDR=<ip:port from the phone's pairing screen>"; exit 1; }
	$(ADB) pair $(ADDR)

connect: ## Connect to the phone over wireless ADB (make connect ADDR=<ip:port>)
	@test -n "$(ADDR)" || { echo "Usage: make connect ADDR=<ip:port>"; exit 1; }
	$(ADB) connect $(ADDR)

uninstall: ## Remove the app from the phone
	$(ADB) uninstall $(PACKAGE)

logcat: ## Tail the app's logs from the phone
	$(ADB) logcat --pid=$$($(ADB) shell pidof -s $(PACKAGE))

clean: ## Clean the Gradle build
	$(GRADLEW) clean

screenshot: ## Capture a screenshot from the phone into .local/screenshots
	@mkdir -p $(SCREENSHOT_DIR)
	$(ADB) shell screencap -p /sdcard/${PACKAGE}-screenshot.png
	$(ADB) pull /sdcard/${PACKAGE}-screenshot.png $(SCREENSHOT_DIR)/$$(date +%Y%m%d-%H%M%S).png
	$(ADB) shell rm /sdcard/${PACKAGE}-screenshot.png
