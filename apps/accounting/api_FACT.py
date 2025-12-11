import requests
import decimal
from django.db.models import Max
from django.db.models.functions import Coalesce

from .format_to_dates import utc_to_local
from .models import *
from ..sales.models import Order, OrderDetail, Product
from datetime import datetime, date

GRAPHQL_URL = "https://ng.tuf4ctur4.net.pe/graphql"
# GRAPHQL_URL = "http://192.168.1.80:9050/graphql"

tokens = {
    "10471315198": "gAAAAABpNGSrdx4rldIqTvwIF3OXemYIfqzx9My1YT9hNVKW9ruOLVfzAeL0MsUUKOqh6XPA1HFX7tu-MmvFu7JojTEM8PGizg==",
}


def get_new_correlative(serial, document_type):
    """
    Obtiene un nuevo correlativo para el serial y tipo de documento especificado.
    document_type: '1' para Factura, '2' para Boleta
    """
    # Buscar el último correlativo usando los campos de Order directamente
    # bill_type: '1' para Factura, '2' para Boleta
    last_order = Order.objects.filter(
        subsidiary__serial=serial,
        bill_type=document_type
    ).exclude(bill_number__isnull=True).order_by('-bill_number').first()
    
    if last_order and last_order.bill_number:
        return last_order.bill_number + 1
    else:
        return 1


