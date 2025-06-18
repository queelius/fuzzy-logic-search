from typing import Any, List

def get_values_by_field_path(obj: Any, field_path: str) -> List[Any]:
    """
    Retrieves values from the JSON-like object based on the field path,
    supporting wildcards '*' and '**'.

    Args:
        obj (Any): The JSON-like object.
        field_path (str): The field path string.

    Returns:
        List[Any]: A list of values matching the field path.
    """
    
    def recursive_get(cur_obj, fields):
        if not fields:
            return [cur_obj]
        
        field = fields[0]
        rest = fields[1:]
        results = []
        
        if field == '**':
            # Traverse into dictionaries and lists
            if isinstance(cur_obj, dict):
                for key, value in cur_obj.items():
                    results.extend(recursive_get(value, rest))
                    results.extend(recursive_get(value, fields))
            elif isinstance(cur_obj, list):
                for item in cur_obj:
                    results.extend(recursive_get(item, rest))
                    results.extend(recursive_get(item, fields))

        
        elif field == '*':
            # Match any single level
            if isinstance(cur_obj, dict):
                for key, value in cur_obj.items():
                    results.extend(recursive_get(value, rest))
            elif isinstance(cur_obj, list):
                for item in cur_obj:
                    results.extend(recursive_get(item, rest))
        
        else:
            # Match specific field
            if isinstance(cur_obj, dict) and field in cur_obj:
                results.extend(recursive_get(cur_obj[field], rest))
            elif isinstance(cur_obj, list):
                for item in cur_obj:
                    if isinstance(item, dict) and field in item:
                        results.extend(recursive_get(item[field], rest))
        
        return results

    fields = field_path.split('.')
    return recursive_get(obj, fields)


def field_path_count(obj: Any, field_path: str) -> int:
    """
    Counts the number of times the field path exists in the JSON-like object.

    Args:
        obj (Any): The JSON-like object.
        field_path (str): The field path string.

    Returns:
        int: The number of times the field path exists.
    """

    return len(get_values_by_field_path(obj, field_path))