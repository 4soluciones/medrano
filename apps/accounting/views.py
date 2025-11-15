import itertools

from django.shortcuts import render
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.views.generic import TemplateView, View, CreateView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView
from http import HTTPStatus
import re
import locale
import decimal
import calendar

from .models import *
import pytz
from django.contrib.auth.models import User
import json
import requests
import decimal
import math
import random
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.files import ImageFieldFile
from django.template import loader
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db import DatabaseError, IntegrityError
from django.core import serializers
from django.db.models import Min, Sum, Max, Q, Prefetch, Subquery, OuterRef, Value, IntegerField, Case, ExpressionWrapper, DecimalField
from django.db.models.functions import ExtractYear
from medrano import settings
import os
from decimal import Decimal
from django.db.models import F


from ..sales.models import Person, Order, OrderDetail
from ..sales.views_API import query_apis_net_money
from ..users.models import CustomUser
from ..hrm.models import Subsidiary


# =============================================================================
# VISTAS PARA GESTIÓN DE CUENTAS/CAJAS
# =============================================================================

def cash_list(request):
    """Vista principal del listado de cuentas/cajas"""
    if request.method == 'GET':
        subsidiary_set = Subsidiary.objects.all()
        currency_types = Cash.CURRENCY_TYPE_CHOICES
        
        return render(request, 'accounting/cash_list.html', {
            'subsidiary_set': subsidiary_set,
            'currency_types': currency_types,
        })
    elif request.method == 'POST':
        try:
            # Filtrar cuentas según parámetros
            subsidiary_id = request.POST.get('subsidiary')
            currency_type = request.POST.get('currency_type')
            
            cash_accounts = Cash.objects.all()
        
            if subsidiary_id and subsidiary_id != '0':
                cash_accounts = cash_accounts.filter(subsidiary_id=subsidiary_id)
            if currency_type and currency_type != '0':
                cash_accounts = cash_accounts.filter(currency_type=currency_type)

            cash_accounts = cash_accounts.select_related('subsidiary').order_by('name')

            tpl = loader.get_template('accounting/cash_list_grid.html')
            context = {
                'cash_accounts': cash_accounts,
            }

            return JsonResponse({
                'grid': tpl.render(context, request),
            }, status=HTTPStatus.OK)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cargar las cuentas: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def cash_create(request):
    """Vista para crear nueva cuenta/caja"""
    if request.method == 'GET':
        subsidiary_set = Subsidiary.objects.all()
        currency_types = Cash.CURRENCY_TYPE_CHOICES
        
        return render(request, 'accounting/cash_create.html', {
            'subsidiary_set': subsidiary_set,
            'currency_types': currency_types,
        })


