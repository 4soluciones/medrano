from django.core.management.base import BaseCommand
from apps.sales.models import ProductCategory, Unit


class Command(BaseCommand):
    help = 'Inicializa categorías y unidades básicas para productos'

    def handle(self, *args, **options):
        self.stdout.write('Inicializando categorías y unidades básicas...')
        
        # Crear categorías básicas
        categories = [
            'IMPRESIÓN',
            'RENOVACIÓN',
            'ESTRUCTURA',
            'LETREROS',
            'PARASOL Y TAPASOLES',
            'LETREROS GEOMETRICOS',
            'PARANTES',
            'TARJETAS PERSONALES',
            'VOLANTES',
            'MODULOS',
            'OTROS',
        ]
        
        for category_name in categories:
            category, created = ProductCategory.objects.get_or_create(
                name=category_name.upper(),
                defaults={'is_enabled': True}
            )
            if created:
                self.stdout.write(f'Categoría creada: {category_name}')
            else:
                self.stdout.write(f'Categoría ya existe: {category_name}')
        
        # Crear unidades básicas
        units = [
            ('UN', 'Unidades'),
            ('M', 'Metros'),
            ('KG', 'Kilogramos'),
            ('M2', 'Metros Cuadrados'),
            ('PAR', 'Pares'),
            ('DOC', 'Docenas'),
        ]

        for unit_name, unit_description in units:
            unit, created = Unit.objects.get_or_create(
                name=unit_name.upper(),
                defaults={
                    'description': unit_description.upper(),
                    'is_enabled': True
                }
            )
            if created:
                self.stdout.write(f'Unidad creada: {unit_name} - {unit_description}')
            else:
                self.stdout.write(f'Unidad ya existe: {unit_name} - {unit_description}')
        
        self.stdout.write(
            self.style.SUCCESS('Inicialización completada exitosamente!')
        )
