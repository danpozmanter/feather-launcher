#!/usr/bin/env python3
"""Mock desktop shortcut services on a private session bus.

This stays in Python while the checks are Gossamer: GLib's D-Bus stack is
independent of Feather's own libdbus client (src/bus.gos), so a mistake in
how Feather encodes or decodes a message cannot be mirrored here and pass.

`kde` serves org.kde.kglobalaccel; `portal` serves the desktop portal's
GlobalShortcuts and host Registry. Every call is appended to LOG as a JSON
line. The org.feather.Test interface at /test lets a test send the signals a
real desktop sends when the user presses the shortcut.

Usage: desktop_mock.py kde|portal LOG
"""
import json
import sys

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

CTRL_SPACE = 0x04000020
# A key the mock KDE refuses to assign, standing in for one KWin reserves.
REFUSED = 0x0C00003B  # Ctrl+Alt+F12

KDE_XML = """
<node>
  <interface name="org.kde.KGlobalAccel">
    <method name="doRegister"><arg type="as" direction="in"/></method>
    <method name="getComponent"><arg type="s" direction="in"/><arg type="o" direction="out"/></method>
    <method name="setShortcutKeys">
      <arg type="as" direction="in"/><arg type="a(ai)" direction="in"/><arg type="u" direction="in"/>
      <arg type="a(ai)" direction="out"/>
    </method>
    <method name="setInactive"><arg type="as" direction="in"/></method>
    <method name="unregister">
      <arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="b" direction="out"/>
    </method>
    <method name="action"><arg type="i" direction="in"/><arg type="as" direction="out"/></method>
    <method name="shortcutKeys"><arg type="as" direction="in"/><arg type="a(ai)" direction="out"/></method>
    <method name="setForeignShortcutKeys"><arg type="as" direction="in"/><arg type="a(ai)" direction="in"/></method>
    <signal name="yourShortcutsChanged"><arg type="as"/><arg type="a(ai)"/></signal>
  </interface>
</node>
"""

COMPONENT_XML = """
<node>
  <interface name="org.kde.kglobalaccel.Component">
    <signal name="globalShortcutPressed"><arg type="s"/><arg type="s"/><arg type="x"/></signal>
    <signal name="globalShortcutReleased"><arg type="s"/><arg type="s"/><arg type="x"/></signal>
  </interface>
</node>
"""

PORTAL_XML = """
<node>
  <interface name="org.freedesktop.portal.GlobalShortcuts">
    <method name="CreateSession"><arg type="a{sv}" direction="in"/><arg type="o" direction="out"/></method>
    <method name="BindShortcuts">
      <arg type="o" direction="in"/><arg type="a(sa{sv})" direction="in"/><arg type="s" direction="in"/>
      <arg type="a{sv}" direction="in"/><arg type="o" direction="out"/>
    </method>
    <signal name="Activated"><arg type="o"/><arg type="s"/><arg type="t"/><arg type="a{sv}"/></signal>
    <signal name="Deactivated"><arg type="o"/><arg type="s"/><arg type="t"/><arg type="a{sv}"/></signal>
  </interface>
  <interface name="org.freedesktop.host.portal.Registry">
    <method name="Register"><arg type="s" direction="in"/><arg type="a{sv}" direction="in"/></method>
  </interface>
</node>
"""

REQUEST_XML = """
<node>
  <interface name="org.freedesktop.portal.Request">
    <signal name="Response"><arg type="u"/><arg type="a{sv}"/></signal>
  </interface>
  <interface name="org.freedesktop.portal.Session">
    <method name="Close"/>
  </interface>
</node>
"""

TEST_XML = """
<node>
  <interface name="org.feather.Test">
    <method name="Press"><arg type="s" direction="in"/></method>
    <method name="Rebind"><arg type="i" direction="in"/></method>
  </interface>
</node>
"""


