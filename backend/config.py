"""Configuración y reglas del negocio.

Lo que cambia de un ordenador a otro (claves, direcciones) viene del archivo .env.
Las reglas de la zapatería (abono mínimo, plazo del apartado...) están aquí, en un solo sitio.
"""

import os
from pathlib import Path

# --- Entorno (.env) ---
DB_PATH = os.getenv("DB_PATH", "tienda.db")
API_KEY = os.getenv("API_KEY", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
SEED = os.getenv("SEED", "1") != "0"
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parent.parent / "frontend"))

# --- Reglas del negocio ---
ABONO_MINIMO = 5
PLAZO_DIAS = 90
FORMAS_PAGO = ["efectivo", "tarjeta", "bizum", "transferencia"]
