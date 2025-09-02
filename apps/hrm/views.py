import decimal
from datetime import datetime, timedelta, time
from http import HTTPStatus
import json
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Max, Q, F, Sum
from django.db.models.functions import Coalesce
from django.template import loader
from django.core import serializers
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from django.utils import timezone

# Create your views here.
from apps.hrm.models import Subsidiary, FunctionArea, FunctionCharge, Charge, Area, PaymentPeriod, PaymentTemplate, DailyPayment
from django.http import JsonResponse
from django.shortcuts import render

from apps.sales.views_API import query_apis_net_dni_ruc
from apps.users.models import CustomUser
from medrano import settings
from apps.accounting.models import CashFlow


class Home(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        pk = self.request.user.id
        user_obj = CustomUser.objects.get(id=int(pk))
        subsidiary_obj = user_obj.subsidiary
        current_date = datetime.now()

        context = {
            'current': current_date,
            'subsidiary_obj': subsidiary_obj,
        }
        return context


def get_subsidiary_list(request):
    if request.method == 'GET':
        subsidiary_set = Subsidiary.objects.all().order_by('id')
        return render(request, 'hrm/subsidiary_list.html', {
            'subsidiary_set': subsidiary_set,
        })


def modal_subsidiary_create(request):
    if request.method == 'GET':
        t = loader.get_template('hrm/subsidiary_create.html')
        return JsonResponse({
            'form': t.render({}, request),
        })


@csrf_exempt
def create_subsidiary(request):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            _serial = request.POST.get('serial', '')
            _name = request.POST.get('name', '')
            _phone = request.POST.get('phone', '')
            _email = request.POST.get('email', '')
            _ruc = request.POST.get('ruc', '')
            _address = request.POST.get('address', '')
            _business = request.POST.get('business-name', '')
            _representative_dni = request.POST.get('representative-dni', '')
            _representative_name = request.POST.get('representative-name', '')
            _observation = request.POST.get('observation-input', '')
            
            # Validar campos requeridos
            if not _name or not _ruc or not _business:
                return JsonResponse({
                    'success': False,
                    'message': 'Los campos Nombre, RUC y Razón Social son obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Crear objeto Subsidiary con los campos del modelo
            subsidiary_obj = Subsidiary(
                name=_name,
                serial=_serial,
                phone=_phone,
                address=_address,
                ruc=_ruc,
                email=_email,
                business_name=_business,
                representative_dni=_representative_dni,
                representative_name=_representative_name,
                observation=_observation,
            )
            
            # Manejar la foto si se subió una
            if 'photo' in request.FILES:
                subsidiary_obj.photo = request.FILES['photo']
            
            subsidiary_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Sucursal registrada con éxito'
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar la sucursal: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def modal_subsidiary_update(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        subsidiary_obj = None
        if pk:
            subsidiary_obj = Subsidiary.objects.get(id=int(pk))
        t = loader.get_template('hrm/subsidiary_update.html')
        c = ({
            'subsidiary_obj': subsidiary_obj,
        })
        return JsonResponse({
            'form': t.render(c, request),
        })


@csrf_exempt
def update_subsidiary(request):
    if request.method == 'POST':
        _pk = request.POST.get('pk', '')
        subsidiary_obj = None
        if _pk:
            subsidiary_obj = Subsidiary.objects.get(id=int(_pk))
        _serial = request.POST.get('serial', '')
        _name = request.POST.get('name', '')
        _phone = request.POST.get('phone', '')
        _email = request.POST.get('email', '')
        _ruc = request.POST.get('ruc', '')
        _address = request.POST.get('address', '')
        _business = request.POST.get('business-name', '')
        _representative_dni = request.POST.get('representative-dni', '')
        _representative_name = request.POST.get('representative-name', '')
        _observation_input = request.POST.get('observation-input', '')
        if subsidiary_obj is not None:
            # Validar campos requeridos
            if not _name or not _ruc or not _business:
                return JsonResponse({
                    'success': False,
                    'message': 'Los campos Nombre, RUC y Razón Social son obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Actualizar objeto Subsidiary
            subsidiary_obj.serial = _serial
            subsidiary_obj.name = _name
            subsidiary_obj.phone = _phone
            subsidiary_obj.email = _email
            subsidiary_obj.address = _address
            subsidiary_obj.ruc = _ruc
            subsidiary_obj.business_name = _business
            subsidiary_obj.representative_dni = _representative_dni
            subsidiary_obj.representative_name = _representative_name
            subsidiary_obj.observation = _observation_input  # Usar el campo correcto del modelo
            
            # Manejar la foto si se subió una nueva
            if 'photo' in request.FILES:
                subsidiary_obj.photo = request.FILES['photo']
            
            subsidiary_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Sucursal actualizada con éxito'
            }, status=HTTPStatus.OK)
        else:
            return JsonResponse({
                'success': False,
                'message': 'No se identificó la sucursal'
            }, status=HTTPStatus.BAD_REQUEST)


def get_employee_list(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = CustomUser.objects.get(id=int(user_id))
        user_set = CustomUser.objects.filter(is_superuser=False).order_by('id')
        return render(request, 'hrm/employee_list.html', {
            'user_set': user_set,
            'user_log': user_obj
        })


def modal_user_create(request):
    if request.method == 'GET':
        my_date = datetime.now()
        date_now = my_date.strftime("%Y-%m-%d")
        t = loader.get_template('hrm/user_create.html')
        c = ({
            'date_now': date_now,
            'gender_set': CustomUser._meta.get_field('gender').choices,
            'nationality_set': CustomUser._meta.get_field('nationality').choices,
            'education_set': CustomUser._meta.get_field('education').choices,
            'marital_status_set': CustomUser._meta.get_field('marital_status').choices,
            'subsidiary_set': Subsidiary.objects.all(),
        })
        return JsonResponse({
            'form': t.render(c, request),
        })


# registrar empleado
@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            _document = request.POST.get('document', '')
            _first_name = request.POST.get('first-name', '')
            _last_name = request.POST.get('last-name', '')
            _phone = request.POST.get('phone', '')
            _gender = request.POST.get('gender', '')
            _subsidiary = request.POST.get('subsidiary', '')
            _education = request.POST.get('education', '')
            _nationality = request.POST.get('nationality', '')
            _marital_status = request.POST.get('marital-status', '')
            _reference = request.POST.get('reference', '')
            _observations = request.POST.get('observations', '')
            _cellphone = request.POST.get('cellphone', '')
            _address = request.POST.get('address', '')
            _email = request.POST.get('email', '')
            _user = request.POST.get('user', '')
            _password = request.POST.get('password', '')
            
            # Checkboxes de permisos
            _check_access = request.POST.get('customCheckboxAccess', False)
            _check_active = request.POST.get('customCheckActive', False)
            _check_sales = request.POST.get('customCheckboxSales', False)
            _check_admin = request.POST.get('customCheckboxAdmin', False)

            # Convertir checkboxes a boolean
            if _check_access == 'on':
                _check_access = True
            if _check_active == 'on':
                _check_active = True
            if _check_sales == 'on':
                _check_sales = True
            if _check_admin == 'on':
                _check_admin = True
            
            # Validar campos requeridos
            if not _first_name or not _last_name or not _email or not _password:
                return JsonResponse({
                    'success': False,
                    'message': 'Los campos Nombres, Apellidos, Email y Contraseña son obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Validar sucursal
            if _subsidiary == '0' or not _subsidiary:
                return JsonResponse({
                    'success': False,
                    'message': 'Seleccione una sucursal'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener objeto sucursal
            _subsidiary_obj = Subsidiary.objects.get(id=int(_subsidiary))
            
            # Procesar fecha de nacimiento
            _birth_date = None
            if request.POST.get('birth-date', '') != '':
                _birth_date = datetime.strptime(request.POST.get('birth-date', ''), '%Y-%m-%d')
            
            # Procesar foto
            try:
                _photo = request.FILES['exampleInputFile']
            except Exception as e:
                _photo = 'employee/employee0.jpg'
            
            # Generar username si no se proporciona
            if not _user:
                _user = _email
            
            # Verificar si el usuario ya existe
            try:
                user_obj = CustomUser.objects.get(username=_user)
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de usuario ya existe'
                }, status=HTTPStatus.BAD_REQUEST)
            except CustomUser.DoesNotExist:
                pass
            
            # Verificar si el email ya existe
            try:
                user_obj = CustomUser.objects.get(email=_email)
                return JsonResponse({
                    'success': False,
                    'message': 'El correo electrónico ya existe'
                }, status=HTTPStatus.BAD_REQUEST)
            except CustomUser.DoesNotExist:
                pass
            
            # Crear usuario
            user_obj = CustomUser(
                username=_user,
                email=_email,
                first_name=_first_name,
                last_name=_last_name,
                is_active=_check_active,
                document=_document,
                birth_date=_birth_date,
                phone=_phone,
                gender=_gender,
                subsidiary=_subsidiary_obj,
                address=_address,
                education=_education,
                nationality=_nationality,
                marital_status=_marital_status,
                reference=_reference,
                cellphone=_cellphone,
                observations=_observations,
                has_access_system=_check_access,
                has_access_to_sales=_check_sales,
                has_access_to_all=_check_admin
            )
            
            # Establecer contraseña
            user_obj.set_password(_password)
            
            # Guardar usuario
            user_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Colaborador registrado con éxito'
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar el colaborador: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def modal_user_update(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        user_obj = None
        if pk:
            user_obj = CustomUser.objects.get(id=int(pk))

        my_date = datetime.now()
        date_now = my_date.strftime("%Y-%m-%d")

        t = loader.get_template('hrm/user_update.html')
        c = ({
            'user_obj': user_obj,
            'gender_set': CustomUser._meta.get_field('gender').choices,
            'nationality_set': CustomUser._meta.get_field('nationality').choices,
            'education_set': CustomUser._meta.get_field('education').choices,
            'marital_status_set': CustomUser._meta.get_field('marital_status').choices,
            'subsidiary_set': Subsidiary.objects.all(),
            'date_now': date_now,
        })
        return JsonResponse({
            'form': t.render(c, request),
        })


def validate_date(date_text):
    try:
        if date_text != datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        return True
    except ValueError:
        return False


@csrf_exempt
def update_user(request):
    if request.method == 'POST':
        try:
            _pk = request.POST.get('pk-user', '')
            
            if not _pk:
                return JsonResponse({
                    'success': False,
                    'message': 'No se identificó al usuario'
                }, status=HTTPStatus.BAD_REQUEST)
            
            user_obj = CustomUser.objects.get(id=int(_pk))
            if not user_obj:
                return JsonResponse({
                    'success': False,
                    'message': 'Problemas al obtener el usuario'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener datos del formulario
            _document = request.POST.get('document', '')
            _first_name = request.POST.get('first-name', '')
            _last_name = request.POST.get('last-name', '')
            _phone = request.POST.get('phone', '')
            _gender = request.POST.get('gender', '')
            _subsidiary = request.POST.get('subsidiary', '')
            _education = request.POST.get('education', '')
            _nationality = request.POST.get('nationality', '')
            _marital_status = request.POST.get('marital-status', '')
            _reference = request.POST.get('reference', '')
            _observations = request.POST.get('observations', '')
            _cellphone = request.POST.get('cellphone', '')
            _address = request.POST.get('address', '')
            _email = request.POST.get('email', '')
            _user = request.POST.get('user', '')
            _password = request.POST.get('password', '')
            
            # Checkboxes de permisos
            _check_active = request.POST.get('customCheckActive', False)
            _check_access = request.POST.get('customCheckboxAccess', False)
            _check_sales = request.POST.get('customCheckboxSales', False)
            _check_admin = request.POST.get('customCheckboxAdmin', False)
            
            # Convertir checkboxes a boolean
            if _check_active == 'on':
                _check_active = True
            if _check_access == 'on':
                _check_access = True
            if _check_sales == 'on':
                _check_sales = True
            if _check_admin == 'on':
                _check_admin = True
            
            # Validar campos requeridos
            if not _first_name or not _last_name or not _email:
                return JsonResponse({
                    'success': False,
                    'message': 'Los campos Nombres, Apellidos y Email son obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Validar sucursal
            if _subsidiary == '0' or not _subsidiary:
                return JsonResponse({
                    'success': False,
                    'message': 'Seleccione una sucursal'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Obtener objeto sucursal
            _subsidiary_obj = Subsidiary.objects.get(id=int(_subsidiary))
            
            # Procesar fecha de nacimiento
            _birth_date = None
            if request.POST.get('birth-date', '') != '':
                _birth_date = datetime.strptime(request.POST.get('birth-date', ''), '%Y-%m-%d')
            
            # Verificar si el username ya existe (si cambió)
            if _user and _user != user_obj.username:
                try:
                    existing_user = CustomUser.objects.get(username=_user)
                    if existing_user.id != user_obj.id:
                        return JsonResponse({
                            'success': False,
                            'message': 'El nombre de usuario ya existe'
                        }, status=HTTPStatus.BAD_REQUEST)
                except CustomUser.DoesNotExist:
                    pass
            
            # Verificar si el email ya existe (si cambió)
            if _email != user_obj.email:
                try:
                    existing_user = CustomUser.objects.get(email=_email)
                    if existing_user.id != user_obj.id:
                        return JsonResponse({
                            'success': False,
                            'message': 'El correo electrónico ya existe'
                        }, status=HTTPStatus.BAD_REQUEST)
                except CustomUser.DoesNotExist:
                    pass
            
            # Procesar foto
            _photo = request.FILES.get('exampleInputFile', False)
            
            # Actualizar campos del usuario
            user_obj.first_name = _first_name
            user_obj.last_name = _last_name
            user_obj.email = _email
            user_obj.username = _user
            user_obj.is_active = _check_active
            user_obj.document = _document
            user_obj.birth_date = _birth_date
            user_obj.gender = _gender
            user_obj.phone = _phone
            user_obj.subsidiary = _subsidiary_obj
            user_obj.address = _address
            user_obj.education = _education
            user_obj.nationality = _nationality
            user_obj.marital_status = _marital_status
            user_obj.reference = _reference
            user_obj.cellphone = _cellphone
            user_obj.observations = _observations
            user_obj.has_access_system = _check_access
            user_obj.has_access_to_sales = _check_sales
            user_obj.has_access_to_all = _check_admin
            
            # Actualizar foto si se proporcionó una nueva
            if _photo:
                user_obj.photo = _photo
            
            # Actualizar contraseña si se proporcionó una nueva
            if _password:
                user_obj.set_password(_password)
            
            # Guardar cambios
            user_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Colaborador actualizado con éxito'
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar el colaborador: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


# ============================================================================
# VISTAS PARA EL SISTEMA DE PAGOS
# ============================================================================

def get_payment_dashboard(request):
    """Dashboard principal de pagos"""
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = CustomUser.objects.get(id=int(user_id))
        
        # Obtener períodos de pago recientes
        recent_payments = PaymentPeriod.objects.select_related('employee').order_by('-created_at')[:10]
        
        # Obtener empleados activos (no superusuarios)
        employees_with_templates = CustomUser.objects.filter(
            is_superuser=False,
            is_active=True
        ).order_by('first_name')
        
        # Estadísticas
        total_paid = PaymentPeriod.objects.filter(is_paid=True).aggregate(
            total=Sum('total_amount')
        )['total'] or 0.00
        
        pending_payments = PaymentPeriod.objects.filter(is_paid=False).count()
        
        context = {
            'user_log': user_obj,
            'recent_payments': recent_payments,
            'employees_with_templates': employees_with_templates,
            'total_paid': total_paid,
            'pending_payments': pending_payments,
        }
        return render(request, 'hrm/payment_dashboard.html', context)


def get_payment_periods_list(request):
    """Lista de períodos de pago"""
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = CustomUser.objects.get(id=int(user_id))
        
        # Filtros
        employee_filter = request.GET.get('employee', '')
        status_filter = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        payment_periods = PaymentPeriod.objects.select_related('employee').all()
        
        # Aplicar filtros
        if employee_filter:
            payment_periods = payment_periods.filter(employee_id=employee_filter)
        if status_filter:
            if status_filter == 'paid':
                payment_periods = payment_periods.filter(is_paid=True)
            elif status_filter == 'pending':
                payment_periods = payment_periods.filter(is_paid=False)
        if date_from:
            payment_periods = payment_periods.filter(start_date__gte=date_from)
        if date_to:
            payment_periods = payment_periods.filter(end_date__lte=date_to)
        
        payment_periods = payment_periods.order_by('-start_date')
        
        # Paginación
        paginator = Paginator(payment_periods, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'hrm/payment_periods_list.html', {
            'user_log': user_obj,
            'page_obj': page_obj,
            'employees': CustomUser.objects.filter(is_superuser=False, is_active=True).order_by('first_name'),
        })



def modal_payment_period_create(request):
    """Modal para crear nuevo período de pago"""
    if request.method == 'GET':
        # Obtener fecha actual
        current_date = datetime.now()
        
        # Calcular lunes de la semana actual
        days_since_monday = current_date.weekday()
        monday_date = current_date - timedelta(days=days_since_monday)
        saturday_date = monday_date + timedelta(days=5)
        
        # Obtener empleados con plantillas activas
        employees = PaymentTemplate.objects.filter(
            is_active=True
        ).select_related('employee').order_by('employee__first_name')
        
        t = loader.get_template('hrm/payment_period_create.html')
        c = {
            'monday_date': monday_date.strftime('%Y-%m-%d'),
            'saturday_date': saturday_date.strftime('%Y-%m-%d'),
            'employees': employees,
        }
        return JsonResponse({
            'form': t.render(c, request),
        })


@csrf_exempt
def create_payment_period(request):
    """Crear nuevo período de pago con días automáticos"""
    if request.method == 'POST':
        try:
            employee_id = request.POST.get('employee', '')
            start_date_str = request.POST.get('start_date', '')
            end_date_str = request.POST.get('end_date', '')
            daily_rate = request.POST.get('daily_rate', '')
            notes = request.POST.get('notes', '')
            
            # Validaciones
            if not employee_id or not start_date_str or not end_date_str or not daily_rate:
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Convertir fechas
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Verificar que sea de lunes a sábado
            if start_date.weekday() != 0 or end_date.weekday() != 5:
                return JsonResponse({
                    'success': False,
                    'message': 'El período debe ser de lunes a sábado'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Verificar que no exista un período para el mismo empleado y fechas
            existing_period = PaymentPeriod.objects.filter(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date
            ).first()
            
            if existing_period:
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe un período de pago para estas fechas'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Crear período de pago
            payment_period = PaymentPeriod(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                notes=notes
            )
            payment_period.save()
            
            # Crear pagos diarios automáticamente
            current_date = start_date
            daily_rate_decimal = decimal.Decimal(daily_rate)
            
            while current_date <= end_date:
                day_names = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO']
                day_name = day_names[current_date.weekday()]
                
                daily_payment = DailyPayment(
                    payment_period=payment_period,
                    date=current_date,
                    day_of_week=day_name,
                    status='COMPLETO',
                    daily_rate=daily_rate_decimal
                )
                daily_payment.save()
                
                current_date += timedelta(days=1)
            
            return JsonResponse({
                'success': True,
                'message': 'Período de pago creado exitosamente',
                'period_id': payment_period.id
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear el período de pago: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def get_payment_period_detail(request, period_id):
    """Vista detallada de un período de pago"""
    if request.method == 'GET':
        try:
            payment_period = PaymentPeriod.objects.select_related('employee').get(id=period_id)
            daily_payments = payment_period.daily_payments.all().order_by('date')
            
            context = {
                'payment_period': payment_period,
                'daily_payments': daily_payments,
            }
            return render(request, 'hrm/payment_period_detail.html', context)
            
        except PaymentPeriod.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Período de pago no encontrado'
            }, status=HTTPStatus.NOT_FOUND)


@csrf_exempt
def update_daily_payment_status(request):
    """Actualizar estado de un pago diario"""
    if request.method == 'POST':
        try:
            daily_payment_id = request.POST.get('daily_payment_id', '')
            new_status = request.POST.get('status', '')
            notes = request.POST.get('notes', '')
            
            if not daily_payment_id or not new_status:
                return JsonResponse({
                    'success': False,
                    'message': 'ID del pago diario y estado son obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            daily_payment = DailyPayment.objects.get(id=daily_payment_id)
            daily_payment.status = new_status
            if notes:
                daily_payment.notes = notes
            daily_payment.save()
            
            # Recalcular total del período
            daily_payment.payment_period.calculate_total()
            daily_payment.payment_period.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Estado actualizado exitosamente',
                'new_amount': str(daily_payment.amount),
                'new_total': str(daily_payment.payment_period.total_amount)
            }, status=HTTPStatus.OK)
            
        except DailyPayment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Pago diario no encontrado'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@csrf_exempt
def mark_payment_as_paid(request):
    """Marcar período de pago como pagado"""
    if request.method == 'POST':
        try:
            period_id = request.POST.get('period_id', '')
            payment_date_str = request.POST.get('payment_date', '')
            
            if not period_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID del período es obligatorio'
                }, status=HTTPStatus.BAD_REQUEST)
            
            payment_period = PaymentPeriod.objects.get(id=period_id)
            payment_period.is_paid = True
            
            if payment_date_str:
                payment_period.payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            else:
                payment_period.payment_date = datetime.now().date()
            
            payment_period.save()
            
            # Crear registro en CashFlow para el pago del período
            try:
                # Formatear fechas para la descripción
                start_date_formatted = payment_period.start_date.strftime('%d/%m/%Y')
                end_date_formatted = payment_period.end_date.strftime('%d/%m/%Y')
                employee_name = f"{payment_period.employee.first_name} {payment_period.employee.last_name}"
                
                # Crear descripción del pago
                description = f"PAGO SEMANA del {start_date_formatted} AL {end_date_formatted} DE {employee_name}"
                
                # Crear registro en CashFlow
                cash_flow = CashFlow(
                    transaction_date=datetime.now(),
                    created_at=datetime.now(),
                    description=description,
                    type='S',  # Salida
                    type_expense='F',  # Gasto fijo
                    document_type_attached='O',  # Otro
                    subtotal=0,
                    total=payment_period.total_amount,
                    igv=0,
                    user=request.user
                )
                cash_flow.save()
                
            except Exception as cash_flow_error:
                # Si falla la creación del CashFlow, solo log el error pero no falla la operación principal
                print(f"Error al crear CashFlow: {str(cash_flow_error)}")
            
            return JsonResponse({
                'success': True,
                'message': 'Pago marcado como realizado exitosamente'
            }, status=HTTPStatus.OK)
            
        except PaymentPeriod.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Período de pago no encontrado'
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al marcar como pagado: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def get_payment_templates_list(request):
    """Lista de plantillas de pago"""
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = CustomUser.objects.get(id=int(user_id))
        
        templates = PaymentTemplate.objects.select_related('employee').filter(
            is_active=True
        ).order_by('employee__first_name')
        
        context = {
            'user_log': user_obj,
            'templates': templates,
        }
        return render(request, 'hrm/payment_templates_list.html', context)


def modal_payment_template_create(request):
    """Modal para crear plantilla de pago"""
    if request.method == 'GET':
        employees = CustomUser.objects.filter(
            is_superuser=False,
            is_active=True
        ).exclude(
            payment_templates__is_active=True
        ).order_by('first_name')
        
        t = loader.get_template('hrm/payment_template_create.html')
        c = {
            'employees': employees,
            'current_date': datetime.now().strftime('%Y-%m-%d'),
        }
        return JsonResponse({
            'form': t.render(c, request),
        })


@csrf_exempt
def create_payment_template(request):
    """Crear nueva plantilla de pago"""
    if request.method == 'POST':
        try:
            employee_id = request.POST.get('employee', '')
            daily_rate = request.POST.get('daily_rate', '')
            effective_date = request.POST.get('effective_date', '')
            notes = request.POST.get('notes', '')
            
            if not employee_id or not daily_rate or not effective_date:
                return JsonResponse({
                    'success': False,
                    'message': 'Empleado, tarifa diaria y fecha efectiva son obligatorios'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Desactivar plantillas anteriores del empleado
            PaymentTemplate.objects.filter(
                employee_id=employee_id,
                is_active=True
            ).update(is_active=False)
            
            # Crear nueva plantilla
            template = PaymentTemplate(
                employee_id=employee_id,
                daily_rate=daily_rate,
                effective_date=effective_date,
                notes=notes
            )
            template.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Plantilla de pago creada exitosamente'
            }, status=HTTPStatus.OK)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear la plantilla: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def get_payment_reports(request):
    """Reportes de pagos"""
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = CustomUser.objects.get(id=int(user_id))
        
        # Filtros para reportes
        employee_filter = request.GET.get('employee', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Obtener datos para reportes
        payments_query = PaymentPeriod.objects.select_related('employee').all()
        
        if employee_filter:
            payments_query = payments_query.filter(employee_id=employee_filter)
        if date_from:
            payments_query = payments_query.filter(start_date__gte=date_from)
        if date_to:
            payments_query = payments_query.filter(end_date__lte=date_to)
        
        # Estadísticas
        total_payments = payments_query.count()
        total_amount = payments_query.aggregate(total=Sum('total_amount'))['total'] or 0.00
        paid_amount = payments_query.filter(is_paid=True).aggregate(total=Sum('total_amount'))['total'] or 0.00
        pending_amount = payments_query.filter(is_paid=False).aggregate(total=Sum('total_amount'))['total'] or 0.00
        
        context = {
            'user_log': user_obj,
            'total_payments': total_payments,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount,
            'employees': CustomUser.objects.filter(is_superuser=False).order_by('first_name'),
        }
        return render(request, 'hrm/payment_reports.html', context)

