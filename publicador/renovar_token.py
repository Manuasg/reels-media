"""Renueva la clave de Instagram (caduca a los 60 días) y la guarda en el secreto IG_TOKEN del repo.

Lo ejecuta GitHub Actions el día 1 y el 15 de cada mes. Usa GH_PAT (clave de GitHub con permiso
«Secrets: lectura y escritura» solo para este repo) para poder actualizar el secreto.
Nunca imprime la clave.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ig  # noqa: E402

r = ig.llamar("GET", "refresh_access_token", base="https://graph.instagram.com", grant_type="ig_refresh_token")
nuevo, dias = r["access_token"], int(r.get("expires_in", 0)) // 86400
if not os.environ.get("GH_TOKEN"):
    sys.exit("Falta GH_PAT (secreto del repo) para guardar la clave renovada.")
subprocess.run(["gh", "secret", "set", "IG_TOKEN", "--repo", os.environ.get("GITHUB_REPOSITORY", "Manuasg/reels-media")],
               input=nuevo.encode(), check=True)
print(f"Clave de Instagram renovada: válida {dias} días más.")
