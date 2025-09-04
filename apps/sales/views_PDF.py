from django.db.models import Prefetch, Q
from reportlab.lib.pagesizes import letter, landscape, A4, A5, C7
import io
import pdfkit
import decimal
import reportlab
from django.contrib.auth.models import User
from django.http import HttpResponse
from reportlab.lib.colors import black, blue, red, Color
from reportlab.lib.pagesizes import landscape, A5, portrait, letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle, Spacer, Image, Flowable
from reportlab.platypus import Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.rl_settings import defaultPageSize
from medrano import settings
import io
from django.conf import settings
import datetime
from datetime import datetime
import requests

from ..users.models import CustomUser

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, leading=8, fontName='Square', fontSize=14))
styles.add(ParagraphStyle(name='Center-Blue', alignment=TA_CENTER, leading=8, fontName='Square-Bold', fontSize=14,
                          textColor=colors.cornflowerblue))
styles.add(ParagraphStyle(name='Center_White', alignment=TA_CENTER, leading=8, fontName='Square', fontSize=14,
                          textColor=colors.white))
styles.add(ParagraphStyle(name='Left_Square', alignment=TA_LEFT, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='Left_Newgot', alignment=TA_LEFT, leading=12, fontName='Newgot', fontSize=10))
styles.add(ParagraphStyle(name='Center_Newgot', alignment=TA_CENTER, leading=12, fontName='Newgot', fontSize=10))
styles.add(
    ParagraphStyle(name='Justify_Newgot_title', alignment=TA_JUSTIFY, leading=14, fontName='Newgot', fontSize=14))
styles.add(
    ParagraphStyle(name='Justify_Newgot_text', alignment=TA_JUSTIFY, leading=10, fontName='Newgot', fontSize=12))
styles.add(
    ParagraphStyle(name='Justify_Newgot_text_red', alignment=TA_CENTER, leading=14, fontName='Newgot', fontSize=14,
                   textColor=colors.darkred))
styles.add(ParagraphStyle(name='Center_Newgot_title', alignment=TA_CENTER, leading=15, fontName='Newgot', fontSize=15))
styles.add(ParagraphStyle(name='Center_Newgot_title_blue', alignment=TA_CENTER, leading=15, fontName='Newgot',
                          fontSize=15, textColor=colors.dodgerblue))
styles.add(
    ParagraphStyle(name='Center_Newgot_title_f12', alignment=TA_CENTER, leading=15, fontName='Newgot', fontSize=12))
styles.add(
    ParagraphStyle(name='Center_Newgot_sub_title', alignment=TA_CENTER, leading=10, fontName='Newgot', fontSize=10,
                   textColor=colors.lightslategrey))
styles.add(
    ParagraphStyle(name='Center_Newgot_sub_title_2', alignment=TA_CENTER, leading=10, fontName='Newgot', fontSize=8))
styles.add(
    ParagraphStyle(name='Center_Newgot_sub_title_3', alignment=TA_CENTER, leading=10, fontName='Newgot', fontSize=10))
styles.add(ParagraphStyle(name='Justify_Square', alignment=TA_JUSTIFY, leading=12, fontName='Square', fontSize=11))
styles.add(ParagraphStyle(name='Justify_Square_Blue', alignment=TA_JUSTIFY, leading=10, fontName='Square', fontSize=10,
                          textColor=colors.dodgerblue))
styles.add(
    ParagraphStyle(name='Justify_Square_bold', alignment=TA_JUSTIFY, leading=10, fontName='Square-Bold', fontSize=10))

reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + '/static/fonts')
pdfmetrics.registerFont(TTFont('Square', 'square-721-condensed-bt.ttf'))
pdfmetrics.registerFont(TTFont('Square-Bold', 'sqr721bc.ttf'))
pdfmetrics.registerFont(TTFont('Newgot', 'newgotbc.ttf'))

logo = "static/assets/img/log_medrano_no_bg.png"

I = Image(logo)
I.drawHeight = 3.10 * inch / 2.9
I.drawWidth = 6.1 * inch / 2.9

