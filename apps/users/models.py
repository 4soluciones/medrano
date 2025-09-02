import decimal

from django.db import models
from django.contrib.auth.models import AbstractUser
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, Adjust


class CustomUser(AbstractUser):
    id = models.AutoField(primary_key=True)
    GENDER_CHOICES = (('1', 'MASCULINO'), ('2', 'FEMENINO'),)
    MARITAL_STATUS_CHOICES = (('1', 'SOLTERO(A)'), ('2', 'CASADO(A)'), ('3', 'VIUDO(A)'), ('4', 'DIVORCIADO(A)'),)
    LICENSE_TYPE_CHOICES = (
        ('1', 'A-I'), ('2', 'A-IIB'), ('3', 'A-IIIC'), ('4', 'A-IIIB'), ('5', 'A-IVA'), ('6', 'A-IIA'),
        ('7', 'A-IIIA'), ('8', 'B-I'), ('9', 'B-IIA'), ('10', 'B-IIB'), ('11', 'B-IIC'), ('12', 'SIN LICENCIA'),)
    NATIONALITY_CHOICES = (
        ('1', 'PERUANA'),
        ('2', 'ARGENTINA'),
        ('3', 'BOLIVIANA'),
        ('4', 'COLOMBIANA'),
        ('5', 'ECUATORIANA'),
        ('6', 'VENEZOLANA'),
        ('0', 'OTRA'),
    )
    EDUCATION_CHOICES = (
        ('1', 'PRIMARIA'), ('2', 'SECUNDARIA'), ('3', 'SUPERIOR TECNICO'),
        ('4', 'SUPERIOR UNIVERSITARIO'))
    document = models.CharField('Documento', max_length=15, null=True, blank=True)
    birth_date = models.DateField('Fecha de nacimiento', null=True, blank=True)
    gender = models.CharField('Sexo', max_length=1, choices=GENDER_CHOICES, default='1', )
    phone = models.CharField('Celular', max_length=12, null=True, blank=True)
    address = models.CharField('Direccion', max_length=200, null=True, blank=True)
    subsidiary = models.ForeignKey('hrm.Subsidiary', on_delete=models.CASCADE, null=True, blank=True)
    photo = models.ImageField(upload_to='employee/', default='employee/employee0.jpg', blank=True)
    photo_thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(100, 100)], source='photo', format='JPEG', options={'quality': 90})
    education = models.CharField('Educación', max_length=1, choices=EDUCATION_CHOICES, default='1', )
    nationality = models.CharField(max_length=2, choices=NATIONALITY_CHOICES, default='1',)
    n_license = models.CharField(max_length=12, null=True, blank=True)
    place_of_birth = models.CharField(max_length=400, null=True, blank=True)
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES, default='1', )
    cellphone = models.CharField(max_length=12, null=True, blank=True)
    reference = models.CharField(max_length=200, null=True, blank=True)
    observations = models.CharField(max_length=400, null=True, blank=True)
    has_access_system = models.BooleanField(default=False)
    has_access_to_sales = models.BooleanField(default=False)
    has_access_to_all = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
