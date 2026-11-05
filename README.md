# feather-launcher

[![CI](https://github.com/danpozmanter/feather-launcher/actions/workflows/ci.yml/badge.svg)](https://github.com/danpozmanter/feather-launcher/actions/workflows/ci.yml)
[![Docs](https://github.com/danpozmanter/feather-launcher/actions/workflows/docs.yml/badge.svg)](https://github.com/danpozmanter/feather-launcher/actions/workflows/docs.yml)

**[Documentation](https://danpozmanter.github.io/feather-launcher/)** | **[Releases](https://github.com/danpozmanter/feather-launcher/releases)**

A background run box for Linux, in the spirit of KRunner, written in
[Gossamer](https://github.com/gossamer-lang/gossamer) on gui-gos. Press
**Ctrl+Space**, type a few letters of an application's name, press **Enter**.

```sh
gos build --release .         # target/release/feather-launcher
./install.sh                  # build and install into ~/.local (no sudo)
feather-launcher --daemon     # start hidden, detached from the terminal
```

Requires libdbus; building requires Gossamer 0.76.0+. The release builds need
glibc 2.39+ (Ubuntu 24.04, Fedora 40, Debian 13).
`install.sh` also takes `--no-build` and `--prefix /absolute/path`; it does not
start Feather or enable autostart.

## Usage

| Key | Action |
|---|---|
| Ctrl+Space | Show or hide the launcher |
| Enter | Launch the highlighted entry, or the best match |
| Escape / click elsewhere | Hide the launcher |
| Ctrl+Shift+Q | Quit Feather |

- Search matches the text whole, anywhere in an application's name, ignoring
  case: `rite` finds LibreOffice Writer, `lit` does not. Names starting with
  the text come first. Generic names and keywords match too. Launches are not
  remembered.
- A command line runs a program from `PATH` with its arguments:
  `waftty --drop-down`. Words split like a shell's, with quotes, backslashes,
  and `~`, but nothing is sent to a shell: no variables, globs, or pipes.
- The catalog and icons rebuild in the background whenever a desktop entry
  under the XDG application folders changes.
- One instance runs per user; starting it again shows the existing one.
- The settings icon left of the entry box rebinds both shortcuts live and
  sets the run box's font, font size, theme (system, light or dark), icons,
  and highlight color. Settings are kept between runs; Reset to Defaults
  brings them all back.

## Platform notes

- Feather runs on X11 or Wayland, with only that session's libraries
  installed. On X11 it grabs its shortcut itself. On Wayland the compositor
  owns global keys: KDE's shortcut service assigns it, and elsewhere the
  desktop portal does (GNOME 48+, Hyprland), which may ask you to confirm.
  Where neither exists, bind `feather-launcher` to a key in your desktop's
  keyboard settings: a second launch shows the running instance.
- On KDE, Feather removes conflicting desktop shortcuts for its launch key
  (persistently). Other applications' X11 grabs cannot be replaced, and
  Feather reports the failure.

## Testing

```sh
gos test .
SDL_VIDEO_DRIVER=offscreen ./target/release/feather-launcher --fixture
gos run e2e/src/main.gos instance    # concurrency and crash recovery
gos run e2e/src/main.gos daemon      # --daemon behavior (--x11 for focus checks)
gos run e2e/src/main.gos focus       # X11 focus and stacking (needs libXtst)
gos run e2e/src/main.gos shortcuts   # X11 shortcut recording (needs libXtst)
gos run e2e/src/main.gos wayland     # KDE and portal shortcuts on Wayland (mocked)
```

Stop any running Feather before the end-to-end checks. The Wayland check
needs dbus-daemon and PyGObject for its mock desktop services.
