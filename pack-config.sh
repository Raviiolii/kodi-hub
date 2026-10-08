#!/usr/bin/env bash
# Empaqueta la configuracion actual del hub como paquete de actualizacion.
# Uso: ./pack-config.sh 1.0.0 "notas de la version"
set -euo pipefail
cd "$(dirname "$0")"
VER="${1:?version requerida, ej: 1.0.0}"
NOTES="${2:-}"
KODI="$HOME/.var/app/tv.kodi.Kodi/data/userdata"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/userdata/addon_data/skin.arctic.zephyr.mod" \
         "$STAGE/userdata/addon_data/script.skinshortcuts"

# 1) configuracion viva del skin + menu (skinshortcuts)
for f in "addon_data/skin.arctic.zephyr.mod/settings.xml" "addon_data/script.skinshortcuts"; do
  [ -e "$KODI/$f" ] && cp -r "$KODI/$f" "$STAGE/userdata/$f"
done

# 2) favoritos base (el updater los fusiona, no reemplaza)
cat > "$STAGE/userdata/favourites.xml" <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<favourites>
    <favourite name="Actualizar VillaHub" thumb="">RunPlugin(plugin://plugin.program.villahub/?action=update)</favourite>
    <favourite name="VillaHub: estado" thumb="">RunPlugin(plugin://plugin.program.villahub/?action=status)</favourite>
</favourites>
XML

# 3) metadatos del paquete (incluye ajustes que el updater aplica via JSON-RPC local)
cat > "$STAGE/pack.json" <<EOF
{
  "version": "$VER",
  "date": "$(date +%F)",
  "notes": "$NOTES",
  "settings": {
    "locale.audiolanguage": "Spanish",
    "locale.subtitlelanguage": "Spanish"
  }
}
EOF

mkdir -p config
rm -f "config/hubconfig-$VER.zip"
(cd "$STAGE" && zip -qr "$OLDPWD/config/hubconfig-$VER.zip" .)

cat > config/version.json <<EOF
{
  "version": "$VER",
  "date": "$(date +%F)",
  "file": "config/hubconfig-$VER.zip",
  "notes": "$NOTES"
}
EOF
echo "listo: config/hubconfig-$VER.zip + config/version.json"
