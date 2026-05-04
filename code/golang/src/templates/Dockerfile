FROM golang:1.25-alpine AS builder
ARG APPLICATION={{APPLICATION}}
ARG VERSION=dev
ARG REVISION=local
ARG BUILD_RFC3339=1970-01-01T00:00:00Z

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .

RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build \
    -ldflags "-s -w \
      -X main.version=${VERSION} \
      -X main.revision=${REVISION} \
      -X main.buildRFC3339=${BUILD_RFC3339}" \
    -o /bin/${APPLICATION} \
    ./cmd/${APPLICATION}/main.go

FROM scratch
ARG APPLICATION={{APPLICATION}}
COPY --from=builder /bin/${APPLICATION} /bin/${APPLICATION}
USER 10001
ENTRYPOINT ["/bin/${APPLICATION}"]
