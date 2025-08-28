from django import template
import decimal

register = template.Library()


@register.filter(name='thousands_separator')
def thousands_separator(value):
    if value is not None and value != '':
        return '{:,}'.format(value)
    return ''


@register.filter(name='replace_round')
def replace_round(value):
    if value is not None and value != '':
        return str(round(value, 2)).replace(',', '.')
    return value


@register.filter(name='zfill')
def zfill(value):
    if value is not None and value != '':
        return str(value).zfill(3)
    return value


@register.filter(name='get')
def get(d, k):
    return d.get(k, None)


@register.filter(name='calculate_balance')
def calculate_balance(total, cash_advance):
    """Calcula el saldo: total - a cuenta"""
    if total is not None and cash_advance is not None:
        try:
            total_decimal = decimal.Decimal(str(total))
            cash_advance_decimal = decimal.Decimal(str(cash_advance))
            balance = total_decimal - cash_advance_decimal
            return balance
        except (ValueError, TypeError):
            return 0
    return 0


@register.filter(name='get_expense_total_by_type')
def get_expense_total_by_type(cashflows, expense_type):
    """Obtiene el total de gastos por tipo específico"""
    if cashflows:
        total = 0
        for cashflow in cashflows:
            if cashflow.type == 'S' and cashflow.type_expense == expense_type:
                total += cashflow.total
        return total
    return 0


@register.filter(name='sum_order_quantities')
def sum_order_quantities(order):
    """Suma todas las cantidades de los productos de una orden"""
    if hasattr(order, 'orderdetail_set') and order.orderdetail_set.exists():
        total = 0
        for detail in order.orderdetail_set.all():
            if detail.quantity:
                total += detail.quantity
        return total
    return 1  # Valor por defecto si no hay detalles