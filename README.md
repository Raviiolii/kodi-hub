# Kubo — hub de Kodi actualizable

Repositorio propio de Kodi + paquete de configuración, para que **el admin (Isaac)
publique una versión nueva y los dispositivos se actualicen solos** (una vez
instalado `plugin.program.kubo`).

## URLs (públicas, HTTPS)

- Repositorio (instalar una vez desde Kodi → Ajustes → Add-ons → Instalar desde zip):
  `https://raw.githubusercontent.com/Raviiolii/kubo/main/repo/repository.kubo/repository.kubo-1.0.0.zip`
- Índice del repo: `repo/addons.xml`
- Última versión de config: `config/version.json` → `config/hubconfig-X.Y.Z.zip`

## Publicar una actualización

1. Cambiar el menú/skin/config en el Kodi de desarrollo (el laptop).
2. `./pack-config.sh 1.1.0 "notas de la version"`  (empaqueta userdata → config/)
3. `./build.sh`  (re-zipea addons + regenera índice) — solo si tocaste `src/`
4. `git add -A && git commit -m "hub v1.1.0" && git push`
5. En el dispositivo: Add-ons → Kubo Updater → **Actualizar hub ahora**
   (o esperar el aviso automático al iniciar; se reinicia solo).

## Qué actualiza el paquete

- `userdata/addon_data/skin.arctic.zephyr.mod/settings.xml` (ajustes del skin)
- `userdata/addon_data/script.skinshortcuts/` (menú del hub)
- `userdata/favourites.xml` (**se fusiona**, no borra los tuyos)
- `pack.json.settings` → ajustes via JSON-RPC local (audio/subtítulos en español)
- Antes de sobrescribir algo, se guarda copia en
  `userdata/addon_data/plugin.program.kubo/backups/<fecha>/`

## Estructura

- `src/` — código de los addons (`repository.kubo`, `plugin.program.kubo`)
- `repo/` — repositorio Kodi publicado (zips + addons.xml + md5)
- `config/` — paquetes de configuración + `version.json` (la fuente de verdad)
- `build.sh`, `pack-config.sh` — generadores
