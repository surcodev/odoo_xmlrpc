# 3. Métodos del ORM y domains (referencia rápida)

Todos los ejemplos usan la clase del proyecto:

```python
from odoo_conexion import Odoo
odoo = Odoo()
```

## Métodos principales

| Método | Entrada | Devuelve |
|---|---|---|
| `search` | domain | lista de IDs |
| `search_count` | domain | `int` |
| `read` | lista de IDs | lista de dicts |
| `search_read` | domain | lista de dicts |
| `create` | dict o lista de dicts | ID o lista de IDs |
| `write` | IDs + dict de valores | `True` |
| `unlink` | IDs | `True` |
| `fields_get` | — | dict con la definición de cada campo |

### Leer

```python
ids = odoo.call("res.partner", "search", [["is_company", "=", True]], limit=10)
datos = odoo.call("res.partner", "read", ids, fields=["name", "email"])

# Lo mismo en una llamada
datos = odoo.call("res.partner", "search_read",
                  [["is_company", "=", True]], fields=["name", "email"], limit=10)
```

Parámetros útiles: `fields`, `limit`, `offset` (paginar), `order` (`"name asc"`, `"id desc"`).

### Crear

```python
nuevo_id = odoo.call("res.partner", "create", {"name": "Cliente A", "email": "a@x.com"})

# En bloque: mucho más rápido que crear uno por uno
ids = odoo.call("res.partner", "create", [
    {"name": "Cliente B"},
    {"name": "Cliente C"},
])
```

Para importación masiva, crear en **lotes** (ej. de 100 a 500 registros por llamada) reduce el número de peticiones HTTP.

### Actualizar

```python
odoo.call("res.partner", "write", [nuevo_id], {"phone": "999 888 777"})
```

### Borrar

```python
odoo.call("res.partner", "unlink", [nuevo_id])
```

> **Cuidado:** `unlink` borra de forma permanente. Para ocultar sin borrar, mejor archivar: `write(ids, {"active": False})`.

### Descubrir los campos de un modelo

```python
campos = odoo.call("res.partner", "fields_get", attributes=["string", "type", "required"])
for nombre, info in campos.items():
    print(nombre, info["type"], info["string"], "(obligatorio)" if info["required"] else "")
```

Imprescindible antes de importar: dice el nombre técnico, el tipo y si es obligatorio.

## Domains (filtros)

Un domain es una lista de condiciones `[campo, operador, valor]`. Varias condiciones seguidas se unen con **AND**.

```python
[["is_company", "=", True], ["country_id.code", "=", "PE"]]
```

### Operadores

| Operador | Ejemplo |
|---|---|
| `=`, `!=` | `["active", "=", True]` |
| `>`, `>=`, `<`, `<=` | `["create_date", ">=", "2026-01-01"]` |
| `in`, `not in` | `["id", "in", [1, 2, 3]]` |
| `like` / `ilike` | `["name", "ilike", "juan"]` (contiene; `ilike` ignora mayúsculas) |
| `=like` / `=ilike` | `["email", "=ilike", "%@gmail.com"]` (patrón exacto con `%`) |
| `child_of` | `["parent_id", "child_of", 5]` |

### OR y NOT

Se escriben en **notación prefija**: el operador va antes de las condiciones.

```python
# nombre contiene "juan" O email contiene "juan"
["|", ["name", "ilike", "juan"], ["email", "ilike", "juan"]]

# NOT
["!", ["active", "=", True]]
```

### Campos relacionales con punto

Se puede filtrar por campos de un modelo relacionado:

```python
["country_id.code", "=", "PE"]        # país del contacto
["parent_id.name", "ilike", "acme"]   # nombre de la empresa padre
```

## Tipos de campo y cómo enviarlos

| Tipo | Leer devuelve | Para escribir |
|---|---|---|
| `char`, `text` | `"texto"` | `"texto"` |
| `integer`, `float` | `5`, `3.14` | `5`, `3.14` |
| `boolean` | `True` / `False` | `True` / `False` |
| `date` | `"2026-10-10"` | `"2026-10-10"` |
| `datetime` | `"2026-10-10 13:00:00"` (UTC) | mismo formato, en UTC |
| `selection` | `"draft"` | la clave técnica, no la etiqueta |
| `many2one` | `[5, "Perú"]` | solo el ID: `5` |
| `one2many` / `many2many` | `[1, 2, 3]` | comandos especiales (ver abajo) |

**Ojo:** un campo vacío llega como `False`, incluso si es texto o fecha.

### Comandos para `many2many` / `one2many`

| Comando | Efecto |
|---|---|
| `(0, 0, {valores})` | Crear un registro nuevo y vincularlo |
| `(4, id)` | Vincular un registro existente |
| `(3, id)` | Desvincular (sin borrar) |
| `(6, 0, [ids])` | Reemplazar todos los vínculos por esta lista |

```python
# Asignar etiquetas 1 y 2 a un contacto, reemplazando las anteriores
odoo.call("res.partner", "write", [nuevo_id], {"category_id": [(6, 0, [1, 2])]})
```

## Errores frecuentes

| Síntoma | Causa probable |
|---|---|
| `authenticate` devuelve `False` | DB, login o API key incorrectos |
| `Fault: ... AccessError` | El usuario no tiene permiso sobre ese modelo |
| `Fault: ... ValueError: Invalid field` | Nombre de campo mal escrito (revisar con `fields_get`) |
| `TypeError: cannot marshal None` | Falta `allow_none=True` en el `ServerProxy` |
| No aparecen registros que sí existen | Están archivados; añadir `["active", "in", [True, False]]` |
| Resultado con lista dentro de lista inesperada | Revisar niveles de listas en `args` |