def send_bill_4_fact(order_id, product_type='bien'):  # FACTURA 4 FACT
    order_obj = Order.objects.select_related('client', 'bill_client', 'subsidiary').get(id=int(order_id))
    
    # Obtener serial de la sucursal
    if not order_obj.subsidiary:
        return {"error": "La orden no tiene sucursal asignada"}
    serial = order_obj.subsidiary.serial or ""
    
    correlative = get_new_correlative(serial, '1')
    details = OrderDetail.objects.filter(order=order_obj)
    
    # Usar bill_client si existe, sino usar client
    if order_obj.bill_client:
        client_obj = order_obj.bill_client
    elif order_obj.client:
        client_obj = order_obj.client
    else:
        return {"error": "La orden no tiene cliente asignado"}
    
    # Obtener nombre del cliente
    client_name = str(client_obj.full_name or "").replace('"', "'")
    if not client_name:
        client_name = f"{client_obj.first_name or ''} {client_obj.surname or ''}".strip()
    
    # Obtener dirección del cliente
    client_address = str(client_obj.address or "").replace('"', "'")
    
    # Obtener documento del cliente (RUC para factura)
    if client_obj.document == '06':
        client_document_number = client_obj.number or ""
    else:
        return {"error": "El cliente debe tener RUC para generar una factura"}
    
    # Obtener fecha de registro - siempre usar fecha actual del día
    # Revisar bill_date si existe, sino usar fecha/hora actual
    if order_obj.bill_date:
        register_date = order_obj.bill_date
        formatdate = register_date.strftime("%Y-%m-%d")
        hour_date = register_date.strftime("%H:%M:%S")
    else:
        # Siempre usar la fecha actual del día
        formatdate = date.today().strftime("%Y-%m-%d")
        hour_date = datetime.now().strftime("%H:%M:%S")
    
    # Obtener total de detracción
    total_detraction = decimal.Decimal(order_obj.total_detraction or 0)
    
    items = []
    items_credit_graphql = []
    index = 1
    sub_total = decimal.Decimal(0)
    total = decimal.Decimal(0)
    igv_total = decimal.Decimal(0)
    
    # Verificar si es pago a crédito
    if order_obj.way_to_pay == 'C':
        # Para crédito, necesitaríamos PaymentFees si existe ese modelo
        # Por ahora, asumimos que no hay cuotas definidas
        payment = 9
        items_credit_graphql = "[]"
    else:
        payment = 1
        items_credit_graphql = "[]"
    
    # Procesar detalles de la orden
    for d in details:
        if not d.product:
            # Si no hay producto, usar product_name
            product_name = str(d.product_name or "").replace('"', "'")
        else:
            product_name = str(d.product.name or "").replace('"', "'")
        
        # Obtener cantidad (usar quantity en lugar de quantity_sold)
        quantity = decimal.Decimal(d.quantity or 0)
        if quantity == 0:
            continue
        
        base_total = quantity * decimal.Decimal(d.price_unit or 0)
        base_amount = base_total / decimal.Decimal(1.1800)
        igv = base_total - base_amount
        sub_total = sub_total + decimal.Decimal(base_amount)
        total = total + base_total
        igv_total = igv_total + decimal.Decimal(igv)
        _base_amount_v = (base_amount / quantity).quantize(decimal.Decimal('0.000001'))
        
        # Unidad según tipo de producto: NIU para bien, ZZ para servicio
        _unit = 'ZZ' if product_type == 'servicio' else 'NIU'
        
        item = {
            "index": str(index),
            "codigoUnidad": str(_unit),
            "codigoProducto": "0000",
            "codigoSunat": "10000000",
            "producto": product_name,
            "cantidad": quantity,
            "precioBase": _base_amount_v,
            "tipoIgvCodigo": "10"
        }
        items.append(item)
        index += 1
    
    if not items:
        return {"error": "La orden no tiene items válidos"}
    
    items_graphql = ", ".join(
        f"""{{  
               producto: "{item['producto']}", 
               cantidad: {item['cantidad']}, 
               precioBase: {item['precioBase']}, 
               codigoSunat: "{item['codigoSunat']}",
               codigoProducto: "{item['codigoProducto']}",
               codigoUnidad: "{item['codigoUnidad']}",                                            
               tipoIgvCodigo: "{item['tipoIgvCodigo']}" 
        }}"""
        for item in items
    )
    
    items_graphql = f"[{items_graphql}]"
    
    graphql_query = f"""
    mutation RegisterSale  {{
        registerSale(            
            cliente: {{
                razonSocialNombres: "{client_name}",
                numeroDocumento: "{client_document_number}",
                codigoTipoEntidad: 6,
                clienteDireccion: "{client_address}"
            }},
            venta: {{
                serie: "F{serial}",
                numero: "{int(correlative)}",
                fechaEmision: "{formatdate}",
                horaEmision: "{hour_date}",
                fechaVencimiento: "",
                monedaId: 1,                
                formaPagoId: {payment},
                totalGravada: {float(sub_total)},
                totalDescuentoGlobalPorcentaje: 0,
                totalDescuentoGlobal: 0,
                totalIgv: {float(igv_total)},
                totalExonerada: 0,
                totalInafecta: 0,
                totalImporte: {float(total.quantize(decimal.Decimal('0.01')))},
                totalAPagar: {float(total.quantize(decimal.Decimal('0.01')))},
                totalDetraction: {float(total_detraction.quantize(decimal.Decimal('0.01')))},
                tipoDocumentoCodigo: "01",
                nota: " "
            }},
            items: {items_graphql}
            creditPay: {items_credit_graphql}
        ) {{
            message
            success
            operationId
        }}
    }}
    """
    # print(graphql_query)
    
    token = tokens.get("10471315198", "ID no encontrado")
    
    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json={"query": graphql_query}, headers=HEADERS)
        response.raise_for_status()
        
        result = response.json()
        
        success = result.get("data", {}).get("registerSale", {}).get("success")
        
        if success:
            return {
                "success": success,
                "message": result.get("data", {}).get("registerSale", {}).get("message"),
                "operationId": result.get("data", {}).get("registerSale", {}).get("operationId"),
                "serie": "F" + serial,
                "numero": correlative,
                "tipo_de_comprobante": "1",
            }
        else:
            # Maneja el caso en que la operación no fue exitosa
            return {
                "success": False,
                "message": "La operación no fue exitosa, revise la venta e informe a Sistemas",
            }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"error": "La respuesta no es un JSON válido"}


