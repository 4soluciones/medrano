import requests
import html
from django.http import JsonResponse
from http import HTTPStatus
from datetime import datetime


def query_apis_net_dni_ruc(nro_doc, type_document):
    # context = {}
    url = {}
    if type_document == 'DNI':
        url = 'https://api.decolecta.com/v1/reniec/dni?numero=' + nro_doc

    if type_document == 'RUC':
        url = 'https://api.decolecta.com/v1/sunat/ruc?numero=' + nro_doc

    headers = {
        "Content-Type": 'application/json',
        "Authorization": 'sk_9208.RYV679GaMxTuXFUiSElimKi0YSPYCgKD'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        result = response.json()
        # print(result)
        if type_document == 'DNI':
            context = {
                # 'nombre': result.get("nombre"),
                'fullName': result.get("full_name"),
                # 'tipoDocumento': result.get("tipoDocumento"),
                'numeroDocumento': result.get('document_number'),
                'apellidoPaterno': result.get('first_last_name'),
                'apellidoMaterno': result.get('second_last_name'),
                'nombres': result.get('first_name'),
                'direccion': result.get('direccion'),
            }
        else:
            context = {
                'razonSocial': result.get("razon_social"),
                'numeroDocumento': result.get('numero_documento'),
                'direccion': result.get('direccion'),
            }
    else:
        result = response.status_code
        context = {
            'errors': True
        }
    return context


def query_apis_net_money(date_now):
    context = {}

    url = 'https://api.apis.net.pe/v1/tipo-cambio-sunat?fecha={}'.format(date_now)
    headers = {
        "Content-Type": 'application/json',
        'authorization': 'Bearer apis-token-4758.Q8If8ovdUU8yjl-7qcRgank5qS3MkLPI',
    }

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        result = r.json()

        context = {
            'success': True,
            'fecha_busqueda': result.get('fecha'),
            'fecha_sunat': result.get('fecha'),
            'venta': result.get('venta'),
            'compra': result.get('compra'),
            'origen': result.get('origen'),
            'moneda': result.get('moneda'),
        }
    else:
        result = r.json()
        context = {
            'status': False,
            'errors': '400 Bad Request',
        }

    return context
