"""Conexión reutilizable a Odoo vía XML-RPC (credenciales en .env)."""
import os
import xmlrpc.client
from pathlib import Path


def cargar_env(ruta=Path(__file__).with_name(".env")):
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())


class Odoo:
    def __init__(self):
        cargar_env()
        self.url = os.environ["ODOO_URL"].rstrip("/").removesuffix("/odoo")
        self.db = os.environ["ODOO_DB"]
        self.user = os.environ["ODOO_USER"]
        self.key = os.environ["ODOO_API_KEY"]
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, self.user, self.key, {})
        if not self.uid:
            raise RuntimeError("Autenticación fallida: revisar ODOO_USER (login) y ODOO_API_KEY")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)

    def call(self, modelo, metodo, *args, **kwargs):
        return self.models.execute_kw(self.db, self.uid, self.key, modelo, metodo, list(args), kwargs)
