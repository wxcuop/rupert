import datetime

def month_to_char(mm_str: str) -> str:
    """
    Convert a two-digit month string to its corresponding futures contract code.
    """
    month_map = {
        "01": "F", "02": "G", "03": "H", "04": "J", "05": "K", "06": "M",
        "07": "N", "08": "Q", "09": "U", "10": "V", "11": "X", "12": "Z"
    }
    return month_map.get(mm_str, "")

def char_to_month(month_code: str) -> int:
    """
    Convert a futures contract month code to its numeric month.
    """
    month_codes = "FGHJKMNQUVXZ"
    return month_codes.find(month_code) + 1 if month_code in month_codes else -1

def generate_exchange_code(underlying: str, maturity_ym: str) -> str:
    """
    Generate an exchange code based on the underlying symbol and maturity date.
    """
    if len(maturity_ym) not in (4, 6, 8):
        return ""
    
    month_char = month_to_char(maturity_ym[-4:-2])
    if not month_char:
        return ""
    
    return f"{underlying}{month_char}{maturity_ym[-3]}"

def get_exchange_code(underlying: str, maturity_monthyear: str) -> str:
    """
    Generate an exchange code from a month-year formatted string (MMYYYY).
    """
    if len(maturity_monthyear) != 6:
        return ""
    
    month_char = month_to_char(maturity_monthyear[:2])
    return f"{underlying}{month_char}{maturity_monthyear[-1]}" if month_char else ""

def convert_month_code(identifier: str) -> str:
    """
    Convert a 2-character contract month code into YYYYMM format.
    """
    if len(identifier) < 2:
        raise ValueError("Invalid identifier: cannot be converted into a month code")
    
    month_code = identifier[-2:]
    if month_code[1].isdigit():
        year = 2000 + int(month_code[1])
    else:
        current_year = datetime.datetime.utcnow().year
        decade = (current_year // 10) * 10
        year = decade + int(month_code[1]) if int(month_code[1]) >= current_year % 10 else decade + 10 + int(month_code[1])
    
    month = char_to_month(month_code[0])
    if month == -1:
        raise ValueError(f"Unrecognized contract month code: {month_code[0]}")
    
    return f"{year}{month:02d}"
