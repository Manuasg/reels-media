"""Guarda estadísticas de la cuenta (comunidad) en metricas/_cuenta.json. GitHub Actions, 1 vez al día.

- historial: una fila por día con seguidores y totales del día (alcance, vistas, visitas al perfil...).
- demografia: seguidores por edad, sexo, país y ciudad (última lectura).
- online: seguidores conectados por hora, tal como lo da Instagram (última lectura).
Cada dato se pide por separado: si Instagram no da alguno, se apunta en "errores" y los demás siguen.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ig  # noqa: E402

DESTINO = Path(__file__).resolve().parent.parent / "metricas" / "_cuenta.json"
TOTALES = ["reach", "views", "profile_views", "accounts_engaged", "total_interactions"]


def main():
    uid, ahora = ig.user_id(), datetime.now(timezone.utc)
    todo = json.loads(DESTINO.read_text(encoding="utf-8")) if DESTINO.exists() else {}
    errores, fila = {}, {"fecha": ahora.date().isoformat(), "hora": ahora.isoformat(timespec="minutes")}

    def pedir(clave, ruta, **params):
        try:
            return ig.llamar("GET", ruta, **params)
        except ig.ErrorIG as e:
            errores[clave] = str(e)[:300]
            return None

    r = pedir("perfil", uid, fields="followers_count,follows_count,media_count")
    if r:
        fila.update(seguidores=r.get("followers_count"), seguidos=r.get("follows_count"), publicaciones=r.get("media_count"))

    for m in TOTALES:
        r = pedir(m, f"{uid}/insights", metric=m, period="day", metric_type="total_value")
        if r and r.get("data"):
            fila[m] = r["data"][0].get("total_value", {}).get("value")

    demo = {}
    for b in ["age", "gender", "country", "city"]:
        r = pedir(f"demografia_{b}", f"{uid}/insights", metric="follower_demographics", period="lifetime",
                  metric_type="total_value", breakdown=b)
        try:
            res = r["data"][0]["total_value"]["breakdowns"][0]["results"]
            demo[b] = {x["dimension_values"][0]: x["value"] for x in res}
        except (TypeError, KeyError, IndexError):
            if r is not None:
                errores[f"demografia_{b}"] = "respuesta sin datos: " + json.dumps(r)[:200]
    if demo:
        todo["demografia"] = {"hora": fila["hora"], **demo}

    # Instagram da este dato con unos días de retraso: se piden los últimos 30 días por tramos y se queda con los que traen valores.
    vals, t1 = {}, int(ahora.timestamp())
    for i in range(0, 30, 10):
        r = pedir("online_followers", f"{uid}/insights", metric="online_followers", period="lifetime",
                  since=t1 - (i + 10) * 86400, until=t1 - i * 86400)
        for v in ((r or {}).get("data") or [{}])[0].get("values", []):
            if v.get("value"):
                vals[v["end_time"]] = v["value"]
    if vals:
        todo["online"] = {"hora": fila["hora"], "valores": [{"end_time": k, "value": vals[k]} for k in sorted(vals)]}
    elif "online_followers" not in errores:
        errores["online_followers"] = "Instagram no devolvió valores en los últimos 30 días"

    hist = [h for h in todo.get("historial", []) if h.get("fecha") != fila["fecha"]]
    todo["historial"] = (hist + [fila])[-400:]
    todo["errores"] = errores
    DESTINO.parent.mkdir(exist_ok=True)
    DESTINO.write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(fila, ensure_ascii=False)); print("demografia:", list(demo)); print("online:", "online" in todo)
    print("errores:", json.dumps(errores, ensure_ascii=False))


if __name__ == "__main__":
    main()