class Mock:
    def __init__(self, kind, log):
        self.kind = kind
        self.log = log
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION)
        self.released = False
        self.session = None
        self.registered = []
        self.loop = GLib.MainLoop()

    def record(self, method, args):
        with open(self.log, "a") as out:
            out.write(json.dumps([method, args]) + "\n")

    def serve(self, path, xml, handler):
        for info in Gio.DBusNodeInfo.new_for_xml(xml).interfaces:
            self.registered.append(self.bus.register_object(path, info, handler, None, None))

    def emit(self, path, interface, member, signature, args):
        self.bus.emit_signal(None, path, interface, member, GLib.Variant(signature, args))

    def kde_call(self, conn, sender, path, iface, method, params, invocation):
        args = params.unpack()
        self.record(method, args)
        if method == "getComponent":
            reply = GLib.Variant("(o)", ("/component/" + args[0].replace("-", "_"),))
        elif method == "setShortcutKeys":
            keys = [k for k in args[1] if k[0][0] != REFUSED]
            reply = GLib.Variant("(a(ai))", (keys,))
        elif method == "action":
            owner = [] if self.released or args[0] != CTRL_SPACE else ["test", "action", "Test", "Action"]
            reply = GLib.Variant("(as)", (owner,))
        elif method == "shortcutKeys":
            reply = GLib.Variant("(a(ai))", ([([CTRL_SPACE, 0, 0, 0],), ([777, 888, 0, 0],)],))
        elif method == "setForeignShortcutKeys":
            self.released = True
            reply = None
        elif method == "unregister":
            reply = GLib.Variant("(b)", (True,))
        else:
            reply = None
        invocation.return_value(reply)

    def portal_call(self, conn, sender, path, iface, method, params, invocation):
        args = params.unpack()
        self.record(method, args)
        unique = sender[1:].replace(".", "_")
        if method == "CreateSession":
            request = f"/org/freedesktop/portal/desktop/request/{unique}/{args[0]['handle_token']}"
            self.session = f"/org/freedesktop/portal/desktop/session/{unique}/{args[0]['session_handle_token']}"
            self.serve(self.session, REQUEST_XML, self.portal_call)
            invocation.return_value(GLib.Variant("(o)", (request,)))
            results = {"session_handle": GLib.Variant("s", self.session)}
            GLib.idle_add(self.respond, request, results)
        elif method == "BindShortcuts":
            request = f"/org/freedesktop/portal/desktop/request/{unique}/{args[3]['handle_token']}"
            invocation.return_value(GLib.Variant("(o)", (request,)))
            shortcuts = [(sid, {"description": GLib.Variant("s", props["description"]),
                                "trigger_description": GLib.Variant("s", props["preferred_trigger"])})
                         for sid, props in args[1]]
            GLib.idle_add(self.respond, request, {"shortcuts": GLib.Variant("a(sa{sv})", shortcuts)})
        else:
            if method == "Close":
                self.session = None
            invocation.return_value(None)

    def respond(self, request, results):
        self.emit(request, "org.freedesktop.portal.Request", "Response", "(ua{sv})", (0, results))
        return False

    def test_call(self, conn, sender, path, iface, method, params, invocation):
        args = params.unpack()
        if method == "Press" and self.kind == "kde":
            component = "/component/feather_launcher"
            for member in ("globalShortcutPressed", "globalShortcutReleased"):
                self.emit(component, "org.kde.kglobalaccel.Component", member, "(ssx)",
                          ("feather-launcher", "launch", 1))
        elif method == "Press" and self.session:
            options = {"activation_token": GLib.Variant("s", args[0])} if args[0] else {}
            for member in ("Activated", "Deactivated"):
                self.emit("/org/freedesktop/portal/desktop", "org.freedesktop.portal.GlobalShortcuts",
                          member, "(osta{sv})", (self.session, "launch", 1, options))
        elif method == "Rebind":
            action = ["feather-launcher", "launch", "Feather", "Show Feather"]
            self.emit("/kglobalaccel", "org.kde.KGlobalAccel", "yourShortcutsChanged", "(asa(ai))",
                      (action, [([args[0], 0, 0, 0],)]))
        invocation.return_value(None)

    def run(self):
        self.serve("/test", TEST_XML, self.test_call)
        if self.kind == "kde":
            self.serve("/kglobalaccel", KDE_XML, self.kde_call)
            self.serve("/component/feather_launcher", COMPONENT_XML, self.kde_call)
            name = "org.kde.kglobalaccel"
        else:
            self.serve("/org/freedesktop/portal/desktop", PORTAL_XML, self.portal_call)
            name = "org.freedesktop.portal.Desktop"
        Gio.bus_own_name_on_connection(self.bus, name, Gio.BusNameOwnerFlags.NONE,
                                       lambda *_: print("ready", flush=True), None)
        self.loop.run()


if __name__ == "__main__":
    Mock(sys.argv[1], sys.argv[2]).run()
