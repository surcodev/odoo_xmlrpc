# 2. Archivos del proyecto

## `.env` y `.gitignore`

`.env` guarda las credenciales fuera del código:

```
ODOO_URL=https://miempresa.odoo.com
ODOO_DB=miempresa
ODOO_USER=usuario@correo.com
ODOO_API_KEY=xxxxxxxxxxxxxxxx
```

- `ODOO_USER` es el **login** del usuario (normalmente su email), no su nombre.
- `ODOO_DB` en Odoo Online suele coincidir con el subdominio.

`.gitignore` evita que `.env` y `__pycache__` se suban a un repositorio. **Nunca compartas el `.env`.**

---

## `odoo_conexion.py` — conexión reutilizable

Es la pieza central. Cualquier script nuevo empieza con:

```python
from odoo_conexion import Odoo
odoo = Odoo()
```

### `cargar_env()` (líneas 7-14)

```python
def cargar_env(ruta=Path(__file__).with_name(".env")):
```

- `Path(__file__).with_name(".env")` busca el `.env` **en la misma carpeta que el script**, sin importar desde dónde lo ejecutes.
- Lee línea por línea, ignora vacías y comentarios (`#`), y separa en `clave=valor` con `split("=", 1)`. El `1` hace que solo corte en el primer `=`, por si la API key contiene `=`.
- `os.environ.setdefault(...)` guarda el valor **solo si no existe ya**. Así, una variable de entorno del sistema tiene prioridad sobre el `.env`.

Se escribió a mano para no depender de `python-dotenv`.

### `class Odoo` → `__init__` (líneas 18-28)

```python
self.url = os.environ["ODOO_URL"].rstrip("/").removesuffix("/odoo")
```
Limpia la URL. Si copias `https://miempresa.odoo.com/odoo/` desde el navegador, queda `https://miempresa.odoo.com`. Los endpoints XML-RPC están en la raíz del dominio, no bajo `/odoo`.

```python
common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
self.uid = common.authenticate(self.db, self.user, self.key, {})
if not self.uid:
    raise RuntimeError("Autenticación fallida: ...")
```
Autentica una sola vez al crear el objeto. Como `authenticate` devuelve `False` en vez de lanzar error, aquí se convierte en una excepción clara.

```python
self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)
```
`allow_none=True` permite enviar `None` en los datos. Sin esto, XML-RPC estándar falla si algún valor es `None` (frecuente al leer celdas vacías de un Excel).

### `call()` (líneas 30-31)

```python
def call(self, modelo, metodo, *args, **kwargs):
    return self.models.execute_kw(self.db, self.uid, self.key, modelo, metodo, list(args), kwargs)
```

Atajo para no repetir credenciales. Usa:

- `*args` → junta los argumentos posicionales en una tupla; `list(args)` la convierte en la lista que espera `execute_kw`. **Esto elimina la trampa de la lista doble.**
- `**kwargs` → junta los argumentos con nombre en un diccionario.

Comparación:

```python
# Sin la clase
models.execute_kw(DB, uid, KEY, "res.partner", "search_read",
                  [[["is_company", "=", True]]], {"fields": ["name"], "limit": 5})

# Con la clase
odoo.call("res.partner", "search_read",
          [["is_company", "=", True]], fields=["name"], limit=5)
```

---

## `listar_usuarios.py` — script de ejemplo

```
python listar_usuarios.py           # solo activos
python listar_usuarios.py --todos   # incluye archivados
```

### Lógica

```python
dominio = [["active", "in", [True, False]]] if "--todos" in sys.argv else []
```
Por defecto, Odoo **oculta los registros archivados** (`active = False`) en toda búsqueda. Para verlos hay que pedirlos explícitamente con `active in [True, False]`. Un domain vacío `[]` significa "sin filtro" (pero igual oculta archivados).

```python
usuarios = odoo.call(
    "res.users", "search_read", dominio,
    fields=["login", "name", "email", "active", "share", "login_date"],
    order="id",
)
```
- `search_read` busca y lee en una sola llamada. Devuelve una lista de diccionarios; cada uno incluye siempre `id`.
- `fields` limita las columnas. Sin `fields`, Odoo devuelve todas (lento y pesado).
- `order="id"` ordena como un `ORDER BY` de SQL.

```python
tipo = "portal" if u["share"] else "interno"
```
El campo `share` es `True` en usuarios portal/públicos (clientes con acceso web) y `False` en usuarios internos (los que pagan licencia).

```python
u['login_date'] or '-'
```
Los campos vacíos en Odoo llegan como `False` (no como `None`). El `or '-'` lo reemplaza para imprimir.

---

## `test_conexion.py` — diagnóstico de la conexión

```
python -m unittest test_conexion -v
```

Usa `unittest` (incluido en Python) para verificar la conexión **por etapas**. Si algo falla, sabes exactamente dónde.

| Test | Qué verifica | Si falla, revisar |
|---|---|---|
| `test_1_version_servidor` | El servidor responde (`common.version()`, no requiere login) | `ODOO_URL`, internet |
| `test_2_autenticacion` | `authenticate` devuelve un `uid` | `ODOO_DB`, `ODOO_USER`, `ODOO_API_KEY` |
| `test_3_lectura_usuario` | Puede leer su propio usuario en `res.users` y el login coincide | — |
| `test_4_permiso_lectura_partners` | Tiene permiso de lectura sobre `res.partner` y cuenta los contactos | Permisos del usuario en Odoo |

Detalles:

- `setUpClass` se ejecuta **una sola vez** antes de todos los tests: crea los proxies y autentica.
- `setUp` se ejecuta antes de **cada** test: si no hubo login, salta los tests 3 y 4 (`skipTest`) para no mostrar errores en cascada.
- Los números en los nombres (`test_1_`, `test_2_`...) fuerzan el orden, porque `unittest` ejecuta los tests en orden alfabético.
- `check_access_rights` con `raise_exception=False` devuelve `True/False` en vez de lanzar error.

Este archivo **no** usa la clase `Odoo` a propósito: muestra las llamadas XML-RPC "crudas", útil para aprender y para diagnosticar.
