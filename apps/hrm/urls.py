from django.urls import path, include
from django.contrib.auth.decorators import login_required
# from apps.user.views import users_list, UserList, user_create, user_update, user_save
from .views import *

urlpatterns = [
    path('subsidiary/', login_required(get_subsidiary_list), name='subsidiary'),
    path('modal_subsidiary_create/', login_required(modal_subsidiary_create), name='modal_subsidiary_create'),
    path('create_subsidiary/', login_required(create_subsidiary), name='create_subsidiary'),
    path('modal_subsidiary_update/', login_required(modal_subsidiary_update), name='modal_subsidiary_update'),
    path('update_subsidiary/', login_required(update_subsidiary), name='update_subsidiary'),

    path('employee/', login_required(get_employee_list), name='employee'),
    path('modal_user_create/', login_required(modal_user_create), name='modal_user_create'),
    path('create_user/', login_required(create_user), name='create_user'),
    path('modal_user_update/', login_required(modal_user_update), name='modal_user_update'),
    path('update_user/', login_required(update_user), name='update_user'),

    # ============================================================================
    # URLs PARA EL SISTEMA DE PAGOS
    # ============================================================================
    path('payments/', login_required(get_payment_dashboard), name='payment_dashboard'),
    path('payments/periods/', login_required(get_payment_periods_list), name='payment_periods_list'),
    path('payments/periods/create/', login_required(modal_payment_period_create), name='modal_payment_period_create'),
    path('payments/periods/save/', login_required(create_payment_period), name='create_payment_period'),
    path('payments/periods/<int:period_id>/', login_required(get_payment_period_detail), name='payment_period_detail'),
    path('payments/daily/update-status/', login_required(update_daily_payment_status), name='update_daily_payment_status'),
    path('payments/periods/mark-paid/', login_required(mark_payment_as_paid), name='mark_payment_as_paid'),
    
    path('payments/templates/', login_required(get_payment_templates_list), name='payment_templates_list'),
    path('payments/templates/create/', login_required(modal_payment_template_create), name='modal_payment_template_create'),
    path('payments/templates/save/', login_required(create_payment_template), name='create_payment_template'),
    
    path('payments/reports/', login_required(get_payment_reports), name='payment_reports'),
]