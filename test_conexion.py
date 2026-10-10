"""Prueba de conexión a Odoo vía XML-RPC.

Ejecutar:  python -m unittest test_conexion -v
Credenciales se leen de .env (o variables de entorno).
"""
import os
import unittest
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


cargar_env()
URL = os.environ["ODOO_URL"].rstrip("/").removesuffix("/odoo")
DB = os.environ["ODOO_DB"]
USER = os.environ["ODOO_USER"]
API_KEY = os.environ["ODOO_API_KEY"]


class TestConexionOdoo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
        cls.models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
        cls.uid = cls.common.authenticate(DB, USER, API_KEY, {})

    def setUp(self):
        if not self.uid and self._testMethodName not in ("test_1_version_servidor", "test_2_autenticacion"):
            self.skipTest("sin autenticación")

    def test_1_version_servidor(self):
        version = self.common.version()
        print(f"\n  Versión servidor: {version.get('server_version')}")
        self.assertIn("server_version", version)

    def test_2_autenticacion(self):
        print(f"\n  UID: {self.uid}")
        self.assertTrue(self.uid, "Autenticación fallida: revisar DB, usuario o API key")

    def test_3_lectura_usuario(self):
        usuario = self.models.execute_kw(
            DB, self.uid, API_KEY, "res.users", "read",
            [[self.uid]], {"fields": ["name", "login"]},
        )[0]
        print(f"\n  Usuario: {usuario['name']} <{usuario['login']}>")
        self.assertEqual(usuario["login"], USER)

    def test_4_permiso_lectura_partners(self):
        puede = self.models.execute_kw(
            DB, self.uid, API_KEY, "res.partner", "check_access_rights",
            ["read"], {"raise_exception": False},
        )
        total = self.models.execute_kw(DB, self.uid, API_KEY, "res.partner", "search_count", [[]])
        print(f"\n  Partners visibles: {total}")
        self.assertTrue(puede)


if __name__ == "__main__":
    unittest.main(verbosity=2)
