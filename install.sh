#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./install.sh [--prefix PATH] [--no-build]

Build and install Feather on Linux. Defaults to ~/.local/bin and
${XDG_DATA_HOME:-~/.local/share}/applications, without requiring sudo.

  --prefix PATH  Install into PATH/bin and PATH/share/applications instead
  --no-build     Install the existing target/release/feather-launcher binary
  -h, --help     Show this help

Building requires Gossamer; dependencies are fetched as pinned in project.lock.
Does not start Feather or enable login autostart.
EOF
}

fail() { printf 'install.sh: %s\n' "$*" >&2; exit 1; }

[[ $(uname -s) == Linux ]] || fail 'Only Linux is supported.'
prefix="$HOME/.local"
data_dir="${XDG_DATA_HOME:-$HOME/.local/share}"
build=true
while (($#)); do
    case "$1" in
        --prefix)
            (($# >= 2)) || fail '--prefix requires an absolute path.'
            prefix="$2"
            data_dir="$prefix/share"
            shift 2
            ;;
        --no-build) build=false; shift ;;
        -h|--help) usage; exit 0 ;;
        *) fail "Unknown option: $1 (see --help)." ;;
    esac
done
for directory in "$prefix" "$data_dir"; do
    [[ $directory == /* ]] || fail "Install paths must be absolute: $directory"
    [[ $directory != *$'\n'* && $directory != *$'\r'* && $directory != *$'\t'* ]] ||
        fail 'Install paths cannot contain control characters.'
done

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if "$build"; then
    command -v gos >/dev/null || fail 'Gossamer (gos) is required to build. Use --no-build with an existing release binary.'
    gos build --release "$source_dir"
fi
source_binary="$source_dir/target/release/feather-launcher"
[[ -x $source_binary ]] || fail "Release executable not found: $source_binary"

bin_dir="$prefix/bin"
applications="$data_dir/applications"
binary="$bin_dir/feather-launcher"
desktop="$applications/dev.gossamer.feather-launcher.desktop"
icons="$data_dir/icons/hicolor/scalable/apps"
install -d -- "$bin_dir" "$applications" "$icons"
temporary_binary=$(mktemp "$bin_dir/.feather-launcher.XXXXXX")
temporary_desktop=''
trap 'rm -f -- "$temporary_binary" "${temporary_desktop:-}"' EXIT
temporary_desktop=$(mktemp "$applications/.feather-launcher.XXXXXX")

# Quote the Exec argument, then escape backslashes for the desktop file itself.
exec_path=${binary//\\/\\\\}
exec_path=${exec_path//\"/\\\"}
exec_path=${exec_path//\$/\\\$}
exec_path=${exec_path//\`/\\\`}
exec_path=${exec_path//\\/\\\\}
exec_path=${exec_path//%/%%}
cat > "$temporary_desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Feather
Comment=Start an installed application by name
Exec=/usr/bin/env "$exec_path"
Icon=dev.gossamer.feather-launcher
Terminal=false
Categories=Utility;
StartupNotify=false
EOF
chmod 644 "$temporary_desktop"
install -m 755 -- "$source_binary" "$temporary_binary"
# Rename a new inode into place so updating a running executable also works.
mv -f -- "$temporary_binary" "$binary"
mv -f -- "$temporary_desktop" "$desktop"
install -m 644 -- "$source_dir/src/assets/feather-launcher.svg" "$icons/dev.gossamer.feather-launcher.svg"
if command -v gtk-update-icon-cache >/dev/null && [[ -f $data_dir/icons/hicolor/index.theme ]]; then
    gtk-update-icon-cache -q "$data_dir/icons/hicolor" || printf 'Could not refresh the icon cache.\n' >&2
fi
if command -v update-desktop-database >/dev/null; then
    update-desktop-database "$applications" || printf 'Could not refresh the desktop application cache.\n' >&2
fi

printf 'Installed %s\nDesktop entry: %s\n' "$binary" "$desktop"
case ":$PATH:" in
    *":$bin_dir:"*) ;;
    *) printf 'Add %s to your PATH to run feather-launcher by name.\n' "$bin_dir" ;;
esac
printf 'To start in the background: "%s" --daemon\nQuit any older running copy first to use the new version.\n' "$binary"
