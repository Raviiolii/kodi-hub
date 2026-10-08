# -*- coding: utf-8 -*-
# Servicio: al iniciar, avisa si hay una version nueva del hub.
import os
import json
import time

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()
BASE = "https://raw.githubusercontent.com/Raviiolii/kodi-hub/main"
VERSION_URL = BASE + "/config/version.json"


def log(msg):
    xbmc.log("[villahub-service] {}".format(msg), xbmc.LOGINFO)


def run():
    xbmc.sleep(20000)  # dejar que el hub cargue
    try:
        if ADDON.getSetting("auto_check") == "false":
            return
    except Exception:
        pass
    try:
        import urllib.request
        req = urllib.request.Request(VERSION_URL, headers={"User-Agent": "kodi-villahub"})
        with urllib.request.urlopen(req, timeout=20) as r:
            remote = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log("sin conexion: {}".format(e))
        return
    state_file = os.path.join(xbmcvfs.translatePath("special://profile/addon_data/plugin.program.villahub"),
                              "state.json")
    local = {"version": "0.0.0"}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            local = json.load(f)
    except Exception:
        pass

    def newer(a, b):
        try:
            return [int(x) for x in str(a).split(".")] > [int(x) for x in str(b).split(".")]
        except Exception:
            return str(a) != str(b)

    if newer(remote.get("version"), local.get("version")):
        xbmcgui.Dialog().notification(
            "VillaHub",
            "Actualizacion disponible: v{}".format(remote.get("version")),
            xbmcgui.NOTIFICATION_INFO, 8000)
        try:
            if ADDON.getSetting("auto_apply") == "true":
                xbmc.executebuiltin(
                    "RunPlugin(plugin://plugin.program.villahub/?action=update)")
        except Exception:
            pass


if __name__ == "__main__":
    monitor = xbmc.Monitor()
    run()
    while not monitor.abortRequested():
        if monitor.waitForAbort(3600):
            break
        run()