@csrf_exempt
def cash_save(request):
    """Vista para guardar nueva cuenta/caja"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.POST.get('cash_name', '').strip()
            subsidiary_id = request.POST.get('subsidiary_id', '')
            account_number = request.POST.get('account_number', '').strip()
            currency_type = request.POST.get('currency_type', 'S')
            account_type = request.POST.get('account_type', 'C')
            
            # Validaciones básicas
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de la cuenta es obligatorio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not subsidiary_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una sucursal'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar si ya existe una cuenta con el mismo nombre en la misma sucursal
            if Cash.objects.filter(name__iexact=name, subsidiary_id=subsidiary_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Ya existe una cuenta con el nombre "{name}" en esta sucursal'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Crear la cuenta
            subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary_id))
            cash_obj = Cash(
                name=name.upper(),
                subsidiary=subsidiary_obj,
                account_number=account_number.upper() if account_number else None,
                currency_type=currency_type,
                account_type=account_type
            )
            cash_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cuenta creada exitosamente',
                'cash_id': cash_obj.id
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear la cuenta: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def cash_edit(request, cash_id):
    """Vista para editar cuenta existente"""
    try:
        cash_obj = Cash.objects.select_related('subsidiary').get(id=cash_id)
        subsidiary_set = Subsidiary.objects.all()
        currency_types = Cash.CURRENCY_TYPE_CHOICES
        
        return render(request, 'accounting/cash_edit.html', {
            'cash': cash_obj,
            'subsidiary_set': subsidiary_set,
            'currency_types': currency_types,
        })
        
    except Cash.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cuenta no encontrada'
        }, status=HTTPStatus.NOT_FOUND)


@csrf_exempt
def cash_get(request):
    """Vista para obtener datos de una cuenta específica"""
    if request.method == 'POST':
        try:
            cash_id = request.POST.get('cash_id')
            if not cash_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de cuenta no proporcionado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            cash_obj = Cash.objects.select_related('subsidiary').get(id=int(cash_id))
            
            # Preparar datos para el formulario
            cash_data = {
                'id': cash_obj.id,
                'name': cash_obj.name,
                'subsidiary_id': cash_obj.subsidiary.id,
                'account_number': cash_obj.account_number,
                'currency_type': cash_obj.currency_type,
                'account_type': cash_obj.account_type,
            }
            
            return JsonResponse({
                'success': True,
                'cash': cash_data
            }, status=HTTPStatus.OK)
            
        except Cash.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Cuenta no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener los datos de la cuenta: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def cash_update(request):
    """Vista para actualizar cuenta existente"""
    if request.method == 'POST':
        try:
            cash_id = request.POST.get('cash_id')
            if not cash_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de cuenta no proporcionado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            cash_obj = Cash.objects.get(id=int(cash_id))
            
            # Obtener datos del formulario
            name = request.POST.get('cash_name', '').strip()
            subsidiary_id = request.POST.get('subsidiary_id', '')
            account_number = request.POST.get('account_number', '').strip()
            currency_type = request.POST.get('currency_type', 'S')
            account_type = request.POST.get('account_type', 'C')
            
            # Validaciones básicas
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de la cuenta es obligatorio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not subsidiary_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una sucursal'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar si ya existe una cuenta con el mismo nombre en la misma sucursal (excluyendo la actual)
            if Cash.objects.filter(name__iexact=name, subsidiary_id=subsidiary_id).exclude(id=cash_obj.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Ya existe una cuenta con el nombre "{name}" en esta sucursal'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Actualizar la cuenta
            subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary_id))
            cash_obj.name = name.upper()
            cash_obj.subsidiary = subsidiary_obj
            cash_obj.account_number = account_number.upper() if account_number else None
            cash_obj.currency_type = currency_type
            cash_obj.account_type = account_type
            cash_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cuenta actualizada correctamente'
            }, status=HTTPStatus.OK)
            
        except Cash.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Cuenta no encontrada'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar la cuenta: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def cashflow_get(request):
    """Vista para obtener datos de un gasto específico - Solo para administradores"""
    if request.method == 'POST':
        try:
            # Verificar permisos de administrador
            if not (hasattr(request.user, 'has_access_to_all') and request.user.has_access_to_all):
                return JsonResponse({
                    'success': False,
                    'message': 'No tiene permisos para editar gastos. Solo los administradores pueden realizar esta acción.'
                }, status=HTTPStatus.FORBIDDEN)
            
            cashflow_id = request.POST.get('cashflow_id')
            if not cashflow_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de gasto no proporcionado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            cashflow_obj = CashFlow.objects.select_related('cash', 'user').get(id=int(cashflow_id))
            
            # Preparar datos para el formulario
            cashflow_data = {
                'id': cashflow_obj.id,
                'transaction_date': cashflow_obj.transaction_date.strftime('%Y-%m-%d'),
                'type': cashflow_obj.type,
                'cash_id': cashflow_obj.cash.id,
                'type_expense': cashflow_obj.type_expense,
                'user_id': cashflow_obj.user.id,
                'document_type_attached': cashflow_obj.document_type_attached,
                'description': cashflow_obj.description,
                'serial': cashflow_obj.serial,
                'n_receipt': cashflow_obj.n_receipt,
                'operation_code': cashflow_obj.operation_code,
                'subtotal': float(cashflow_obj.subtotal),
                'igv': float(cashflow_obj.igv),
                'total': float(cashflow_obj.total),
                'way_to_pay': cashflow_obj.way_to_pay,
            }
            
            return JsonResponse({
                'success': True,
                'cashflow': cashflow_data
            }, status=HTTPStatus.OK)
            
        except CashFlow.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Gasto no encontrado'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener los datos del gasto: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


@csrf_exempt
def cashflow_delete(request):
    """Vista para eliminar gasto existente - Solo para administradores"""
    if request.method == 'POST':
        try:
            # Verificar permisos de administrador
            if not (hasattr(request.user, 'has_access_to_all') and request.user.has_access_to_all):
                return JsonResponse({
                    'success': False,
                    'message': 'No tiene permisos para eliminar gastos. Solo los administradores pueden realizar esta acción.'
                }, status=HTTPStatus.FORBIDDEN)
            
            cashflow_id = request.POST.get('cashflow_id')
            if not cashflow_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de gasto no proporcionado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            cashflow_obj = CashFlow.objects.get(id=int(cashflow_id))
            
            # Obtener información del gasto para el mensaje
            description = cashflow_obj.description
            amount = cashflow_obj.total
            
            # Eliminar el gasto
            cashflow_obj.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Gasto eliminado exitosamente: {description} - S/ {amount}'
            }, status=HTTPStatus.OK)
            
        except CashFlow.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Gasto no encontrado'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar el gasto: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


# =============================================================================
# VISTAS PARA GESTIÓN DE GASTOS (CASHFLOW)
# =============================================================================

def cashflow_list(request):
    """Vista principal del listado de gastos"""
    if request.method == 'GET':
        document_types = CashFlow.DOCUMENT_TYPE_ATTACHED_CHOICES
        transaction_types = [('A', 'Apertura'), ('C', 'Cierre'), ('E', 'Entrada'), ('S', 'Salida')]  # Apertura, cierre, entrada y salida
        expense_types = CashFlow.TYPE_EXPENSE
        user_set = CustomUser.objects.filter(is_active=True, is_staff=False)
        subsidiary_set = Subsidiary.objects.all()
        # Fecha actual para los filtros
        peru_tz = pytz.timezone("America/Lima")
        date_now = datetime.now(peru_tz).strftime('%Y-%m-%d')
        
        # Obtener la sucursal del usuario actual
        user_subsidiary = None
        first_cash_account = None

        if hasattr(request.user, 'subsidiary') and request.user.subsidiary:
            user_subsidiary = request.user.subsidiary

        # Verificar si el usuario tiene permisos de administrador
        is_admin = hasattr(request.user, 'has_access_to_all') and request.user.has_access_to_all

        # Filtrar cajas según permisos del usuario
        if is_admin:
            # Usuario admin puede ver todas las cajas
            cash_accounts = Cash.objects.all().order_by('subsidiary_id')
            # Buscar la primera cuenta de tipo 'E' de cualquier sucursal
            first_cash_account = Cash.objects.filter(account_type='E').first()
        else:
            # Usuario normal solo ve cajas de su sucursal
            cash_accounts = Cash.objects.filter(subsidiary=user_subsidiary)
            # Buscar la primera cuenta de tipo 'E' de la sucursal del usuario
            if user_subsidiary:
                first_cash_account = Cash.objects.filter(
                    subsidiary=user_subsidiary,
                    account_type='E'
                ).first()

        # Si no hay cuenta de tipo 'E', buscar cualquier cuenta según permisos
        if not first_cash_account:
            if is_admin:
                first_cash_account = Cash.objects.first()
            elif user_subsidiary:
                first_cash_account = Cash.objects.filter(subsidiary=user_subsidiary).first()
        
        return render(request, 'accounting/cashflow_list.html', {
            'cash_accounts': cash_accounts,
            'document_types': document_types,
            'transaction_types': transaction_types,
            'expense_types': expense_types,
            'subsidiary_set': subsidiary_set,
            'user_set': user_set,
            'date_now': date_now,
            'user_subsidiary': user_subsidiary,
            'first_cash_account': first_cash_account,
            'is_admin': is_admin,
        })
    elif request.method == 'POST':
        try:
            # Filtrar gastos según parámetros
            cash_id = request.POST.get('cash_account')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            expense_type = request.POST.get('expense_type')
            
            cashflows = CashFlow.objects.filter(type__in=['S', 'A'])
        
            # Verificar permisos del usuario
            is_admin = hasattr(request.user, 'has_access_to_all') and request.user.has_access_to_all
            
            # Si no es admin, solo mostrar sus propios gastos
            if not is_admin:
                cashflows = cashflows.filter(user=request.user)
        
            if cash_id and cash_id != '0':
                cashflows = cashflows.filter(cash_id=cash_id)
            
            # Filtro por tipo de gasto (solo para admins)
            if is_admin and expense_type and expense_type != '0':
                cashflows = cashflows.filter(type_expense=expense_type)

            # Filtro por rango de fechas
            # Por defecto, si no se especifica, usar la fecha de hoy
            if not start_date and not end_date:
                # Si no se proporcionan fechas, usar la fecha de hoy
                peru_tz = pytz.timezone("America/Lima")
                today = datetime.now(peru_tz).date()
                cashflows = cashflows.filter(transaction_date=today)
            else:
                # Si se proporciona fecha de inicio, filtrar desde esa fecha
                if start_date:
                    cashflows = cashflows.filter(transaction_date__gte=start_date)
                # Si se proporciona fecha de fin, filtrar hasta esa fecha
                if end_date:
                    cashflows = cashflows.filter(transaction_date__lte=end_date)

            # Ordenar: aperturas primero, luego por id
            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary').order_by(
                'type',  # Aperturas (A) aparecerán primero
                'id'
            )

            # Calcular totales
            # Entradas: tipo 'E' (Entrada) + tipo 'A' (Apertura)
            total_income = cashflows.filter(type__in=['E', 'A']).aggregate(total=Sum('total'))['total'] or 0
            # Salidas: tipo 'S' (Salida)
            total_expenses = cashflows.filter(type='S').aggregate(total=Sum('total'))['total'] or 0
            # Balance: Entradas - Salidas
            net_balance = total_income - total_expenses

            # Totales por tipo de gasto
            expense_totals = {}
            for expense_code, expense_name in CashFlow.TYPE_EXPENSE:
                total = cashflows.filter(type__in=['S', 'A'], type_expense=expense_code).aggregate(
                    total=Sum('total')
                )['total'] or 0
                expense_totals[expense_code] = total

            tpl = loader.get_template('accounting/cashflow_list_grid.html')
            context = {
                'cashflows': cashflows,
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_balance': net_balance,
                'expense_totals': expense_totals,
                # 'date_now': date_now,
            }

            return JsonResponse({
                'grid': tpl.render(context, request),
            }, status=HTTPStatus.OK)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cargar los gastos: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def cashflow_create(request):
    """Vista para crear nuevo gasto"""
    if request.method == 'GET':
        cash_accounts = Cash.objects.all()
        document_types = CashFlow.DOCUMENT_TYPE_ATTACHED_CHOICES
        transaction_types = [('A', 'Apertura'), ('C', 'Cierre'), ('E', 'Entrada'), ('S', 'Salida')]  # Apertura, cierre, entrada y salida
        expense_types = CashFlow.TYPE_EXPENSE
        user_set = CustomUser.objects.filter(is_active=True, is_staff=False)
        
        # Fecha actual
        date_now = datetime.now().strftime('%Y-%m-%d')
        
        return render(request, 'accounting/cashflow_create.html', {
            'cash_accounts': cash_accounts,
            'document_types': document_types,
            'transaction_types': transaction_types,
            'expense_types': expense_types,
            'user_set': user_set,
            'date_now': date_now,
        })


@csrf_exempt
def cashflow_save(request):
    """Vista para guardar nuevo gasto"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            transaction_date = request.POST.get('transaction_date')
            description = request.POST.get('description', '').strip()
            serial = request.POST.get('serial', '').strip()
            n_receipt = request.POST.get('n_receipt', '0')
            document_type = request.POST.get('document_type', 'O')
            transaction_type = request.POST.get('transaction_type', 'S')
            subtotal = request.POST.get('subtotal', '0.00')
            total = request.POST.get('total', '0.00')
            igv = request.POST.get('igv', '0.00')
            cash_id = request.POST.get('cash_id')
            operation_code = request.POST.get('operation_code', '').strip()
            expense_type = request.POST.get('expense_type', 'O')
            payment_type = request.POST.get('payment_type', 'E')
            user_id = request.POST.get('user_id')
            
            # Validaciones básicas
            if not transaction_date:
                return JsonResponse({
                    'success': False,
                    'message': 'La fecha de transacción es obligatoria'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not description:
                return JsonResponse({
                    'success': False,
                    'message': 'La descripción es obligatoria'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not cash_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una cuenta/caja'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar un usuario'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener objetos relacionados
            cash_obj = Cash.objects.get(id=int(cash_id))
            user_obj = CustomUser.objects.get(id=int(user_id))
            
            # Crear el gasto
            cashflow_obj = CashFlow(
                transaction_date=transaction_date,
                description=description.upper(),
                serial=serial.upper() if serial else None,
                n_receipt=int(n_receipt) if n_receipt else 0,
                document_type_attached=document_type,
                type=transaction_type,
                subtotal=Decimal(str(subtotal)),
                total=Decimal(str(total)),
                igv=Decimal(str(igv)),
                cash=cash_obj,
                operation_code=operation_code.upper() if operation_code else None,
                type_expense=expense_type,
                way_to_pay=payment_type,
                user=user_obj,
                subsidiary=cash_obj.subsidiary
            )
            cashflow_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{cashflow_obj.get_type_display()} registrado exitosamente',
                'cashflow_id': cashflow_obj.id
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar el gasto: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def cashflow_edit(request, cashflow_id):
    """Vista para editar gasto existente"""
    try:
        cashflow_obj = CashFlow.objects.select_related('cash', 'user', 'cash__subsidiary').get(id=cashflow_id)
        cash_accounts = Cash.objects.all()
        document_types = CashFlow.DOCUMENT_TYPE_ATTACHED_CHOICES
        transaction_types = [('A', 'Apertura'), ('C', 'Cierre'), ('E', 'Entrada'), ('S', 'Salida')]  # Apertura, cierre, entrada y salida
        expense_types = CashFlow.TYPE_EXPENSE
        user_set = CustomUser.objects.filter(is_active=True, is_staff=False)
        
        return render(request, 'accounting/cashflow_edit.html', {
            'cashflow': cashflow_obj,
            'cash_accounts': cash_accounts,
            'document_types': document_types,
            'transaction_types': transaction_types,
            'expense_types': expense_types,
            'user_set': user_set,
        })
        
    except CashFlow.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Gasto no encontrado'
        }, status=HTTPStatus.NOT_FOUND)


@csrf_exempt
def cashflow_update(request):
    """Vista para actualizar gasto existente"""
    if request.method == 'POST':
        try:
            cashflow_id = request.POST.get('cashflow_id')
            if not cashflow_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de gasto no proporcionado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            cashflow_obj = CashFlow.objects.get(id=int(cashflow_id))
            
            # Obtener datos del formulario
            transaction_date = request.POST.get('transaction_date')
            description = request.POST.get('description', '').strip()
            serial = request.POST.get('serial', '').strip()
            n_receipt = request.POST.get('n_receipt', '0')
            document_type = request.POST.get('document_type', 'O')
            transaction_type = request.POST.get('transaction_type', 'S')
            subtotal = request.POST.get('subtotal', '0.00')
            total = request.POST.get('total', '0.00')
            igv = request.POST.get('igv', '0.00')
            cash_id = request.POST.get('cash_id')
            operation_code = request.POST.get('operation_code', '').strip()
            expense_type = request.POST.get('expense_type', 'O')
            payment_type = request.POST.get('payment_type', 'E')
            user_id = request.POST.get('user_id')
            
            # Validaciones básicas
            if not transaction_date:
                return JsonResponse({
                    'success': False,
                    'message': 'La fecha de transacción es obligatoria'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not description:
                return JsonResponse({
                    'success': False,
                    'message': 'La descripción es obligatoria'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not cash_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una cuenta/caja'
                }, status=HTTPStatus.BAD_REQUEST)
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar un usuario'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener objetos relacionados
            cash_obj = Cash.objects.get(id=int(cash_id))
            user_obj = CustomUser.objects.get(id=int(user_id))
            
            # Actualizar el gasto
            cashflow_obj.transaction_date = transaction_date
            cashflow_obj.description = description.upper()
            cashflow_obj.serial = serial.upper() if serial else None
            cashflow_obj.n_receipt = int(n_receipt) if n_receipt else 0
            cashflow_obj.document_type_attached = document_type
            cashflow_obj.type = transaction_type
            cashflow_obj.subtotal = Decimal(str(subtotal))
            cashflow_obj.total = Decimal(str(total))
            cashflow_obj.igv = Decimal(str(igv))
            cashflow_obj.cash = cash_obj
            cashflow_obj.operation_code = operation_code.upper() if operation_code else None
            cashflow_obj.type_expense = expense_type
            cashflow_obj.way_to_pay = payment_type
            cashflow_obj.user = user_obj
            cashflow_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Gasto actualizado correctamente'
            }, status=HTTPStatus.OK)
            
        except CashFlow.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Gasto no encontrado'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar el gasto: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


def get_cash_accounts_by_subsidiary(request):
    """Vista para obtener cuentas por sucursal"""
    if request.method == 'GET':
        subsidiary_id = request.GET.get('subsidiary', '')
        if subsidiary_id:
            try:
                cash_accounts = Cash.objects.filter(subsidiary_id=int(subsidiary_id)).order_by('name')
                accounts_list = []
                
                for account in cash_accounts:
                    accounts_list.append({
                        'id': account.id,
                        'name': account.name,
                        'currency': account.get_currency_type_display(),
                        'account_type': account.account_type,
                        # 'balance': float(account.initial)
                    })
                
                return JsonResponse({
                    'success': True,
                    'accounts': accounts_list
                }, status=HTTPStatus.OK)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error al obtener las cuentas: {str(e)}'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        
        return JsonResponse({
            'success': False,
            'message': 'ID de sucursal no proporcionado'
        }, status=HTTPStatus.BAD_REQUEST)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)


# =============================================================================
# VISTAS PARA REPORTES
# =============================================================================
@csrf_exempt
def monthly_report(request):
    """Vista para reporte mensual con gráficos profesionales"""
    if request.method == 'GET':
        subsidiary_set = Subsidiary.objects.all()
        
        # Obtener la sucursal del usuario actual
        user_subsidiary = None
        if hasattr(request.user, 'subsidiary') and request.user.subsidiary:
            user_subsidiary = request.user.subsidiary
        
        # Fecha actual para el filtro
        current_date = datetime.now()
        current_month = current_date.strftime('%Y-%m')
        
        return render(request, 'accounting/monthly_report.html', {
            'subsidiary_set': subsidiary_set,
            'user_subsidiary': user_subsidiary,
            'current_month': current_month,
        })
    elif request.method == 'POST':
        try:
            # Obtener parámetros del filtro
            report_month = request.POST.get('report_month')
            subsidiary_id = request.POST.get('subsidiary')
            
            if not report_month:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar un mes'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Convertir mes a rango de fechas
            year, month = report_month.split('-')
            start_date = datetime(int(year), int(month), 1)
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1)
            else:
                end_date = datetime(int(year), int(month) + 1, 1)
            
            # Filtrar datos por sucursal si se especifica
            subsidiary_obj = None
            if subsidiary_id and subsidiary_id != '0':
                subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary_id))
                orders_filter = {'subsidiary_id': subsidiary_id}
                cashflows_filter = {'cash__subsidiary_id': subsidiary_id}
            else:
                orders_filter = {}
                cashflows_filter = {}
            
            # 1. Órdenes completadas del mes (solo tipo 'O', no cotizaciones)
            completed_orders = Order.objects.filter(
                register_date__gte=start_date,
                register_date__lt=end_date,
                status='C',
                type='O',  # Solo órdenes de servicio, no cotizaciones
                **orders_filter
            ).select_related('subsidiary', 'client')
            
            # 2. Órdenes pendientes por sucursal y en general (solo tipo 'O', no cotizaciones)
            pending_orders = Order.objects.filter(
                register_date__gte=start_date,
                register_date__lt=end_date,
                status='P',
                type='O',  # Solo órdenes de servicio, no cotizaciones
                **orders_filter
            ).select_related('subsidiary', 'client')
            
            # 3. Productos más solicitados (solo órdenes tipo 'O', no cotizaciones)
            from django.db.models import Sum, Count
            top_products = OrderDetail.objects.filter(
                order__register_date__gte=start_date,
                order__register_date__lt=end_date,
                order__status__in=['P', 'C'],
                order__type='O',  # Solo órdenes de servicio, no cotizaciones
                **{'order__' + k: v for k, v in orders_filter.items()}
            ).values('product__name').annotate(
                total_quantity=Sum('quantity'),
                total_orders=Count('order')
            ).order_by('-total_quantity')[:10]
            
            # 4. Órdenes pendientes de entrega (solo tipo 'O', no cotizaciones)
            pending_delivery = Order.objects.filter(
                register_date__gte=start_date,
                register_date__lt=end_date,
                delivery_status='P',
                status__in=['P', 'C'],
                type='O',  # Solo órdenes de servicio, no cotizaciones
                **orders_filter
            ).select_related('subsidiary', 'client')
            
            # 5. Ingresos mensuales (CashFlow tipo 'E')
            monthly_income = CashFlow.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lt=end_date,
                type='E',
                **cashflows_filter
            ).select_related('cash', 'cash__subsidiary')
            
            # 6. Gastos por sucursal
            monthly_expenses = CashFlow.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lt=end_date,
                type='S',
                **cashflows_filter
            ).select_related('cash', 'cash__subsidiary')
            
            # Calcular estadísticas
            monthly_income_total = monthly_income.aggregate(Sum('total'))['total__sum'] or 0
            monthly_expenses_total = monthly_expenses.aggregate(Sum('total'))['total__sum'] or 0
            
            stats = {
                'completed_orders_count': completed_orders.count(),
                'completed_orders_total': completed_orders.aggregate(Sum('total'))['total__sum'] or 0,
                'pending_orders_count': pending_orders.count(),
                'pending_orders_total': pending_orders.aggregate(Sum('total'))['total__sum'] or 0,
                'pending_delivery_count': pending_delivery.count(),
                'monthly_income_total': monthly_income_total,
                'monthly_expenses_total': monthly_expenses_total,
                'monthly_profit_total': monthly_income_total - monthly_expenses_total,  # Nueva métrica: diferencia ingresos - gastos
            }
            
            # Datos para gráficos
            chart_data = {
                'completed_orders_by_subsidiary': list(
                    completed_orders.values('subsidiary__name')
                    .annotate(count=Count('id'), total=Sum('total'))
                    .order_by('-count')
                ),
                'pending_orders_by_subsidiary': list(
                    pending_orders.values('subsidiary__name')
                    .annotate(count=Count('id'), total=Sum('total'))
                    .order_by('-count')
                ),
                'top_products': list(top_products),
                'income_by_subsidiary': list(
                    monthly_income.values('cash__subsidiary__name')
                    .annotate(total=Sum('total'))
                    .order_by('-total')
                ),
                'expenses_by_subsidiary': list(
                    monthly_expenses.values('cash__subsidiary__name')
                    .annotate(total=Sum('total'))
                    .order_by('-total')
                ),
                'daily_completed_orders': list(
                    completed_orders.extra(
                        select={'day': 'DATE(register_date)'}
                    ).values('day').annotate(count=Count('id')).order_by('day')
                ),
                'daily_income': list(
                    monthly_income.extra(
                        select={'day': 'DATE(transaction_date)'}
                    ).values('day').annotate(total=Sum('total')).order_by('day')
                ),
            }
            
            return JsonResponse({
                'success': True,
                'stats': stats,
                'chart_data': chart_data,
                'subsidiary': subsidiary_obj.name if subsidiary_obj else 'Todas las sucursales',
                'month_name': start_date.strftime('%B %Y')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al generar reporte mensual: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

@csrf_exempt
def weekly_report(request):
    from datetime import datetime
    """Vista para reporte semanal con gráficos profesionales"""
    if request.method == 'GET':
        subsidiary_set = Subsidiary.objects.all()
        
        # Obtener la sucursal del usuario actual
        user_subsidiary = None
        if hasattr(request.user, 'subsidiary') and request.user.subsidiary:
            user_subsidiary = request.user.subsidiary
        
        # Fecha actual para el filtro
        current_date = datetime.now()
        current_week = current_date.isocalendar()
        current_week_str = f"{current_week[0]}-W{current_week[1]:02d}"
        
        return render(request, 'accounting/weekly_report.html', {
            'subsidiary_set': subsidiary_set,
            'user_subsidiary': user_subsidiary,
            'current_week': current_week_str,
        })
    elif request.method == 'POST':
        try:
            # Obtener parámetros del filtro
            report_week = request.POST.get('report_week')
            subsidiary_id = request.POST.get('subsidiary')
            
            if not report_week:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una semana'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Convertir semana a rango de fechas
            year, week = report_week.split('-W')
            year = int(year)
            week = int(week)
            
            # Calcular fechas de inicio y fin de la semana
            from datetime import datetime, timedelta
            jan_1 = datetime(year, 1, 1)
            start_date = jan_1 + timedelta(weeks=week-1, days=-jan_1.weekday())
            end_date = start_date + timedelta(days=7)
            
            # Filtrar datos por sucursal si se especifica
            subsidiary_obj = None
            if subsidiary_id and subsidiary_id != '0':
                subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary_id))
                orders_filter = {'subsidiary_id': subsidiary_id}
                cashflows_filter = {'cash__subsidiary_id': subsidiary_id}
            else:
                orders_filter = {}
                cashflows_filter = {}
            
            # 1. Órdenes completadas de la semana (solo tipo 'O', no cotizaciones)
            completed_orders = Order.objects.filter(
                register_date__gte=start_date,
                register_date__lt=end_date,
                status='C',
                type='O',  # Solo órdenes de servicio, no cotizaciones
                **orders_filter
            ).select_related('subsidiary', 'client')
            
            # 2. Órdenes pendientes por sucursal y en general (solo tipo 'O', no cotizaciones)
            pending_orders = Order.objects.filter(
                register_date__gte=start_date,
                register_date__lt=end_date,
                status='P',
                type='O',  # Solo órdenes de servicio, no cotizaciones
                **orders_filter
            ).select_related('subsidiary', 'client')
            
            # 3. Productos más solicitados (solo órdenes tipo 'O', no cotizaciones)
            from django.db.models import Sum, Count
            top_products = OrderDetail.objects.filter(
                order__register_date__gte=start_date,
                order__register_date__lt=end_date,
                order__status__in=['P', 'C'],
                order__type='O',  # Solo órdenes de servicio, no cotizaciones
                **{'order__' + k: v for k, v in orders_filter.items()}
            ).values('product__name').annotate(
                total_quantity=Sum('quantity'),
                total_orders=Count('order')
            ).order_by('-total_quantity')[:10]
            
            # 4. Órdenes pendientes de entrega (solo tipo 'O', no cotizaciones)
            pending_delivery = Order.objects.filter(
                register_date__gte=start_date,
                register_date__lt=end_date,
                delivery_status='P',
                status__in=['P', 'C'],
                type='O',  # Solo órdenes de servicio, no cotizaciones
                **orders_filter
            ).select_related('subsidiary', 'client')
            
            # 5. Ingresos semanales (CashFlow tipo 'E')
            weekly_income = CashFlow.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lt=end_date,
                type='E',
                **cashflows_filter
            ).select_related('cash', 'cash__subsidiary')
            
            # 6. Gastos por sucursal
            weekly_expenses = CashFlow.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lt=end_date,
                type='S',
                **cashflows_filter
            ).select_related('cash', 'cash__subsidiary')
            
            # Calcular estadísticas
            weekly_income_total = weekly_income.aggregate(Sum('total'))['total__sum'] or 0
            weekly_expenses_total = weekly_expenses.aggregate(Sum('total'))['total__sum'] or 0
            
            stats = {
                'completed_orders_count': completed_orders.count(),
                'completed_orders_total': completed_orders.aggregate(Sum('total'))['total__sum'] or 0,
                'pending_orders_count': pending_orders.count(),
                'pending_orders_total': pending_orders.aggregate(Sum('total'))['total__sum'] or 0,
                'pending_delivery_count': pending_delivery.count(),
                'weekly_income_total': weekly_income_total,
                'weekly_expenses_total': weekly_expenses_total,
                'weekly_profit_total': weekly_income_total - weekly_expenses_total,  # Nueva métrica: diferencia ingresos - gastos
            }
            
            # Datos para gráficos
            chart_data = {
                'completed_orders_by_subsidiary': list(
                    completed_orders.values('subsidiary__name')
                    .annotate(count=Count('id'), total=Sum('total'))
                    .order_by('-count')
                ),
                'pending_orders_by_subsidiary': list(
                    pending_orders.values('subsidiary__name')
                    .annotate(count=Count('id'), total=Sum('total'))
                    .order_by('-count')
                ),
                'top_products': list(top_products),
                'income_by_subsidiary': list(
                    weekly_income.values('cash__subsidiary__name')
                    .annotate(total=Sum('total'))
                    .order_by('-total')
                ),
                'expenses_by_subsidiary': list(
                    weekly_expenses.values('cash__subsidiary__name')
                    .annotate(total=Sum('total'))
                    .order_by('-total')
                ),
                'daily_completed_orders': list(
                    completed_orders.extra(
                        select={'day': 'DATE(register_date)'}
                    ).values('day').annotate(count=Count('id')).order_by('day')
                ),
                'daily_income': list(
                    weekly_income.extra(
                        select={'day': 'DATE(transaction_date)'}
                    ).values('day').annotate(total=Sum('total')).order_by('day')
                ),
            }
            
            return JsonResponse({
                'success': True,
                'stats': stats,
                'chart_data': chart_data,
                'subsidiary': subsidiary_obj.name if subsidiary_obj else 'Todas las sucursales',
                'week_name': f'Semana {week} de {year}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al generar reporte semanal: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def sales_report_test(request):
    """Vista de prueba para el reporte"""
    if request.method == 'GET':
        subsidiary_set = Subsidiary.objects.all()
        cash_accounts = Cash.objects.all()
        
        # Fecha actual para el filtro
        date_now = datetime.now().strftime('%Y-%m-%d')
        
        return render(request, 'accounting/sales_report_test.html', {
            'subsidiary_set': subsidiary_set,
            'cash_accounts': cash_accounts,
            'date_now': date_now,
        })


def sales_report(request):
    """Vista principal del reporte de ventas y gastos"""
    if request.method == 'GET':
        subsidiary_set = Subsidiary.objects.all()
        cash_accounts = Cash.objects.all()
        
        # Fecha actual para el filtro
        date_now = datetime.now().strftime('%Y-%m-%d')
        
        # Obtener la sucursal del usuario actual
        user_subsidiary = None
        first_cash_account = None
        
        if hasattr(request.user, 'subsidiary') and request.user.subsidiary:
            user_subsidiary = request.user.subsidiary
            # Buscar la primera cuenta de tipo 'C' (Caja Chica/Efectivo) de la sucursal del usuario
            first_cash_account = Cash.objects.filter(
                subsidiary=user_subsidiary,
                account_type='C'
            ).first()
        
        # Si no hay cuenta de tipo 'C', buscar cualquier cuenta de la sucursal
        if not first_cash_account and user_subsidiary:
            first_cash_account = Cash.objects.filter(subsidiary=user_subsidiary).first()
        
        return render(request, 'accounting/sales_report.html', {
            'subsidiary_set': subsidiary_set,
            'cash_accounts': cash_accounts,
            'date_now': date_now,
            'user_subsidiary': user_subsidiary,
            'first_cash_account': first_cash_account,
        })
    elif request.method == 'POST':
        try:
            # Obtener parámetros del filtro
            report_date = request.POST.get('report_date')
            subsidiary_id = request.POST.get('subsidiary')
            cash_id = request.POST.get('cash_account')
            subsidiary_obj = None

            if not report_date:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una fecha'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Filtrar cashflows del día por sucursal
            if subsidiary_id and subsidiary_id != '0':
                subsidiary_obj = Subsidiary.objects.get(id=int(subsidiary_id))
                cashflows = CashFlow.objects.filter(
                    transaction_date=report_date,
                    cash__subsidiary_id=subsidiary_id
                )
            else:
                # Si no hay sucursal específica, mostrar todos los cashflows del día
                cashflows = CashFlow.objects.filter(
                    transaction_date=report_date
                )
            
            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary', 'order', 'order__client', 'order__subsidiary').prefetch_related('order__orderdetail_set')
            
            # Filtrar cashflows con order_id (ventas) y sin order_id (gastos)
            # Excluir órdenes anuladas (status='A')
            order_cashflows = cashflows.filter(order__isnull=False, order__status__in=['P', 'C'])
            
            # Calcular totales desde accounting_cashflow
            # total_sales: Suma total de todas las órdenes relacionadas con cashflows del día
            total_sales = sum(cf.order.total for cf in order_cashflows if cf.order) or 0
            
            # total_cash_advance: Suma de adelantos (tipo 'A') desde accounting_cashflow
            total_cash_advance = order_cashflows.filter(
                type='E',  # Entrada
                order_type_entry='A'  # Adelanto
            ).aggregate(total=Sum('total'))['total'] or 0
            
            # total_paid: Suma de pagos totales (tipo 'T') desde accounting_cashflow
            total_paid = order_cashflows.filter(
                type='E',  # Entrada
                order_type_entry='T'  # Pago Total
            ).aggregate(total=Sum('total'))['total'] or 0
            
            # total_balance: Saldo pendiente (ventas totales - adelantos totales - pagos totales)
            total_balance = total_sales - total_cash_advance - total_paid
            
            # Calcular totales de gastos
            total_income = cashflows.filter(type='E').aggregate(total=Sum('total'))['total'] or 0
            total_expenses = cashflows.filter(type='S').aggregate(total=Sum('total'))['total'] or 0
            net_expenses = total_expenses - total_income
            
            # Calcular subtotales por tipo de gasto según TYPE_EXPENSE
            total_variable_expenses = cashflows.filter(type='S', type_expense='V').aggregate(total=Sum('total'))['total'] or 0
            total_fixed_expenses = cashflows.filter(type='S', type_expense='F').aggregate(total=Sum('total'))['total'] or 0
            total_personal_expenses = cashflows.filter(type='S', type_expense='P').aggregate(total=Sum('total'))['total'] or 0
            total_other_expenses = cashflows.filter(type='S', type_expense='O').aggregate(total=Sum('total'))['total'] or 0
            
            # Calcular ingreso real: A Cuenta + Total Pagado
            real_income = total_cash_advance + total_paid
            
            # Calcular caja final
            # final_cash: Caja final = Ingreso real - Gastos netos
            # Donde: Gastos netos = Gastos totales - Ingresos por otros conceptos
            final_cash = real_income - net_expenses

            # NUEVA LÓGICA: 
            # 1. ADELANTOS = Todas las órdenes del día (con sus cashflows)
            # 2. SALDOS = Solo cashflows de cancelación (order_type_entry='T')
            
            # Obtener todas las órdenes del día del reporte
            orders_of_day = Order.objects.filter(
                register_date=report_date,
                status__in=['P', 'C']  # Pendientes y completadas
            ).order_by('id')
            
            if subsidiary_id and subsidiary_id != '0':
                orders_of_day = orders_of_day.filter(subsidiary_id=subsidiary_id)
            
            orders_of_day = orders_of_day.select_related('client', 'subsidiary', 'user').prefetch_related('orderdetail_set')
            
            # ========================================
            # DICT 1: ADVANCES OF THE DAY
            # ========================================
            advances_of_day = {}
            
            for order in orders_of_day:
                order_advances = cashflows.filter(
                    order=order,
                    type='E',  # Solo entradas
                    order_type_entry='A',  # Solo adelantos
                    transaction_date=report_date,  # Solo del día del reporte
                ).order_by('id')
                
                if order_advances.exists():
                    # Verificar si la orden tiene pagos totales
                    order_total_payments = cashflows.filter(
                        order=order,
                        type='E',  # Solo entradas
                        order_type_entry='T',  # Solo pagos totales
                        transaction_date=report_date  # Solo del día del reporte
                    )
                    
                    # Solo incluir en adelantos si NO tiene pagos totales
                    if not order_total_payments.exists():
                        total_advances = sum(float(cf.total) for cf in order_advances)
                        saldo = float(order.total) - total_advances
                        is_paid_in_full = abs(saldo) < 0.01
                        
                        advances_of_day[f"advance_{order.id}"] = {
                            'type': 'advance',
                            'order': order,
                            'cashflows': list(order_advances),
                            'total_amount': total_advances,
                            'balance': saldo,
                            'is_paid_in_full': is_paid_in_full,
                            'cashflow_count': order_advances.count()
                        }
            
            # ========================================
            # DICT 2: FULL PAYMENTS OF THE DAY
            # ========================================
            full_payments_of_day = {}
            
            for order in orders_of_day:
                order_payments = cashflows.filter(
                    order=order,
                    type='E',  # Solo entradas
                    order_type_entry='T',  # Solo pagos totales
                    transaction_date=report_date,  # Solo del día del reporte
                ).order_by('id')
                
                if order_payments.exists():
                    # También incluir adelantos si existen
                    order_advances = cashflows.filter(
                        order=order,
                        type='E',  # Solo entradas
                        order_type_entry='A',  # Solo adelantos
                        transaction_date=report_date  # Solo del día del reporte
                    ).order_by('id')
                    
                    # Combinar adelantos y pagos totales
                    all_cashflows = list(order_advances) + list(order_payments)
                    total_payments = sum(float(cf.total) for cf in all_cashflows)
                    
                    full_payments_of_day[f"payment_{order.id}"] = {
                        'type': 'full_payment',
                        'order': order,
                        'cashflows': all_cashflows,
                        'total_amount': total_payments,
                        'cashflow_count': len(all_cashflows)
                    }
            
            # ========================================
            # COMBINE THE TWO DICTS IN DAY INCOME
            # ========================================
            day_income = {}
            
            # 1. Add advances
            day_income.update(advances_of_day)
            
            # 2. Add separator
            day_income['separator'] = {'type': 'separator'}
            
            # 3. Add full payments
            day_income.update(full_payments_of_day)
            
            # ========================================
            # DICT 3: PREVIOUS DATE PAYMENTS
            # ========================================
            previous_payments = {}
            
            # Full payments from previous dates made on the report date
            previous_payments_cashflows = cashflows.filter(
                type='E',  # Solo entradas
                order_type_entry='T',  # Solo pagos totales
                transaction_date=report_date,  # Pagados en la fecha del reporte
                order__register_date__lt=report_date  # De órdenes de fechas anteriores
            ).order_by('order_id', 'id')
            
            for cashflow in previous_payments_cashflows:
                previous_payments[f"previous_{cashflow.id}"] = {
                    'order': cashflow.order,
                    'cashflows': [cashflow],
                    'total_amount': float(cashflow.total),
                    'transaction_date': cashflow.order.register_date,
                    'cashflow_count': 1
                }
            
            # ========================================
            # EXPENSES (mantener como estaba)
            # ========================================
            expenses_cashflows = cashflows.filter(
                order__isnull=True,
                type='S'  # Solo salidas (gastos)
            )

            # ========================================
            # CALCULATE TOTALS
            # ========================================
            
            # Total de apertura de caja (tipo 'A')
            total_apertura = cashflows.filter(type='A').aggregate(total=Sum('total'))['total'] or 0
            
            # Totales de ingresos del día
            total_day_income = 0
            day_income_cash = 0
            day_income_yape = 0
            day_income_deposit = 0
            
            for key, data in day_income.items():
                if data['type'] != 'separator':
                    total_day_income += data['total_amount']
                    for cashflow in data['cashflows']:
                        if cashflow.way_to_pay == 'E':
                            day_income_cash += decimal.Decimal(cashflow.total)
                        elif cashflow.way_to_pay == 'Y':
                            day_income_yape += decimal.Decimal(cashflow.total)
                        elif cashflow.way_to_pay == 'D':
                            day_income_deposit += decimal.Decimal(cashflow.total)
            
            # Totales de pagos de fechas anteriores
            total_previous_payments = 0
            previous_payments_cash = 0
            previous_payments_yape = 0
            previous_payments_deposit = 0
            
            for key, data in previous_payments.items():
                total_previous_payments += data['total_amount']
                for cashflow in data['cashflows']:
                    if cashflow.way_to_pay == 'E':
                        previous_payments_cash += decimal.Decimal(cashflow.total)
                    elif cashflow.way_to_pay == 'Y':
                        previous_payments_yape += decimal.Decimal(cashflow.total)
                    elif cashflow.way_to_pay == 'D':
                        previous_payments_deposit += decimal.Decimal(cashflow.total)
            
            # Totales de egresos
            total_expenses_amount = expenses_cashflows.aggregate(total=Sum('total'))['total'] or 0
            
            # Totales generales
            total_cash = day_income_cash + previous_payments_cash
            total_yape = day_income_yape + previous_payments_yape
            total_deposit = day_income_deposit + previous_payments_deposit
            total_general = total_cash + total_yape + total_deposit + total_apertura

            context = {
                'report_date': datetime.strptime(report_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                'day_income': day_income,  # Nuevo dict con ingresos del día
                'previous_payments': previous_payments,  # Nuevo dict con pagos anteriores
                'orders_of_day': orders_of_day,  # Todas las órdenes del día
                'expenses_cashflows': expenses_cashflows.order_by('id'),
                'total_day_income': total_day_income,  # Total ingresos del día
                'total_previous_payments': total_previous_payments,  # Total pagos anteriores
                'total_expenses_amount': total_expenses_amount,
                'total_apertura': total_apertura,  # Total apertura de caja
                'day_income_cash': day_income_cash,
                'day_income_yape': day_income_yape,
                'day_income_deposit': day_income_deposit,
                'previous_payments_cash': previous_payments_cash,
                'previous_payments_yape': previous_payments_yape,
                'previous_payments_deposit': previous_payments_deposit,
                'total_cash': total_cash,
                'total_yape': total_yape,
                'total_deposit': total_deposit,
                'total_general': total_general,
                'subsidiary': subsidiary_obj,
            }
            
            tpl = loader.get_template('accounting/sales_report_grid.html')
            
            return JsonResponse({
                'success': True,
                'grid': tpl.render(context, request),
                'summary': {
                    'total_sales': float(total_sales),
                    'total_cash_advance': float(total_cash_advance),
                    'total_paid': float(total_paid),
                    'total_balance': float(total_balance),
                    'real_income': float(real_income),
                    'total_income': float(total_income),
                    'total_expenses': float(total_expenses),
                    'net_expenses': float(net_expenses),
                    'final_cash': float(final_cash),
                    'total_variable_expenses': float(total_variable_expenses),
                    'total_fixed_expenses': float(total_fixed_expenses),
                    'total_personal_expenses': float(total_personal_expenses),
                    'total_other_expenses': float(total_other_expenses),
                }
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            print(f"ERROR en sales_report: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error al generar el reporte: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def sales_report_by_user(request):
    """Vista principal del reporte de ventas y gastos por usuario"""
    if request.method == 'GET':
        from apps.users.models import CustomUser
        
        # Verificar si el usuario tiene permisos de administrador
        is_admin = hasattr(request.user, 'has_access_to_all') and request.user.has_access_to_all
        
        # Obtener usuarios según permisos
        if is_admin:
            # Admin: mostrar todos los usuarios
            users_set = CustomUser.objects.filter(
                has_access_system=True,
                is_active=True,
                is_staff=False
            ).order_by('first_name', 'last_name')
        else:
            # Usuario normal: solo mostrar su propio usuario
            users_set = CustomUser.objects.filter(
                id=request.user.id,
                has_access_system=True,
                is_active=True
            )
        
        # Fecha actual para el filtro
        date_now = datetime.now().strftime('%Y-%m-%d')
        
        return render(request, 'accounting/sales_report_by_user.html', {
            'users_set': users_set,
            'date_now': date_now,
            'current_user': request.user,
            'is_admin': is_admin,
        })
    elif request.method == 'POST':
        try:
            from apps.users.models import CustomUser
            
            # Obtener parámetros del filtro
            report_date = request.POST.get('report_date')
            user_id = int(request.POST.get('user'))
            user_obj = None

            if not report_date:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una fecha'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Filtrar cashflows del día por usuario
            if user_id and user_id != '0':
                user_obj = CustomUser.objects.get(id=int(user_id))
                cashflows = CashFlow.objects.filter(
                    transaction_date=report_date,
                    user_id=user_id
                )
            else:
                # Si no hay usuario específico, mostrar todos los cashflows del día
                cashflows = CashFlow.objects.filter(
                    transaction_date=report_date
                )
            
            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary', 'order', 'order__client', 'order__subsidiary').prefetch_related('order__orderdetail_set')
            
            # Filtrar cashflows con order_id (ventas) y sin order_id (gastos)
            # Excluir órdenes anuladas (status='A')
            order_cashflows = cashflows.filter(order__isnull=False, order__status__in=['P', 'C'])
            
            # Calcular totales desde accounting_cashflow
            # total_sales: Suma total de todas las órdenes relacionadas con cashflows del día
            total_sales = sum(cf.order.total for cf in order_cashflows if cf.order) or 0
            
            # total_cash_advance: Suma de adelantos (tipo 'A') desde accounting_cashflow
            total_cash_advance = order_cashflows.filter(
                type='E',  # Entrada
                order_type_entry='A'  # Adelanto
            ).aggregate(total=Sum('total'))['total'] or 0
            
            # total_paid: Suma de pagos totales (tipo 'T') desde accounting_cashflow
            total_paid = order_cashflows.filter(
                type='E',  # Entrada
                order_type_entry='T'  # Pago Total
            ).aggregate(total=Sum('total'))['total'] or 0
            
            # total_balance: Saldo pendiente (ventas totales - adelantos totales - pagos totales)
            total_balance = total_sales - total_cash_advance - total_paid
            
            # Calcular totales de gastos
            total_income = cashflows.filter(type='E').aggregate(total=Sum('total'))['total'] or 0
            total_expenses = cashflows.filter(type='S').aggregate(total=Sum('total'))['total'] or 0
            net_expenses = total_expenses - total_income
            
            # Calcular subtotales por tipo de gasto según TYPE_EXPENSE
            total_variable_expenses = cashflows.filter(type='S', type_expense='V').aggregate(total=Sum('total'))['total'] or 0
            total_fixed_expenses = cashflows.filter(type='S', type_expense='F').aggregate(total=Sum('total'))['total'] or 0
            total_personal_expenses = cashflows.filter(type='S', type_expense='P').aggregate(total=Sum('total'))['total'] or 0
            total_other_expenses = cashflows.filter(type='S', type_expense='O').aggregate(total=Sum('total'))['total'] or 0
            
            # Calcular ingreso real: A Cuenta + Total Pagado
            real_income = total_cash_advance + total_paid
            
            # Calcular caja final
            # final_cash: Caja final = Ingreso real - Gastos netos
            # Donde: Gastos netos = Gastos totales - Ingresos por otros conceptos
            final_cash = real_income - net_expenses

            # NUEVA LÓGICA: 
            # 1. ADELANTOS = Todas las órdenes del día (con sus cashflows)
            # 2. SALDOS = Solo cashflows de cancelación (order_type_entry='T')
            
            # Obtener todas las órdenes del día del reporte
            orders_of_day = Order.objects.filter(
                register_date=report_date,
                status__in=['P', 'C']  # Pendientes y completadas
            ).order_by('id')
            
            # Si hay filtro por usuario, incluir órdenes que:
            # 1. Fueron creadas por el usuario, O
            # 2. Tienen cashflows del día realizados por el usuario
            if user_id and user_id != '0':
                # Obtener IDs de órdenes que tienen cashflows del usuario del día
                orders_with_user_cashflows = order_cashflows.filter(
                    user_id=user_id
                ).values_list('order_id', flat=True).distinct()
                
                # Filtrar órdenes: creadas por el usuario O con cashflows del usuario
                orders_of_day = orders_of_day.filter(
                    Q(user_id=user_id) | Q(id__in=orders_with_user_cashflows)
                )
            
            orders_of_day = orders_of_day.select_related('client', 'subsidiary', 'user').prefetch_related('orderdetail_set')
            
            # ========================================
            # DICT 1: ADELANTOS DEL USUARIO
            # ========================================
            adelantos_usuario = {}
            
            for order in orders_of_day:
                order_advances = cashflows.filter(
                    order=order,
                    type='E',  # Solo entradas
                    order_type_entry='A',  # Solo adelantos
                    transaction_date=report_date,  # Solo del día del reporte
                    user_id=user_id  # Solo hechos por el usuario
                ).order_by('id')
                
                if order_advances.exists():
                    # Verificar si la orden tiene pagos totales
                    order_total_payments = cashflows.filter(
                        order=order,
                        type='E',  # Solo entradas
                        order_type_entry='T',  # Solo pagos totales
                        transaction_date=report_date,  # Solo del día del reporte
                        user_id=user_id  # Solo hechos por el usuario
                    )
                    
                    # Solo incluir en adelantos si NO tiene pagos totales
                    if not order_total_payments.exists():
                        total_advances = sum(float(cf.total) for cf in order_advances)
                        saldo = float(order.total) - total_advances
                        is_paid_in_full = abs(saldo) < 0.01
                        
                        adelantos_usuario[f"advance_{order.id}"] = {
                            'tipo': 'adelanto',
                            'order': order,
                            'cashflows': list(order_advances),
                            'total_amount': total_advances,
                            'saldo': saldo,
                            'is_paid_in_full': is_paid_in_full,
                            'cashflow_count': order_advances.count()
                        }
            
            # ========================================
            # DICT 2: PAGOS TOTALES DE ÓRDENES DEL USUARIO
            # ========================================
            pagos_totales_usuario = {}
            
            for order in orders_of_day:
                # Solo procesar órdenes creadas por el usuario
                if order.user_id == int(user_id):
                    order_payments = cashflows.filter(
                        order=order,
                        type='E',  # Solo entradas
                        order_type_entry='T',  # Solo pagos totales
                        transaction_date=report_date,  # Solo del día del reporte
                        user_id=user_id  # Solo hechos por el usuario
                    ).order_by('id')
                    
                    if order_payments.exists():
                        # También incluir adelantos si existen
                        order_advances = cashflows.filter(
                            order=order,
                            type='E',  # Solo entradas
                            order_type_entry='A',  # Solo adelantos
                            transaction_date=report_date,  # Solo del día del reporte
                            user_id=user_id  # Solo hechos por el usuario
                        ).order_by('id')
                        
                        # Combinar adelantos y pagos totales
                        all_cashflows = list(order_advances) + list(order_payments)
                        total_payments = sum(float(cf.total) for cf in all_cashflows)
                        
                        pagos_totales_usuario[f"payment_{order.id}"] = {
                            'tipo': 'pago_total_usuario',
                            'order': order,
                            'cashflows': all_cashflows,
                            'total_amount': total_payments,
                            'cashflow_count': len(all_cashflows)
                        }
            
            # ========================================
            # DICT 3: PAGOS TOTALES DE ÓRDENES NO DEL USUARIO
            # ========================================
            pagos_totales_otros = {}
            
            other_orders_payments = cashflows.filter(
                type='E',  # Solo entradas
                order_type_entry='T',  # Solo pagos totales
                transaction_date=report_date,  # Solo del día del reporte
                user_id=user_id,  # Hechos por el usuario
                order__register_date=report_date  # De órdenes de hoy
            ).exclude(
                order__user_id=user_id  # Excluir órdenes creadas por el usuario
            ).order_by('order_id', 'id')
            
            for cashflow in other_orders_payments:
                pagos_totales_otros[f"cancellation_{cashflow.id}"] = {
                    'tipo': 'pago_total_otros',
                    'order': cashflow.order,
                    'cashflows': [cashflow],
                    'total_amount': float(cashflow.total),
                    'cashflow_count': 1
                }
            
            # ========================================
            # COMBINAR LOS TRES DICT EN INGRESOS DEL DÍA
            # ========================================
            ingresos_del_dia = {}
            
            # 1. Agregar adelantos
            ingresos_del_dia.update(adelantos_usuario)
            
            # 2. Agregar separador
            ingresos_del_dia['separador'] = {'tipo': 'separador'}
            
            # 3. Agregar pagos totales del usuario
            ingresos_del_dia.update(pagos_totales_usuario)
            
            # 4. Agregar separador de cancelaciones (solo si hay cancelaciones)
            if pagos_totales_otros:
                ingresos_del_dia['separador_cancelaciones'] = {'tipo': 'separador_cancelaciones'}
            
            # 5. Agregar pagos totales de otros (cancelaciones)
            ingresos_del_dia.update(pagos_totales_otros)
            
            # ========================================
            # DICT 2: PAGOS DE FECHAS ANTERIORES
            # ========================================
            pagos_fechas_anteriores = {}
            
            # Pagos totales de fechas anteriores hechas por el usuario

            previous_payments = cashflows.filter(
                type='E',  # Solo entradas
                order_type_entry='T',  # Solo pagos totales
                user_id=user_id,  # Hechos por el usuario
                transaction_date=report_date,  # Pagados en la fecha del reporte
                order__register_date__lt=report_date  # De órdenes de fechas anteriores
            ).order_by('order_id', 'id')
            
            for cashflow in previous_payments:
                pagos_fechas_anteriores[f"previous_{cashflow.id}"] = {
                    'order': cashflow.order,
                    'cashflows': [cashflow],
                    'total_amount': float(cashflow.total),
                    'transaction_date': cashflow.order.register_date,
                    'cashflow_count': 1
                }

            # Adelantos de fechas anteriores hechos en la fecha actual
            previous_advances = cashflows.filter(
                type='E',  # Solo entradas
                order_type_entry='A',  # Adelantos
                user_id=user_id,  # Hechos por el usuario
                transaction_date=report_date,  # Registrados en la fecha del reporte
                order__register_date__lt=report_date  # Pertenecen a órdenes de fechas anteriores
            ).order_by('order_id', 'id')

            for cashflow in previous_advances:
                pagos_fechas_anteriores[f"previous_advance_{cashflow.id}"] = {
                    'order': cashflow.order,
                    'cashflows': [cashflow],
                    'total_amount': float(cashflow.total),
                    'transaction_date': cashflow.order.register_date,
                    'cashflow_count': 1
                }
            
            # ========================================
            # EGRESOS (mantener como estaba)
            # ========================================
            expenses_cashflows = cashflows.filter(
                order__isnull=True,
                type='S'  # Solo salidas (gastos)
            )

            # ========================================
            # CÁLCULO DE TOTALES
            # ========================================
            
            # Total de apertura de caja (tipo 'A')
            total_apertura = cashflows.filter(type='A').aggregate(total=Sum('total'))['total'] or 0
            
            # Totales de ingresos del día
            total_ingresos_dia = 0
            ingresos_efectivo = 0
            ingresos_yape = 0
            ingresos_deposito = 0
            total_cancelaciones_otros = 0
            cancelaciones_efectivo = 0
            cancelaciones_yape = 0
            cancelaciones_deposito = 0
            
            for key, data in ingresos_del_dia.items():
                if data['tipo'] not in ['separador', 'separador_cancelaciones']:
                    total_ingresos_dia += data['total_amount']
                    for cashflow in data['cashflows']:
                        if cashflow.way_to_pay == 'E':
                            ingresos_efectivo += decimal.Decimal(cashflow.total)
                        elif cashflow.way_to_pay == 'Y':
                            ingresos_yape += decimal.Decimal(cashflow.total)
                        elif cashflow.way_to_pay == 'D':
                            ingresos_deposito += decimal.Decimal(cashflow.total)
                        
                        # Calcular totales específicos para cancelaciones de otros
                        if data['tipo'] == 'pago_total_otros':
                            total_cancelaciones_otros += float(cashflow.total)
                            if cashflow.way_to_pay == 'E':
                                cancelaciones_efectivo += decimal.Decimal(cashflow.total)
                            elif cashflow.way_to_pay == 'Y':
                                cancelaciones_yape += decimal.Decimal(cashflow.total)
                            elif cashflow.way_to_pay == 'D':
                                cancelaciones_deposito += decimal.Decimal(cashflow.total)
            
            # Totales de pagos de fechas anteriores
            total_pagos_anteriores = 0
            pagos_anteriores_efectivo = 0
            pagos_anteriores_yape = 0
            pagos_anteriores_deposito = 0
            
            for key, data in pagos_fechas_anteriores.items():
                total_pagos_anteriores += data['total_amount']
                for cashflow in data['cashflows']:
                    if cashflow.way_to_pay == 'E':
                        pagos_anteriores_efectivo += decimal.Decimal(cashflow.total)
                    elif cashflow.way_to_pay == 'Y':
                        pagos_anteriores_yape += decimal.Decimal(cashflow.total)
                    elif cashflow.way_to_pay == 'D':
                        pagos_anteriores_deposito += decimal.Decimal(cashflow.total)
            
            # Totales de egresos
            total_expenses_amount = expenses_cashflows.aggregate(total=Sum('total'))['total'] or 0
            
            # Totales generales
            total_efectivo = ingresos_efectivo + pagos_anteriores_efectivo
            total_yape = ingresos_yape + pagos_anteriores_yape
            total_deposito = ingresos_deposito + pagos_anteriores_deposito
            total_general = total_efectivo + total_yape + total_deposito + total_apertura

            context = {
                'report_date': datetime.strptime(report_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                'ingresos_del_dia': ingresos_del_dia,  # Nuevo dict con ingresos del día
                'pagos_fechas_anteriores': pagos_fechas_anteriores,  # Nuevo dict con pagos anteriores
                'orders_of_day': orders_of_day,  # Todas las órdenes del día
                'expenses_cashflows': expenses_cashflows.order_by('id'),
                'total_ingresos_dia': total_ingresos_dia,  # Total ingresos del día
                'total_pagos_anteriores': total_pagos_anteriores,  # Total pagos anteriores
                'total_expenses_amount': total_expenses_amount,
                'total_apertura': total_apertura,  # Total apertura de caja
                'ingresos_efectivo': ingresos_efectivo,
                'ingresos_yape': ingresos_yape,
                'ingresos_deposito': ingresos_deposito,
                'pagos_anteriores_efectivo': pagos_anteriores_efectivo,
                'pagos_anteriores_yape': pagos_anteriores_yape,
                'pagos_anteriores_deposito': pagos_anteriores_deposito,
                'total_efectivo': total_efectivo,
                'total_yape': total_yape,
                'total_deposito': total_deposito,
                'total_general': total_general,
                'user': user_obj,
                'total_cancelaciones_otros': total_cancelaciones_otros,  # Total cancelaciones de otros usuarios
                'cancelaciones_efectivo': cancelaciones_efectivo,
                'cancelaciones_yape': cancelaciones_yape,
                'cancelaciones_deposito': cancelaciones_deposito,
            }
            
            tpl = loader.get_template('accounting/sales_report_by_user_grid.html')
            
            return JsonResponse({
                'success': True,
                'grid': tpl.render(context, request),
                'summary': {
                    'total_sales': float(total_sales),
                    'total_cash_advance': float(total_cash_advance),
                    'total_paid': float(total_paid),
                    'total_balance': float(total_balance),
                    'real_income': float(real_income),
                    'total_income': float(total_income),
                    'total_expenses': float(total_expenses),
                    'net_expenses': float(net_expenses),
                    'final_cash': float(final_cash),
                    'total_variable_expenses': float(total_variable_expenses),
                    'total_fixed_expenses': float(total_fixed_expenses),
                    'total_personal_expenses': float(total_personal_expenses),
                    'total_other_expenses': float(total_other_expenses),
                }
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            print(f"ERROR en sales_report_by_user: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error al generar el reporte: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)



