from django.shortcuts import render
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.views.generic import TemplateView, View, CreateView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView
from http import HTTPStatus

from .models import *
import pytz
from django.contrib.auth.models import User
import json
from decimal import Decimal
import math
import random
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.files import ImageFieldFile
from django.template import loader
from datetime import datetime, date
from django.db import DatabaseError, IntegrityError
from django.core import serializers
from django.db.models import Min, Sum, Max, Q, Prefetch, Subquery, OuterRef, Value, Case, When
from medrano import settings
import os
from django.db.models import F, Count, CharField
from .views_API import query_apis_net_dni_ruc
from ..hrm.models import Subsidiary
from ..users.models import CustomUser


# Create your views here.

def get_client_list(request):
    if request.method == 'GET':
        client_set = Person.objects.filter(type='C').order_by('id')

        occupation_client_set = Person.objects.exclude(occupation__isnull=True).exclude(occupation=' ').exclude(occupation='')
        occupation_client_set = occupation_client_set.values('occupation').annotate(
            quantity_client=Count('id')).order_by('-quantity_client')

        occupation_name = [item['occupation'].upper() for item in occupation_client_set]

        return render(request, 'sales/client_list.html', {
            'client_set': client_set,
            'occupation_name': occupation_name,
            'quantity_occupation': [item['quantity_client'] for item in occupation_client_set],
        })


def modal_client_create(request):
    if request.method == 'GET':
        my_date = datetime.now()
        date_now = my_date.strftime("%Y-%m-%d")

        t = loader.get_template('sales/client_create.html')
        c = ({
            'date_now': date_now,

        })
        return JsonResponse({
            'form': t.render(c, request),
        })


def get_api_person(request):
    if request.method == 'GET':
        document_number = request.GET.get('nro_document')
        type_document = str(request.GET.get('type'))
        result = ''
        address = '-'
        first_name = ''
        second_name = ''
        paternal_name = ''
        maternal_name = ''
        client_obj = None
        client_set_search = Person.objects.filter(document=type_document, type='C', number=document_number)
        if client_set_search.exists():
            client_obj_search = client_set_search.last()
            if client_obj_search.address:
                address = client_obj_search.address
            client_id = client_obj_search.id
            names = client_obj_search.full_name
            first_name = client_obj_search.first_name
            second_name = client_obj_search.second_name
            surname = client_obj_search.surname
            second_surname = client_obj_search.second_surname
            phone1 = client_obj_search.phone1
            email = client_obj_search.email
            occupation = client_obj_search.occupation

            return JsonResponse({
                'pk': client_id,
                'names': names,
                'firstName': first_name,
                'secondName': second_name,
                'surname': surname,
                'secondSurname': second_surname,
                'phone1': phone1,
                'email': email,
                'occupation': occupation,
                'address': address,
                'message': 'Cliente encontrado en BD'
            },
                status=HTTPStatus.OK)

        else:
            if type_document == '01':
                type_name = 'DNI'
                r = query_apis_net_dni_ruc(document_number, type_name)
                name = r.get('nombres')
                paternal_name = r.get('apellidoPaterno')
                maternal_name = r.get('apellidoMaterno')
                if paternal_name is not None and len(paternal_name) > 0:

                    res = name.split()

                    if len(res) > 1:
                        if res[1] == 'DEL':
                            first_name = res[0] + ' ' + res[1] + ' ' + res[2]
                        else:
                            first_name = res[0]
                            second_name = res[1]
                    else:
                        first_name = res[0]

                    result = name + ' ' + paternal_name + ' ' + maternal_name

                    if len(result.strip()) != 0:
                        client_obj = Person(
                            full_name=result.upper(),
                            number=document_number,
                            document=type_document,
                            first_name=first_name,
                            second_name=second_name,
                            surname=paternal_name,
                            second_surname=maternal_name,
                        )
                        client_obj.save()

                    else:
                        data = {'error': 'NO EXISTE DNI. REGISTRE MANUALMENTE'}
                        response = JsonResponse(data)
                        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                        return response

                else:
                    data = {
                        'error': 'PROBLEMAS CON LA CONSULTA A LA RENIEC, FAVOR DE INTENTAR MAS TARDE O REGISTRE '
                                 'MANUALMENTE'}
                    response = JsonResponse(data)
                    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    return response

            elif type_document == '06':
                type_name = 'RUC'
                r = query_apis_net_dni_ruc(document_number, type_name)

                if r.get('numeroDocumento') == document_number:

                    business_name = r.get('nombre')
                    address_business = r.get('direccion')
                    result = business_name
                    address = address_business

                    client_obj = Person(
                        full_name=result.upper(),
                        number=document_number,
                        address=address.upper(),
                        document=type_document,
                    )
                    client_obj.save()

                else:
                    data = {'error': 'NO EXISTE RUC. REGISTRE MANUAL O CORREGIRLO'}
                    response = JsonResponse(data)
                    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    return response

        return JsonResponse({
            'pk': client_obj.id,
            'names': result,
            'firstName': first_name,
            'secondName': second_name,
            'surname': paternal_name,
            'secondSurname': maternal_name,
            'address': address},
            status=HTTPStatus.OK)

    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


# registrar cliente
@csrf_exempt
def save_client(request):
    if request.method == 'POST':
        full_name = ''
        client_exist_id = request.POST.get('client-id', '')

        client_type_document = request.POST.get('type-client', '')
        client_number_document = request.POST.get('client-number', '')

        client_first_name = request.POST.get('first-name', '')
        client_second_name = request.POST.get('second-name', '')
        client_surname = request.POST.get('surname', '')
        client_second_surname = request.POST.get('second-surname', '')
        client_business_name = request.POST.get('business-name', '')

        client_address = request.POST.get('client-address', '')
        client_occupation = request.POST.get('client-occupation', '')
        client_email = request.POST.get('client-email', '')
        client_phone1 = request.POST.get('client-phone1', '')
        client_phone2 = request.POST.get('client-phone2', '')

        # Construir el nombre completo según el tipo de documento
        if client_type_document == '06':
            full_name = client_business_name
        elif client_type_document == '01':
            full_name = client_first_name.upper() + ' ' + client_second_name.upper() + ' ' + client_surname.upper() + ' ' + client_second_surname.upper()

        # Crear y guardar el cliente
        client_obj = Person(
            type='C',  # Cliente
            document=client_type_document,
            number=client_number_document,
            full_name=full_name.upper(),
            first_name=client_first_name.upper() if client_first_name else '',
            second_name=client_second_name.upper() if client_second_name else '',
            surname=client_surname.upper() if client_surname else '',
            second_surname=client_second_surname.upper() if client_second_surname else '',
            address=client_address.upper() if client_address else '',
            occupation=client_occupation.upper() if client_occupation else '',
            email=client_email,
            phone1=client_phone1,
        )
        client_obj.save()

        return JsonResponse({
            'success': True,
            'message': 'Cliente registrado con éxito'
        }, status=HTTPStatus.OK)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def modal_client_update(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        client_obj = None
        if pk:
            client_obj = Person.objects.get(id=int(pk))
        t = loader.get_template('sales/client_update.html')
        c = ({
            'client_obj': client_obj,
        })
        return JsonResponse({
            'form': t.render(c, request),
        })


@csrf_exempt
def update_client(request):
    if request.method == 'POST':
        _id = request.POST.get('client-id', '')
        client_obj = None
        full_name = ''
        
        if _id:
            try:
                client_obj = Person.objects.get(id=int(_id))
            except Person.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Cliente no encontrado'
                }, status=HTTPStatus.OK)
        
        if client_obj is None:
            return JsonResponse({
                'success': False,
                'message': 'Problemas al obtener el cliente'
            }, status=HTTPStatus.OK)

        client_type_document = request.POST.get('type-client', '')
        client_number_document = request.POST.get('client-number', '')
        client_first_name = request.POST.get('first-name', '')
        client_second_name = request.POST.get('second-name', '')
        client_surname = request.POST.get('surname', '')
        client_second_surname = request.POST.get('second-surname', '')
        client_business_name = request.POST.get('business-name', '')
        client_address = request.POST.get('client-address', '')
        client_occupation = request.POST.get('client-occupation', '')
        client_email = request.POST.get('client-email', '')
        client_phone1 = request.POST.get('client-phone1', '')
        client_phone2 = request.POST.get('client-phone2', '')

        # Construir el nombre completo según el tipo de documento
        if client_type_document == '06':
            full_name = client_business_name
        elif client_type_document == '01':
            full_name = client_first_name.upper() + ' ' + client_second_name.upper() + ' ' + client_surname.upper() + ' ' + client_second_surname.upper()

        # Actualizar los campos del cliente
        client_obj.document = client_type_document
        client_obj.number = client_number_document
        client_obj.first_name = client_first_name.upper() if client_first_name else ''
        client_obj.second_name = client_second_name.upper() if client_second_name else ''
        client_obj.surname = client_surname.upper() if client_surname else ''
        client_obj.second_surname = client_second_surname.upper() if client_second_surname else ''
        client_obj.full_name = full_name.upper()
        client_obj.phone1 = client_phone1
        client_obj.phone2 = client_phone2
        client_obj.email = client_email
        client_obj.address = client_address.upper() if client_address else ''
        client_obj.occupation = client_occupation.upper() if client_occupation else ''
        
        client_obj.save()

        return JsonResponse({
            'success': True,
            'message': 'Datos actualizados correctamente',
        }, status=HTTPStatus.OK)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def get_correlative_order_by_subsidiary(subsidiary_obj=None, type_document=None):
    search = Order.objects.filter(subsidiary=subsidiary_obj, type=type_document)
    if search.exists():
        order_obj = search.last()
        correlative = order_obj.correlative
        if correlative:
            new_correlative = correlative + 1
            result = str(new_correlative).zfill(3)
        else:
            result = str(1).zfill(3)
    else:
        result = str(1).zfill(3)

    return result


