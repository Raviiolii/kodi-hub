# -*- coding: utf-8 -*-
# Kubo Updater - pulsa "Actualizar" o abre el addon para mas opciones.
import os
import sys
import json
import time
import shutil
import zipfile
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()
BASE = "https://raw.githubusercontent.com/Raviiolii/kubo/main"
VERSION_URL = BASE + "/config/version.json"  # + cache buster en runtime
PROFILE = xbmcvfs.translatePath("special://profile")
STATE_DIR = os.path.join(PROFILE, "addon_data", "plugin.program.kubo")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
BACKUP_DIR = os.path.join(STATE_DIR, "backups")


def log(msg):
    xbmc.log("[kubo] {}".format(msg), xbmc.LOGINFO)


def notify(msg, icon=xbmcgui.NOTIFICATION_INFO, ms=6000):
    xbmcgui.Dialog().notification("Kubo", msg, icon, ms)


def http_get(url, timeout=30):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "kodi-kubo"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": "0.0.0"}


def save_state(data):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def remote_info():
    return json.loads(http_get(VERSION_URL + "?t=" + str(int(time.time()))).decode("utf-8"))


def is_newer(remote, local):
    try:
        r = [int(x) for x in str(remote).split(".")]
        l = [int(x) for x in str(local).split(".")]
        return r > l
    except Exception:
        return remote != local


def merge_favourites(path, remove_names=None):
    """Agrega entradas nuevas sin borrar las existentes; quita las retiradas."""
    try:
        new = ET.parse(path).getroot()
    except Exception:
        return
    target = os.path.join(PROFILE, "favourites.xml")
    if not os.path.exists(target):
        shutil.copy(path, target)
        return
    try:
        tree = ET.parse(target)
        root = tree.getroot()
        removed = 0
        if remove_names:
            for f in list(root.findall("favourite")):
                if f.get("name") in remove_names:
                    root.remove(f)
                    removed += 1
        names = {f.get("name") for f in root.findall("favourite")}
        added = 0
        for f in new.findall("favourite"):
            if f.get("name") not in names:
                root.append(f)
                added += 1
        if added or removed:
            tree.write(target, encoding="utf-8", xml_declaration=True)
            log("favoritos: +{} -{}".format(added, removed))
    except Exception as e:
        log("no se pudo fusionar favoritos: {}".format(e))


def apply_settings(data):
    """Aplica ajustes (p. ej. idioma de audio/subtitulos) via JSON-RPC local. Best-effort."""
    settings = (data or {}).get("settings") or {}
    if not settings:
        return
    import urllib.request
    for key, value in settings.items():
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "Settings.SetSettingValue",
                           "params": {"setting": key, "value": value}}).encode()
        try:
            req = urllib.request.Request("http://127.0.0.1:8080/jsonrpc", data=body,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5).read()
        except Exception as e:
            log("ajuste {} no aplicado: {}".format(key, e))


def apply_pack(zip_path, version):
    tmp = os.path.join(STATE_DIR, "tmp_pack")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(tmp)
    count = 0
    pack_meta = {}
    try:
        with open(os.path.join(tmp, "pack.json"), "r", encoding="utf-8") as f:
            pack_meta = json.load(f)
    except Exception:
        pass
    remove_favs = pack_meta.get("remove_favourites") or []
    for root, _dirs, files in os.walk(tmp):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, tmp)
            if rel.split(os.sep)[0] != "userdata":
                continue                      # pack.json y otros: se ignoran
            rel = os.path.join(*rel.split(os.sep)[1:])
            dest = os.path.join(PROFILE, rel)
            if rel == "favourites.xml":
                merge_favourites(full, remove_favs)
                count += 1
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if os.path.exists(dest):
                bkp = os.path.join(BACKUP_DIR, time.strftime("%Y%m%d-%H%M%S"), rel)
                os.makedirs(os.path.dirname(bkp), exist_ok=True)
                shutil.copy(dest, bkp)
            shutil.copy(full, dest)
            count += 1
    shutil.rmtree(tmp, ignore_errors=True)
    apply_settings(pack_meta)
    save_state({"version": version, "applied": time.strftime("%Y-%m-%d %H:%M")})
    log("paquete {} aplicado ({} archivos)".format(version, count))
    return count


def do_update(cfg=None):
    dialog = xbmcgui.Dialog()
    try:
        info = cfg or remote_info()
    except Exception as e:
        notify("No se pudo consultar el servidor: {}".format(e), xbmcgui.NOTIFICATION_ERROR)
        return
    state = load_state()
    remote_v = info.get("version", "0")
    if not is_newer(remote_v, state.get("version", "0.0.0")):
        if cfg is None:
            notify("Ya estas al dia (v{})".format(state.get("version")))
        return
    if cfg is None and not dialog.yesno("Kubo", "Nueva version {} disponible.\n\n{}".format(
            remote_v, info.get("notes", "")), yeslabel="Actualizar", nolabel="Ahora no"):
        return
    pack_url = BASE + "/" + info.get("file", "config/hubconfig-{}.zip".format(remote_v))
    tmp_zip = os.path.join(STATE_DIR, "update.zip")
    os.makedirs(STATE_DIR, exist_ok=True)
    try:
        data = http_get(pack_url + "?t=" + str(int(time.time())), timeout=60)
        with open(tmp_zip, "wb") as f:
            f.write(data)
        n = apply_pack(tmp_zip, remote_v)
    except Exception as e:
        notify("Fallo la actualizacion: {}".format(e), xbmcgui.NOTIFICATION_ERROR)
        return
    if xbmc.getCondVisibility("System.Platform.Android"):
        # En Android RestartApp cierra la app sin relanzarla: avisamos y se aplica al reabrir.
        notify("Hub actualizado a v{}. Cierra y abre Kodi para aplicar.".format(remote_v))
    else:
        notify("Hub actualizado a v{} ({} archivos). Reiniciando...".format(remote_v, n))
        xbmc.sleep(1500)
        xbmc.executebuiltin("RestartApp")


def status():
    st = load_state()
    try:
        r = remote_info()
        msg = "Instalado: v{}\nServidor: v{}\n{}".format(st.get("version", "?"), r.get("version", "?"),
                                                        r.get("notes", ""))
    except Exception as e:
        msg = "Instalado: v{}\nServidor inaccesible: {}".format(st.get("version", "?"), e)
    xbmcgui.Dialog().textviewer("Kubo", msg)


def main():
    handle = int(sys.argv[1])
    args = sys.argv[2] if len(sys.argv) > 2 else ""
    if "action=update" in args:
        do_update()
        xbmcplugin.endOfDirectory(handle)
        return
    if "action=force" in args:          # admin: aplica sin preguntar
        do_update(remote_info())
        xbmcplugin.endOfDirectory(handle)
        return
    if "action=status" in args:
        status()
        xbmcplugin.endOfDirectory(handle)
        return
    # menu
    st = load_state()
    items = [
        ("Actualizar hub ahora", "action=update", "Descarga y aplica la ultima version"),
        ("Estado".format(), "action=status", "Version instalada vs. servidor"),
    ]
    for label, action, info in items:
        li = xbmcgui.ListItem(label=label)
        li.setInfo("video", {"plot": info})
        xbmcplugin.addDirectoryItem(handle, "{}?{}".format(sys.argv[0], action), li, isFolder=False)
    xbmcplugin.setContent(handle, "files")
    xbmcplugin.endOfDirectory(handle)


if __name__ == "__main__":
    main()
