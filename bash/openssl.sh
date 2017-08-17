#!/bin/bash

generate_self_signed_cert() {
    openssl req -sha256 -nodes -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 3650
}