def send_receipt_4_fact(order_id, product_type='bien'):  # BOLETA 4 FACT
    order_obj = Order.objects.select_related('client', 'bill_client', 'subsidiary').get(id=int(order_id))
    
    # Obtener serial de la sucursal
    if not order_obj.subsidiary:
        return {"error": "La orden no tiene sucursal asignada"}
    serial = order_obj.subsidiary.serial or ""
    
    correlative = get_new_correlative(serial, '2')
    details = OrderDetail.objects.filter(order=order_obj)
    
    # Usar bill_client si existe, sino usar client
    if order_obj.bill_client:
        client_obj = order_obj.bill_client
    elif order_obj.client:
        client_obj = order_obj.client
    else:
        return {"error": "La orden no tiene cliente asignado"}
    
    # Obtener nombre del cliente
    client_name = str(client_obj.full_name or "").replace('"', "'")
    if not client_name:
        client_name = f"{client_obj.first_name or ''} {client_obj.surname or ''}".strip()
    
    # Obtener dirección del cliente
    client_address = str(client_obj.address or "").replace('"', "'")
    
    # Obtener documento del cliente (DNI para boleta)
    if client_obj.document == '01':
        client_document_number = client_obj.number or ""
    else:
        # Si no es DNI, intentar usar el número de documento que tenga
        client_document_number = client_obj.number or ""
    
    # Obtener fecha de registro - siempre usar fecha actual del día
    # Revisar bill_date si existe, sino usar fecha/hora actual
    if order_obj.bill_date:
        register_date = utc_to_local(order_obj.bill_date) if hasattr(order_obj.bill_date, 'tzinfo') and order_obj.bill_date.tzinfo else order_obj.bill_date
        formatdate = register_date.strftime("%Y-%m-%d")
        hour_date = register_date.strftime("%H:%M:%S")
    else:
        # Siempre usar la fecha actual del día
        formatdate = date.today().strftime("%Y-%m-%d")
        hour_date = datetime.now().strftime("%H:%M:%S")
    
    # Obtener total de detracción
    total_detraction = decimal.Decimal(order_obj.total_detraction or 0)
    
    items = []
    index = 1
    sub_total = decimal.Decimal(0)
    total = decimal.Decimal(0)
    igv_total = decimal.Decimal(0)
    
    # Procesar detalles de la orden
    for d in details:
        if not d.product:
            # Si no hay producto, usar product_name
            product_name = str(d.product_name or "").replace('"', "'")
        else:
            product_name = str(d.product.name or "").replace('"', "'")
        
        # Obtener cantidad (usar quantity en lugar de quantity_sold)
        quantity = decimal.Decimal(d.quantity or 0)
        if quantity == 0:
            continue
        
        base_total = quantity * decimal.Decimal(d.price_unit or 0)
        base_amount = base_total / decimal.Decimal(1.1800)
        igv = base_total - base_amount
        sub_total = sub_total + decimal.Decimal(base_amount)
        total = total + base_total
        igv_total = igv_total + decimal.Decimal(igv)
        _base_amount_v = (base_amount / quantity).quantize(decimal.Decimal('0.000001'))
        
        # Unidad según tipo de producto: NIU para bien, ZZ para servicio
        _unit = 'ZZ' if product_type == 'servicio' else 'NIU'
        
        item = {
            "index": str(index),
            "codigoUnidad": _unit,
            "codigoProducto": "0000",
            "codigoSunat": "10000000",
            "producto": product_name,
            "cantidad": quantity,
            "precioBase": _base_amount_v,
            "tipoIgvCodigo": "10"
        }
        items.append(item)
        index += 1
    
    if not items:
        return {"error": "La orden no tiene items válidos"}
    
    items_graphql = ", ".join(
        f"""{{                     
                codigoUnidad: "{item['codigoUnidad']}", 
                codigoProducto: "{item['codigoProducto']}", 
                codigoSunat: "{item['codigoSunat']}", 
                producto: "{item['producto']}", 
                cantidad: {item['cantidad']}, 
                precioBase: {item['precioBase']}, 
                tipoIgvCodigo: "{item['tipoIgvCodigo']}" 
            }}"""
        for item in items
    )
    
    items_graphql = f"[{items_graphql}]"
    
    graphql_query = f"""
        mutation RegisterSale  {{
            registerSale(            
                cliente: {{
                    razonSocialNombres: "{client_name}",
                    numeroDocumento: "{client_document_number}",
                    codigoTipoEntidad: 1,
                    clienteDireccion: "{client_address}"
                }},
                venta: {{
                    serie: "B{serial}",
                    numero: "{int(correlative)}",
                    fechaEmision: "{formatdate}",
                    horaEmision: "{hour_date}",
                    fechaVencimiento: "",
                    monedaId: 1,                
                    formaPagoId: 1,
                    totalGravada: {float(sub_total)},
                    totalDescuentoGlobalPorcentaje: 0,
                    totalDescuentoGlobal: 0,
                    totalIgv: {float(igv_total)},
                    totalExonerada: 0,
                    totalInafecta: 0,
                    totalImporte: {float(total.quantize(decimal.Decimal('0.01')))},
                    totalAPagar: {float(total.quantize(decimal.Decimal('0.01')))},
                    totalDetraction: {float(total_detraction.quantize(decimal.Decimal('0.01')))},
                    tipoDocumentoCodigo: "03",
                    nota: " "
                }},
                items: {items_graphql}
            ) {{
                message
                success
                operationId
            }}
        }}
        """
    
    # print(graphql_query)
    
    token = tokens.get("10471315198", "ID no encontrado")
    
    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json={"query": graphql_query}, headers=HEADERS)
        response.raise_for_status()
        
        result = response.json()
        
        success = result.get("data", {}).get("registerSale", {}).get("success")
        
        if success:
            return {
                "success": success,
                "message": result.get("data", {}).get("registerSale", {}).get("message"),
                "operationId": result.get("data", {}).get("registerSale", {}).get("operationId"),
                "serie": "B" + serial,
                "numero": correlative,
                "tipo_de_comprobante": "2",
            }
        else:
            # Maneja el caso en que la operación no fue exitosa
            return {
                "success": False,
                "message": "La operación no fue exitosa",
            }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"error": "La respuesta no es un JSON válido"}


