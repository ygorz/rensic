#!/usr/bin/env bash
export NODE_INSTALLATION_VERSION=$(sed 's/^v//' "$(dirname "${BASH_SOURCE[0]}")/../.nvmrc")
export REPOSITORY_RID="ri.stemma.main.repository.9a581b2f-6dc7-45ee-b40b-48baf29375c0"
export REQUESTS_CA_BUNDLE=${SSL_CERT_FILE} # Used by the Python requests module
