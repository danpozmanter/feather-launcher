# Changelog

## 0.3.1 - whole-text search and best-match selection

- Search matches what you type whole, anywhere in a name and ignoring case,
  instead of letters scattered through it: `rite` finds LibreOffice Writer and
  `lit` does not. Names starting with the text come first, then names with a
  word starting with it.
- The best match is selected as you type, instead of a result picked during
  an earlier search staying selected further down the list.

## 0.3.0 - appearance settings

- Settings chooses the run box's font and font size, the theme (system, light
  or dark), whether application icons show, and the highlight color around the
  run box, on the selected result and on buttons.
- Reset to Defaults in Settings brings back every setting, the shortcuts
  included.
- Settings, the shortcuts among them, are kept between runs.
- A larger font grows the run box and its window; the results keep their size.
- Require Gossamer 0.76.0 or later to build.

## 0.2.0 - commands & arguments support

- Run commands from the run box: a program on `PATH`, or an absolute or `~/`
  path, with arguments (`waftty --drop-down`). Quotes and backslashes group
  words; nothing goes through a shell.

## 0.1.1

- Require Gossamer 0.75.17 or later to build.

## 0.1.0

- Initial release.
