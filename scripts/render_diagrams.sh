#!/usr/bin/env bash
set -euo pipefail

npx --yes @mermaid-js/mermaid-cli -i docs/architecture.mmd -o docs/architecture.svg
