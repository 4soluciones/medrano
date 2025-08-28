# Módulos de Contabilidad - Sistema Medrano

## Descripción General

Se han implementado dos módulos principales para la gestión contable del sistema Medrano:

1. **Gestión de Cuentas/Cajas** - Basado en el modelo `Cash`
2. **Gestión de Gastos y Flujo de Caja** - Basado en el modelo `CashFlow`

## Módulo 1: Gestión de Cuentas/Cajas

### Funcionalidades
- ✅ Crear nuevas cuentas/cajas
- ✅ Editar cuentas existentes
- ✅ Listar todas las cuentas con filtros
- ✅ Reporte de totales por tipo de moneda
- ✅ Validación de nombres únicos por sucursal

### Características Técnicas
- **Modelo**: `Cash`
- **URLs**: `/accounting/cash/`
- **Vistas**: `cash_list`, `cash_create`, `cash_edit`, `cash_save`, `cash_update`
- **Templates**: `cash_list.html`, `cash_list_grid.html`, `cash_create.html`, `cash_edit.html`

### Campos del Modelo Cash
- Nombre de la cuenta
- Sucursal asociada
- Número de cuenta
- Saldo inicial
- Tipo de moneda (Soles, Euros, Dólares)
- Fecha de creación

## Módulo 2: Gestión de Gastos y Flujo de Caja

### Funcionalidades
- ✅ Registrar nuevos gastos/transacciones
- ✅ Editar gastos existentes
- ✅ Listar gastos con filtros avanzados
- ✅ Reporte de totales (ingresos, gastos, balance neto)
- ✅ Desglose por tipo de gasto
- ✅ Filtros por fecha, sucursal, cuenta, usuario, tipo

### Características Técnicas
- **Modelo**: `CashFlow`
- **URLs**: `/accounting/cashflow/`
- **Vistas**: `cashflow_list`, `cashflow_create`, `cashflow_edit`, `cashflow_save`, `cashflow_update`
- **Templates**: `cashflow_list.html`, `cashflow_list_grid.html`, `cashflow_create.html`, `cashflow_edit.html`

### Campos del Modelo CashFlow
- Fecha de transacción
- Tipo de transacción (Apertura, Cierre, Entrada, Salida, Depósito)
- Descripción
- Cuenta/Caja asociada
- Usuario responsable
- Tipo de gasto (Variable, Fijo, Personal, Otros)
- Montos (Subtotal, IGV, Total)
- Información del documento (Serie, N° Comprobante, Tipo)
- Código de operación

## Integración en el Menú Principal

Los módulos han sido integrados en la sección **Finanzas** del menú principal:

```
Finanzas
├── Cuentas / Cajas
└── Gastos y Flujo de Caja
```

## Características de Diseño

### UI/UX
- ✅ Diseño profesional y elegante
- ✅ Interfaz responsive para dispositivos móviles
- ✅ Filtros colapsables para optimizar espacio
- ✅ Modales para crear/editar registros
- ✅ Validación en tiempo real
- ✅ Notificaciones con SweetAlert2

### Estilos
- ✅ Bordes redondeados (15px para cards, 25px para botones)
- ✅ Sombras y efectos hover
- ✅ Gradientes y transiciones suaves
- ✅ Iconos FontAwesome para mejor identificación
- ✅ Colores consistentes con el tema del sistema

## Funcionalidades JavaScript

### Validaciones
- ✅ Campos obligatorios
- ✅ Validación de montos positivos
- ✅ Filtrado dinámico de cuentas por sucursal
- ✅ Cálculo automático de totales

### AJAX
- ✅ Carga dinámica de grillas
- ✅ Envío de formularios sin recarga
- ✅ Actualización en tiempo real de contadores
- ✅ Manejo de errores con feedback visual

## Estructura de Archivos

