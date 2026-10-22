FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod *.go ./
RUN go mod tidy && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /notifier .

FROM alpine:3.20
RUN apk add --no-cache ca-certificates tzdata
COPY --from=build /notifier /notifier
USER nobody
ENTRYPOINT ["/notifier"]
