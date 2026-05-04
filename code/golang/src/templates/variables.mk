APPLICATION   ?= $(shell basename $(CURDIR))
VERSION       ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
REVISION      ?= $(shell git rev-parse HEAD 2>/dev/null || echo "local")
BUILD_RFC3339 ?= $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

GO_LDFLAGS := -s -w \
    -X main.version=$(VERSION) \
    -X main.revision=$(REVISION) \
    -X main.buildRFC3339=$(BUILD_RFC3339)
