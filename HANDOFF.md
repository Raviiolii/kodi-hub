# Kubo — HANDOFF (reinicio limpio · 8-oct-2026)

> Lee esto primero. Todo lo demás son detalles.

## 1. Qué está corriendo (systemd user, sobrevive reinicios)

| Unidad | Qué es | URL local |
|---|---|---|
| `kubo-app.service` | **interfaz del cliente** (animada, hero + filas) | http://localhost:8896 |
| `kubo-hub.service` | portada web (versión previa, sigue viva) | http://localhost:8897 |
| `kubo-monitor.service` | **panel de dispositivos** (admin: pausa/stop/actualizar) | http://localhost:8898 |
| Kodi (Flatpak) | reproductor + **sirve la UI en su webserver** | http://[::1]:8080 |

Comprobar: `systemctl --user status kubo-app kubo-hub kubo-monitor`
Reiniciar uno: `systemctl --user restart kubo-app`
Linger activado → arrancan aunque no inicies sesión. El 8080 IPv4 lo ocupa el dev server de Villa Gym.

## 2. Dónde está cada cosa

- **Hub de Kodi (repo público)**: `github.com/Raviiolii/kubo` · local `~/kubo/`
  - addons: `plugin.program.kubo` (updater + lanzador de servicios), `repository.kubo`, `plugin.video.plutotv` 1.6.3 (parche propio), `webinterface.kubo` (la UI como interfaz web de Kodi)
  - publicar: `./build.sh` (re-empaqueta) · `./pack-config.sh <version> "notas"` (config del hub) · `git push`
- **App del cliente**: `~/kubo-app/` (services.json = catálogo de servicios, content.json = películas libres)
- **Panel**: `~/kubo-dashboard/` (`devices.json` = dispositivos)
- **Docs**: negocio `~/PLAN-streaming-kubo.md` · técnica `~/ARQUITECTURA-kubo.md` · detalle/ops/trampas `~/kubo/NOTAS-detalle.md`
- **Capturas**: `~/Downloads/kubo-app1.png`, `kubo-web-hub5.png`, `kubo-kodi-ui.png`

## 3. Dispositivos

- **Laptop** (dev): Kodi 21.3 Flatpak, skin Arctic Zephyr, UI es-MX, JSON-RPC en `[::1]:8080`.
- **Tablet SM-P610** (Android 13): adb inalámbrico `192.168.68.103:5555`, Kodi 21.3 con el hub espejo. Ojo: su webserver solo responde con **Kodi en primer plano**.
- **Roku TV**: Kodi **no** corre en Roku. Caminos: Jellyfin (app oficial en Roku) · DLNA desde Kodi · espejo Miracast · o el box por HDMI. No está conectado a la red todavía (sin respuesta en 8060).
- **Hardware pendiente**: box Amlogic S905X4 (X96 X4 / HK1 RBOX X4) + CoreELEC → el aparato definitivo de TV.

## 4. Siguiente paso técnico (cuando retomes)

**T1 del plan** = API mínima con un título real de punta a punta:
`/api/catalog/home` + `/api/playback/:id/token` (URL firmada 60 s) + login. Criterio: el video se reproduce desde la app y desde Kodi.
Después: T2 auth · T3 admin (pausar/reanudar/cancelar) · T4 Mercado Pago · T5 worker ffmpeg + R2.

Decisiones abiertas: contenido del piloto (liga local + dominio público), marca definitiva, si el menú definitivo es la web app (recomendado) o widgets del skin.

## 5. Reglas que no se rompen

1. **Solo contenido legal** (propio, con permiso, o dominio público). No se instalan ni se enlazan addons de piratería — pedido 5 veces, respuesta final.
2. Pluto TV en México sirve tarjeta de geobloqueo: no se monta bypass.
3. `raw.githubusercontent.com` cachea minutos tras un push → el updater consulta primero la API de GitHub.
4. Addon instalado a mano en Kodi queda **deshabilitado**: habilitar con `Addons.SetAddonEnabled` + reiniciar.
