from django.urls import path, include
from django.contrib.auth.decorators import login_required
# from apps.user.views import users_list, UserList, user_create, user_update, user_save
from .views import *
from .views_PDF import download_ticket_pdf

urlpatterns = [
    # URLs existentes para clientes
    path('client_list/', login_required(get_client_list), name='get_client_list'),
    path('get_api_person/', login_required(get_api_person), name='get_api_person'),
    path('modal_client_create/', login_required(modal_client_create), name='modal_client_create'),
    path('save_client/', login_required(save_client), name='save_client'),
    path('modal_client_update/', login_required(modal_client_update), name='modal_client_update'),
    path('update_client/', login_required(update_client), name='update_client'),

    # URLs existentes para órdenes (legacy)
    path('order_client/', login_required(order_client), name='order_client'),
    path('get_order_by_client/', login_required(get_order_by_client), name='get_order_by_client'),
    path('get_correlative_order/', login_required(get_correlative_order), name='get_correlative_order'),

    # URLs para el módulo de productos
    path('product_list/', login_required(get_product_list), name='get_product_list'),
    path('modal_product_create/', login_required(modal_product_create), name='modal_product_create'),
    path('save_product/', login_required(save_product), name='save_product'),
    path('modal_product_update/', login_required(modal_product_update), name='modal_product_update'),
    path('update_product/', login_required(update_product), name='update_product'),
    path('modal_category_create/', login_required(modal_category_create), name='modal_category_create'),
    path('save_category/', login_required(save_category), name='save_category'),
    path('modal_unit_create/', login_required(modal_unit_create), name='modal_unit_create'),
    path('save_unit/', login_required(save_unit), name='save_unit'),
    path('get_product_data/', login_required(get_product_data), name='get_product_data'),

    # =============================================================================
    # NUEVAS URLs PARA EL SISTEMA DE ÓRDENES MODERNO
    # =============================================================================
    path('orders/', login_required(order_list), name='order_list'),
    path('orders/save/', login_required(order_save), name='order_save'),
    path('orders/update/', login_required(order_update), name='order_update'),
    path('orders/detail/', login_required(order_detail_modal), name='order_detail_modal'),
    path('orders/correlative/', login_required(get_correlative_order), name='get_correlative_order'),
    path('orders/serial/', login_required(get_serial_order), name='get_serial_order'),
    path('orders/products/', login_required(get_products_for_order), name='get_products_for_order'),
    path('orders/get-for-edit/', login_required(get_order_for_edit), name='get_order_for_edit'),
    path('orders/status-modal/', login_required(order_status_modal), name='order_status_modal'),
    path('orders/update-status/', login_required(update_order_status), name='update_order_status'),
    path('orders/update-delivery-status/', login_required(update_order_delivery_status), name='update_order_delivery_status'),
    path('orders/get-for-conversion/', login_required(get_order_for_conversion), name='get_order_for_conversion'),
    path('orders/convert-to-service/', login_required(convert_order_to_service), name='convert_order_to_service'),
    path('clients/create/', login_required(create_client), name='create_client'),
    path('clients/search-autocomplete/', login_required(search_clients_autocomplete), name='search_clients_autocomplete'),
    # path('order_delivery_status_modal', login_required(order_delivery_status_modal), name='order_delivery_status_modal'),

    # =============================================================================
    # URLs PARA MANEJO DE ESTADOS DE ÓRDENES CON CASHFLOW
    # =============================================================================
    path('orders/get-for-completion/', login_required(get_order_for_completion), name='get_order_for_completion'),
    path('orders/get-for-cancellation/', login_required(get_order_for_cancellation), name='get_order_for_cancellation'),
    path('orders/complete-with-payment/', login_required(complete_order_with_payment), name='complete_order_with_payment'),
    path('orders/cancel-with-reason/', login_required(cancel_order_with_reason), name='cancel_order_with_reason'),

    # =============================================================================
    # URLs PARA PDFs
    # =============================================================================
    path('orders/<int:order_id>/ticket-pdf/', login_required(download_ticket_pdf), name='download_ticket_pdf'),

    # =============================================================================
    # URLs DEL DASHBOARD
    # =============================================================================
    path('dashboard/stats/', login_required(dashboard_stats), name='dashboard_stats'),
    path('dashboard/recent-orders/', login_required(recent_orders), name='recent_orders'),
    path('dashboard/monthly-chart/', login_required(monthly_orders_chart), name='monthly_orders_chart'),
    path('dashboard/weekly-chart/', login_required(weekly_orders_chart), name='weekly_orders_chart'),
]