def get_last_correlative_by_order_type(order_type=None, subsidiary_obj=None):
    """
    Obtiene el último correlativo filtrado por tipo de orden y sucursal
    """
    if not order_type:
        return None
    
    # Filtrar órdenes por tipo y sucursal
    orders = Order.objects.filter(type=order_type)
    if subsidiary_obj:
        orders = orders.filter(subsidiary=subsidiary_obj)
    
    # Obtener la última orden ordenada por correlativo descendente
    last_order = orders.order_by('-correlative').first()
    
    if last_order and last_order.correlative:
        return last_order.correlative + 1
    else:
        return 1


def order_client(request):
    if request.method == 'GET':
        search = request.GET.get('search')
        order = []
        if search:
            order_set = Order.objects.filter(client__full_name__icontains=search, type='C')
            for o in order_set:
                order.append({
                    'id': o.id,
                    'client': o.client.full_name,
                    'code': o.code,
                    'date': o.register_date.strftime("%d-%m-%Y")
                })
        return JsonResponse({
            'status': True,
            'order': order
        })


def get_order_by_client(request):
    if request.method == 'GET':
        order_id = request.GET.get('order_id', '')
        order_dict = []
        if order_id:
            order_obj = Order.objects.get(id=int(order_id))
            order_item = {
                'id': order_obj.id,
                'code': order_obj.code,
                'correlative': str(order_obj.correlative).zfill(3),
                'type': order_obj.type,
                'date': order_obj.register_date,
                'coin': order_obj.coin,
                'way_to_pay': order_obj.way_to_pay,
                'district': order_obj.district,
                'type_plan': order_obj.type_plan,
                'type_construction_site': order_obj.type_construction_site,
                'land_area': order_obj.land_area,
                'covered_area_level': order_obj.covered_area_level,
                'nro_level_design': order_obj.nro_level_design,
                'nro_level_different': order_obj.nro_level_different,
                'total_area': order_obj.total_area,
                'discount': order_obj.discount,
                'subtotal': order_obj.subtotal,
                'igv': order_obj.igv,
                'total': order_obj.total,
                'subsidiary': order_obj.subsidiary.id,
                'client_document': order_obj.client.document,
                'client_number': order_obj.client.number,
                'client_name': order_obj.client.full_name,
                'client_address': order_obj.client.address,
                'client_phone': order_obj.client.phone1,
                'client_mail': order_obj.client.email,
                'type_file': order_obj.type_file.id,
                'user_id': order_obj.user.id,
                'user': order_obj.user.first_name,
                'details': []
            }
            for d in order_obj.orderdetail_set.all().order_by('id'):
                details = {
                    'id': d.id,
                    'code': d.code,
                    'include': d.include,
                    'quantity': d.quantity,
                    'price_unit': d.price_unit,
                    'specialty_text': d.specialty.name,
                    'specialty_id': d.specialty.id,
                    'specialty_element_text': d.specialty_element.name,
                    'specialty_element_id': d.specialty_element.id,
                }
                # for e in d.specialty.specialtyelement_set.all().order_by('id'):
                #     specialty_element = {
                #         'id': e.id,
                #         'code': e.code,
                #         'name': e.name,
                #         'unit': e.unit,
                #         'price': e.price,
                #     }
                #     details.get('specialty_element').append(specialty_element)
                order_item.get('details').append(details)
            order_dict.append(order_item)

            return JsonResponse({
                'success': True,
                'order': order_dict,
            }, status=HTTPStatus.OK, content_type="application/json")
        return JsonResponse({
            'success': False,
            'message': 'Problemas al obtener el cliente, intente nuevamente'
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion. Contactar con sistemas'}, status=HTTPStatus.BAD_REQUEST)


def get_correlative_order(request):
    if request.method == 'GET':
        doc_type = request.GET.get('doc_type', '')
        subsidiary = request.GET.get('subsidiary', '')
        subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary))
        correlative = get_correlative_order_by_subsidiary(subsidiary_obj=subsidiary_obj, type_document=doc_type)
        correlative_order_service = 'PY-' + str(correlative).zfill(3) + '-2023-' + str(subsidiary_obj.serial)
        return JsonResponse({
            'success': True,
            'message': 'Cambios guardados con exito.',
            'correlative': correlative,
            'serial': subsidiary_obj.serial,
            'correlative_order_service': correlative_order_service
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion. Actualice'}, status=HTTPStatus.BAD_REQUEST)


def get_product_list(request):
    if request.method == 'GET':
        product_set = Product.objects.all().order_by('id')
        category_set = ProductCategory.objects.filter(is_enabled=True).order_by('name')
        unit_set = Unit.objects.filter(is_enabled=True).order_by('name')
        
        return render(request, 'sales/product_list.html', {
            'product_set': product_set,
            'category_set': category_set,
            'unit_set': unit_set,
        })


def modal_product_create(request):
    if request.method == 'GET':
        category_set = ProductCategory.objects.filter(is_enabled=True).order_by('name')
        unit_set = Unit.objects.filter(is_enabled=True).order_by('name')
        
        t = loader.get_template('sales/product_create.html')
        c = ({
            'category_set': category_set,
            'unit_set': unit_set,
        })
        return JsonResponse({
            'form': t.render(c, request),
        })


@csrf_exempt
def save_product(request):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.POST.get('product-name', '').strip()
            code = request.POST.get('product-code', '').strip()
            observation = request.POST.get('product-observation', '').strip()
            category_id = request.POST.get('product-category', '')
            type_product = request.POST.get('product-type', 'P')
            stock_min = request.POST.get('product-stock-min', 0)
            stock_max = request.POST.get('product-stock-max', 0)
            
            # Validaciones básicas
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre del producto es obligatorio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not category_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una categoría'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar si ya existe un producto con el mismo código
            if code and Product.objects.filter(code=code).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe un producto con el código: ' + code
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Crear el producto
            category_obj = ProductCategory.objects.get(id=int(category_id))
            product_obj = Product(
                name=name.upper(),
                code=code.upper() if code else None,
                observation=observation.upper() if observation else '',
                product_category=category_obj,
                type_product=type_product,
                stock_min=int(stock_min) if stock_min else 0,
                stock_max=int(stock_max) if stock_max else 0,
                is_enabled=True
            )
            product_obj.save()
            
            # Crear el detalle del producto con precios
            unit_id = request.POST.get('product-unit', '')
            price_sale = request.POST.get('product-price-sale', 0)
            price_purchase = request.POST.get('product-price-purchase', 0)
            
            if unit_id and (price_sale or price_purchase):
                unit_obj = Unit.objects.get(id=int(unit_id))
                product_detail_obj = ProductDetail(
                    product=product_obj,
                    unit=unit_obj,
                    price_sale=decimal.Decimal(price_sale) if price_sale else 0,
                    price_purchase=decimal.Decimal(price_purchase) if price_purchase else 0,
                    is_enabled=True
                )
                product_detail_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Producto registrado con éxito',
                'product_id': product_obj.id
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar el producto: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def modal_product_update(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        product_obj = None
        category_set = ProductCategory.objects.filter(is_enabled=True).order_by('name')
        unit_set = Unit.objects.filter(is_enabled=True).order_by('name')
        
        if pk:
            try:
                product_obj = Product.objects.get(id=int(pk))
            except Product.DoesNotExist:
                pass
        
        t = loader.get_template('sales/product_update.html')
        c = ({
            'product_obj': product_obj,
            'category_set': category_set,
            'unit_set': unit_set,
        })
        return JsonResponse({
            'form': t.render(c, request),
        })


@csrf_exempt
def update_product(request):
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product-id', '')
            if not product_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de producto no proporcionado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            product_obj = Product.objects.get(id=int(product_id))
            
            # Obtener datos del formulario
            name = request.POST.get('product-name', '').strip()
            code = request.POST.get('product-code', '').strip()
            observation = request.POST.get('product-observation', '').strip()
            category_id = request.POST.get('product-category', '')
            type_product = request.POST.get('product-type', 'P')
            stock_min = request.POST.get('product-stock-min', 0)
            stock_max = request.POST.get('product-stock-max', 0)
            
            # Validaciones básicas
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre del producto es obligatorio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not category_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una categoría'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar si ya existe un producto con el mismo código (excluyendo el actual)
            if code and Product.objects.filter(code=code).exclude(id=product_obj.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe un producto con el código: ' + code
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Actualizar el producto
            category_obj = ProductCategory.objects.get(id=int(category_id))
            product_obj.name = name.upper()
            product_obj.code = code.upper() if code else None
            product_obj.observation = observation.upper() if observation else ''
            product_obj.product_category = category_obj
            product_obj.type_product = type_product
            product_obj.stock_min = int(stock_min) if stock_min else 0
            product_obj.stock_max = int(stock_max) if stock_max else 0
            product_obj.save()
            
            # Actualizar o crear el detalle del producto con precios
            unit_id = request.POST.get('product-unit', '')
            price_sale = request.POST.get('product-price-sale', 0)
            price_purchase = request.POST.get('product-price-purchase', 0)
            
            if unit_id:
                unit_obj = Unit.objects.get(id=int(unit_id))
                
                # Buscar si ya existe un ProductDetail para este producto y unidad
                try:
                    product_detail_obj = ProductDetail.objects.get(product=product_obj, unit=unit_obj)
                    product_detail_obj.price_sale = decimal.Decimal(price_sale) if price_sale else 0
                    product_detail_obj.price_purchase = decimal.Decimal(price_purchase) if price_purchase else 0
                    product_detail_obj.save()
                except ProductDetail.DoesNotExist:
                    # Crear nuevo detalle si no existe
                    if price_sale or price_purchase:
                        product_detail_obj = ProductDetail(
                            product=product_obj,
                            unit=unit_obj,
                            price_sale=decimal.Decimal(price_sale) if price_sale else 0,
                            price_purchase=decimal.Decimal(price_purchase) if price_purchase else 0,
                            is_enabled=True
                        )
                        product_detail_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Producto actualizado correctamente'
            }, status=HTTPStatus.OK)
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Producto no encontrado'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar el producto: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def modal_category_create(request):
    if request.method == 'GET':
        t = loader.get_template('sales/category_create.html')
        c = ({})
        return JsonResponse({
            'form': t.render(c, request),
        })


@csrf_exempt
def save_category(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('category-name', '').strip()
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de la categoría es obligatorio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar si ya existe una categoría con el mismo nombre
            if ProductCategory.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una categoría con el nombre: ' + name
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Crear la categoría
            category_obj = ProductCategory(
                name=name.upper(),
                is_enabled=True
            )
            category_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Categoría registrada con éxito',
                'category_id': category_obj.id,
                'category_name': category_obj.name
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar la categoría: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def modal_unit_create(request):
    if request.method == 'GET':
        t = loader.get_template('sales/unit_create.html')
        c = ({})
        return JsonResponse({
            'form': t.render(c, request),
        })


@csrf_exempt
def save_unit(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('unit-name', '').strip()
            description = request.POST.get('unit-description', '').strip()
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de la unidad es obligatorio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar si ya existe una unidad con el mismo nombre
            if Unit.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una unidad con el nombre: ' + name
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Crear la unidad
            unit_obj = Unit(
                name=name.upper(),
                description=description.upper() if description else '',
                is_enabled=True
            )
            unit_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Unidad registrada con éxito',
                'unit_id': unit_obj.id,
                'unit_name': unit_obj.name
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar la unidad: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def get_product_data(request):
    if request.method == 'GET':
        product_id = request.GET.get('product_id', '')
        if product_id:
            try:
                product_obj = Product.objects.get(id=int(product_id))
                product_detail = ProductDetail.objects.filter(product=product_obj, is_enabled=True).first()
                
                data = {
                    'id': product_obj.id,
                    'name': product_obj.name,
                    'code': product_obj.code or '',
                    'type': product_obj.get_type_product_display(),
                    'category': product_obj.product_category.name,
                    'stock_min': product_obj.stock_min,
                    'stock_max': product_obj.stock_max,
                    'is_enabled': product_obj.is_enabled,
                    'price_sale': float(product_detail.price_sale) if product_detail else 0,
                    'price_purchase': float(product_detail.price_purchase) if product_detail else 0,
                    'unit': product_detail.unit.name if product_detail else '',
                }
                
                return JsonResponse({
                    'success': True,
                    'product': data
                }, status=HTTPStatus.OK)
                
            except Product.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto no encontrado'
                }, status=HTTPStatus.NOT_FOUND)
        
        return JsonResponse({
            'success': False,
            'message': 'ID de producto no proporcionado'
        }, status=HTTPStatus.BAD_REQUEST)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


# =============================================================================
# NUEVAS VISTAS PARA EL SISTEMA DE ÓRDENES MODERNO
# =============================================================================

def order_list(request):
    """Vista principal del listado de órdenes"""
    if request.method == 'GET':
        subsidiary_set = Subsidiary.objects.all()
        user_set = CustomUser.objects.filter(is_active=True, is_staff=False)
        client_set = Person.objects.filter(type='C')
        # Usar zona horaria de Perú (GMT-5)
        peru_tz = pytz.timezone('America/Lima')
        my_date = datetime.now(peru_tz)
        date_now = my_date.strftime("%Y-%m-%d")
        product_set = Product.objects.filter(is_enabled=True).select_related('product_category')
        
        # Obtener cuentas de caja para los modales (solo de la sucursal del usuario)
        try:
            from apps.accounting.models import Cash
            if request.user.subsidiary:
                cash_accounts = Cash.objects.filter(subsidiary=request.user.subsidiary).select_related('subsidiary')
            else:
                # Si el usuario no tiene sucursal asignada, mostrar todas las cuentas
                cash_accounts = Cash.objects.all().select_related('subsidiary')
        except ImportError:
            cash_accounts = []
        
        return render(request, 'sales/order_list.html', {
            'subsidiary_set': subsidiary_set,
            'user_set': user_set,
            'client_set': client_set,
            'product_set': product_set,
            'date_now': date_now,
            'cash_accounts': cash_accounts,
        })
    elif request.method == 'POST':
        try:
            # Filtrar órdenes según parámetros
            subsidiary_id = request.POST.get('subsidiary')
            user_id = request.POST.get('user')
            order_type = request.POST.get('order_type')
            status = request.POST.get('status')
            date_from = request.POST.get('date_from')
            date_to = request.POST.get('date_to')
            client_id_filter = request.POST.get('client_id_filter')
            
            orders = Order.objects.all()
        
            if subsidiary_id and subsidiary_id != '0':
                orders = orders.filter(subsidiary_id=subsidiary_id)
            if user_id and user_id != '0':
                orders = orders.filter(user_id=user_id)
            if order_type and order_type != '0':
                orders = orders.filter(type=order_type)
            if status and status != '0':
                orders = orders.filter(status=status)
            if client_id_filter and client_id_filter != '':
                orders = orders.filter(client_id=client_id_filter)

            # Filtros de fecha - Si no se especifican fechas, cargar solo del día actual
            if not date_from and not date_to:
                # Usar zona horaria de Perú (GMT-5)
                peru_tz = pytz.timezone('America/Lima')
                current_date = datetime.now(peru_tz).strftime('%Y-%m-%d')
                date_from = current_date
                date_to = current_date
                orders = orders.filter(register_date=current_date)
            else:
                if date_from:
                    orders = orders.filter(register_date__gte=date_from).order_by('id')
                if date_to:
                    orders = orders.filter(register_date__lte=date_to).order_by('id')

            orders = orders.select_related('client', 'user', 'subsidiary', 'completed_by', 'delivered_by').prefetch_related('orderdetail_set')

            # Crear diccionario con cálculos de saldo para cada orden
            order_dict = []
            for order in orders:
                # if order.cash_pay > 0:
                #     balance = order.total - order.cash_pay
                # else:
                #     balance = order.total - order.cash_advance
                # if balance < 0:
                #     balance = Decimal('0.00')
                balance = order.total - order.cash_advance
                if order.cash_advance + order.cash_pay == order.total:
                    balance = decimal.Decimal(0.00)
                order_data = {
                    'id': order.id,
                    'order': order,
                    'type_order': order.type,
                    'type_order_display': order.get_type_display(),
                    'register_date': order.register_date,
                    'delivery_date': order.delivery_date,
                    'serial': order.subsidiary.serial,
                    'correlative': order.correlative,
                    'status': order.status,
                    'status_display': order.get_status_display(),
                    'delivery_status': order.delivery_status,
                    'delivery_status_display': order.get_delivery_status_display(),
                    'client': order.client.full_name,
                    'client_document': order.client.document,
                    'client_number': order.client.number,
                    'user': order.user.first_name,
                    'details': [],
                    'balance': str(round(balance, 2)),
                    'cash_pay': str(round(order.cash_pay, 2)),
                    'total': str(round(order.total, 2)),
                    'cash_advance': str(round(order.cash_advance, 2)),
                    # Información de completado
                    'completed_by': order.completed_by.first_name if order.completed_by else None,
                    'completed_at': order.completed_at,
                    # Información de entrega
                    'delivered_by': order.delivered_by.first_name if order.delivered_by else None,
                    'delivered_at': order.delivered_at,
                    # 'is_paid': order.cash_pay >= order.total if order.cash_pay > 0 else False,
                    # 'has_advance': order.cash_advance > 0,
                    # 'payment_status': 'PAID' if order.cash_pay >= order.total else 'PARTIAL' if order.cash_pay > 0 else 'PENDING'
                }
                for detail in order.orderdetail_set.all():
                    product_id = ''
                    product_name = ''
                    if detail.product:
                        product_id = detail.product.id
                        product_name = detail.product.name
                    detail_data = {
                        'id': detail.id,
                        'product': product_id,
                        'quantity': str(round(detail.quantity, 0)),
                        'product_name': product_name,
                        'description': detail.product_name,
                        'observation': detail.observation,
                    }
                    order_data.get('details').append(detail_data)
                order_dict.append(order_data)

            # Calcular totales del período
            total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
            total_cash_advance = orders.aggregate(total=Sum('cash_advance'))['total'] or 0
            total_cash_pay = orders.aggregate(total=Sum('cash_pay'))['total'] or 0
            
            # El balance total se calcula basándose en los pagos reales
            if total_cash_pay > 0:
                total_balance = total_sales - total_cash_pay
            else:
                total_balance = total_sales - total_cash_advance

            tpl = loader.get_template('sales/order_list_grid.html')
            context = {
                'order_dict': order_dict,
                'total_sales': total_sales,
                'total_cash_advance': total_cash_advance,
                'total_cash_pay': total_cash_pay,
                'total_balance': total_balance,
                'date_from': date_from,
                'date_to': date_to
            }

            return JsonResponse({
                'grid': tpl.render(context, request),
            }, status=HTTPStatus.OK)
        
        except Exception as e:
            print(e)
            return JsonResponse({
                'success': False,
                'message': f'Error al cargar las órdenes: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@csrf_exempt
def order_save(request):
    """Vista para guardar nueva orden"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            order_type = request.POST.get('order_type')
            client_id = request.POST.get('client_id')
            user_id = request.POST.get('user_id')
            subsidiary_id = request.POST.get('subsidiary_id')
            register_date = request.POST.get('register_date')
            delivery_date = request.POST.get('delivery_date')
            way_to_pay = request.POST.get('way_to_pay', 'E')
            cash_advance = request.POST.get('advance_input', 0)
            voucher_type = request.POST.get('voucher_type', 'T')
            observation = request.POST.get('observation', '')
            
            # Validaciones básicas
            if not client_id or not user_id or not subsidiary_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Faltan datos obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener objetos relacionados
            client_obj = Person.objects.get(id=int(client_id))
            user_obj = CustomUser.objects.get(id=int(user_id))
            subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary_id))
            
            # Obtener el último correlativo filtrado por tipo de orden
            last_correlative = get_last_correlative_by_order_type(order_type, subsidiary_obj)
            
            # correlative = get_correlative_order_by_subsidiary(subsidiary_obj, order_type)
            code = f'0{subsidiary_obj.serial}-{str(last_correlative).zfill(4)}'
            
            # Verificar si el adelanto es igual al total para marcar como completado
            cash_advance_decimal = decimal.Decimal(str(cash_advance)) if cash_advance else decimal.Decimal('0.00')
            
            # Crear la orden
            order_obj = Order(
                code=code,
                serial=f'0{subsidiary_obj.serial}',
                correlative=last_correlative,
                type=order_type,
                client=client_obj,
                user=user_obj,
                subsidiary=subsidiary_obj,
                register_date=register_date,
                delivery_date=delivery_date if delivery_date else None,
                way_to_pay=way_to_pay,
                cash_advance=cash_advance_decimal,
                voucher_type=voucher_type,
                observation=observation.upper(),
                status='P'
            )
            order_obj.save()
            
            # Procesar detalles de la orden
            details_data = request.POST.get('details', '')
            if details_data:
                details = json.loads(details_data)
                for detail in details:
                    product_id = detail.get('product_id')
                    product_name = detail.get('product_name', '')
                    quantity = decimal.Decimal(detail.get('quantity', 0))
                    price_unit = decimal.Decimal(detail.get('price_unit', 0))
                    # observation = str(detail.get('observation', ''))

                    if quantity and price_unit:
                        # Si hay product_id, usar el producto existente
                        if product_id:
                            try:
                                product_obj = Product.objects.get(id=int(product_id))
                            except Product.DoesNotExist:
                                product_obj = None
                        else:
                            product_obj = None
                        
                        order_detail = OrderDetail(
                            order=order_obj,
                            product=product_obj,
                            product_name=product_name.upper(),
                            quantity=decimal.Decimal(quantity),
                            price_unit=decimal.Decimal(price_unit),
                            # observation=observation
                        )
                        order_detail.save()
            
            # Calcular totales
            order_obj.calculate_totals()
            
            # Verificar si el adelanto es igual al total para marcar como completado
            if cash_advance_decimal >= order_obj.total and order_obj.total > 0:
                order_obj.status = 'C'  # COMPLETADO
                order_obj.cash_pay = order_obj.total  # El pago total es igual al total
                order_obj.save()
            
            # Generar PDF del ticket automáticamente
            try:
                from .views_PDF import generate_ticket_pdf
                pdf_content = generate_ticket_pdf(order_obj.id)
                if pdf_content:
                    # Generar nombre del archivo PDF
                    # Manejar la fecha correctamente (puede ser string o datetime)
                    if hasattr(order_obj.register_date, 'strftime'):
                        # Si es un objeto datetime
                        date_str = order_obj.register_date.strftime('%Y-%m-%d')
                    else:
                        # Si es un string, intentar parsearlo
                        try:
                            from datetime import datetime
                            if isinstance(order_obj.register_date, str):
                                # Asumir formato YYYY-MM-DD
                                date_str = order_obj.register_date
                            else:
                                # Fallback a fecha actual
                                date_str = datetime.now().strftime('%Y-%m-%d')
                        except:
                            # Fallback a fecha actual si hay error
                            from datetime import datetime
                            date_str = datetime.now().strftime('%Y-%m-%d')

                    order_type = 'Order' if order_obj.type == 'O' else 'Cotizacion'

                    pdf_filename = f"{order_type}_{order_obj.code}.pdf"
                    
                    # Convertir el contenido del PDF a base64 para enviarlo en la respuesta
                    import base64
                    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                    

                    return JsonResponse({
                        'success': True,
                        'message': f'{order_obj.get_type_display()} registrada correctamente',
                        'order_id': order_obj.id,
                        'order_code': order_obj.code,
                        'last_correlative': last_correlative,
                        'pdf_content': pdf_base64,
                        'pdf_filename': pdf_filename
                    }, status=HTTPStatus.OK)
                else:

                    return JsonResponse({
                        'success': True,
                        'message': f'{order_obj.get_type_display()} registrada correctamente',
                        'order_id': order_obj.id,
                        'order_code': order_obj.code,
                        'last_correlative': last_correlative
                    }, status=HTTPStatus.OK)
            except Exception as e:

                return JsonResponse({
                    'success': True,
                    'message': f'{order_obj.get_type_display()} registrada correctamente',
                    'order_id': order_obj.id,
                    'order_code': order_obj.code,
                    'last_correlative': last_correlative
                }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar la orden: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def get_order_for_edit(request):
    """Vista para obtener datos de una orden para edición en el modal"""
    if request.method == 'GET':
        order_id = request.GET.get('order_id')
        if order_id:
            try:
                order_obj = Order.objects.select_related(
                    'client', 'user', 'subsidiary'
                ).prefetch_related('orderdetail_set__product').get(id=int(order_id))
                
                # Preparar datos de la orden
                order_data = {
                    'id': order_obj.id,
                    'code': order_obj.code,
                    'type': order_obj.type,
                    'client_id': order_obj.client.id if order_obj.client else None,
                    'user_id': order_obj.user.id if order_obj.user else None,
                    'subsidiary_id': order_obj.subsidiary.id if order_obj.subsidiary else None,
                    'register_date': order_obj.register_date.strftime('%Y-%m-%d') if order_obj.register_date else None,
                    'delivery_date': order_obj.delivery_date.strftime('%Y-%m-%d') if order_obj.delivery_date else None,
                    'way_to_pay': order_obj.way_to_pay,
                    'cash_advance': float(order_obj.cash_advance),
                    'voucher_type': order_obj.voucher_type,
                    'observation': order_obj.observation or '',
                    'status': order_obj.status,
                    'subtotal': float(order_obj.subtotal),
                    'igv': float(order_obj.igv),
                    'total': float(order_obj.total),
                    'details': []
                }
                
                # Preparar detalles
                for detail in order_obj.orderdetail_set.all():
                    detail_data = {
                        'id': detail.id,
                        'product_id': detail.product.id if detail.product else None,
                        'product_name': detail.product_name or (detail.product.name if detail.product else ''),
                        'quantity': float(detail.quantity),
                        'price_unit': float(detail.price_unit),
                        'subtotal': float(detail.quantity * detail.price_unit),
                        'observation': detail.observation
                    }
                    order_data['details'].append(detail_data)
                
                return JsonResponse({
                    'success': True,
                    'order': order_data
                }, status=HTTPStatus.OK)
                
            except Order.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Orden no encontrada'
                }, status=HTTPStatus.NOT_FOUND)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error al cargar la orden: {str(e)}'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        
        return JsonResponse({
            'success': False,
            'message': 'ID de orden no proporcionado'
        }, status=HTTPStatus.BAD_REQUEST)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def order_update(request):
    """Vista para actualizar orden existente"""
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            if not order_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de orden no proporcionado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            order_obj = Order.objects.get(id=int(order_id))
            
            # Actualizar campos básicos
            order_obj.type = request.POST.get('order_type', order_obj.type)
            order_obj.client_id = request.POST.get('client_id')
            order_obj.user_id = request.POST.get('user_id')
            order_obj.subsidiary_id = request.POST.get('subsidiary_id')
            order_obj.register_date = request.POST.get('register_date')
            order_obj.delivery_date = request.POST.get('delivery_date') if request.POST.get('delivery_date') else None
            order_obj.way_to_pay = request.POST.get('way_to_pay', 'E')
            order_obj.cash_advance = decimal.Decimal(request.POST.get('cash_advance', 0))
            order_obj.voucher_type = request.POST.get('voucher_type', 'T')
            order_obj.observation = request.POST.get('observation', '')
            
            order_obj.save()
            
            # Actualizar detalles
            details_data = request.POST.get('details', '')
            if details_data:
                # Eliminar detalles existentes
                order_obj.orderdetail_set.all().delete()
                
                # Crear nuevos detalles
                details = json.loads(details_data)
                for detail in details:
                    product_id = detail.get('product_id')
                    product_name = detail.get('product_name', '')
                    quantity = detail.get('quantity', 0)
                    price_unit = detail.get('price_unit', 0)
                    observation = detail.get('observation', '')
                    
                    if quantity and price_unit:
                        # Si hay product_id, usar el producto existente
                        if product_id:
                            try:
                                product_obj = Product.objects.get(id=int(product_id))
                                product_name = product_obj.name
                            except Product.DoesNotExist:
                                product_obj = None
                        else:
                            product_obj = None
                        
                        order_detail = OrderDetail(
                            order=order_obj,
                            product=product_obj,
                            product_name=product_name,
                            quantity=decimal.Decimal(quantity),
                            price_unit=decimal.Decimal(price_unit),
                            observation=observation.upper()
                        )
                        order_detail.save()
            
            # Calcular totales
            order_obj.calculate_totals()
            
            return JsonResponse({
                'success': True,
                'message': 'Orden actualizada correctamente'
            }, status=HTTPStatus.OK)
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar la orden: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def order_detail_modal(request):
    """Vista para mostrar modal de detalles de orden"""
    if request.method == 'GET':
        order_id = request.GET.get('order_id')
        if order_id:
            try:
                order_obj = Order.objects.select_related(
                    'client', 'user', 'subsidiary'
                ).prefetch_related('orderdetail_set__product').get(id=int(order_id))
                
                t = loader.get_template('sales/order_detail_modal.html')
                context = {'order': order_obj}
                
                return JsonResponse({
                    'success': True,
                    'form': t.render(context, request),
                })
                
            except Order.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Orden no encontrada'
                }, status=HTTPStatus.NOT_FOUND)
        
        return JsonResponse({
            'success': False,
            'message': 'ID de orden no proporcionado'
        }, status=HTTPStatus.BAD_REQUEST)


def get_products_for_order(request):
    """Vista para obtener productos para la orden"""
    if request.method == 'GET':
        category_id = request.GET.get('category_id')
        search_term = request.GET.get('search', '')
        product_type = request.GET.get('product_type', '')
        
        products = Product.objects.filter(is_enabled=True)
        
        if category_id and category_id != '0':
            products = products.filter(product_category_id=int(category_id))
        
        if product_type:
            products = products.filter(type_product=product_type)
        
        if search_term:
            products = products.filter(
                Q(name__icontains=search_term) | Q(code__icontains=search_term)
            )
        
        products = products.select_related('product_category').prefetch_related('productdetail_set__unit')
        
        product_list = []
        for product in products:
            product_detail = product.productdetail_set.filter(is_enabled=True).first()
            product_data = {
                'id': product.id,
                'name': product.name,
                'code': product.code or '',
                'category': product.product_category.name,
                'type': product.type_product,
                'price_sale': float(product_detail.price_sale) if product_detail else 0,
                'unit': product_detail.unit.name if product_detail else '',
            }
            product_list.append(product_data)
        
        return JsonResponse({
            'success': True,
            'products': product_list
        }, status=HTTPStatus.OK)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def create_client(request):
    """Vista para crear nuevo cliente desde el modal de órdenes"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            document = request.POST.get('document', '')
            number = request.POST.get('number', '')
            full_name = request.POST.get('full_name')
            address = request.POST.get('address', '')
            phone = request.POST.get('phone', '')
            email = request.POST.get('email', '')
            
            # Validaciones básicas - solo el nombre es obligatorio
            if not full_name:
                return JsonResponse({
                    'success': False,
                    'message': 'El campo Nombre Completo es obligatorio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Si se proporciona documento y número, verificar si ya existe
            if document and number:
                existing_client = Person.objects.filter(document=document, number=number, type='C').first()
                if existing_client:
                    # Si ya existe, devolver los datos del cliente existente
                    return JsonResponse({
                        'success': True,
                        'message': f'Cliente ya existe con {document} número {number}',
                        'client': {
                            'id': existing_client.id,
                            'full_name': existing_client.full_name,
                            'document': existing_client.document,
                            'number': existing_client.number,
                            'address': existing_client.address or '',
                            'phone': existing_client.phone1 or '',
                            'email': existing_client.email or ''
                        },
                        'existing': True
                    }, status=HTTPStatus.OK)
            
            # Crear el cliente si no existe
            client_obj = Person(
                type='C',  # Cliente
                document=document if document else '',
                number=number if number else '',
                full_name=full_name.upper(),
                address=address.upper() if address else '',
                phone1=phone if phone else '',
                email=email if email else ''
            )
            client_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cliente creado exitosamente',
                'client': {
                    'id': client_obj.id,
                    'full_name': client_obj.full_name,
                    'document': client_obj.document,
                    'number': client_obj.number,
                    'address': client_obj.address or '',
                    'phone': client_obj.phone1 or '',
                    'email': client_obj.email or ''
                },
                'existing': False
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear el cliente: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def get_serial_order(request):
    """Vista para obtener la serie de la sucursal"""
    if request.method == 'GET':
        subsidiary_id = request.GET.get('subsidiary', '')
        if subsidiary_id:
            try:
                subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary_id))
                return JsonResponse({
                    'success': True,
                    'serial': subsidiary_obj.serial
                }, status=HTTPStatus.OK)
            except Subsidiary.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Sucursal no encontrada'
                }, status=HTTPStatus.NOT_FOUND)
        
        return JsonResponse({
            'success': False,
            'message': 'ID de sucursal no proporcionado'
        }, status=HTTPStatus.BAD_REQUEST)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def search_clients_autocomplete(request):
    """Vista para autocompletado de clientes en filtros"""
    if request.method == 'GET':
        search_term = request.GET.get('search', '')
        
        if len(search_term) < 2:
            return JsonResponse({
                'success': False,
                'message': 'Término de búsqueda muy corto'
            }, status=HTTPStatus.BAD_REQUEST)
        
        try:
            # Buscar clientes por nombre o documento
            clients = Person.objects.filter(
                type='C'
            ).filter(
                Q(full_name__icontains=search_term) |
                Q(number__icontains=search_term)
            ).select_related().order_by('full_name')[:10]  # Limitar a 10 resultados
            
            client_list = []
            for client in clients:
                client_data = {
                    'id': client.id,
                    'full_name': client.full_name,
                    'document': client.document,
                    'number': client.number,
                    'address': client.address or '',
                    'phone': client.phone1 or '',
                    'email': client.email or ''
                }
                client_list.append(client_data)
            
            return JsonResponse({
                'success': True,
                'clients': client_list
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al buscar clientes: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def order_status_modal(request):
    """Vista para mostrar modal de cambio de estado de orden"""
    if request.method == 'GET':
        order_id = request.GET.get('order_id')
        if order_id:
            try:
                order_obj = Order.objects.select_related('client').get(id=int(order_id))
                user_set = CustomUser.objects.filter(is_active=True, is_staff=False)
                
                t = loader.get_template('sales/order_status_modal.html')
                context = {
                    'order': order_obj,
                    'user_set': user_set
                }
                
                return JsonResponse({
                    'success': True,
                    'form': t.render(context, request),
                })
                
            except Order.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Orden no encontrada'
                }, status=HTTPStatus.NOT_FOUND)
        
        return JsonResponse({
            'success': False,
            'message': 'ID de orden no proporcionado'
        }, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def update_order_status(request):
    """Vista para actualizar el estado de una orden"""
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            new_status = request.POST.get('status')
            completed_by_id = request.POST.get('completed_by')
            cancellation_reason = request.POST.get('cancellation_reason', '')
            
            if not order_id or not new_status or not completed_by_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Faltan datos obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Validar que el estado sea válido
            valid_statuses = ['P', 'C', 'A']
            if new_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'message': 'Estado no válido'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Si es anulación, validar que se haya proporcionado el motivo
            if new_status == 'A' and not cancellation_reason.strip():
                return JsonResponse({
                    'success': False,
                    'message': 'Debe proporcionar el motivo de la anulación'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la orden y el usuario
            order_obj = Order.objects.get(id=int(order_id))
            completed_by_user = CustomUser.objects.get(id=int(completed_by_id))
            
            old_status = order_obj.status
            order_obj.status = new_status
            
            # Si se está completando la orden, guardar quien la completó y cuándo
            if new_status == 'C':
                order_obj.completed_by = completed_by_user
                order_obj.completed_at = datetime.now()
            
            # Si se está anulando, guardar el motivo
            if new_status == 'A':
                order_obj.cancellation_reason = cancellation_reason
            
            order_obj.save()
            
            # Mensaje de confirmación
            status_display = {
                'P': 'PENDIENTE',
                'C': 'COMPLETADO',
                'A': 'ANULADO'
            }
            
            message = f'Estado de la orden actualizado de {status_display[old_status]} a {status_display[new_status]}'
            if new_status == 'C':
                message += f' por {completed_by_user.first_name} {completed_by_user.last_name}'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'order_id': order_id,
                'old_status': old_status,
                'new_status': new_status
            }, status=HTTPStatus.OK)
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar el estado: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


# =============================================================================
# VISTAS DEL DASHBOARD
# =============================================================================

def dashboard_stats(request):
    """Vista para obtener estadísticas del dashboard"""
    if request.method == 'GET':
        try:
            # Obtener la sucursal del usuario actual
            user_subsidiary = request.user.subsidiary
            
            # Filtrar órdenes por sucursal si el usuario tiene una asignada
            orders = Order.objects.all()
            if user_subsidiary:
                orders = orders.filter(subsidiary=user_subsidiary)
            
            # Estadísticas generales
            total_orders = orders.count()
            completed_orders = orders.filter(status='C').count()
            pending_orders = orders.filter(status='P').count()
            total_sales = orders.filter(status='C').aggregate(total=Sum('total'))['total'] or 0
            
            stats = {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'pending_orders': pending_orders,
                'total_sales': float(total_sales)
            }
            
            return JsonResponse({
                'success': True,
                'stats': stats
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cargar estadísticas: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def recent_orders(request):
    """Vista para obtener órdenes recientes del dashboard"""
    if request.method == 'GET':
        try:
            # Obtener la sucursal del usuario actual
            user_subsidiary = request.user.subsidiary
            
            # Filtrar órdenes por sucursal si el usuario tiene una asignada
            orders = Order.objects.all()
            if user_subsidiary:
                orders = orders.filter(subsidiary=user_subsidiary)
            
            # Obtener las 10 órdenes más recientes
            recent_orders = orders.select_related('client').order_by('-register_date')[:10]
            
            orders_data = []
            for order in recent_orders:
                order_data = {
                    'id': order.id,
                    'code': order.code or f'ORD-{order.id}',
                    'client_name': order.client.full_name if order.client else 'Sin Cliente',
                    'type': order.type,
                    'register_date': order.register_date.strftime('%Y-%m-%d') if order.register_date else '',
                    'total': float(order.total),
                    'status': order.status
                }
                orders_data.append(order_data)
            
            return JsonResponse({
                'success': True,
                'orders': orders_data
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cargar órdenes recientes: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def monthly_orders_chart(request):
    """Vista para obtener datos del gráfico mensual de órdenes"""
    if request.method == 'GET':
        try:
            # Obtener la sucursal del usuario actual
            user_subsidiary = request.user.subsidiary
            
            # Filtrar órdenes por sucursal si el usuario tiene una asignada
            orders = Order.objects.all()
            if user_subsidiary:
                orders = orders.filter(subsidiary=user_subsidiary)
            
            # Obtener datos de los últimos 6 meses
            from datetime import datetime, timedelta
            import calendar
            
            current_date = datetime.now()
            months_data = []
            
            for i in range(5, -1, -1):
                month_date = current_date - timedelta(days=30*i)
                month_start = month_date.replace(day=1)
                month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
                
                month_orders = orders.filter(
                    register_date__gte=month_start,
                    register_date__lte=month_end
                ).count()
                
                months_data.append({
                    'month': month_start.strftime('%B %Y'),
                    'count': month_orders
                })
            
            chart_data = {
                'labels': [item['month'] for item in months_data],
                'values': [item['count'] for item in months_data]
            }
            
            return JsonResponse({
                'success': True,
                'data': chart_data
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cargar gráfico mensual: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def weekly_orders_chart(request):
    """Vista para obtener datos del gráfico semanal de órdenes"""
    if request.method == 'GET':
        try:
            # Obtener la sucursal del usuario actual
            user_subsidiary = request.user.subsidiary
            
            # Filtrar órdenes por sucursal si el usuario tiene una asignada
            orders = Order.objects.all()
            if user_subsidiary:
                orders = orders.filter(subsidiary=user_subsidiary)
            
            # Obtener datos de las últimas 4 semanas
            from datetime import datetime, timedelta
            
            current_date = datetime.now()
            weeks_data = []
            
            for i in range(3, -1, -1):
                week_start = current_date - timedelta(weeks=i+1)
                week_start = week_start - timedelta(days=week_start.weekday())
                week_end = week_start + timedelta(days=6)
                
                week_orders = orders.filter(
                    register_date__gte=week_start.date(),
                    register_date__lte=week_end.date()
                ).count()
                
                weeks_data.append({
                    'week': f'Semana {week_start.strftime("%d/%m")}',
                    'count': week_orders
                })
            
            chart_data = {
                'labels': [item['week'] for item in weeks_data],
                'values': [item['count'] for item in weeks_data]
            }
            
            return JsonResponse({
                'success': True,
                'data': chart_data
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cargar gráfico semanal: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


# =============================================================================
# VISTAS PARA MANEJO DE ESTADOS DE ÓRDENES CON CASHFLOW
# =============================================================================

def get_order_for_completion(request):
    """Vista para obtener información de una orden para completarla"""
    if request.method == 'GET':
        try:
            order_id = request.GET.get('order_id')
            
            if not order_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de orden requerido'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la orden con información del cliente
            order = Order.objects.select_related('client', 'subsidiary').get(id=int(order_id))
            
            # Calcular el saldo faltante
            balance = float(order.total - order.cash_advance)
            
            order_data = {
                'id': order.id,
                'serial': order.serial,
                'correlative': order.correlative,
                'client': {
                    'id': order.client.id,
                    'full_name': order.client.full_name,
                    'document': order.client.document,
                    'number': order.client.number
                },
                'total': float(order.total),
                'cash_advance': float(order.cash_advance),
                'balance': balance,
                'subsidiary': {
                    'id': order.subsidiary.id,
                    'name': order.subsidiary.name
                }
            }
            
            return JsonResponse({
                'success': True,
                'order': order_data
            }, status=HTTPStatus.OK)
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener información de la orden: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def get_order_for_cancellation(request):
    """Vista para obtener información de una orden para anularla"""
    if request.method == 'GET':
        try:
            order_id = request.GET.get('order_id')
            
            if not order_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de orden requerido'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la orden con información del cliente
            order = Order.objects.select_related('client', 'subsidiary').get(id=int(order_id))
            
            order_data = {
                'id': order.id,
                'serial': order.serial,
                'correlative': order.correlative,
                'client': {
                    'id': order.client.id,
                    'full_name': order.client.full_name,
                    'document': order.client.document,
                    'number': order.client.number
                },
                'total': float(order.total),
                'cash_advance': float(order.cash_advance),
                'subsidiary': {
                    'id': order.subsidiary.id,
                    'name': order.subsidiary.name
                }
            }
            
            return JsonResponse({
                'success': True,
                'order': order_data
            }, status=HTTPStatus.OK)
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener información de la orden: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def complete_order_with_payment(request):
    """Vista para completar una orden con registro de pago en cashflow"""
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            payment_amount = request.POST.get('payment_amount')
            payment_date = request.POST.get('payment_date')
            cash_account_id = request.POST.get('cash_account_id')
            completed_by_id = request.POST.get('completed_by')
            
            if not all([order_id, payment_amount, payment_date, cash_account_id, completed_by_id]):
                return JsonResponse({
                    'success': False,
                    'message': 'Faltan datos obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la orden
            order = Order.objects.select_related('client', 'subsidiary').get(id=int(order_id))
            
            # Verificar que la orden no esté ya completada
            if order.status == 'C':
                return JsonResponse({
                    'success': False,
                    'message': 'La orden ya está completada'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar que la orden no esté anulada
            if order.status == 'A':
                return JsonResponse({
                    'success': False,
                    'message': 'No se puede completar una orden anulada'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la cuenta de caja
            try:
                from apps.accounting.models import Cash
                cash_account = Cash.objects.get(id=int(cash_account_id))
            except Cash.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Cuenta de caja no encontrada'
                }, status=HTTPStatus.NOT_FOUND)
            
            # Obtener el usuario que completó la orden
            try:
                completed_by_user = CustomUser.objects.get(id=int(completed_by_id))
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario no encontrado'
                }, status=HTTPStatus.NOT_FOUND)
            
            # Calcular el saldo faltante
            balance = order.total - order.cash_advance
            payment_amount_decimal = Decimal(payment_amount)
            
            # Verificar que el monto del pago sea correcto
            if payment_amount_decimal != balance:
                return JsonResponse({
                    'success': False,
                    'message': f'El monto del pago debe ser exactamente S/ {balance}'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Registrar el pago en cashflow
            from apps.accounting.models import CashFlow
            from datetime import datetime
            
            # Convertir la fecha del pago
            payment_datetime = datetime.strptime(payment_date, '%Y-%m-%d')
            
            # Crear entrada en cashflow
            cashflow_entry = CashFlow.objects.create(
                transaction_date=payment_datetime,
                created_at=datetime.now(),
                description=f"Pago de la orden {order.subsidiary.serial}-{order.correlative:03d} - {order.client.full_name}",
                serial=order.subsidiary.serial,
                n_receipt=order.correlative,
                document_type_attached='O',  # Otro
                type='E',  # Entrada
                subtotal=payment_amount_decimal,
                total=payment_amount_decimal,
                igv=Decimal('0.00'),
                cash=cash_account,
                order=order,
                user=request.user,
                type_expense='O'  # Otros
            )
            
            # Actualizar el estado de la orden a completado
            order.status = 'C'
            order.cash_pay = payment_amount_decimal  # Guardar el monto pagado
            order.completed_by = completed_by_user  # Guardar quién completó la orden
            order.completed_at = datetime.now()  # Guardar cuándo se completó
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Orden completada exitosamente por {completed_by_user.first_name} {completed_by_user.last_name}. Pago de S/ {payment_amount} registrado en {cash_account.name}',
                'order_id': order_id,
                'cashflow_id': cashflow_entry.id
            }, status=HTTPStatus.OK)
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al completar la orden: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def cancel_order_with_reason(request):
    """Vista para anular una orden con motivo y posible devolución de adelanto"""
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            cancellation_reason = request.POST.get('cancellation_reason')
            refund_advance = request.POST.get('refund_advance') == 'true'
            refund_amount = request.POST.get('refund_amount', '0')
            refund_cash_account_id = request.POST.get('refund_cash_account_id')
            
            if not all([order_id, cancellation_reason]):
                return JsonResponse({
                    'success': False,
                    'message': 'Faltan datos obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Si se va a devolver el adelanto, se requiere la cuenta de caja
            if (refund_advance and not refund_cash_account_id):
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una cuenta de caja para la devolución'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la orden
            order = Order.objects.select_related('client', 'subsidiary').get(id=int(order_id))
            
            # Verificar que la orden no esté ya anulada
            if order.status == 'A':
                return JsonResponse({
                    'success': False,
                    'message': 'La orden ya está anulada'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar que la orden no esté completada
            if order.status == 'C':
                return JsonResponse({
                    'success': False,
                    'message': 'No se puede anular una orden completada'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Si se va a devolver el adelanto, obtener la cuenta de caja
            cash_account = None
            if refund_advance:
                try:
                    from apps.accounting.models import Cash
                    cash_account = Cash.objects.get(id=int(refund_cash_account_id))
                except Cash.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Cuenta de caja no encontrada'
                    }, status=HTTPStatus.NOT_FOUND)
            
            # Registrar la devolución en cashflow si es necesario
            if refund_advance and order.cash_advance > 0:
                from apps.accounting.models import CashFlow
                from datetime import datetime
                
                # Crear salida en cashflow por la devolución
                cashflow_refund = CashFlow.objects.create(
                    transaction_date=datetime.now(),
                    created_at=datetime.now(),
                    description=f"Devolución de adelanto - Orden anulada {order.subsidiary.serial}-{order.correlative:03d} - {order.client.full_name}",
                    serial=order.subsidiary.serial,
                    n_receipt=order.correlative,
                    document_type_attached='O',  # Otro
                    type='S',  # Salida
                    subtotal=order.cash_advance,
                    total=order.cash_advance,
                    igv=decimal.Decimal('0.00'),
                    cash=cash_account,
                    order=order,
                    user=request.user,
                    type_expense='O'  # Otros
                )
            
            # Actualizar la orden
            order.status = 'A'
            order.cancellation_reason = cancellation_reason
            order.save()
            
            # Mensaje de confirmación
            message = f'Orden anulada exitosamente. Motivo: {cancellation_reason}'
            if refund_advance and order.cash_advance > 0:
                message += f'. Devolución de S/ {order.cash_advance} registrada en {cash_account.name}'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'order_id': order_id,
                'refund_registered': refund_advance
            }, status=HTTPStatus.OK)
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al anular la orden: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


# Vista comentada - ya no se usa porque el modal está integrado en order_list.html
# def delivery_status_modal(request):
#     """Vista para mostrar modal de cambio de estado de entrega de orden"""
#     if request.method == 'GET':
#         order_id = request.GET.get('order_id')
#         if order_id:
#             try:
#                 order_obj = Order.objects.select_related('client').get(id=int(order_id))
#                 user_set = CustomUser.objects.filter(is_active=True, is_staff=False)
# 
#                 t = loader.get_template('sales/order_delivery_status_modal.html')
#                 context = {
#                     'order': order_obj,
#                     'user_set': user_set
#                 }
# 
#                 return JsonResponse({
#                     'success': True,
#                     'form': t.render(context, request),
#                 })
#                 
#             except Order.DoesNotExist:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Orden no encontrada'
#                 }, status=HTTPStatus.NOT_FOUND)
#         
#         return JsonResponse({
#             'success': False,
#             'message': 'ID de orden no proporcionado'
#         }, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def update_order_delivery_status(request):
    """Vista para actualizar el estado de entrega de una orden"""
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            new_delivery_status = request.POST.get('delivery_status')
            delivered_by_id = request.POST.get('delivered_by')
            
            if not order_id or not new_delivery_status or not delivered_by_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Faltan datos obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Validar que el estado sea válido
            valid_delivery_statuses = ['P', 'E', 'C']
            if new_delivery_status not in valid_delivery_statuses:
                return JsonResponse({
                    'success': False,
                    'message': 'Estado de entrega no válido'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la orden y el usuario
            order_obj = Order.objects.get(id=int(order_id))
            delivered_by_user = CustomUser.objects.get(id=int(delivered_by_id))
            old_delivery_status = order_obj.delivery_status
            
            # VALIDACIÓN: No permitir cambiar a ENTREGADO si el status es PENDIENTE o ANULADO
            if new_delivery_status == 'E' and order_obj.status in ['P', 'A']:
                return JsonResponse({
                    'success': False,
                    'message': 'No se puede marcar como ENTREGADO una orden que está PENDIENTE o ANULADA. Primero debe completar la orden.',
                    'order_id': order_id,
                    'old_delivery_status': old_delivery_status,
                    'new_delivery_status': new_delivery_status,
                    'validation_error': True
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Actualizar el estado de entrega
            order_obj.delivery_status = new_delivery_status
            
            # Si se está marcando como entregado, guardar quien lo entregó y cuándo
            if new_delivery_status == 'E':
                order_obj.delivered_by = delivered_by_user
                order_obj.delivered_at = datetime.now()
            
            order_obj.save()
            
            # Mensaje de confirmación
            status_display = {
                'P': 'PENDIENTE',
                'E': 'ENTREGADO',
                'C': 'CANCELADO'
            }
            
            message = f'Estado de entrega actualizado de {status_display[old_delivery_status]} a {status_display[new_delivery_status]}'
            if new_delivery_status == 'E':
                message += f' por {delivered_by_user.first_name} {delivered_by_user.last_name}'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'order_id': order_id,
                'old_delivery_status': old_delivery_status,
                'new_delivery_status': new_delivery_status
            }, status=HTTPStatus.OK)
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar el estado de entrega: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def get_order_for_conversion(request):
    """Vista para obtener los datos de una orden para convertir a orden de servicio"""
    if request.method == 'GET':
        try:
            order_id = request.GET.get('order_id')
            
            if not order_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de orden no proporcionado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la orden con sus detalles
            order_obj = Order.objects.select_related('client', 'subsidiary', 'user').prefetch_related('orderdetail_set').get(id=int(order_id))
            
            # Verificar que la orden sea una cotización (type='C')
            if order_obj.type != 'C':
                return JsonResponse({
                    'success': False,
                    'message': 'Solo se pueden convertir cotizaciones a órdenes de servicio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener los detalles de la orden
            order_details = []
            for detail in order_obj.orderdetail_set.all():
                order_details.append({
                    'id': detail.id,
                    'product_name': detail.product_name,
                    'quantity': float(detail.quantity),
                    'price_unit': float(detail.price_unit),
                    'total': float(detail.multiply()),
                    'observation': detail.observation or ''
                })
            
            # Preparar los datos de la orden
            order_data = {
                'id': order_obj.id,
                'code': f"{order_obj.serial}-{order_obj.correlative:03d}",
                'client_name': str(order_obj.client) if order_obj.client else '',
                'client_id': order_obj.client.id if order_obj.client else None,
                'register_date': order_obj.register_date.strftime('%Y-%m-%d') if order_obj.register_date else '',
                'delivery_date': order_obj.delivery_date.strftime('%Y-%m-%d') if order_obj.delivery_date else '',
                'subtotal': float(order_obj.subtotal),
                'igv': float(order_obj.igv),
                'total': float(order_obj.total),
                'way_to_pay': order_obj.way_to_pay,
                'cash_advance': float(order_obj.cash_advance),
                'observation': order_obj.observation or '',
                'subsidiary_id': order_obj.subsidiary.id if order_obj.subsidiary else None,
                'subsidiary_name': str(order_obj.subsidiary) if order_obj.subsidiary else '',
                'details': order_details
            }
            
            return JsonResponse({
                'success': True,
                'order': order_data
            })
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error al obtener los datos de la orden: ' + str(e)
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=HTTPStatus.METHOD_NOT_ALLOWED)


@csrf_exempt
def convert_order_to_service(request):
    """Vista para convertir una cotización a orden de servicio"""
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            subsidiary_id = request.POST.get('subsidiary_id')
            register_date = request.POST.get('register_date')
            delivery_date = request.POST.get('delivery_date')
            way_to_pay = request.POST.get('way_to_pay')
            cash_advance = request.POST.get('cash_advance', 0)
            observation = request.POST.get('observation', '')
            
            # Validaciones básicas
            if not order_id or not subsidiary_id or not register_date or not way_to_pay:
                return JsonResponse({
                    'success': False,
                    'message': 'Faltan datos obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la orden original
            order_obj = Order.objects.get(id=int(order_id))
            
            # Verificar que sea una cotización
            if order_obj.type != 'C':
                return JsonResponse({
                    'success': False,
                    'message': 'Solo se pueden convertir cotizaciones a órdenes de servicio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener la sucursal
            subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary_id))
            
            # Obtener el correlativo para la nueva orden de servicio
            correlative = get_correlative_order_by_subsidiary(subsidiary_obj, 'O')
            
            # Actualizar la orden existente
            order_obj.type = 'O'  # Cambiar a Orden de Servicio
            order_obj.serial = subsidiary_obj.serial
            order_obj.correlative = correlative
            order_obj.subsidiary = subsidiary_obj
            order_obj.register_date = datetime.strptime(register_date, '%Y-%m-%d').date()
            order_obj.delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date() if delivery_date else None
            order_obj.way_to_pay = way_to_pay
            order_obj.cash_advance = Decimal(cash_advance) if cash_advance else Decimal('0.00')
            order_obj.observation = observation
            order_obj.status = 'P'  # Poner como pendiente
            order_obj.delivery_status = 'P'  # Poner como pendiente de entrega
            
            # Recalcular totales
            order_obj.calculate_totals()
            
            # Guardar los cambios
            order_obj.save()
            
            # Generar el código de la nueva orden
            new_code = f"{order_obj.serial}-{order_obj.correlative:03d}"
            
            return JsonResponse({
                'success': True,
                'message': 'Orden convertida exitosamente a Orden de Servicio',
                'new_code': new_code,
                'order_id': order_obj.id
            })
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Orden no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Subsidiary.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Sucursal no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': 'Error en el formato de fecha: ' + str(e)
            }, status=HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error al convertir la orden: ' + str(e)
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=HTTPStatus.METHOD_NOT_ALLOWED)






