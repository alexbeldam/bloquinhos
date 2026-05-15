#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: scripts/get-meta.sh <key>" >&2
    exit 2
fi

PYPROJECT="pyproject.toml"
ENV_FILE="environment.yml"

section_block() {
    local section="$1"
    awk -v section="[$section]" '
        $0 == section { in_section = 1; next }
        /^\[[^]]+\]/ { if (in_section) exit }
        in_section { print }
    ' "$PYPROJECT"
}

read_scalar() {
    local section="$1"
    local key="$2"
    local default="${3-}"

    local value
    value="$(section_block "$section" | sed -n "s/^[[:space:]]*$key[[:space:]]*=[[:space:]]*\"\([^\"]*\)\"[[:space:]]*$/\1/p" | head -n 1)"
    if [[ -n "$value" ]]; then
        printf '%s\n' "$value"
    else
        printf '%s\n' "$default"
    fi
}

read_env_name() {
    sed -n 's/^name:[[:space:]]*//p' "$ENV_FILE" | head -n 1
}

title_from_app_id() {
    local app_id="$1"
    printf '%s\n' "$app_id" | tr '-' ' ' | awk '{
        for (i = 1; i <= NF; i++) {
            $i = toupper(substr($i,1,1)) tolower(substr($i,2))
        }
        print
    }'
}

extract_people_array() {
    local key="$1"
    section_block "project" | awk -v key="$key" '
        $0 ~ "^[[:space:]]*" key "[[:space:]]*=[[:space:]]*\\[" { in_array = 1; next }
        in_array && $0 ~ "^[[:space:]]*\\]" { exit }
        in_array { print }
    '
}

maintainer_line() {
    local rows
    rows="$(extract_people_array "maintainers")"
    if [[ -z "$rows" ]]; then
        rows="$(extract_people_array "authors")"
    fi

    local out=""
    while IFS= read -r row; do
        [[ -z "$row" ]] && continue
        local name email entry
        name="$(printf '%s\n' "$row" | sed -n 's/.*name[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p')"
        email="$(printf '%s\n' "$row" | sed -n 's/.*email[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p')"

        if [[ -n "$name" && -n "$email" ]]; then
            entry="$name <$email>"
        elif [[ -n "$name" ]]; then
            entry="$name"
        elif [[ -n "$email" ]]; then
            entry="$email"
        else
            continue
        fi

        if [[ -n "$out" ]]; then
            out+=", "
        fi
        out+="$entry"
    done <<< "$rows"

    printf '%s\n' "$out"
}

APP_ID="$(read_scalar "project" "name")"
APP_DISPLAY="$(read_scalar "tool.bloquinhos" "display_name")"
if [[ -z "$APP_DISPLAY" ]]; then
    APP_DISPLAY="$(title_from_app_id "$APP_ID")"
fi

case "$1" in
    env_name)
        read_env_name
        ;;
    app_id)
        printf '%s\n' "$APP_ID"
        ;;
    app_display)
        printf '%s\n' "$APP_DISPLAY"
        ;;
    version)
        read_scalar "project" "version"
        ;;
    maintainer_line)
        maintainer_line
        ;;
    vendor)
        read_scalar "tool.bloquinhos.packaging" "vendor"
        ;;
    deb_arch)
        read_scalar "tool.bloquinhos.packaging.variants" "linux_deb_arch" "amd64"
        ;;
    rpm_arch)
        read_scalar "tool.bloquinhos.packaging.variants" "linux_rpm_arch" "x86_64"
        ;;
    windows_arch)
        read_scalar "tool.bloquinhos.packaging.variants" "windows_arch" "x64"
        ;;
    *)
        echo "unknown key: $1" >&2
        exit 2
        ;;
esac