from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class Cash(models.Model):
    CURRENCY_TYPE_CHOICES = (('S', 'Soles'), ('E', 'Euros'), ('D', 'Dolares'),)
    name = models.CharField('Nombre', max_length=100, unique=True, null=True, blank=True)
    subsidiary = models.ForeignKey('hrm.Subsidiary', on_delete=models.SET_NULL, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    initial = models.DecimalField(max_digits=10, decimal_places=2, default='0',)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    currency_type = models.CharField('Tipo de moneda', max_length=1, choices=CURRENCY_TYPE_CHOICES, default='S', )

    def __str__(self):
        return str(self.name)


class CashFlow(models.Model):
    DOCUMENT_TYPE_ATTACHED_CHOICES = (
        ('F', 'Factura'), ('B', 'Boleta'), ('T', 'Ticket'), ('O', 'Otro'))
    TYPE_CHOICES = (('A', 'Apertura'), ('C', 'Cierre'), ('E', 'Entrada'), ('S', 'Salida'), ('D', 'Deposito'))
    TYPE_EXPENSE = (('V', 'GASTOS VARIABLES'), ('F', 'GASTOS FIJOS'), ('P', 'GASTOS PERSONALES'), ('O', 'OTROS'))
    transaction_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    description = models.CharField('Descripcion', max_length=100, null=True, blank=True)
    serial = models.CharField('Serie', max_length=5, null=True, blank=True)
    n_receipt = models.IntegerField('Numero de Comprobante', default=0, null=True, blank=True)
    document_type_attached = models.CharField('Tipo documento', max_length=1, choices=DOCUMENT_TYPE_ATTACHED_CHOICES,
                                              default='O')
    type = models.CharField('Tipo de transaccion', max_length=1, choices=TYPE_CHOICES, default='E', )
    subtotal = models.DecimalField('subtotal', max_digits=30, decimal_places=15, default=0)
    total = models.DecimalField('total', max_digits=30, decimal_places=15, default=0)
    igv = models.DecimalField('Igv total', max_digits=30, decimal_places=15, default=0)
    cash = models.ForeignKey(Cash, on_delete=models.SET_NULL, null=True, blank=True)
    operation_code = models.CharField(
        verbose_name='Codigo de operación', max_length=45, null=True, blank=True)
    order = models.ForeignKey('sales.Order', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey('users.CustomUser', verbose_name='Usuario', on_delete=models.CASCADE, null=True, blank=True)
    type_expense = models.CharField('Tipo de gasto', max_length=1, choices=TYPE_EXPENSE, default='O')

    def __str__(self):
        return str(self.pk)