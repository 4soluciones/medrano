"""
Vistas para exportación de reportes a PDF
"""
import os
import decimal
from decimal import Decimal
from datetime import datetime

from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q
from http import HTTPStatus

from medrano import settings
from .models import CashFlow
from ..sales.models import Order
from ..hrm.models import Subsidiary


@csrf_exempt
def export_sales_report_pdf(request):
    """Exportar reporte de ventas a PDF"""
    if request.method == 'POST':
        try:
            # Obtener datos del reporte
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
                cashflows = CashFlow.objects.filter(
                    transaction_date=report_date
                )
            
            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary', 'order', 'order__client', 'order__subsidiary').prefetch_related('order__orderdetail_set')
            
            # Filtrar cashflows con order_id (ventas) y sin order_id (gastos)
            order_cashflows = cashflows.filter(order__isnull=False, order__status__in=['P', 'C'])
            
            # Obtener todas las órdenes del día del reporte
            orders_of_day = Order.objects.filter(
                register_date=report_date,
                status__in=['P', 'C']
            ).order_by('id')
            
            if subsidiary_id and subsidiary_id != '0':
                orders_of_day = orders_of_day.filter(subsidiary_id=subsidiary_id)
            
            orders_of_day = orders_of_day.select_related('client', 'subsidiary', 'user').prefetch_related('orderdetail_set')
            
            # Crear estructura de datos para adelantos (ingresos del día)
            advances_grouped = {}
            for order in orders_of_day:
                order_cashflows_day = cashflows.filter(
                    order=order,
                    type='E',
                    transaction_date=report_date
                ).order_by('id')
                
                if order_cashflows_day.exists():
                    total_paid = sum(decimal.Decimal(cf.total) for cf in order_cashflows_day)
                    saldo = decimal.Decimal(order.total) - total_paid
                    is_paid_in_full = abs(saldo) < 0.01
                    
                    advances_grouped[order.id] = {
                        'order': order,
                        'cashflows': list(order_cashflows_day),
                        'total_advances': total_paid,
                        'saldo': saldo,
                        'is_paid_in_full': is_paid_in_full,
                        'cashflow_count': order_cashflows_day.count()
                    }
            
            # Preparar datos de saldos (cancelaciones)
            payments_cashflows = order_cashflows.filter(
                type='E',
                order_type_entry='T'
            ).exclude(
                order__register_date__gte=report_date
            )
            
            # Preparar datos de egresos
            expenses_cashflows = cashflows.filter(
                order__isnull=True,
                type='S'
            )
            
            # Calcular totales
            total_advances = sum(data['total_advances'] for data in advances_grouped.values())
            total_payments = payments_cashflows.aggregate(total=Sum('total'))['total'] or 0
            total_expenses_amount = expenses_cashflows.aggregate(total=Sum('total'))['total'] or 0
            
            # Calcular totales por tipo de pago
            advances_efectivo = 0
            advances_yape = 0
            
            for data in advances_grouped.values():
                for cashflow in data['cashflows']:
                    if cashflow.way_to_pay == 'E':
                        advances_efectivo += decimal.Decimal(cashflow.total)
                    elif cashflow.way_to_pay == 'Y':
                        advances_yape += decimal.Decimal(cashflow.total)
            
            payments_efectivo = payments_cashflows.filter(way_to_pay='E').aggregate(total=Sum('total'))['total'] or 0
            payments_yape = payments_cashflows.filter(way_to_pay='Y').aggregate(total=Sum('total'))['total'] or 0
            
            total_efectivo = advances_efectivo + payments_efectivo
            total_yape = advances_yape + payments_yape
            total_general = total_efectivo + total_yape
            
            # Crear archivo PDF
            filename = f"reporte_ventas_gastos_{report_date}.pdf"
            filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            doc = SimpleDocTemplate(filepath, pagesize=landscape(letter), 
                                  leftMargin=0.5*inch, rightMargin=0.5*inch, 
                                  topMargin=0.5*inch, bottomMargin=0.5*inch)
            story = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,
                textColor=colors.HexColor('#007bff')
            )
            
            # Título
            subsidiary_name = subsidiary_obj.name.upper() if subsidiary_obj else 'TODAS'
            formatted_date = datetime.strptime(report_date, '%Y-%m-%d').strftime('%d-%m-%Y')
            story.append(Paragraph(f"TIENDA: {subsidiary_name} - DÍA: {formatted_date}", title_style))
            story.append(Spacer(1, 20))
            
            # Tabla de INGRESOS DEL DÍA
            income_data = [['N° CPTE.', 'CLIENTE', 'CANT.', 'DESCRIPCIÓN', 'USUARIO', 'TIPO PAGO', 'A CUENTA S/.', 'SALDO S/.', 'TOTAL S/.']]
            
            # Crear estilo para párrafos en celdas
            cell_style = ParagraphStyle(
                'CellStyle',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                alignment=1,  # Center alignment
                leftIndent=0,
                rightIndent=0
            )
            
            for order_id, data in advances_grouped.items():
                if not data['is_paid_in_full']:  # Solo adelantos
                    for i, cashflow in enumerate(data['cashflows']):
                        if i == 0:  # Primera fila con datos de la orden
                            product_desc = ""
                            if data['order'].orderdetail_set.exists():
                                product_desc = " | ".join([detail.product_name or "Producto Manual" for detail in data['order'].orderdetail_set.all()])
                            else:
                                product_desc = data['order'].observation or "ORDEN DE SERVICIO"
                            
                            payment_type = ""
                            if cashflow.way_to_pay == 'E':
                                payment_type = "EFECTIVO"
                            elif cashflow.way_to_pay == 'Y':
                                payment_type = "YAPE"
                            elif cashflow.way_to_pay == 'D':
                                payment_type = "DEPÓSITO"
                            
                            income_data.append([
                                f"{data['order'].subsidiary.serial}-{data['order'].correlative:03d}",
                                data['order'].client.full_name if data['order'].client else '-',
                                '1',
                                Paragraph(product_desc, cell_style),
                                cashflow.user.first_name or cashflow.user.username or '-',
                                payment_type,
                                f"S/. {decimal.Decimal(cashflow.total):.2f}",
                                f"S/. {Decimal(data['saldo']):.2f}",
                                f"S/. {Decimal(data['order'].total):.2f}"
                            ])
                        else:
                            # Filas adicionales sin datos de orden
                            payment_type = ""
                            if cashflow.way_to_pay == 'E':
                                payment_type = "EFECTIVO"
                            elif cashflow.way_to_pay == 'Y':
                                payment_type = "YAPE"
                            elif cashflow.way_to_pay == 'D':
                                payment_type = "DEPÓSITO"
                            
                            income_data.append([
                                '',
                                '',
                                '',
                                '',
                                cashflow.user.first_name or cashflow.user.username or '-',
                                payment_type,
                                f"S/. {decimal.Decimal(cashflow.total):.2f}",
                                '',
                                ''
                            ])
                
                # Pagos completos
                if data['is_paid_in_full']:
                    for i, cashflow in enumerate(data['cashflows']):
                        if i == 0:  # Primera fila con datos de la orden
                            product_desc = ""
                            if data['order'].orderdetail_set.exists():
                                product_desc = " | ".join([detail.product_name or "Producto Manual" for detail in data['order'].orderdetail_set.all()])
                            else:
                                product_desc = data['order'].observation or "ORDEN DE SERVICIO"
                            
                            payment_type = ""
                            if cashflow.way_to_pay == 'E':
                                payment_type = "EFECTIVO"
                            elif cashflow.way_to_pay == 'Y':
                                payment_type = "YAPE"
                            elif cashflow.way_to_pay == 'D':
                                payment_type = "DEPÓSITO"
                            
                            income_data.append([
                                f"{data['order'].subsidiary.serial}-{data['order'].correlative:03d}",
                                data['order'].client.full_name if data['order'].client else '-',
                                '1',
                                Paragraph(product_desc, cell_style),
                                cashflow.user.first_name or cashflow.user.username or '-',
                                payment_type,
                                f"S/. {decimal.Decimal(cashflow.total):.2f}",
                                "PAGADO",
                                f"S/. {Decimal(data['order'].total):.2f}"
                            ])
                        else:
                            payment_type = ""
                            if cashflow.way_to_pay == 'E':
                                payment_type = "EFECTIVO"
                            elif cashflow.way_to_pay == 'Y':
                                payment_type = "YAPE"
                            elif cashflow.way_to_pay == 'D':
                                payment_type = "DEPÓSITO"
                            
                            income_data.append([
                                '',
                                '',
                                '',
                                '',
                                cashflow.user.first_name or cashflow.user.username or '-',
                                payment_type,
                                f"S/. {decimal.Decimal(cashflow.total):.2f}",
                                '',
                                ''
                            ])
            
            # Agregar totales de ingresos
            income_data.append(['', '', '', '', '', 'YAPE:', '', '', f"S/. {decimal.Decimal(advances_yape):.2f}"])
            income_data.append(['', '', '', '', '', 'EFECTIVO:', '', '', f"S/. {decimal.Decimal(advances_efectivo):.2f}"])
            income_data.append(['', '', '', '', '', 'TOTAL INGRESOS:', '', '', f"S/. {decimal.Decimal(total_advances):.2f}"])
            
            income_table = Table(income_data, colWidths=[50, 120, 30, 180, 90, 70, 70, 70, 70])
            income_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, -3), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#adb5bd'))
            ]))
            
            story.append(Paragraph("INGRESOS DEL DÍA", styles['Heading2']))
            story.append(income_table)
            story.append(Spacer(1, 20))
            
            # Tabla de SALDOS
            saldos_data = [['N° COMPROBANTE', 'FECHA', 'DESCRIPCIÓN', 'USUARIO', 'TIPO PAGO', 'S/TOTAL']]
            
            for cashflow in payments_cashflows:
                payment_type = ""
                if cashflow.way_to_pay == 'E':
                    payment_type = "EFECTIVO"
                elif cashflow.way_to_pay == 'Y':
                    payment_type = "YAPE"
                elif cashflow.way_to_pay == 'D':
                    payment_type = "DEPÓSITO"
                
                saldos_data.append([
                    f"{cashflow.order.subsidiary.serial}-{cashflow.order.correlative:03d}",
                    cashflow.order.register_date.strftime('%d-%m-%Y'),
                    Paragraph(cashflow.description or "PAGO TOTAL", cell_style),
                    cashflow.user.first_name or cashflow.user.username or '-',
                    payment_type,
                    f"S/. {decimal.Decimal(cashflow.total):.2f}"
                ])
            
            # Agregar totales de saldos
            saldos_data.append(['', '', '', '', 'YAPE:', f"S/. {decimal.Decimal(payments_yape):.2f}"])
            saldos_data.append(['', '', '', '', 'EFECTIVO:', f"S/. {decimal.Decimal(payments_efectivo):.2f}"])
            saldos_data.append(['', '', '', '', 'TOTAL CANCELACIONES:', f"S/. {decimal.Decimal(total_payments):.2f}"])
            
            saldos_table = Table(saldos_data, colWidths=[120, 80, 200, 100, 80, 80])
            saldos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, -3), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#adb5bd'))
            ]))
            
            story.append(Paragraph("SALDOS", styles['Heading2']))
            story.append(saldos_table)
            story.append(Spacer(1, 20))
            
            # Tabla de EGRESOS
            egresos_data = [['NRO', 'DESCRIPCIÓN', 'TIPO EGRESO', 'USUARIO', 'MONTO']]
            
            for i, cashflow in enumerate(expenses_cashflows, 1):
                expense_type = ""
                if cashflow.type_expense == 'V':
                    expense_type = "VARIABLE"
                elif cashflow.type_expense == 'F':
                    expense_type = "FIJO"
                elif cashflow.type_expense == 'P':
                    expense_type = "PERSONAL"
                elif cashflow.type_expense == 'O':
                    expense_type = "OTRO"
                
                egresos_data.append([
                    str(i),
                    Paragraph(cashflow.description or '-', cell_style),
                    expense_type,
                    cashflow.user.first_name or cashflow.user.username or '-',
                    f"S/. {decimal.Decimal(cashflow.total):.2f}"
                ])
            
            # Agregar total de egresos
            egresos_data.append(['', '', '', 'TOTAL EGRESOS:', f"S/. {decimal.Decimal(total_expenses_amount):.2f}"])
            
            egresos_table = Table(egresos_data, colWidths=[50, 250, 100, 100, 80])
            egresos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#adb5bd'))
            ]))
            
            story.append(Paragraph("EGRESOS", styles['Heading2']))
            story.append(egresos_table)
            story.append(Spacer(1, 20))
            
            # Resumen final
            summary_data = [
                ['RESUMENES'],
                ['INGRESOS', ''],
                ['INGRESOS DEL DÍA:', f"S/. {decimal.Decimal(total_advances):.2f}"],
                ['SALDOS:', f"S/. {decimal.Decimal(total_payments):.2f}"],
                ['SUBTOTAL INGRESOS:', f"S/. {decimal.Decimal(total_advances + total_payments):.2f}"],
                ['', ''],
                ['EGRESOS', ''],
                ['TOTAL EGRESOS:', f"S/. {decimal.Decimal(total_expenses_amount):.2f}"],
                ['', ''],
                ['TOTAL EFECTIVO:', f"S/. {decimal.Decimal(total_efectivo):.2f}"],
                ['TOTAL YAPE:', f"S/. {decimal.Decimal(total_yape):.2f}"],
                ['TOTAL EGRESOS:', f"S/. {decimal.Decimal(total_expenses_amount):.2f}"],
                ['TOTAL FINAL:', f"S/. {decimal.Decimal(total_general - total_expenses_amount):.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[120, 80])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.whitesmoke),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 6), (-1, 6), colors.whitesmoke),
                ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ffc107')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#adb5bd'))
            ]))
            
            story.append(Paragraph("RESUMENES", styles['Heading2']))
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


