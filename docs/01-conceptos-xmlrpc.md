# 1. Conceptos: cómo funciona XML-RPC con Odoo

## ¿Qué es XML-RPC?

XML-RPC (*Remote Procedure Call*) es un protocolo para **llamar funciones que viven en otro servidor** como si fueran locales. Por debajo:

1. Python convierte tu llamada (nombre de función + argumentos) a XML.
2. La envía por HTTP POST al servidor.
3. El servidor ejecuta la función y responde en XML.
4. Python convierte la respuesta a tipos nativos (`dict`, `list`, `int`, `str`, `bool`).

Python lo trae incluido en la librería estándar (`xmlrpc.client`), así que **no hay que instalar nada**.

## Los dos endpoints de Odoo

| Endpoint | Requiere login | Para qué sirve |
|---|---|---|
| `/xmlrpc/2/common` | No | `version()` (info del servidor) y `authenticate()` (obtener el `uid`) |
| `/xmlrpc/2/object` | Sí | `execute_kw()`: leer, crear, modificar y borrar registros de cualquier modelo |

## `ServerProxy`: el "control remoto"

```python
import xmlrpc.client
common = xmlrpc.client.ServerProxy("https://miempresa.odoo.com/xmlrpc/2/common")
common.version()   # ← esto hace un HTTP POST real
```

`ServerProxy` es un objeto que representa al servidor. Cualquier método que llames sobre él (`common.version()`, `common.authenticate(...)`) se traduce en una petición HTTP. **Crear el proxy no conecta nada**; la conexión ocurre en la primera llamada.

## Autenticación

```python
uid = common.authenticate(DB, USER, API_KEY, {})
```

- **Éxito:** devuelve un `int`, el ID del usuario en Odoo (ej. `2`).
- **Fallo:** devuelve `False`. **No lanza excepción**, por eso siempre hay que comprobar el valor.
- El `{}` final es un diccionario de entorno del cliente; casi siempre va vacío.

### Importante: no hay sesión

Odoo **no** guarda una sesión ni te da un token. En cada llamada posterior hay que reenviar `DB`, `uid` y `API_KEY`. Por eso conviene envolver todo en una clase (ver `odoo_conexion.py`).

### API key en vez de contraseña

La API key se genera en Odoo: *avatar → Mi perfil / Preferencias → Seguridad de la cuenta → Nueva clave API*. Se usa exactamente donde iría la contraseña. Ventajas:

- Si se filtra, se revoca sin cambiar tu contraseña.
- Funciona aunque tengas activada la verificación en dos pasos (2FA).

## `execute_kw`: la función que lo hace todo

Toda operación sobre datos pasa por aquí:

```python
models.execute_kw(DB, uid, API_KEY, modelo, metodo, args, kwargs)
```

| Parámetro | Ejemplo | Significado |
|---|---|---|
| `DB, uid, API_KEY` | | Credenciales (se repiten siempre) |
| `modelo` | `"res.partner"` | Modelo de Odoo (equivale a una tabla) |
| `metodo` | `"search_read"` | Método del ORM a ejecutar |
| `args` | `[[["is_company", "=", True]]]` | **Lista** de argumentos posicionales |
| `kwargs` | `{"fields": ["name"], "limit": 10}` | **Diccionario** de argumentos con nombre |

### La trampa de las listas dobles

`args` es siempre una lista que *contiene* los argumentos. Si el primer argumento ya es una lista (IDs o un domain), quedan dos niveles:

```python
# read(ids)          → args = [ [1, 2, 3] ]
# search(domain)     → args = [ [ ["name", "=", "Juan"] ] ]
# search_count([])   → args = [ [] ]
```

Este es el error más común al empezar. La clase `Odoo` del proyecto lo resuelve: en `odoo.call(...)` pasas los argumentos "normales" y ella arma la lista externa.

## Modelos más comunes

| Modelo | Contenido |
|---|---|
| `res.partner` | Contactos (clientes, proveedores, empresas, personas) |
| `res.users` | Usuarios del sistema |
| `product.template` / `product.product` | Productos (plantilla / variante) |
| `sale.order` | Pedidos de venta |
| `account.move` | Facturas y asientos contables |
| `res.country` | Países |

Para ver el nombre técnico de cualquier modelo en la interfaz web: activar **modo desarrollador** (*Ajustes → Activar modo desarrollador*) y pasar el cursor sobre un campo.
