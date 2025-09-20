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

    def recursive_get(cur_obj, fields, visited_objects=None):
        if visited_objects is None:
            visited_objects = set()

        if not fields:
            return [cur_obj]

        field = fields[0]
        rest = fields[1:]
        results = []

        # Use object id to track visited objects for cycle detection
        obj_id = id(cur_obj)

        if field == '**':
            # Deep traversal: search within nested structures
            # First, try to match the remaining path at current level
            if rest:
                results.extend(recursive_get(cur_obj, rest, visited_objects.copy()))

            # Then continue deep search into children
            if obj_id not in visited_objects:
                visited_objects.add(obj_id)
                if isinstance(cur_obj, dict):
                    for key, value in cur_obj.items():
                        # Continue deep search with ** still in pattern
                        results.extend(recursive_get(value, fields, visited_objects.copy()))
                elif isinstance(cur_obj, list):
                    for item in cur_obj:
                        # Continue deep search with ** still in pattern
                        results.extend(recursive_get(item, fields, visited_objects.copy()))
                visited_objects.remove(obj_id)


        elif field == '*':
            # Match any single level
            if isinstance(cur_obj, dict):
                for key, value in cur_obj.items():
                    results.extend(recursive_get(value, rest, visited_objects))
            elif isinstance(cur_obj, list):
                for item in cur_obj:
                    results.extend(recursive_get(item, rest, visited_objects))

        else:
            # Match specific field
            if isinstance(cur_obj, dict) and field in cur_obj:
                results.extend(recursive_get(cur_obj[field], rest, visited_objects))
            elif isinstance(cur_obj, list):
                for item in cur_obj:
                    if isinstance(item, dict) and field in item:
                        results.extend(recursive_get(item[field], rest, visited_objects))

        return results

    fields = field_path.split('.')
    raw_results = recursive_get(obj, fields)

    # Remove duplicates while preserving order
    seen = set()
    unique_results = []
    for item in raw_results:
        # Use a tuple representation for hashability
        item_key = str(item) if item is not None else None
        if item_key not in seen:
            seen.add(item_key)
            unique_results.append(item)

    return unique_results


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