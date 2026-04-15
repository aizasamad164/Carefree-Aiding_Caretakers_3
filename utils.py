from datetime import datetime

def format_rows(rows, keys):
    """
    Converts Oracle rows into a list of dictionaries 
    and automatically formats any datetime objects to strings.
    """
    result = []
    for r in rows:
        d = {keys[i]: r[i] for i in range(len(keys))}
        for key, value in d.items():
            # If the column is a TIMESTAMP/Date, convert it to string
            if isinstance(value, datetime):
                d[key] = value.strftime("%Y-%m-%d %H:%M")
        result.append(d)
    return result