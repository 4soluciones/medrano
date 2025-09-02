from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models import Sum
from apps.users.models import CustomUser
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, Adjust


class Subsidiary(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    serial = models.CharField(max_length=4, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=45, null=True, blank=True)
    email = models.EmailField(max_length=45, null=True, blank=True)
    ruc = models.CharField('RUC', max_length=11, null=True, blank=True)
    business_name = models.CharField('Razón social', max_length=100, null=True, blank=True)
    representative_name = models.CharField(max_length=100, null=True, blank=True)
    representative_dni = models.CharField(max_length=45, null=True, blank=True)
    observation = models.CharField(max_length=500, null=True, blank=True)
    url = models.CharField(max_length=500, null=True, blank=True)
    token = models.CharField(max_length=500, null=True, blank=True)
    photo = models.ImageField(upload_to='subsidiary/', default='subsidiary/employee0.jpg', blank=True)
    photo_thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(100, 100)], source='photo',
                                     format='JPEG', options={'quality': 90})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'


class Area(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Area'
        verbose_name_plural = 'Areas'


class FunctionArea(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.description)


class Charge(models.Model):
    id = models.AutoField(primary_key=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True)
    charge = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.charge)


class FunctionCharge(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    charge = models.ForeignKey('Charge', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.charge)


class Department(models.Model):
    id = models.CharField(primary_key=True, max_length=6)
    description = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = 'Departameto'
        verbose_name_plural = 'Departametos'


class Province(models.Model):
    id = models.CharField(primary_key=True, max_length=6)
    description = models.CharField(max_length=200, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = 'Provincia'
        verbose_name_plural = 'Provincias'


class District(models.Model):
    id = models.CharField(primary_key=True, max_length=6)
    description = models.CharField(max_length=200, null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = 'Distrito'
        verbose_name_plural = 'Distritos'


class PaymentPeriod(models.Model):
    """Período de pago semanal"""
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_periods')
    start_date = models.DateField('Fecha de inicio (Lunes)')
    end_date = models.DateField('Fecha de fin (Sábado)')
    total_amount = models.DecimalField('Monto total', max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField('Pagado', default=False)
    payment_date = models.DateField('Fecha de pago', null=True, blank=True)
    notes = models.TextField('Observaciones', max_length=500, null=True, blank=True)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de actualización', auto_now=True)

    def __str__(self):
        return f"Pago {self.employee.first_name} {self.employee.last_name} - {self.start_date} a {self.end_date}"

    class Meta:
        verbose_name = 'Período de Pago'
        verbose_name_plural = 'Períodos de Pago'
        ordering = ['-start_date', '-created_at']

    def calculate_total(self):
        """Calcula el total del período basado en los días trabajados"""
        total = self.daily_payments.aggregate(
            total=Sum('amount')
        )['total'] or 0.00
        self.total_amount = total
        return total

    def get_working_days_count(self):
        """Retorna el número de días trabajados"""
        return self.daily_payments.filter(status='COMPLETO').count()

    def get_permission_days_count(self):
        """Retorna el número de días de permiso"""
        return self.daily_payments.filter(status='PERMISO').count()


class DailyPayment(models.Model):
    """Pago diario individual"""
    STATUS_CHOICES = [
        ('COMPLETO', 'Completo'),
        ('PERMISO', 'Permiso'),
        ('FALTA', 'Falta'),
        ('VACACIONES', 'Vacaciones'),
    ]

    id = models.AutoField(primary_key=True)
    payment_period = models.ForeignKey(PaymentPeriod, on_delete=models.CASCADE, related_name='daily_payments')
    date = models.DateField('Fecha')
    day_of_week = models.CharField('Día de la semana', max_length=20)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='COMPLETO')
    amount = models.DecimalField('Monto', max_digits=10, decimal_places=2, default=0.00)
    daily_rate = models.DecimalField('Tarifa diaria', max_digits=10, decimal_places=2)
    notes = models.CharField('Observaciones', max_length=200, null=True, blank=True)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.employee_name} - {self.status} - S/ {self.amount}"

    class Meta:
        verbose_name = 'Pago Diario'
        verbose_name_plural = 'Pagos Diarios'
        ordering = ['date']
        unique_together = ['payment_period', 'date']

    @property
    def employee_name(self):
        return f"{self.payment_period.employee.first_name} {self.payment_period.employee.last_name}"

    def save(self, *args, **kwargs):
        """Calcula automáticamente el monto basado en el estado y tarifa diaria"""
        if self.status == 'COMPLETO':
            self.amount = self.daily_rate
        elif self.status == 'PERMISO':
            self.amount = 0.00
        elif self.status == 'FALTA':
            self.amount = 0.00
        elif self.status == 'VACACIONES':
            self.amount = self.daily_rate  # Puedes ajustar según tu política
        
        super().save(*args, **kwargs)
        
        # Actualizar el total del período
        if self.payment_period:
            self.payment_period.calculate_total()
            self.payment_period.save()


class PaymentTemplate(models.Model):
    """Plantilla de tarifas diarias por empleado"""
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_templates')
    daily_rate = models.DecimalField('Tarifa diaria', max_digits=10, decimal_places=2)
    is_active = models.BooleanField('Activo', default=True)
    effective_date = models.DateField('Fecha efectiva')
    notes = models.TextField('Observaciones', max_length=500, null=True, blank=True)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - S/ {self.daily_rate}"

    class Meta:
        verbose_name = 'Plantilla de Pago'
        verbose_name_plural = 'Plantillas de Pago'
        ordering = ['-effective_date']
