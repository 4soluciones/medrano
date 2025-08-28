from django import template

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
