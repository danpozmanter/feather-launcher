# Installation

Feather runs on Linux, on X11 or Wayland, and needs libdbus.

## From source

Building Feather needs [Gossamer](https://github.com/gossamer-lang/gossamer)
0.75.16 or later; `gos build` fetches the GUI libraries pinned in `project.lock`.

```sh
git clone https://github.com/danpozmanter/feather-launcher
cd feather-launcher
./install.sh
```

`install.sh` builds a release binary and installs it into `~/.local/bin`, with a
desktop entry in `${XDG_DATA_HOME:-~/.local/share}/applications`. No sudo is
needed. Make sure `~/.local/bin` is on your `PATH`.

| Option | Effect |
|---|---|
| `--no-build` | Install an existing release build |
| `--prefix /absolute/path` | Install under a different prefix |

The installer does not start Feather or enable autostart. To start it hidden
at login, add `feather-launcher --daemon` to your desktop's autostart
programs.

To build without installing:

```sh
gos build --release .
./target/release/feather-launcher
```
