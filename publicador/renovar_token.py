"""Renueva la clave de Instagram (dura 60 días) y la guarda en el secreto IG_TOKEN del repo.

Necesita GH_TOKEN: un token de GitHub con permiso «Secrets: read and write» sobre este repo.
La clave nueva nunca se imprime: pasa a `gh secret set` por la entrada estándar.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ig  # noqa: E402


def main():
    nuevo, segundos = ig.renovar_token()
    print(f'::add-mask::{nuevo}')
    subprocess.run(['gh', 'secret', 'set', 'IG_TOKEN'], input=nuevo, text=True, check=True)
    dias = round(segundos / 86400) if segundos else '?'
    print(f'Clave renovada: vale {dias} días más.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
