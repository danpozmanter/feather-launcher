# User Guide

## Starting

`feather-launcher` opens the run box, or shows the copy that is already
running: one instance runs per user. `feather-launcher --daemon` starts it
hidden, detached from the terminal.

## Keys

| Key | Action |
|---|---|
| ++ctrl+space++ | Show or hide the launcher |
| ++enter++ | Start the highlighted entry, or the best match |
| ++up++ / ++down++ | Move through the results |
| ++escape++ | Hide the launcher (a click elsewhere also hides it) |
| ++ctrl+shift+q++ | Quit Feather |

## Searching

Matching keeps the order of the letters you type: `ml` finds Mail, `li` does
not. Names, generic names such as "Web Browser", and keywords all match.
When you add, remove, or edit an application, Feather picks up the change the
next time the box opens.

## Running commands

Type a command line to run a program directly, arguments included:
`waftty --drop-down`. Feather looks the program up on `PATH` (an absolute
path or `~/...` also works) and proposes the command line above every
application; ++enter++ runs it.

A single word with no arguments is an application name first: `firefox`
starts the Firefox entry, and the program of that name is offered last in
the list. When no application matches, ++enter++ runs the program.

The text is split into words the way a shell splits them: single quotes keep
text as typed, double quotes group words (a backslash escapes `"`, `\`, `$`,
and `` ` `` inside them), a backslash keeps the next character, and a leading
`~` is your home folder. Nothing else a shell does happens: no variables,
globs, pipes, or redirection. Run `sh -c '...'` when you want those.

## Settings

Click the gear to the left of the entry box. **Change...** records a new
launch or quit shortcut: press the combination, then **Set** or ++enter++.
**Clear**, then **Set**, switches a shortcut off. Changes apply immediately.

!!! note "Desktop shortcuts"
    On X11, Feather grabs its shortcut itself. On Wayland, KDE's shortcut
    service or the desktop portal (GNOME 48+, Hyprland) assigns it, and the
    desktop may ask you to confirm the key. Where neither exists, bind
    `feather-launcher` to a key in your desktop's keyboard settings. On KDE,
    Feather removes a conflicting desktop shortcut for its launch key, keeping
    the action's other shortcuts.
