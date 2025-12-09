from django import template

register = template.Library()


@register.filter(name='cents_to_dollars')
def cents_to_dollars(value):
    """Convert an integer number of cents into a dollar string with 2 decimals.

    Examples:
        500 -> '5.00'
        125 -> '1.25'
    If value is None or not an int, return it unchanged.
    """
    try:
        cents = int(value)
    except Exception:
        return value
    dollars = cents / 100.0
    return "{:.2f}".format(dollars)