@csrf_exempt
def export_sales_report_by_user_pdf(request):
    """Exportar reporte de ventas por usuario a PDF"""
    if request.method == 'POST':
        try:
            # Obtener datos del reporte
            report_date = request.POST.get('report_date')
            user_id = request.POST.get('user')
            user_obj = None
            
            if not report_date:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar una fecha'
                }, status=HTTPStatus.BAD_REQUEST)
            
            # Filtrar cashflows del día por usuario
            if user_id and user_id != '0':
                from apps.users.models import CustomUser
                user_obj = CustomUser.objects.get(id=int(user_id))
                cashflows = CashFlow.objects.filter(
                    transaction_date=report_date,
                    user_id=user_id
                )
            else:
                cashflows = CashFlow.objects.filter(
                    transaction_date=report_date
                )
            
            cashflows = cashflows.select_related('cash', 'user', 'cash__subsidiary', 'order', 'order__client', 'order__subsidiary').prefetch_related('order__orderdetail_set')
            
            # Filtrar cashflows con order_id (ventas) y sin order_id (gastos)
            order_cashflows = cashflows.filter(order__isnull=False, order__status__in=['P', 'C'])
            
            # Obtener todas las órdenes del día del reporte
            orders_of_day = Order.objects.filter(
                register_date=report_date,
                status__in=['P', 'C']
            ).order_by('id')
            
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
            
            # Crear estructura de datos para adelantos (ingresos del día)
            advances_grouped = {}
            for order in orders_of_day:
                order_cashflows_day = cashflows.filter(
                    order=order,
                    type='E',
                    transaction_date=report_date
                ).order_by('id')
                
                if order_cashflows_day.exists():
                    total_paid = sum(decimal.Decimal(cf.total) for cf in order_cashflows_day)
                    saldo = decimal.Decimal(order.total) - total_paid
                    is_paid_in_full = abs(saldo) < 0.01
                    
                    advances_grouped[order.id] = {
                        'order': order,
                        'cashflows': list(order_cashflows_day),
                        'total_advances': total_paid,
                        'saldo': saldo,
                        'is_paid_in_full': is_paid_in_full,
                        'cashflow_count': order_cashflows_day.count()
                    }
            
            # Preparar datos de saldos (cancelaciones)
            payments_cashflows = order_cashflows.filter(
                type='E',
                order_type_entry='T'
            ).exclude(
                order__register_date__gte=report_date
            )
            
            # Preparar datos de egresos
            expenses_cashflows = cashflows.filter(
                order__isnull=True,
                type='S'
            )
            
            # Calcular totales
            total_advances = sum(data['total_advances'] for data in advances_grouped.values())
            total_payments = payments_cashflows.aggregate(total=Sum('total'))['total'] or 0
            total_expenses_amount = expenses_cashflows.aggregate(total=Sum('total'))['total'] or 0
            
            # Calcular totales por tipo de pago para adelantos (ingresos del día)
            advances_efectivo = 0
            advances_yape = 0
            advances_deposito = 0
            
            for data in advances_grouped.values():
                for cashflow in data['cashflows']:
                    if cashflow.way_to_pay == 'E':
                        advances_efectivo += decimal.Decimal(cashflow.total)
                    elif cashflow.way_to_pay == 'Y':
                        advances_yape += decimal.Decimal(cashflow.total)
                    elif cashflow.way_to_pay == 'D':
                        advances_deposito += decimal.Decimal(cashflow.total)
            
            # Crear PDF
            filename = f"reporte_ventas_usuario_{report_date}.pdf"
            file_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Centrado
            )
            
            user_name = f"{user_obj.first_name} {user_obj.last_name}".strip() if user_obj else "TODOS"
            title = Paragraph(f"USUARIO: {user_name.upper()} - DÍA: {datetime.strptime(report_date, '%Y-%m-%d').strftime('%d-%m-%Y')}", title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Sección de INGRESOS DEL DÍA
            story.append(Paragraph("INGRESOS DEL DÍA", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Crear tabla de ingresos
            income_data = [['N° CPTE.', 'CLIENTE', 'CANT.', 'DESCRIPCIÓN', 'USUARIO', 'TIPO PAGO', 'A CUENTA S/.', 'SALDO S/.', 'TOTAL S/.']]
            
            for order_id, data in advances_grouped.items():
                if not data['is_paid_in_full']:  # Solo adelantos
                    for i, cashflow in enumerate(data['cashflows']):
                        row_data = []
                        if i == 0:  # Primera fila con datos de la orden
                            row_data = [
                                f"{data['order'].subsidiary.serial}-{data['order'].correlative:03d}",
                                data['order'].client.full_name if data['order'].client else '-',
                                '1',
                                data['order'].observation or "ORDEN DE SERVICIO",
                                cashflow.user.first_name or cashflow.user.username or '-',
                                'EFECTIVO' if cashflow.way_to_pay == 'E' else 'YAPE' if cashflow.way_to_pay == 'Y' else 'DEPÓSITO',
                                f"S/ {Decimal(cashflow.total):.2f}",
                                f"S/ {Decimal(data['saldo']):.2f}",
                                f"S/ {Decimal(data['order'].total):.2f}"
                            ]
                        else:
                            row_data = ['', '', '', '', cashflow.user.first_name or cashflow.user.username or '-', 
                                      'EFECTIVO' if cashflow.way_to_pay == 'E' else 'YAPE' if cashflow.way_to_pay == 'Y' else 'DEPÓSITO',
                                      f"S/ {Decimal(cashflow.total):.2f}", '', '']
                        income_data.append(row_data)
                
                # Pagos completos
                if data['is_paid_in_full']:
                    for i, cashflow in enumerate(data['cashflows']):
                        row_data = []
                        if i == 0:  # Primera fila con datos de la orden
                            row_data = [
                                f"{data['order'].subsidiary.serial}-{data['order'].correlative:03d}",
                                data['order'].client.full_name if data['order'].client else '-',
                                '1',
                                data['order'].observation or "ORDEN DE SERVICIO",
                                cashflow.user.first_name or cashflow.user.username or '-',
                                'EFECTIVO' if cashflow.way_to_pay == 'E' else 'YAPE' if cashflow.way_to_pay == 'Y' else 'DEPÓSITO',
                                f"S/ {Decimal(cashflow.total):.2f}",
                                "PAGADO",
                                f"S/ {data['order'].total}"
                            ]
                        else:
                            row_data = ['', '', '', '', cashflow.user.first_name or cashflow.user.username or '-', 
                                      'EFECTIVO' if cashflow.way_to_pay == 'E' else 'YAPE' if cashflow.way_to_pay == 'Y' else 'DEPÓSITO',
                                      f"S/ {Decimal(cashflow.total):.2f}", '', '']
                        income_data.append(row_data)
            
            # Agregar totales
            income_data.append(['', '', '', '', '', '', '', 'YAPE:', f"S/ {Decimal(advances_yape):.2f}"])
            income_data.append(['', '', '', '', '', '', '', 'EFECTIVO:', f"S/ {Decimal(advances_efectivo):.2f}"])
            income_data.append(['', '', '', '', '', '', '', 'TOTAL INGRESOS:', f"S/ {Decimal(total_advances):.2f}"])
            
            # Crear tabla
            income_table = Table(income_data)
            income_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
            ]))
            
            story.append(income_table)
            story.append(Spacer(1, 20))
            
            # Sección de SALDOS (solo si hay datos)
            if payments_cashflows.exists():
                story.append(Paragraph("SALDOS", styles['Heading2']))
                story.append(Spacer(1, 12))
                
                # Crear tabla de saldos
                payments_data = [['N° COMPROBANTE', 'FECHA', 'DESCRIPCIÓN', 'USUARIO', 'TIPO PAGO', 'S/TOTAL']]
                
                for cashflow in payments_cashflows:
                    payments_data.append([
                        f"{cashflow.order.subsidiary.serial}-{cashflow.order.correlative:03d}",
                        cashflow.order.register_date.strftime('%d-%m-%Y'),
                        cashflow.description or "PAGO TOTAL",
                        cashflow.user.first_name or cashflow.user.username or '-',
                        'EFECTIVO' if cashflow.way_to_pay == 'E' else 'YAPE' if cashflow.way_to_pay == 'Y' else 'DEPÓSITO',
                        f"S/ {Decimal(cashflow.total):.2f}"
                    ])
                
                # Agregar totales de saldos
                payments_efectivo_section = payments_cashflows.filter(way_to_pay='E').aggregate(total=Sum('total'))['total'] or 0
                payments_yape_section = payments_cashflows.filter(way_to_pay='Y').aggregate(total=Sum('total'))['total'] or 0
                
                payments_data.append(['', '', '', '', 'YAPE:', f"S/ {Decimal(payments_yape_section):.2f}"])
                payments_data.append(['', '', '', '', 'EFECTIVO:', f"S/ {Decimal(payments_efectivo_section):.2f}"])
                payments_data.append(['', '', '', '', 'TOTAL CANCELACIONES:', f"S/ {Decimal(total_payments):.2f}"])
                
                # Crear tabla de saldos
                payments_table = Table(payments_data)
                payments_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                ]))
                
                story.append(payments_table)
                story.append(Spacer(1, 20))
            
            # Sección de EGRESOS (solo si hay datos)
            if expenses_cashflows.exists():
                story.append(Paragraph("EGRESOS", styles['Heading2']))
                story.append(Spacer(1, 12))
                
                # Crear tabla de egresos
                expenses_data = [['NRO', 'DESCRIPCIÓN', 'TIPO EGRESO', 'USUARIO', 'MONTO']]
                
                for i, cashflow in enumerate(expenses_cashflows, 1):
                    expense_type = 'VARIABLE' if cashflow.type_expense == 'V' else 'FIJO' if cashflow.type_expense == 'F' else 'PERSONAL' if cashflow.type_expense == 'P' else 'OTRO'
                    
                    expenses_data.append([
                        str(i),
                        cashflow.description or '-',
                        expense_type,
                        cashflow.user.first_name or cashflow.user.username or '-',
                        f"S/ {Decimal(cashflow.total):.2f}"
                    ])
                
                # Agregar total de egresos
                expenses_data.append(['', '', '', 'TOTAL EGRESOS:', f"S/ {Decimal(total_expenses_amount):.2f}"])
                
                # Crear tabla de egresos
                expenses_table = Table(expenses_data)
                expenses_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                ]))
                
                story.append(expenses_table)
                story.append(Spacer(1, 20))
            
            # Sección de RESUMENES
            story.append(Paragraph("RESUMENES", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Calcular totales de pagos para resúmenes
            payments_efectivo_total = payments_cashflows.filter(way_to_pay='E').aggregate(total=Sum('total'))['total'] or 0
            payments_yape_total = payments_cashflows.filter(way_to_pay='Y').aggregate(total=Sum('total'))['total'] or 0
            
            # Crear tabla de resúmenes
            total_general = advances_efectivo + advances_yape + advances_deposito + payments_efectivo_total + payments_yape_total
            
            summary_data = [
                ['CONCEPTO', 'MONTO'],
                ['INGRESOS DEL DÍA:', f"S/ {Decimal(total_advances):.2f}"],
                ['SALDOS:', f"S/ {Decimal(total_payments):.2f}"],
                ['SUBTOTAL INGRESOS:', f"S/ {float(total_advances + total_payments):.2f}"],
                ['TOTAL EGRESOS:', f"S/ {Decimal(total_expenses_amount):.2f}"],
                ['TOTAL EFECTIVO:', f"S/ {Decimal(advances_efectivo + payments_efectivo_total):.2f}"],
                ['TOTAL YAPE:', f"S/ {Decimal(advances_yape + payments_yape_total):.2f}"],
                ['TOTAL FINAL:', f"S/ {Decimal(total_general - total_expenses_amount):.2f}"]
            ]
            
            # Crear tabla de resúmenes
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),  # Hacer toda la tabla en negrita
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Construir PDF
            doc.build(story)
            
            # URL del archivo
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
