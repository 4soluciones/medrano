from django.contrib import admin
from .models import Product, ProductCategory, ProductDetail, Unit

# Register your models here.

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_enabled', 'id')
    list_filter = ('is_enabled',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_enabled', 'id')
    list_filter = ('is_enabled',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type_product', 'product_category', 'stock_min', 'stock_max', 'is_enabled', 'creation_date')
    list_filter = ('type_product', 'product_category', 'is_enabled', 'creation_date')
    search_fields = ('name', 'code', 'observation')
    ordering = ('-creation_date',)
    readonly_fields = ('creation_date',)
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'code', 'observation', 'type_product', 'product_category')
        }),
        ('Control de Stock', {
            'fields': ('stock_min', 'stock_max')
        }),
        ('Estado', {
            'fields': ('is_enabled', 'creation_date')
        }),
    )


@admin.register(ProductDetail)
class ProductDetailAdmin(admin.ModelAdmin):
    list_display = ('product', 'unit', 'price_sale', 'price_purchase', 'is_enabled')
    list_filter = ('is_enabled', 'unit')
    search_fields = ('product__name', 'unit__name')
    ordering = ('product__name',)
