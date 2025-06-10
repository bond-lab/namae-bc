# filters.py
def format_cell(value):
    """
    Format cell - return formatted number
       and indicate if it should be right-aligned

    used in the render_table macro
    """
    if isinstance(value, (int, float)):
        if isinstance(value, int) and value >= 1989 and value <=2023: # it's a year
            return {'value': f'{value}', 'is_number': False}
        else:
            return {'value': f'{value:,}', 'is_number': True}
    
    if isinstance(value, str):
        clean_value = value.replace(',', '').replace('$', '').strip()
        try:
            if '.' in clean_value:
                num = float(clean_value)
                return {'value': f'{num:,.2f}', 'is_number': True}
            else:
                num = int(clean_value)
                if num >= 1989 and num <=2023: # it's a year
                    return {'value': f'{num}', 'is_number': False}
                else:
                    return {'value': f'{num:,}', 'is_number': True}
        except ValueError:
            pass
    
    return {'value': value, 'is_number': False}
