include scripts/variables.mk

GOOS   ?= $(shell go env GOOS)
GOARCH ?= $(shell go env GOARCH)

.PHONY: build test test-race test-cover vet clean debug-variables

build:
	CGO_ENABLED=0 GOOS=$(GOOS) GOARCH=$(GOARCH) \
	    go build -ldflags "$(GO_LDFLAGS)" \
	    -o bin/$(APPLICATION) \
	    ./cmd/$(APPLICATION)/main.go

test:
	go test ./...

test-race:
	go test -race ./...

test-cover:
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

vet:
	go vet ./...

clean:
	rm -rf bin/ coverage.out coverage.html

debug-variables:
	@echo "APPLICATION   = $(APPLICATION)"
	@echo "VERSION       = $(VERSION)"
	@echo "REVISION      = $(REVISION)"
	@echo "BUILD_RFC3339 = $(BUILD_RFC3339)"
	@echo "GOOS          = $(GOOS)"
	@echo "GOARCH        = $(GOARCH)"
