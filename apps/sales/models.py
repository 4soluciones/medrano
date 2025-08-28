import decimal

from django.db import models


# Create your models here.
class Person(models.Model):
    TYPE_CHOICES = (
        ('C', 'Cliente'), ('P', 'Proveedor'))
    DOCUMENT_CHOICES = (
        ('01', 'DNI'), ('06', 'RUC'))
    id = models.AutoField(primary_key=True)
    type = models.CharField('Cliente - Proveedor', max_length=1, choices=TYPE_CHOICES, default='C')
    document = models.CharField('Tipo Documento', max_length=2, choices=DOCUMENT_CHOICES, default='01')
    number = models.CharField('Numero documento', max_length=15, null=True, blank=True)
    full_name = models.CharField('Nombres y Apellidos', max_length=200, null=True, blank=True)
    first_name = models.CharField('Primer Nombre', max_length=200, null=True, blank=True)
    second_name = models.CharField('Segundo Nombre', max_length=200, null=True, blank=True)
    surname = models.CharField('Primer Apellido', max_length=200, null=True, blank=True)
    second_surname = models.CharField('Segundo Apellido', max_length=200, null=True, blank=True)
    phone1 = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField('Correo', max_length=100, null=True, blank=True)
    address = models.CharField('Direccion', max_length=200, null=True, blank=True)
    occupation = models.CharField('Ocupacion', max_length=200, null=True, blank=True)
    observations = models.CharField('Observaciones', max_length=500, null=True, blank=True)
    creation_date = models.DateTimeField('Fecha de Creación', auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return str(self.full_name)

    class Meta:
        verbose_name = 'Cliente - Proveedor'
        verbose_name_plural = 'Clientes - Proveedores'


class Order(models.Model):
    TYPE_CHOICES = (('O', 'ORDEN DE SERVICIO'), ('C', 'COTIZACIÓN'))
    TYPE_CHOICES_PAYMENT = (('E', 'Efectivo'), ('Y', 'Yape'), ('D', 'Deposito y/o Transferencia'), ('C', 'Credito'))
    STATUS_CHOICES = (('P', 'PENDIENTE'), ('C', 'COMPLETADO'), ('A', 'ANULADO'),)
    DELIVERY_CHOICES = (('P', 'PENDIENTE'), ('E', 'ENTREGADO'), ('C', 'CANCELADO'),)
    VOUCHER_CHOICES = (('T', 'TICKET'), ('B', 'BOLETA'), ('F', 'FACTURA'))
    id = models.AutoField(primary_key=True)
    code = models.CharField('Código', max_length=20, unique=True, null=True, blank=True)
    serial = models.CharField('Serie', max_length=5, null=True, blank=True)
    correlative = models.IntegerField(default=0)
    type = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, default='C')
    client = models.ForeignKey('sales.Person', on_delete=models.SET_NULL, null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    register_date = models.DateField('Fecha de Registro', null=True, blank=True)
    delivery_date = models.DateField('Fecha de Entrega', null=True, blank=True)
    user = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    way_to_pay = models.CharField('Tipo de pago', max_length=1, choices=TYPE_CHOICES_PAYMENT, default='E')
    cash_advance = models.DecimalField('Adelanto', max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField('subtotal', max_digits=10, decimal_places=2, default=0)
    igv = models.DecimalField('igv', max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField('total', max_digits=10, decimal_places=2, default=0)
    subsidiary = models.ForeignKey('hrm.Subsidiary', on_delete=models.SET_NULL, null=True, blank=True)
    observation = models.CharField('Observacion', max_length=200, null=True, blank=True, default=0)
    status = models.CharField('Estado', max_length=1, choices=STATUS_CHOICES, default='P', )
    voucher_type = models.CharField('Tipo de comprobante', max_length=2, choices=VOUCHER_CHOICES, default='T')
    cancellation_reason = models.CharField('Motivo de cancelacion', max_length=500, null=True, blank=True)
    delivery_status = models.CharField(max_length=1, choices=DELIVERY_CHOICES, default='P')

    def __str__(self):
        return str(self.id)
    
    def calculate_totals(self):
        """Calcula los totales de la orden"""
        total_amount = sum(detail.multiply() for detail in self.orderdetail_set.all())
        self.subtotal = total_amount / decimal.Decimal(1.18)
        self.igv = total_amount - self.subtotal
        self.total = total_amount
        self.save()

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Ordenes'


class OrderDetail(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True)
    product_name = models.CharField('Nombre del Producto/Servicio', max_length=200, null=True, blank=True)
    quantity = models.DecimalField('Cantidad', max_digits=10, decimal_places=3, default=0)
    price_unit = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2, default=0)
    observation = models.CharField('Observacion producto', max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    def multiply(self):
        return self.quantity * self.price_unit


class ProductCategory(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=45, unique=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'


class Product(models.Model):
    TYPE_CHOICES = (('P', 'PRODUCTO'), ('S', 'SERVICIO'))
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=150)
    observation = models.CharField('Observacion', max_length=50, null=True, blank=True)
    code = models.CharField('Codigo', max_length=45, null=True, blank=True)
    stock_min = models.IntegerField('Stock Minimno', default=0)
    stock_max = models.IntegerField('Stock Maximo', default=0)
    product_category = models.ForeignKey('ProductCategory', on_delete=models.CASCADE)
    is_enabled = models.BooleanField('Habilitado', default=True)
    type_product = models.CharField('Tipo de Producto', max_length=1, choices=TYPE_CHOICES, default='P')
    creation_date = models.DateTimeField('Fecha de Creación', auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return str(self.name) + " - " + str(self.code or '')

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'


class ProductDetail(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    unit = models.ForeignKey('Unit', on_delete=models.CASCADE)
    price_sale = models.DecimalField('Precio de Venta', max_digits=10, decimal_places=2, default=0)
    price_purchase = models.DecimalField('Precio de Compra', max_digits=10, decimal_places=2, default=0)
    is_enabled = models.BooleanField('Habilitado', default=True)

    def __str__(self):
        return str(self.product.name) + " - " + str(self.unit.name)

    class Meta:
        verbose_name = 'Detalle de Producto'
        verbose_name_plural = 'Detalles de Productos'


class Unit(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=5, unique=True)
    description = models.CharField('Descripcion', max_length=50, null=True, blank=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Unidad'
        verbose_name_plural = 'Unidades'










