#!/usr/bin/env python
"""
Script de prueba para el reporte de ventas
"""
import requests
import json

def test_report():
    # URL del reporte
    url = "http://localhost:8000/accounting/sales-report/"
    
    # Datos de prueba
    data = {
        'report_date': '2024-12-19',
        'subsidiary': '0',
        'cash_account': '0'
    }
    
    # Headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        # Hacer la petición POST
        response = requests.post(url, data=data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"JSON Response: {json.dumps(json_response, indent=2)}")
            except:
                print("No es JSON válido")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error en la petición: {e}")

if __name__ == "__main__":
    test_report()
