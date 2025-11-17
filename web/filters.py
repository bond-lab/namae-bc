# filters.py
def format_cell(value, round_decimals=3):
    """
    Format cell - return formatted number
       and indicate if it should be right-aligned
    used in the render_table macro
    
    Parameters:
    -----------
    value : any
        The value to format
    round_decimals : int, optional
        Number of decimal places to round float values to (default: 3)
    """
    if isinstance(value, (int, float)):
        if isinstance(value, int) and value >= 1989 and value <=2023: # it's a year
            return {'value': f'{value}', 'is_number': False}
        elif isinstance(value, float):
            return {'value': f'{value:,.{round_decimals}f}', 'is_number': True}
        else:
            return {'value': f'{value:,}', 'is_number': True}
    
    if isinstance(value, str):
        clean_value = value.replace(',', '').replace('$', '').strip()
        try:
            if '.' in clean_value:
                num = float(clean_value)
                return {'value': f'{num:,.{round_decimals}f}', 'is_number': True}
            else:
                num = int(clean_value)
                if num >= 1989 and num <=2023: # it's a year
                    return {'value': f'{num}', 'is_number': False}
                else:
                    return {'value': f'{num:,}', 'is_number': True}
        except ValueError:
            pass
    
    return {'value': value, 'is_number': False}

def multisort_filter(items, sort_spec):
    """Sort items by multiple columns with signed direction.
    
    Args:
        items: List of tuples to sort
        sort_spec: List of column numbers (1-indexed), negative for reverse
                   e.g., [3, -2] sorts by col 3 ascending, then col 2 descending
    """
    if not sort_spec:
        return items
    
    result = list(items)
    for col_spec in reversed(sort_spec):
        reverse = col_spec < 0
        idx = abs(col_spec) 
        result = sorted(result, key=lambda x: x[idx], reverse=reverse)
    
    return result