def number_note(serial=None):
    """
    Obtiene el siguiente número de nota de crédito.
    Si no existe el modelo CreditNote, retorna 1.
    """
    try:
        from .models import CreditNote
        number = CreditNote.objects.filter(serial=serial).aggregate(
            r=Coalesce(Max('correlative'), 0)).get('r')
        return number + 1
    except (ImportError, AttributeError):
        # Si no existe el modelo, retornar 1
        return 1


def send_credit_note_fact(pk, details, motive):
    order_obj = Order.objects.get(id=int(pk))
    serial = str(order_obj.voucher_type) + "N01"
    correlative = number_note(serial)
    client_obj = order_obj.client
    # date_voucher = datetime.now().strftime("%d-%m-%Y")
    items = []
    index = 1
    sub_total = decimal.Decimal(0)
    total = decimal.Decimal(0)
    for d in details:
        if d['quantityReturned']:
            product_id = int(d['productID'])
            product_obj = Product.objects.get(id=product_id)
            description = str(str(product_obj.name).upper()).replace('"', "'")
            total_item_igv = decimal.Decimal(d['quantityReturned']) * decimal.Decimal(d['price'])
            price_igv = decimal.Decimal(d['price'])
            price_sin_igv = price_igv / decimal.Decimal(1.1800)
            total_item_sin_igv = total_item_igv / decimal.Decimal(1.1800)
            igv_item = total_item_igv - total_item_sin_igv
            total = total + total_item_igv
            sub_total = sub_total + total_item_sin_igv
            # Unidad siempre será NIU
            _unit = 'NIU'
            
            item = {
                "index": str(index),
                "codigoUnidad": str(_unit),
                "codigoProducto": str(product_obj.code),
                "codigoSunat": "10000000",
                "producto": description,
                "cantidad": decimal.Decimal(d['quantityReturned']).quantize(decimal.Decimal('0.0001')),
                "precioBase": price_sin_igv.quantize(decimal.Decimal('0.000001')),
                "tipoIgvCodigo": "10"
            }
            items.append(item)
    
    items_graphql = ", ".join(
        f"""{{  
                   producto: "{item['producto']}", 
                   cantidad: {item['cantidad']}, 
                   precioBase: {item['precioBase']}, 
                   codigoSunat: "{item['codigoSunat']}",
                   codigoProducto: "{item['codigoProducto']}",
                   codigoUnidad: "{item['codigoUnidad']}",                                            
                   tipoIgvCodigo: "{item['tipoIgvCodigo']}" 
            }}"""
        for item in items
    )
    
    items_graphql = f"[{items_graphql}]"
    
    _type_document = '01' if order_obj.voucher_type == 'B' else '06'
    
    # Obtener datos del cliente según el modelo Person
    client_names = str(client_obj.full_name or "").replace('"', "'")
    if not client_names:
        client_names = f"{client_obj.first_name or ''} {client_obj.surname or ''}".strip()
    
    client_document = client_obj.number or ""
    client_document_type = 1 if client_obj.document == '01' else 6
    
    client_address = str(client_obj.address or "").replace('"', "'")
    
    total_engraved = decimal.Decimal(sub_total)
    total_invoice = total_engraved * decimal.Decimal(1.1800)
    total_igv = total_invoice - total_engraved
    
    # Siempre usar la fecha actual del día
    # Revisar bill_date si existe, sino usar fecha/hora actual
    if order_obj.bill_date:
        register_date = utc_to_local(order_obj.bill_date) if hasattr(order_obj.bill_date, 'tzinfo') and order_obj.bill_date.tzinfo else order_obj.bill_date
        formatdate = register_date.strftime("%Y-%m-%d")
        hour_date = register_date.strftime("%H:%M:%S")
    else:
        formatdate = date.today().strftime("%Y-%m-%d")
        hour_date = datetime.now().strftime("%H:%M:%S")
    
    type_document_code = ''
    
    # Usar los campos de Order directamente en lugar de OrderBill
    # bill_type: '1' para Factura, '2' para Boleta
    if order_obj.bill_type == '2':
        type_document_code = '03'
    elif order_obj.bill_type == '1':
        type_document_code = '01'
    else:
        # Si no hay bill_type, intentar inferir del voucher_type
        if order_obj.voucher_type == 'B':
            type_document_code = '03'
        elif order_obj.voucher_type == 'F':
            type_document_code = '01'
    
    # Obtener serial y número del comprobante desde Order
    bill_serial = order_obj.bill_serial or ""
    bill_number = order_obj.bill_number or 0
    
    graphql_query = f"""
        mutation RegisterCreditNote  {{
            registerCreditNote(            
                client: {{
                    razonSocialNombres: "{client_names}",
                    numeroDocumento: "{client_document}",
                    codigoTipoEntidad: {client_document_type},
                    clienteDireccion: "{client_address}"
                }},
                creditNote: {{
                    serie: "{serial}",
                    numero: "{correlative}",
                    fechaEmision: "{formatdate}",
                    horaEmision: "{hour_date}",
                    fechaVencimiento: "{formatdate}",
                    monedaId: 1,                
                    formaPagoId: 1,
                    totalGravada: {float(total_engraved)},
                    totalDescuentoGlobalPorcentaje: 0,
                    totalDescuentoGlobal: 0,
                    totalIgv: {float(total_igv)},
                    totalExonerada: 0,
                    totalInafecta: 0,
                    totalImporte: {float(total_invoice.quantize(decimal.Decimal('0.01')))},
                    totalAPagar: {float(total_invoice.quantize(decimal.Decimal('0.01')))},
                    tipoDocumentoCodigo: "07",
                    nota: "",
                    motiveCreditNote: "{motive}"
                }},
                relatedDocuments: {{
                    serial: "{str(bill_serial)}"      
                    number: "{str(bill_number)}"      
                    codeTypeDocument: "{str(type_document_code)}"      
                }},
                items: {items_graphql}
            ) {{
                message
                error
                operationId
            }}
        }}
        """
    # print(graphql_query)
    
    token = tokens.get("20603890214", "ID no encontrado")
    
    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json={"query": graphql_query}, headers=HEADERS)
        response.raise_for_status()
        
        result = response.json()
        
        success = not result.get("data", {}).get("registerCreditNote", {}).get("error")
        
        if success:
            operation_id = result.get("data", {}).get("registerCreditNote", {}).get("operationId")
            enlace_pdf = f'https://ng.tuf4ctur4.net.pe/operations/print_credit_note/{operation_id}/'
            # enlace_pdf = f'http://192.168.1.80:9050/operations/print_credit_note/{operation_id}/'
            note_total = total_invoice
            return {
                "success": success,
                'tipo_de_comprobante': '3',
                "message": result.get("data", {}).get("registerCreditNote", {}).get("message"),
                'serial': str(serial),
                'correlative': correlative,
                'enlace_del_pdf': enlace_pdf,
                'note_total': note_total,
                'note_description': f'La Nota de Crédito numero {serial}-{correlative}, ha sido aceptado'
            }
        else:
            return {
                "success": False,
                "message": "La operación no fue exitosa, revise la venta e informe a Sistemas",
                "error": result.get("data", {}).get("registerCreditNote", {}).get("error"),
            }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"error": "La respuesta no es un JSON válido"}


def annul_invoice(order_id):
    # Usar los campos de Order directamente
    order_obj = Order.objects.get(id=int(order_id))
    correlative = order_obj.bill_number or 0
    serial = order_obj.bill_serial or ""
    
    variables = {
        "correlative": correlative,
        "serial": serial
    }
    
    mutation = """
    mutation AnnulInvoice($correlative: Int!, $serial: String!) {
        annulInvoice(correlative: $correlative, serial: $serial) {
            message
            success
        }
    }
    """
    
    token = tokens.get("20603890214", "ID no encontrado")
    
    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }
    
    # print("Enviando mutación GraphQL:")
    # print("Query:", mutation)
    # print("Variables:", variables)
    # print("Headers:", HEADERS)
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": mutation, "variables": variables},
            headers=HEADERS
        )
        response.raise_for_status()
        
        result = response.json()
        
        data = result.get("data", {}).get("annulInvoice")
        
        if data and data.get("success"):
            return {
                "success": True,
                "message": data.get("message"),
            }
        else:
            return {
                "success": False,
                "message": data.get("message") if data else "No se obtuvo respuesta del servidor.",
            }
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"success": False, "message": "La respuesta no es un JSON válido"}
