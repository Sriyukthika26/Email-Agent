def filter_id_fields(data: dict) -> dict:
    """Removes keys from a dictionary that end with 'id'."""
    if not isinstance(data, dict):
        return data
    return {k: v for k, v in data.items() if not k.endswith("id")}