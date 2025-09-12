from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='calculate_balance')
def calculate_balance(order):
    """
    Calcula el saldo de una orden: total - adelanto a cuenta
    """
    try:
        return order.total - order.cash_advance
    except (AttributeError, TypeError):
        return 0.0


@register.filter(name='format_currency')
def format_currency(value):
    """
    Formatea un valor como moneda peruana
    """
    try:
        return f"S/ {float(value):.2f}"
    except (ValueError, TypeError):
        return "S/ 0.00"


@register.simple_tag
def get_total_advances(order):
    """
    Calcula el total de adelantos de una orden sumando todos los registros de cashflow
    """
    try:
        total_advances = Decimal('0.00')
        for cashflow in order.cashflow_set.all():
            if cashflow.type == 'E':  # Solo entradas (adelantos)
                total_advances += Decimal(str(cashflow.total))
        return total_advances
    except (AttributeError, TypeError, ValueError):
        return Decimal('0.00')


@register.simple_tag
def get_balance(order, total_advances):
    """
    Calcula el saldo de una orden: total - adelantos del cashflow
    """
    try:
        total = Decimal(str(order.total))
        advances = Decimal(str(total_advances))
        return total - advances
    except (AttributeError, TypeError, ValueError):
        return Decimal('0.00')
