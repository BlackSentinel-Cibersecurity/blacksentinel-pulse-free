#!/usr/bin/env bash
# Create (or complete) the .env that docker compose reads for this edition,
# filling every secret with a fresh random value. Nothing ships with a default
# secret: a value written in a public repository protects nothing.
#
#   ./scripts/init-env.sh            # run from anywhere; safe to run again
#
# It only fills keys that are missing, empty or still a placeholder, so values
# you set yourself are kept. The file is created with permissions 600 and is
# already in .gitignore. GitHub Codespaces runs this for you on first start.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.env"
EXAMPLE="$ROOT/.env.example"
# KEY:bytes — each becomes 2×bytes hex characters.
KEYS=(SECRET_KEY:32 ADMIN_PASSWORD:12)

rand_hex() {
  if command -v openssl >/dev/null 2>&1; then openssl rand -hex "$1"
  else head -c "$1" /dev/urandom | od -An -tx1 | tr -d ' \n'; fi
}

if [ ! -f "$ENV_FILE" ]; then
  mkdir -p "$(dirname "$ENV_FILE")"
  if [ -f "$EXAMPLE" ]; then cp "$EXAMPLE" "$ENV_FILE"; else : > "$ENV_FILE"; fi
  echo "Created ${ENV_FILE#"$ROOT"/}"
fi
chmod 600 "$ENV_FILE"

ADMIN_NEW=""
for spec in "${KEYS[@]}"; do
  key="${spec%%:*}"; bytes="${spec##*:}"
  current="$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d= -f2- | tr -d '"'"'" || true)"
  if [ -z "$current" ] || printf '%s' "$current" | grep -qiE 'change|your[-_]|example|placeholder|fallback|generate|super-secret|insecure|dev[-_]|[$][(]|^secret$|^password$'; then
    value="$(rand_hex "$bytes")"
    tmp="$(mktemp)"
    grep -vE "^${key}=" "$ENV_FILE" > "$tmp" || true
    printf '%s=%s\n' "$key" "$value" >> "$tmp"
    cat "$tmp" > "$ENV_FILE"; rm -f "$tmp"
    echo "  generated $key"
    [ "$key" = "ADMIN_PASSWORD" ] && ADMIN_NEW="$value"
  fi
done

if [ -n "$ADMIN_NEW" ]; then
  echo ""
  echo "  First admin password: $ADMIN_NEW"
  echo "  (also kept in ${ENV_FILE#"$ROOT"/} as ADMIN_PASSWORD; change it after you sign in)"
fi
echo "Secrets ready."
