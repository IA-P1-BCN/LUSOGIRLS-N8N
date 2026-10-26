"""Prepara exclusivamente secretos locales de pruebas, sin mostrarlos."""
import os
from pathlib import Path
import secrets

path = Path(__file__).with_name('.env.local')
if not path.exists():
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as out:
        out.write('PF_TEST_SECRET=' + secrets.token_urlsafe(32) + '\n')
        # Usamos la misma imagen que ya está instalada en el proyecto.
        out.write('PF_TEST_N8N_IMAGE=docker.n8n.io/n8nio/n8n:latest\n')
print('Entorno de pruebas preparado; secretos guardados solo en .env.local.')