```
templates/accounting/
├── cash_list.html          # Lista principal de cuentas
├── cash_list_grid.html     # Grilla dinámica de cuentas
├── cash_create.html        # Formulario de creación
├── cash_edit.html          # Formulario de edición
├── cashflow_list.html      # Lista principal de gastos
├── cashflow_list_grid.html # Grilla dinámica de gastos
├── cashflow_create.html    # Formulario de creación de gastos
└── cashflow_edit.html      # Formulario de edición de gastos
```

## URLs Configuradas

### Cuentas/Cajas
- `GET /accounting/cash/` - Lista principal
- `GET /accounting/cash/create/` - Formulario de creación
- `POST /accounting/cash/save/` - Guardar nueva cuenta
- `GET /accounting/cash/<id>/edit/` - Formulario de edición
- `POST /accounting/cash/update/` - Actualizar cuenta

### Gastos/Flujo de Caja
- `GET /accounting/cashflow/` - Lista principal
- `GET /accounting/cashflow/create/` - Formulario de creación
- `POST /accounting/cashflow/save/` - Guardar nuevo gasto
- `GET /accounting/cashflow/<id>/edit/` - Formulario de edición
- `POST /accounting/cashflow/update/` - Actualizar gasto

### URLs Auxiliares
- `GET /accounting/get-cash-accounts/` - Obtener cuentas por sucursal

## Dependencias

### Frontend
- ✅ Bootstrap 4
- ✅ jQuery
- ✅ FontAwesome 6
- ✅ SweetAlert2
- ✅ DataTables (opcional)

### Backend
- ✅ Django 3.0+
- ✅ Python 3.7+
- ✅ Base de datos compatible con Django ORM

## Configuración Requerida

### Settings.py
Asegúrate de que la aplicación `accounting` esté incluida en `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... otras apps
    'apps.accounting',
]
```

### URLs.py Principal
Las URLs ya están configuradas en `medrano/urls.py`:

```python
path('accounting/', include(('apps.accounting.urls', 'apps.accounting'))),
```

## Uso

### Acceso a los Módulos
1. Inicia sesión en el sistema
2. Navega al menú **Finanzas**
3. Selecciona **Cuentas / Cajas** o **Gastos y Flujo de Caja**

### Crear Nueva Cuenta
1. Ve a **Cuentas / Cajas**
2. Haz clic en **Nueva Cuenta**
3. Completa el formulario
4. Haz clic en **Guardar Cuenta**

### Registrar Nuevo Gasto
1. Ve a **Gastos y Flujo de Caja**
2. Haz clic en **Nuevo Gasto**
3. Completa el formulario
4. Haz clic en **Guardar Gasto**

## Reportes Disponibles

### Cuentas/Cajas
- Total de saldos por tipo de moneda
- Lista detallada de todas las cuentas
- Filtros por sucursal y tipo de moneda

### Gastos/Flujo de Caja
- Total de ingresos
- Total de gastos
- Balance neto
- Desglose por tipo de gasto
- Filtros por fecha, sucursal, cuenta, usuario
- Conteo de transacciones

## Características de Seguridad

- ✅ Todas las vistas requieren autenticación (`@login_required`)
- ✅ Validación CSRF en todos los formularios
- ✅ Sanitización de datos de entrada
- ✅ Manejo seguro de errores

## Responsive Design

- ✅ Adaptable a dispositivos móviles
- ✅ Filtros colapsables en pantallas pequeñas
- ✅ Botones de tamaño apropiado para touch
- ✅ Layout flexible con Bootstrap Grid

## Notas de Implementación

- Los módulos siguen el patrón de diseño establecido en `order_list.html`
- Se utilizan las mejores prácticas de Django para formularios y vistas
- El código está optimizado para rendimiento con `select_related` y `prefetch_related`
- Se implementa manejo de errores robusto con try-catch y validaciones

## Próximas Mejoras Sugeridas

- [ ] Implementar eliminación de registros
- [ ] Agregar exportación a PDF/Excel
- [ ] Implementar búsqueda de texto completo
- [ ] Agregar gráficos y estadísticas visuales
- [ ] Implementar auditoría de cambios
- [ ] Agregar notificaciones por email para transacciones importantes
