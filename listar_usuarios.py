"""Lista los usuarios de Odoo.

Uso:
    python listar_usuarios.py           # solo usuarios activos
    python listar_usuarios.py --todos   # incluye archivados
"""
import sys

from odoo_conexion import Odoo


def main():
    odoo = Odoo()
    dominio = [["active", "in", [True, False]]] if "--todos" in sys.argv else []
    usuarios = odoo.call(
        "res.users", "search_read", dominio,
        fields=["login", "name", "email", "active", "share", "login_date"],
        order="id",
    )

    print(f"{'ID':>4}  {'LOGIN':<28} {'NOMBRE':<28} {'TIPO':<8} {'ACTIVO':<6} ÚLTIMO ACCESO")
    print("-" * 100)
    for u in usuarios:
        tipo = "portal" if u["share"] else "interno"
        print(f"{u['id']:>4}  {u['login']:<28} {u['name']:<28} {tipo:<8} "
              f"{'sí' if u['active'] else 'no':<6} {u['login_date'] or '-'}")
    print(f"\nTotal: {len(usuarios)} usuarios")


if __name__ == "__main__":
    main()
