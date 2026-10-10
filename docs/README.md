# Documentación del proyecto `odoo_api`

Proyecto para conectarse a Odoo desde Python vía XML-RPC, como base para una importación masiva de datos.

## Índice

1. [Conceptos: cómo funciona XML-RPC con Odoo](01-conceptos-xmlrpc.md)
2. [Archivos del proyecto, explicados línea a línea](02-archivos-del-proyecto.md)
3. [Métodos del ORM y domains (referencia rápida)](03-metodos-y-domains.md)

## Estructura

```
odoo_api/
├── .env                 # Credenciales (NO subir a git)
├── .gitignore           # Excluye .env y __pycache__
├── odoo_conexion.py     # Clase Odoo reutilizable (conexión + método call)
├── listar_usuarios.py   # Script de ejemplo: lista usuarios
├── test_conexion.py     # Tests que verifican la conexión paso a paso
└── docs/                # Esta documentación
```

## Inicio rápido

1. Completar `.env`:
   ```
   ODOO_URL=https://miempresa.odoo.com
   ODOO_DB=miempresa
   ODOO_USER=usuario@correo.com
   ODOO_API_KEY=xxxxxxxxxxxxxxxx
   ```
2. Verificar la conexión:
   ```
   python -m unittest test_conexion -v
   ```
3. Probar un script real:
   ```
   python listar_usuarios.py
   ```
