"""Conexión a la base de datos (SQLite) y creación de las tablas."""

import sqlite3

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS apartados (
  id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, cliente TEXT NOT NULL, telefono TEXT, email TEXT,
  producto TEXT NOT NULL, talla TEXT, precio REAL NOT NULL, fecha_limite TEXT NOT NULL,
  consentimiento_notificaciones INTEGER NOT NULL DEFAULT 0 CHECK (consentimiento_notificaciones IN (0, 1)),
  consentimiento_actualizado TEXT,
  estado TEXT NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'liquidado', 'vencido')));
CREATE TABLE IF NOT EXISTS abonos (
  id INTEGER PRIMARY KEY, apartado_id INTEGER NOT NULL REFERENCES apartados(id),
  fecha TEXT NOT NULL, importe REAL NOT NULL CHECK (importe > 0), forma_pago TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ventas (
  id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, concepto TEXT NOT NULL,
  importe REAL NOT NULL CHECK (importe > 0), forma_pago TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS vales (
  id INTEGER PRIMARY KEY, codigo TEXT UNIQUE NOT NULL, apartado_id INTEGER NOT NULL REFERENCES apartados(id),
  fecha TEXT NOT NULL, importe REAL NOT NULL, usado INTEGER NOT NULL DEFAULT 0);
"""


def conectar():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def consultar(sql, *args):
    """Ejecuta un SELECT y devuelve una lista de diccionarios."""
    with conectar() as con:
        return [dict(fila) for fila in con.execute(sql, args)]


def crear_tablas():
    with conectar() as con:
        con.executescript(SCHEMA)
        # Migración aditiva: conservar registros previos sin atribuirles consentimiento.
        columnas = {fila['name'] for fila in con.execute('PRAGMA table_info(apartados)')}
        if 'consentimiento_notificaciones' not in columnas:
            con.execute('ALTER TABLE apartados ADD COLUMN consentimiento_notificaciones INTEGER NOT NULL DEFAULT 0 CHECK (consentimiento_notificaciones IN (0, 1))')
        if 'consentimiento_actualizado' not in columnas:
            con.execute('ALTER TABLE apartados ADD COLUMN consentimiento_actualizado TEXT')


def esta_vacia():
    return not consultar("SELECT 1 FROM apartados LIMIT 1")