_a4 = (8.3 * inch, 11.7 * inch)
ml = 0.25 * inch
mr = 0.25 * inch
ms = 0.25 * inch
mi = 0.25 * inch


def generate_ticket_pdf(order_id):
    try:
        from .models import Order, OrderDetail
        from ..hrm.models import Subsidiary
        from ..users.models import CustomUser
        
        # Obtener la orden y sus detalles
        order = Order.objects.select_related('client', 'subsidiary', 'user').get(id=order_id)
        order_details = OrderDetail.objects.filter(order=order)
        
        # Obtener todas las sucursales para mostrar sus direcciones
        all_subsidiaries = Subsidiary.objects.all()
        
        # Crear el buffer para el PDF
        buffer = io.BytesIO()
        
        # Configurar el documento con el ancho especificado para tickets
        details = order.orderdetail_set.all()
        _counter = details.count()
        _wt = 2.94 * inch - 4 * 0.05 * inch
        
        # Calcular altura adicional para las direcciones de sucursales
        subsidiaries_with_address = all_subsidiaries.filter(address__isnull=False).exclude(address='').count()
        additional_height = subsidiaries_with_address * 0.2 * inch  # Espacio adicional por sucursal
        
        # pz_thermal = (3.14961 * inch, (11.6 * inch + (_counter * 0.13 * inch)))
        pz_thermal = (2.94 * inch, (11.6 * inch + (_counter * 0.13 * inch) + additional_height))

        ml = 0.05 * inch
        mr = 0.05 * inch
        ms = 0.039 * inch
        mi = 0.039 * inch

        doc = SimpleDocTemplate(
            buffer,
            pagesize=pz_thermal,
            rightMargin=mr,
            leftMargin=ml,
            topMargin=ms,
            bottomMargin=mi,
            title='TICKET'
        )
        
        # Lista de elementos del PDF
        elements = []
        
        # Estilos para el ticket con espaciado reducido
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Helvetica_Bold_Center_10',
            alignment=TA_CENTER,
            leading=11,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=10
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Bold_Center_8',
            alignment=TA_CENTER,
            leading=8,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=7
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Bold_Center_6',
            alignment=TA_CENTER,
            leading=7,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=6
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Bold_Justify_6',
            alignment=TA_JUSTIFY,
            leading=7,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=6
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Bold_Right_6',
            alignment=TA_RIGHT,
            leading=7,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=6
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Bold_Left_8',
            alignment=TA_LEFT,
            leading=9,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=8
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Bold_Left_6',
            alignment=TA_LEFT,
            leading=7,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=6
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Right_6',
            alignment=TA_RIGHT,
            leading=7,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=6
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Left_8',
            alignment=TA_LEFT,
            leading=9,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=8
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Left_7',
            alignment=TA_LEFT,
            leading=8,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=7
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Center_7',
            alignment=TA_CENTER,
            leading=8,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=7
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Left_6',
            alignment=TA_LEFT,
            leading=7,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=6
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Left_5',
            alignment=TA_LEFT,
            leading=6,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=5
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Center_5',
            alignment=TA_CENTER,
            leading=6,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=5
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Right_8',
            alignment=TA_RIGHT,
            leading=9,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=8
        ))
        styles.add(ParagraphStyle(
            name='Helvetica_Bold_Right_8',
            alignment=TA_RIGHT,
            leading=9,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=8
        ))
        styles.add(ParagraphStyle(
            name='TicketTitle',
            alignment=TA_CENTER,
            leading=11,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=10
        ))
        styles.add(ParagraphStyle(
            name='TicketSubtitle',
            alignment=TA_CENTER,
            leading=8,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=9
        ))
        styles.add(ParagraphStyle(
            name='TicketHeader',
            alignment=TA_CENTER,
            leading=12,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=12
        ))
        styles.add(ParagraphStyle(
            name='TicketText',
            alignment=TA_LEFT,
            leading=8,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=8
        ))
        styles.add(ParagraphStyle(
            name='TicketSeparatorLine',
            alignment=TA_LEFT,
            leading=8,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=8,
            textColor=colors.grey  # Color gris más tenue para las líneas separadoras
        ))
        styles.add(ParagraphStyle(
            name='TicketTextBold',
            alignment=TA_LEFT,
            leading=8,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=8
        ))
        styles.add(ParagraphStyle(
            name='TicketTextRight',
            alignment=TA_RIGHT,
            leading=8,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=8
        ))
        styles.add(ParagraphStyle(
            name='TicketTextRightBold',
            alignment=TA_RIGHT,
            leading=8,  # Espaciado reducido
            fontName='Helvetica-Bold',
            fontSize=8
        ))
        styles.add(ParagraphStyle(
            name='TicketSubtitleSmall',
            alignment=TA_CENTER,
            leading=7,  # Espaciado reducido
            fontName='Helvetica',
            fontSize=7
        ))
        
        # Encabezado del ticket
        # Logo en la parte superior - usar logo de la sucursal
        try:
            if order.subsidiary and order.subsidiary.photo:
                logo_path = order.subsidiary.photo.path
            else:
                logo_path = "static/assets/img/log_medrano_no_bg.png"
            logo_img = Image(logo_path)
            logo_img.drawHeight = 1.2 * inch
            logo_img.drawWidth = 1.4 * inch
            elements.append(logo_img)
            elements.append(Spacer(3, 3))
        except:
            # Si no se puede cargar la imagen, mostrar texto
            elements.append(Paragraph("LOGO", styles['TicketHeader']))
            elements.append(Spacer(3, 3))
        
        # Nombre de la empresa
        # if order.subsidiary and order.subsidiary.business_name:
        #     elements.append(Paragraph(order.subsidiary.business_name.upper(), styles['Helvetica_Bold_Center_10']))
        # else:
        # elements.append(Paragraph("PUBLICIDAD BELYGRAF & MEDRANO", styles['Helvetica_Bold_Center_10']))
        # elements.append(Spacer(2, 2))

        elements.append(Paragraph("REALIZAMOS LOS SERVICIOS DE", styles['Helvetica_Bold_Center_6']))
        elements.append(Spacer(2, 2))

        elements.append(Paragraph("LETREROS 3D, LETREROS LUMINOSOS, LETREROS CON FORMA, CARPAS FIJAS, "
                                  "CARPAS ENRROLLABLES, LOGOTIPOS, MODULOS PVC, ROLL SCREEN, SEÑALETICAS,"
                                  " TARJETAS PERSONALES, VOLANTES, AFICHES, FORMATOS, OTROS", styles['Helvetica_Center_5']))
        elements.append(Spacer(2, 2))

        elements.append(Paragraph(order.subsidiary.address.upper(), styles['Helvetica_Center_5']))
        # for index, subsidiary in enumerate(all_subsidiaries):
        #     if subsidiary.address and subsidiary.address.strip():
        #         # Crear tabla para mostrar icono + texto en la misma línea
        #         location_data = []
        #
        #         # Cargar el icono de ubicación
        #         try:
        #             location_icon = Image("media/image_location.png")
        #             location_icon.drawHeight = 0.08 * inch  # Icono más pequeño
        #             location_icon.drawWidth = 0.08 * inch   # Icono más pequeño
        #
        #             # Determinar el texto a mostrar
        #             if index == 0:  # Primera sucursal
        #                 text_to_show = f"PRINCIPAL: {subsidiary.address.upper()}"
        #             else:  # Demás sucursales
        #                 text_to_show = subsidiary.address.upper()
        #
        #             # Crear fila con icono y texto
        #             location_data.append([
        #                 location_icon,
        #                 Paragraph(text_to_show, styles['Helvetica_Left_5'])
        #             ])
        #
        #             # Crear tabla para alinear icono y texto (más compacta)
        #             _wt2 = 1.84 * inch - 4 * 0.05 * inch
        #             location_table = Table(location_data, colWidths=[0.1 * inch, _wt2 - 0.1 * inch])
        #             location_table.setStyle(TableStyle([
        #                 ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        #                 ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        #                 ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        #                 ('LEFTPADDING', (0, 0), (0, 0), 0),      # Sin padding izquierdo en icono
        #                 ('RIGHTPADDING', (0, 0), (0, 0), 0),     # Sin padding derecho en icono
        #                 ('LEFTPADDING', (1, 0), (1, 0), 2),      # Pequeño padding izquierdo en texto
        #                 ('RIGHTPADDING', (1, 0), (1, 0), 0),     # Sin padding derecho en texto
        #                 ('TOPPADDING', (0, 0), (-1, 0), 0),
        #                 ('BOTTOMPADDING', (0, 0), (-1, 0), 1),
        #                 # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        #             ]))
        #
        #             elements.append(location_table)
        #             elements.append(Spacer(0.3, 0.3))
        #
        #         except Exception as e:
        #             # Si no se puede cargar la imagen, usar símbolo de texto como respaldo
        #             if index == 0:  # Primera sucursal
        #                 text_to_show = f"• PRINCIPAL: {subsidiary.address.upper()}"
        #             else:  # Demás sucursales
        #                 text_to_show = f"• {subsidiary.address.upper()}"
        #
        #             elements.append(Paragraph(text_to_show, styles['Helvetica_Center_5']))
        #             elements.append(Spacer(0.5, 0.5))

        elements.append(Spacer(2, 2))

        # Teléfono de la sucursal (más pequeño)
        if order.subsidiary and order.subsidiary.phone:
            elements.append(Paragraph(f"CEL: {order.subsidiary.phone}", styles['Helvetica_Center_5']))
        elements.append(Spacer(2, 2))
        # RUC de la empresa (más pequeño)
        if order.subsidiary and order.subsidiary.ruc:
            elements.append(Paragraph(f"RUC {order.subsidiary.ruc}", styles['TicketSubtitleSmall']))
        elements.append(Spacer(1, 1))

        # Razón social (más pequeña)
        if order.subsidiary and order.subsidiary.name:
            elements.append(Paragraph(order.subsidiary.representative_name.upper(), styles['TicketSubtitleSmall']))
        elements.append(Spacer(1, 1))
        # Título del documento
        elements.append(Paragraph(order.get_type_display(), styles['TicketHeader']))
        elements.append(Spacer(3, 3))
        
        # Número del documento (serie-correlativo)
        elements.append(Paragraph(f"{order.serial}-{str(order.correlative).zfill(3)}", styles['TicketHeader']))
        elements.append(Spacer(0, 0))
        
        # Línea separadora
        elements.append(Paragraph("_" * 43, styles['TicketSeparatorLine']))
        elements.append(Spacer(3, 3))
        
        # Información del cliente y fechas en tabla
        client_data = []
        
        # Fila del cliente
        client_data.append([
            Paragraph("CLIENTE", styles['Helvetica_Left_8']),
            Paragraph(":", styles['Helvetica_Left_8']),
            Paragraph(order.client.full_name.upper() if order.client else "SIN CLIENTE", styles['Helvetica_Left_8'])
        ])
        
        # Fila del documento (DNI/RUC)
        if order.client and order.client.number and order.client.number.strip():
            if order.client.document == '01':
                client_data.append([
                    Paragraph("DNI", styles['Helvetica_Left_8']),
                    Paragraph(":", styles['Helvetica_Left_8']),
                    Paragraph(order.client.number, styles['Helvetica_Left_8'])
                ])
            else:
                client_data.append([
                    Paragraph("RUC", styles['Helvetica_Left_8']),
                    Paragraph(":", styles['Helvetica_Left_8']),
                    Paragraph(order.client.number, styles['Helvetica_Left_8'])
                ])
        
        # Fila de fecha de emisión
        if order.register_date:
            client_data.append([
                Paragraph("FECHA EMISIÓN", styles['Helvetica_Left_8']),
                Paragraph(":", styles['Helvetica_Left_8']),
                Paragraph(order.register_date.strftime('%d/%m/%Y'), styles['Helvetica_Left_8'])
            ])
        
        # Fila de fecha de entrega
        if order.delivery_date:
            client_data.append([
                Paragraph("FECHA ENTREGA", styles['Helvetica_Left_8']),
                Paragraph(":", styles['Helvetica_Left_8']),
                Paragraph(order.delivery_date.strftime('%d/%m/%Y'), styles['Helvetica_Left_8'])
            ])
        if order.user:
            client_data.append([
                Paragraph("VENDEDOR", styles['Helvetica_Left_8']),
                Paragraph(":", styles['Helvetica_Left_8']),
                Paragraph(order.user.first_name, styles['Helvetica_Left_8'])
            ])
        # Crear tabla de información del cliente
        client_table = Table(client_data, colWidths=[_wt * 38 / 100, _wt * 3 / 100, _wt * 59 / 100])
        client_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # Primera columna (etiquetas) a la izquierda
            ('ALIGN', (1, 0), (1, -1), 'CENTER'), # Segunda columna (dos puntos) centrada
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),   # Tercera columna (valores) a la izquierda
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Etiquetas en negrita
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),       # Dos puntos normal
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),       # Valores normal
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        elements.append(client_table)
        elements.append(Spacer(1, 1))
        
        # Línea separadora
        elements.append(Paragraph("_" * 43, styles['TicketSeparatorLine']))
        elements.append(Spacer(1, 1))
        
        # Encabezados de la tabla de productos
        table_data = []
        table_data_title = [[
            Paragraph("Cant.", styles['Helvetica_Bold_Left_6']),
            Paragraph("Descripción", styles['Helvetica_Bold_Left_6']),
            Paragraph("P.U.", styles['Helvetica_Bold_Right_6']),
            Paragraph("Total", styles['Helvetica_Bold_Right_6'])
        ]]
        table_title = Table(table_data_title, colWidths=[_wt * 10 / 100, _wt * 56 / 100, _wt * 17 / 100, _wt * 17 / 100])
        table_title.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Cantidad centrada
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Descripción a la izquierda
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Precio unitario a la derecha
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),  # Total a la derecha
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.4),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (3, -1), (3, -1), 2),
            # ('GRID', (0, 0), (-1, -1), 0.5, colors.red),
        ]))
        elements.append(table_title)
        elements.append(Spacer(1, -10))
        elements.append(Paragraph("_" * 43, styles['TicketSeparatorLine']))

        # Agregar productos/servicios
        for detail in order_details:
            table_data.append([
                Paragraph(f"{detail.quantity:.0f}", styles['Helvetica_Center_7']),
                Paragraph(detail.product_name, styles['Helvetica_Left_6']),
                Paragraph(f"{detail.price_unit:.2f}", styles['Helvetica_Right_6']),
                Paragraph(f"{detail.multiply():.2f}", styles['Helvetica_Right_6'])
            ])
        
        # Crear tabla con 4 columnas
        _wt2 = 2.90 * inch - 4 * 0.05 * inch
        table = Table(table_data, colWidths=[_wt * 10 / 100, _wt * 56 / 100, _wt * 17 / 100, _wt * 17 / 100])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Cantidad centrada
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # Descripción a la izquierda
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # Precio unitario a la derecha
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # Total a la derecha
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.4),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            # ('BACKGROUND', (3, -1), (3, -1), colors.green),
            ('RIGHTPADDING', (3, -1), (3, -1), 3),
        ]))
        
        elements.append(table)
        elements.append(Spacer(2, -5))
        
        # Línea separadora
        elements.append(Paragraph("_" * 43, styles['TicketSeparatorLine']))
        elements.append(Spacer(5, 5))
        
        # Resumen de totales
        # elements.append(Paragraph(f"GRAVADA: S/ {order.subtotal:.2f}", styles['Helvetica_Left_8']))
        # elements.append(Paragraph(f"IGV: S/ {order.igv:.2f}", styles['Helvetica_Left_8']))
        
        # Crear tabla de totales con dos columnas alineadas a la derecha
        totales_data = []
        totales_data.append([
            Paragraph("TOTAL:", styles['Helvetica_Bold_Right_8']),
            Paragraph(f"S/ {order.total:.2f}", styles['Helvetica_Right_8'])
        ])
        
        # Solo mostrar adelanto y faltante para órdenes de servicio (tipo 'O')
        if order.type == 'O' and hasattr(order, 'cash_advance') and order.cash_advance and order.cash_advance > 0:
            totales_data.append([
                Paragraph("ADELANTO:", styles['Helvetica_Bold_Right_8']),
                Paragraph(f"S/ {order.cash_advance:.2f}", styles['Helvetica_Right_8'])
            ])
            # Calcular total faltante
            total_faltante = order.total - order.cash_advance
            if total_faltante > 0:
                totales_data.append([
                    Paragraph("PAGO FALTANTE:", styles['Helvetica_Bold_Right_8']),
                    Paragraph(f"S/ {total_faltante:.2f}", styles['Helvetica_Bold_Right_8'])
                ])
        
        # Crear tabla de totales
        totales_table = Table(totales_data, colWidths=[_wt * 0.70, _wt * 0.30])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # Primera columna (etiquetas) a la derecha
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Segunda columna (valores) a la derecha
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),  # Padding reducido
            ('TOPPADDING', (0, 0), (-1, -1), 2),      # Padding reducido
            # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('RIGHTPADDING', (1, 0), (-1, -1), 2),
            # ('BACKGROUND', (1, 0), (-1, -1), colors.green),
        ]))
        
        elements.append(totales_table)
        elements.append(Spacer(2, -5))
        
        # Línea separadora
        elements.append(Paragraph("_" * 43, styles['TicketSeparatorLine']))
        elements.append(Spacer(3, 3))

        # Forma de pago - texto sin bold, valor con bold
        payment_method = order.get_way_to_pay_display()
        elements.append(Paragraph(f"FORMA DE PAGO: {payment_method.upper()}", styles['Helvetica_Left_8']))
        
        # Observaciones
        if order.observation:
            elements.append(Paragraph(f"OBSERVACIONES: {order.observation}", styles['Helvetica_Left_8']))
        else:
            elements.append(Paragraph("OBSERVACIONES:", styles['Helvetica_Bold_Left_8']))
        
        elements.append(Spacer(1, -5))

        # Línea separadora
        elements.append(Paragraph("_" * 43, styles['TicketSeparatorLine']))
        elements.append(Spacer(3, 3))
        
        # Pie de página centrado
        if order.type == 'O':
            elements.append(Paragraph("Conserve el Ticket para el recojo de su orden", styles['Helvetica_Bold_Center_8']))
        elements.append(Paragraph("**Este documento no tiene validez fiscal, puede ser cambiada por una boleta o factura**", styles['Helvetica_Bold_Center_6']))
        elements.append(Paragraph("•Canjee por factura Y/O boleta dentro del mes", styles['Helvetica_Bold_Justify_6']))
        elements.append(Paragraph("•Todo trabajo sera como mínimo el 50% de adelanto, caso contrario no se realizará el trabajo", styles['Helvetica_Bold_Justify_6']))
        elements.append(Paragraph("•Tiene un plazo de un mes para recoger su trabajo, caso contrario será desechado", styles['Helvetica_Bold_Justify_6']))

        # Construir el PDF
        doc.build(elements)
        
        # Obtener el valor del buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
        
    except Exception as e:
        print(f"Error generando PDF: {str(e)}")
        return None


def download_ticket_pdf(request, order_id):
    """
    Vista para descargar el PDF del ticket
    """
    try:
        from .models import Order
        from django.http import HttpResponse
        
        # Verificar que la orden existe
        order = Order.objects.get(id=order_id)
        
        # Generar el PDF
        pdf_content = generate_ticket_pdf(order_id)
        
        if pdf_content:
            # Crear respuesta HTTP con el PDF
            response = HttpResponse(pdf_content, content_type='application/pdf')
            # Forzar descarga automática del PDF
            if order.type == 'O':
                order_type = 'Order'
            else:
                order_type = 'Cotizacion'
            response['Content-Disposition'] = f'attachment; filename="{order_type}_{order.serial}-{str(order.correlative).zfill(3)}.pdf"'
            return response
        else:
            return HttpResponse("Error generando el PDF", status=500)
            
    except Order.DoesNotExist:
        return HttpResponse("Orden no encontrada", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

