#!/usr/bin/env bash
# Build Feather and package it into OUT (default dist) as
# feather-launcher-VERSION-linux-ARCH.tar.gz, with a .sha256 beside it:
#   bin/feather-launcher
#   share/applications/dev.gossamer.feather-launcher.desktop
#   share/icons/hicolor/scalable/apps/dev.gossamer.feather-launcher.svg
#   share/doc/feather-launcher/  licenses of what the binary carries
# Prints the archive's path.
#
# Usage: scripts/package.sh [OUT]
#
# GOS_LLVM_MCPU overrides the portable CPU baseline.
set -euo pipefail
umask 022

die() { echo "package.sh: $*" >&2; exit 1; }

[ "$(uname -s)" = Linux ] || die "Feather is packaged on Linux only"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$(mkdir -p "${1:-dist}" && cd "${1:-dist}" && pwd)"

# Reads KEY = "value" from a TOML file.
setting() {
    awk -F'"' -v key="$1" '$1 ~ "^" key " *= *$" { print $2; exit }' "$2"
}
version="$(setting version "$root/project.toml")"
name="$(setting name "$root/packaging.toml")"
app_id="$(setting app_id "$root/packaging.toml")"
comment="$(setting comment "$root/packaging.toml")"
categories="$(setting categories "$root/packaging.toml")"
for field in version name app_id comment categories; do
    [ -n "${!field}" ] || die "no $field in project.toml or packaging.toml"
done
exe=feather-launcher

case "$(uname -m)" in
    x86_64 | amd64) arch=x86_64 ;;
    arm64 | aarch64) arch=aarch64 ;;
    *) die "unsupported architecture: $(uname -m)" ;;
esac
base="$exe-$version-linux-$arch"

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

# A package runs on machines other than the one that built it, so its code
# assumes a CPU every supported machine has, not the builder's own.
if [ -z "${GOS_LLVM_MCPU:-}" ]; then
    if [ "$arch" = x86_64 ]; then export GOS_LLVM_MCPU=x86-64-v2; else export GOS_LLVM_MCPU=generic; fi
fi
(cd "$root" && gos fetch >/dev/null && gos build --release . --out-dir "$stage/build" >&2)
binary="$stage/build/$exe"
[ -x "$binary" ] || die "the build did not produce $binary"
if ldd "$binary" | grep -q "not found"; then
    die "unresolved native libraries: $(ldd "$binary" | grep "not found")"
fi
[ "$("$binary" --version)" = "$exe $version" ] || die "the build does not report version $version"

bundle="$stage/$base"
install -Dm755 "$binary" "$bundle/bin/$exe"
install -Dm644 "$root/src/assets/feather-launcher.svg" \
    "$bundle/share/icons/hicolor/scalable/apps/$app_id.svg"

# The binary embeds gui-gos's fonts and statically links SDL, so their licenses
# travel with it, beside the Apache-2.0 of the GUI libraries.
(cd "$root" && gos vendor --out "$stage/vendor" >/dev/null)
gui="$stage/vendor/github.com__gossamer-lang__gui-gos"
windowing="$stage/vendor/github.com__gossamer-lang__windowing-gos"
[ -d "$gui/licenses" ] || die "gos vendor did not produce $gui/licenses"
doc="$bundle/share/doc/$exe"
install -Dm644 -t "$doc" "$gui"/licenses/*
install -Dm644 "$windowing/LICENSE" "$doc/apache-2.0.txt"
printf '%s %s\nSDL 3 is statically linked and gui-gos fonts are embedded; see the accompanying licenses.\n' \
    "$name" "$version" > "$doc/README.txt"

desktop="$bundle/share/applications/$app_id.desktop"
mkdir -p "$(dirname "$desktop")"
cat > "$desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$name
Comment=$comment
Exec=$exe
Icon=$app_id
Terminal=false
Categories=$categories
StartupNotify=false
EOF
if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$desktop"
fi

archive="$out/$base.tar.gz"
tar -czf "$archive" -C "$stage" "$base"
(cd "$out" && sha256sum "$base.tar.gz" > "$base.tar.gz.sha256")
echo "$archive"
