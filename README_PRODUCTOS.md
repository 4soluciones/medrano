# Módulo de Productos - Sistema Medrano

## Descripción
Este módulo permite gestionar productos, categorías y unidades de medida en el sistema Medrano. Incluye funcionalidades completas para crear, editar, ver y administrar el catálogo de productos.

## Características Principales

### 🏷️ Gestión de Productos
- **Crear Productos**: Formulario completo con validaciones
- **Editar Productos**: Modificar información existente
- **Ver Productos**: Vista detallada de cada producto
- **Listado con Filtros**: Búsqueda por nombre, categoría y tipo
- **Control de Stock**: Stock mínimo y máximo configurable

### 📂 Gestión de Categorías
- **Crear Categorías**: Organizar productos por grupos
- **Categorías Predefinidas**: Sistema viene con categorías básicas
- **Validaciones**: Evita duplicados y nombres vacíos

### 📏 Gestión de Unidades
- **Unidades de Medida**: Sistema flexible de unidades
- **Unidades Predefinidas**: Incluye unidades comunes (KG, M, L, etc.)
- **Descripciones**: Información detallada de cada unidad

### 💰 Gestión de Precios
- **Precio de Venta**: Precio al que se vende el producto
- **Precio de Compra**: Precio al que se compra el producto
- **Múltiples Unidades**: Diferentes precios por unidad de medida

## Instalación y Configuración

### 1. Verificar Modelos
Los modelos ya están definidos en `apps/sales/models.py`:
- `Product`: Producto principal
- `ProductCategory`: Categorías de productos
- `ProductDetail`: Detalles de precios y unidades
- `Unit`: Unidades de medida

### 2. Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Inicializar Datos Básicos
```bash
python manage.py init_products
```

### 4. Verificar URLs
Las URLs están configuradas en `apps/sales/urls.py`:
- `/sales/product_list/` - Lista principal de productos
- `/sales/modal_product_create/` - Crear producto
- `/sales/modal_category_create/` - Crear categoría
- `/sales/modal_unit_create/` - Crear unidad

## Uso del Sistema

### Acceso al Módulo
1. Ir al menú principal
2. Seleccionar "Ventas" → "Listado de Productos"
3. Se abrirá la interfaz principal de productos

### Crear un Producto
1. Hacer clic en "Crear Producto"
2. Llenar el formulario con la información requerida
3. Seleccionar categoría y unidad
4. Configurar precios de venta y compra
5. Guardar el producto

### Crear una Categoría
1. Hacer clic en "Nueva Categoría"
2. Ingresar el nombre de la categoría
3. Guardar

### Crear una Unidad
1. Hacer clic en "Nueva Unidad"
2. Ingresar abreviatura (ej: KG)
3. Ingresar descripción (ej: Kilogramos)
4. Guardar

## Estructura de Archivos

```
apps/sales/
├── models.py              # Modelos de datos
├── views.py               # Lógica de negocio
├── urls.py                # Configuración de URLs
├── admin.py               # Configuración del admin
└── management/
    └── commands/
        └── init_products.py  # Comando de inicialización

templates/sales/
├── product_list.html      # Vista principal
├── product_create.html    # Formulario de creación
├── product_update.html    # Formulario de edición
├── category_create.html   # Formulario de categoría
└── unit_create.html       # Formulario de unidad
```

## Funcionalidades Técnicas

### Validaciones
- **Nombre obligatorio**: El nombre del producto es requerido
- **Categoría obligatoria**: Debe seleccionar una categoría
- **Código único**: Evita duplicados de códigos
- **Validación en tiempo real**: Feedback visual del usuario

### Seguridad
- **CSRF Protection**: Todos los formularios están protegidos
- **Autenticación**: Requiere login para acceder
- **Permisos**: Control de acceso por usuario

### Interfaz de Usuario
- **Responsive**: Funciona en dispositivos móviles
- **DataTables**: Tabla con paginación y búsqueda
- **Modales**: Formularios en ventanas emergentes
- **Toastr**: Notificaciones elegantes
- **Bootstrap 4**: Diseño moderno y profesional

## Personalización

### Agregar Nuevas Categorías
```python
# En el admin de Django o usando el comando
category = ProductCategory.objects.create(
    name='NUEVA CATEGORÍA',
    is_enabled=True
)
```

### Agregar Nuevas Unidades
```python
# En el admin de Django o usando el comando
unit = Unit.objects.create(
    name='NUEVA',
    description='Descripción de la nueva unidad',
    is_enabled=True
)
```

### Modificar Tipos de Producto
```python
# En models.py, modificar TYPE_CHOICES
TYPE_CHOICES = (
    ('P', 'PRODUCTO'),
    ('S', 'SERVICIO'),
    ('M', 'MATERIAL'),  # Nueva opción
)
```

## Solución de Problemas

### Error: "No module named 'apps.sales.models'"
- Verificar que la aplicación esté en INSTALLED_APPS
- Verificar la estructura de directorios

### Error: "Table doesn't exist"
- Ejecutar migraciones: `python manage.py migrate`
- Verificar que los modelos estén correctamente definidos

### Error: "Template does not exist"
- Verificar que los templates estén en el directorio correcto
- Verificar la configuración de TEMPLATES en settings.py

### Error: "URL not found"
- Verificar que las URLs estén correctamente configuradas
- Verificar que el namespace esté correcto

## Mantenimiento

### Limpieza de Datos
```python
# Eliminar productos deshabilitados
Product.objects.filter(is_enabled=False).delete()

# Eliminar categorías sin productos
ProductCategory.objects.filter(product__isnull=True).delete()
```

### Backup de Datos
```bash
# Exportar datos
python manage.py dumpdata sales.Product > products_backup.json
python manage.py dumpdata sales.ProductCategory > categories_backup.json
python manage.py dumpdata sales.Unit > units_backup.json
```

### Restaurar Datos
```bash
# Importar datos
python manage.py loaddata products_backup.json
python manage.py loaddata categories_backup.json
python manage.py loaddata units_backup.json
```

## Soporte y Contacto

Para soporte técnico o preguntas sobre este módulo:
- Revisar la documentación de Django
- Verificar los logs del sistema
- Contactar al equipo de desarrollo

---

**Versión**: 1.0  
**Fecha**: 2024  
**Desarrollado por**: Sistema Medrano
