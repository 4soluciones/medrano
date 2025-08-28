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
from django.db import DatabaseError, IntegrityError
from django.core import serializers
from django.db.models import Min, Sum, Max, Q, Prefetch, Subquery, OuterRef, Value, IntegerField, Case, ExpressionWrapper, DecimalField
from django.db.models.functions import ExtractYear
from medrano import settings
import os
from decimal import Decimal
from django.db.models import F


from ..sales.models import Person, Order
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
            initial_balance = request.POST.get('initial_balance', '0.00')
            currency_type = request.POST.get('currency_type', 'S')
            
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
                initial=Decimal(str(initial_balance)),
                currency_type=currency_type
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
                'initial': float(cash_obj.initial),
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
            initial_balance = request.POST.get('initial_balance', '0.00')
            currency_type = request.POST.get('currency_type', 'S')
            
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
            cash_obj.initial = Decimal(str(initial_balance))
            cash_obj.currency_type = currency_type
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


# =============================================================================
# VISTAS PARA GESTIÓN DE GASTOS (CASHFLOW)
# =============================================================================

def cashflow_list(request):
    """Vista principal del listado de gastos"""
    if request.method == 'GET':
        cash_accounts = Cash.objects.all()
        document_types = CashFlow.DOCUMENT_TYPE_ATTACHED_CHOICES
        transaction_types = [('E', 'Entrada'), ('S', 'Salida')]  # Solo entrada y salida
        expense_types = CashFlow.TYPE_EXPENSE
        user_set = CustomUser.objects.filter(is_active=True, is_staff=False)
        
        # Fecha actual para los filtros
        date_now = datetime.now().strftime('%Y-%m-%d')
        
        return render(request, 'accounting/cashflow_list.html', {
            'cash_accounts': cash_accounts,
            'document_types': document_types,
            'transaction_types': transaction_types,
            'expense_types': expense_types,
            'user_set': user_set,
            'date_now': date_now,
        })
    elif request.method == 'POST':
        try:
            # Filtrar gastos según parámetros
            cash_id = request.POST.get('cash_account')
            transaction_type = request.POST.get('transaction_type')
            expense_type = request.POST.get('expense_type')
            user_id = request.POST.get('user')
            date_from = request.POST.get('date_from')
            date_to = request.POST.get('date_to')
            
            cashflows = CashFlow.objects.all()
        
            if cash_id and cash_id != '0':
                cashflows = cashflows.filter(cash_id=cash_id)
            if transaction_type and transaction_type != '0':
                cashflows = cashflows.filter(type=transaction_type)
            if expense_type and expense_type != '0':
                cashflows = cashflows.filter(type_expense=expense_type)
            if user_id and user_id != '0':
                cashflows = cashflows.filter(user_id=user_id)

            # Filtros de fecha
            if date_from:
                cashflows = cashflows.filter(transaction_date__gte=date_from)
            if date_to:
                cashflows = cashflows.filter(transaction_date__lte=date_to)

            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary').order_by('-transaction_date')

            # Calcular totales
            total_income = cashflows.filter(type='E').aggregate(total=Sum('total'))['total'] or 0
            total_expenses = cashflows.filter(type='S').aggregate(total=Sum('total'))['total'] or 0
            net_balance = total_income - total_expenses

            # Totales por tipo de gasto
            expense_totals = {}
            for expense_code, expense_name in CashFlow.TYPE_EXPENSE:
                total = cashflows.filter(type='S', type_expense=expense_code).aggregate(
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
                'date_from': date_from,
                'date_to': date_to,
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
        transaction_types = [('E', 'Entrada'), ('S', 'Salida')]  # Solo entrada y salida
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
                user=user_obj
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
        transaction_types = [('E', 'Entrada'), ('S', 'Salida')]  # Solo entrada y salida
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
                        'balance': float(account.initial)
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
        
        return render(request, 'accounting/sales_report.html', {
            'subsidiary_set': subsidiary_set,
            'cash_accounts': cash_accounts,
            'date_now': date_now,
        })
    elif request.method == 'POST':
        try:
            # Obtener parámetros del filtro
            report_date = request.POST.get('report_date')
            subsidiary_id = request.POST.get('subsidiary')
            cash_id = request.POST.get('cash_account')

            if not report_date:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una fecha'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Filtrar órdenes del día
            orders = Order.objects.filter(
                register_date=report_date,
                status__in=['P', 'C']  # Pendiente o Completado
            )
            
            if subsidiary_id and subsidiary_id != '0':
                orders = orders.filter(subsidiary_id=subsidiary_id)
            
            orders = orders.select_related('client', 'user', 'subsidiary').prefetch_related('orderdetail_set')
            
            # Filtrar gastos del día
            cashflows = CashFlow.objects.filter(
                transaction_date__date=report_date
            )
            
            if cash_id and cash_id != '0':
                cashflows = cashflows.filter(cash_id=cash_id)
            
            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary')
            
            # Calcular totales de ventas
            # total_sales: Suma total de todas las ventas del día
            total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
            # total_cash_advance: Suma total de todos los adelantos recibidos
            total_cash_advance = orders.aggregate(total=Sum('cash_advance'))['total'] or 0
            # total_balance: Saldo pendiente (ventas totales - adelantos totales)
            total_balance = total_sales - total_cash_advance
            
            # Calcular totales de gastos
            total_income = cashflows.filter(type='E').aggregate(total=Sum('total'))['total'] or 0
            total_expenses = cashflows.filter(type='S').aggregate(total=Sum('total'))['total'] or 0
            net_expenses = total_expenses - total_income
            
            # Calcular subtotales por tipo de gasto según TYPE_EXPENSE
            total_variable_expenses = cashflows.filter(type='S', type_expense='V').aggregate(total=Sum('total'))['total'] or 0
            total_fixed_expenses = cashflows.filter(type='S', type_expense='F').aggregate(total=Sum('total'))['total'] or 0
            total_personal_expenses = cashflows.filter(type='S', type_expense='P').aggregate(total=Sum('total'))['total'] or 0
            total_other_expenses = cashflows.filter(type='S', type_expense='O').aggregate(total=Sum('total'))['total'] or 0
            
            # Calcular caja final
            # final_cash: Caja final = Saldo pendiente - Gastos netos
            # Donde: Gastos netos = Gastos totales - Ingresos por otros conceptos
            final_cash = total_balance - net_expenses

            context = {
                'report_date': report_date,
                'orders': orders.order_by('id'),
                'cashflows': cashflows.order_by('id'),
                'total_sales': total_sales,
                'total_cash_advance': total_cash_advance,
                'total_balance': total_balance,
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_expenses': net_expenses,
                'final_cash': final_cash,
                'total_variable_expenses': total_variable_expenses,
                'total_fixed_expenses': total_fixed_expenses,
                'total_personal_expenses': total_personal_expenses,
                'total_other_expenses': total_other_expenses,
                'subsidiary': orders.first().subsidiary if orders.exists() else None,
            }
            
            tpl = loader.get_template('accounting/sales_report_grid.html')
            
            return JsonResponse({
                'success': True,
                'grid': tpl.render(context, request),
                'summary': {
                    'total_sales': float(total_sales),
                    'total_cash_advance': float(total_cash_advance),
                    'total_balance': float(total_balance),
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


@csrf_exempt
def export_sales_report_excel(request):
    """Exportar reporte de ventas a Excel"""
    if request.method == 'POST':
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
            
            # Obtener datos del reporte
            report_date = request.POST.get('report_date')
            subsidiary_id = request.POST.get('subsidiary')
            cash_id = request.POST.get('cash_account')
            
            if not report_date:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una fecha'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Filtrar datos
            orders = Order.objects.filter(
                register_date=report_date,
                status__in=['P', 'C']
            )
            
            if subsidiary_id and subsidiary_id != '0':
                orders = orders.filter(subsidiary_id=subsidiary_id)
            
            orders = orders.select_related('client', 'user', 'subsidiary').prefetch_related('orderdetail_set')
            
            cashflows = CashFlow.objects.filter(
                transaction_date__date=report_date
            )
            
            if cash_id and cash_id != '0':
                cashflows = cashflows.filter(cash_id=cash_id)
            
            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary')
            
            # Calcular totales
            total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
            total_cash_advance = orders.aggregate(total=Sum('cash_advance'))['total'] or 0
            total_balance = total_sales - total_cash_advance
            total_income = cashflows.filter(type='E').aggregate(total=Sum('total'))['total'] or 0
            total_expenses = cashflows.filter(type='S').aggregate(total=Sum('total'))['total'] or 0
            net_expenses = total_expenses - total_income
            final_cash = total_balance - net_expenses
            
            # Crear workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = f"Reporte {report_date}"
            
            # Estilos
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            title_font = Font(bold=True, size=14, color="366092")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # Título principal
            ws.merge_cells('A1:J1')
            ws['A1'] = f"REPORTE DE VENTAS Y GASTOS - {report_date}"
            ws['A1'].font = title_font
            ws['A1'].alignment = Alignment(horizontal='center')
            
            # Sección de Ventas
            ws['A3'] = "PRINCIPAL DÍA"
            ws['A3'].font = header_font
            ws['A3'].fill = header_fill
            ws.merge_cells('A3:J3')
            ws['A3'].alignment = Alignment(horizontal='center')
            
            # Encabezados de ventas
            sales_headers = ['NRO', 'FECHA', 'N° COMPROBANTE', 'CLIENTE', 'CANTIDAD', 'DESCRIPCIÓN', 'A CUENTA', 'SALDO', 'TOTAL', 'CELULAR']
            for col, header in enumerate(sales_headers, 1):
                cell = ws.cell(row=4, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
            
            # Datos de ventas
            row = 5
            for order in orders:
                ws.cell(row=row, column=1, value=row-4).border = border
                ws.cell(row=row, column=2, value=order.register_date.strftime('%d/%m/%Y')).border = border
                ws.cell(row=row, column=3, value=order.code or '').border = border
                ws.cell(row=row, column=4, value=order.client.full_name if order.client else '').border = border
                ws.cell(row=row, column=5, value=1).border = border
                ws.cell(row=row, column=6, value=order.observation or 'ORDEN DE SERVICIO').border = border
                ws.cell(row=row, column=7, value=float(order.cash_advance)).border = border
                ws.cell(row=row, column=8, value=float(order.total - order.cash_advance)).border = border
                ws.cell(row=row, column=9, value=float(order.total)).border = border
                ws.cell(row=row, column=10, value='').border = border
                row += 1
            
            # Totales de ventas
            ws.cell(row=row+1, column=8, value="CAJA").font = Font(bold=True)
            ws.cell(row=row+1, column=9, value=float(total_sales)).font = Font(bold=True)
            
            ws.cell(row=row+2, column=7, value="INGRESO REAL").font = Font(bold=True, color="FF0000")
            ws.cell(row=row+2, column=8, value=float(total_balance)).font = Font(bold=True, color="FF0000")
            ws.cell(row=row+2, column=9, value=float(total_sales)).font = Font(bold=True, color="FF0000")
            
            # Sección de Gastos
            ws['L3'] = "GASTOS"
            ws['L3'].font = header_font
            ws['L3'].fill = header_fill
            ws.merge_cells('L3:M3')
            ws['L3'].alignment = Alignment(horizontal='center')
            
            # Encabezados de gastos
            ws['L4'] = "GASTOS PERSONALES"
            ws['L4'].font = header_font
            ws['L4'].fill = header_fill
            ws['L4'].border = border
            ws['M4'] = "IMPORTE"
            ws['M4'].font = header_font
            ws['M4'].fill = header_fill
            ws['M4'].border = border
            
            # Gastos Variables
            row_gastos = 5
            ws.cell(row=row_gastos, column=12, value="GASTOS VARIABLES").font = header_font
            ws.cell(row=row_gastos, column=12).fill = header_fill
            ws.cell(row=row_gastos, column=12).border = border
            ws.cell(row=row_gastos, column=13, value="IMPORTE").font = header_font
            ws.cell(row=row_gastos, column=13).fill = header_fill
            ws.cell(row=row_gastos, column=13).border = border
            
            row_gastos += 1
            variable_expenses = cashflows.filter(type='S', type_expense='V')
            for expense in variable_expenses:
                ws.cell(row=row_gastos, column=12, value=expense.description).border = border
                ws.cell(row=row_gastos, column=13, value=float(expense.total)).border = border
                row_gastos += 1
            
            # Subtotal gastos variables
            total_variable = variable_expenses.aggregate(total=Sum('total'))['total'] or 0
            if total_variable > 0:
                ws.cell(row=row_gastos, column=12, value="SUB TOTAL").font = Font(bold=True)
                ws.cell(row=row_gastos, column=13, value=float(total_variable)).font = Font(bold=True)
                row_gastos += 1
            
            # Gastos Fijos
            row_gastos += 1
            ws.cell(row=row_gastos, column=12, value="GASTOS FIJOS").font = header_font
            ws.cell(row=row_gastos, column=12).fill = header_fill
            ws.cell(row=row_gastos, column=12).border = border
            ws.cell(row=row_gastos, column=13, value="IMPORTE").font = header_font
            ws.cell(row=row_gastos, column=13).fill = header_fill
            ws.cell(row=row_gastos, column=13).border = border
            
            row_gastos += 1
            fixed_expenses = cashflows.filter(type='S', type_expense='F')
            for expense in fixed_expenses:
                ws.cell(row=row_gastos, column=12, value=expense.description).border = border
                ws.cell(row=row_gastos, column=13, value=float(expense.total)).border = border
                row_gastos += 1
            
            # Subtotal gastos fijos
            total_fixed = fixed_expenses.aggregate(total=Sum('total'))['total'] or 0
            if total_fixed > 0:
                ws.cell(row=row_gastos, column=12, value="SUB TOTAL").font = Font(bold=True)
                ws.cell(row=row_gastos, column=13, value=float(total_fixed)).font = Font(bold=True)
                row_gastos += 1
            
            # Gastos Personales
            row_gastos += 1
            ws.cell(row=row_gastos, column=12, value="GASTOS PERSONALES").font = header_font
            ws.cell(row=row_gastos, column=12).fill = header_fill
            ws.cell(row=row_gastos, column=12).border = border
            ws.cell(row=row_gastos, column=13, value="IMPORTE").font = header_font
            ws.cell(row=row_gastos, column=13).fill = header_fill
            ws.cell(row=row_gastos, column=13).border = border
            
            row_gastos += 1
            personal_expenses = cashflows.filter(type='S', type_expense='P')
            for expense in personal_expenses:
                ws.cell(row=row_gastos, column=12, value=expense.description).border = border
                ws.cell(row=row_gastos, column=13, value=float(expense.total)).border = border
                row_gastos += 1
            
            # Subtotal gastos personales
            total_personal = personal_expenses.aggregate(total=Sum('total'))['total'] or 0
            if total_personal > 0:
                ws.cell(row=row_gastos, column=12, value="SUB TOTAL").font = Font(bold=True)
                ws.cell(row=row_gastos, column=13, value=float(total_personal)).font = Font(bold=True)
                row_gastos += 1
            
            # Otros Gastos
            row_gastos += 1
            ws.cell(row=row_gastos, column=12, value="OTROS GASTOS").font = header_font
            ws.cell(row=row_gastos, column=12).fill = header_fill
            ws.cell(row=row_gastos, column=12).border = border
            ws.cell(row=row_gastos, column=13, value="IMPORTE").font = header_font
            ws.cell(row=row_gastos, column=13).fill = header_fill
            ws.cell(row=row_gastos, column=13).border = border
            
            row_gastos += 1
            other_expenses = cashflows.filter(type='S', type_expense='O')
            for expense in other_expenses:
                ws.cell(row=row_gastos, column=12, value=expense.description).border = border
                ws.cell(row=row_gastos, column=13, value=float(expense.total)).border = border
                row_gastos += 1
            
            # Subtotal otros gastos
            total_other = other_expenses.aggregate(total=Sum('total'))['total'] or 0
            if total_other > 0:
                ws.cell(row=row_gastos, column=12, value="SUB TOTAL").font = Font(bold=True)
                ws.cell(row=row_gastos, column=13, value=float(total_other)).font = Font(bold=True)
                row_gastos += 1
            
            # Total general de gastos
            row_gastos += 1
            ws.cell(row=row_gastos, column=12, value="GASTOS TOTAL").font = Font(bold=True, color="FF0000")
            ws.cell(row=row_gastos, column=13, value=float(total_expenses)).font = Font(bold=True, color="FF0000")
            
            # Ajustar ancho de columnas
            for col in range(1, 14):
                ws.column_dimensions[get_column_letter(col)].width = 15
            
            # Guardar archivo
            filename = f"reporte_ventas_gastos_{report_date}.xlsx"
            filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            wb.save(filepath)
            
            # Retornar URL del archivo
            file_url = f"{settings.MEDIA_URL}reports/{filename}"
            
            return JsonResponse({
                'success': True,
                'message': 'Reporte exportado exitosamente',
                'file_url': file_url,
                'filename': filename
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al exportar el reporte: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@csrf_exempt
def export_sales_report_pdf(request):
    """Exportar reporte de ventas a PDF"""
    if request.method == 'POST':
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            
            # Obtener datos del reporte
            report_date = request.POST.get('report_date')
            subsidiary_id = request.POST.get('subsidiary')
            cash_id = request.POST.get('cash_account')
            
            if not report_date:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una fecha'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Filtrar datos
            orders = Order.objects.filter(
                register_date=report_date,
                status__in=['P', 'C']
            )
            
            if subsidiary_id and subsidiary_id != '0':
                orders = orders.filter(subsidiary_id=subsidiary_id)
            
            orders = orders.select_related('client', 'user', 'subsidiary').prefetch_related('orderdetail_set')
            
            cashflows = CashFlow.objects.filter(
                transaction_date__date=report_date
            )
            
            if cash_id and cash_id != '0':
                cashflows = cashflows.filter(cash_id=cash_id)
            
            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary')
            
            # Calcular totales
            total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
            total_cash_advance = orders.aggregate(total=Sum('cash_advance'))['total'] or 0
            total_balance = total_sales - total_cash_advance
            total_income = cashflows.filter(type='E').aggregate(total=Sum('total'))['total'] or 0
            total_expenses = cashflows.filter(type='S').aggregate(total=Sum('total'))['total'] or 0
            net_expenses = total_expenses - total_income
            final_cash = total_balance - net_expenses
            
            # Crear archivo PDF
            filename = f"reporte_ventas_gastos_{report_date}.pdf"
            filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            doc = SimpleDocTemplate(filepath, pagesize=landscape(letter))
            story = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1,
                textColor=colors.darkblue
            )
            
            # Título
            story.append(Paragraph(f"REPORTE DE VENTAS Y GASTOS - {report_date}", title_style))
            story.append(Spacer(1, 20))
            
            # Tabla de ventas
            sales_data = [['NRO', 'FECHA', 'COMPROBANTE', 'CLIENTE', 'A CUENTA', 'SALDO', 'TOTAL']]
            
            for i, order in enumerate(orders, 1):
                sales_data.append([
                    str(i),
                    order.register_date.strftime('%d/%m/%Y'),
                    order.code or '',
                    order.client.full_name if order.client else '',
                    f"S/. {float(order.cash_advance):.2f}",
                    f"S/. {float(order.total - order.cash_advance):.2f}",
                    f"S/. {float(order.total):.2f}"
                ])
            
            # Agregar totales
            sales_data.append(['', '', '', 'TOTAL VENTAS:', '', '', f"S/. {float(total_sales):.2f}"])
            sales_data.append(['', '', '', 'INGRESO REAL:', '', f"S/. {float(total_balance):.2f}", f"S/. {float(total_sales):.2f}"])
            
            sales_table = Table(sales_data)
            sales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -2), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(sales_table)
            story.append(Spacer(1, 20))
            
            # Tabla de gastos
            expenses_data = [['DESCRIPCIÓN', 'IMPORTE']]
            
            # Gastos Variables
            variable_expenses = cashflows.filter(type='S', type_expense='V')
            if variable_expenses.exists():
                expenses_data.append(['GASTOS VARIABLES', ''])
                for expense in variable_expenses:
                    expenses_data.append([expense.description, f"S/. {float(expense.total):.2f}"])
                total_variable = variable_expenses.aggregate(total=Sum('total'))['total'] or 0
                expenses_data.append(['SUB TOTAL VARIABLES', f"S/. {float(total_variable):.2f}"])
                expenses_data.append(['', ''])
            
            # Gastos Fijos
            fixed_expenses = cashflows.filter(type='S', type_expense='F')
            if fixed_expenses.exists():
                expenses_data.append(['GASTOS FIJOS', ''])
                for expense in fixed_expenses:
                    expenses_data.append([expense.description, f"S/. {float(expense.total):.2f}"])
                total_fixed = fixed_expenses.aggregate(total=Sum('total'))['total'] or 0
                expenses_data.append(['SUB TOTAL FIJOS', f"S/. {float(total_fixed):.2f}"])
                expenses_data.append(['', ''])
            
            # Gastos Personales
            personal_expenses = cashflows.filter(type='S', type_expense='P')
            if personal_expenses.exists():
                expenses_data.append(['GASTOS PERSONALES', ''])
                for expense in personal_expenses:
                    expenses_data.append([expense.description, f"S/. {float(expense.total):.2f}"])
                total_personal = personal_expenses.aggregate(total=Sum('total'))['total'] or 0
                expenses_data.append(['SUB TOTAL PERSONAL', f"S/. {float(total_personal):.2f}"])
                expenses_data.append(['', ''])
            
            # Otros Gastos
            other_expenses = cashflows.filter(type='S', type_expense='O')
            if other_expenses.exists():
                expenses_data.append(['OTROS GASTOS', ''])
                for expense in other_expenses:
                    expenses_data.append([expense.description, f"S/. {float(expense.total):.2f}"])
                total_other = other_expenses.aggregate(total=Sum('total'))['total'] or 0
                expenses_data.append(['SUB TOTAL OTROS', f"S/. {float(total_other):.2f}"])
                expenses_data.append(['', ''])
            
            expenses_data.append(['GASTOS TOTAL', f"S/. {float(total_expenses):.2f}"])
            
            expenses_table = Table(expenses_data)
            expenses_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(expenses_table)
            story.append(Spacer(1, 20))
            
            # Resumen final
            summary_data = [
                ['RESUMEN FINAL'],
                ['Total Ventas:', f"S/. {float(total_sales):.2f}"],
                ['Total Gastos:', f"S/. {float(total_expenses):.2f}"],
                ['Caja Final:', f"S/. {float(final_cash):.2f}"]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            
            # Generar PDF
            doc.build(story)
            
            # Retornar URL del archivo
            file_url = f"{settings.MEDIA_URL}reports/{filename}"
            
            return JsonResponse({
                'success': True,
                'message': 'Reporte PDF generado exitosamente',
                'file_url': file_url,
                'filename': filename
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al generar el PDF: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    
    return JsonResponse({'message': 'Error de petición.'}, status=HTTPStatus.BAD_REQUEST)

