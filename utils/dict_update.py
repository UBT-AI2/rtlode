
def deep_update(original, update):
    """
    Recursive dict update implementation.
    """
    for key, val in update.items():
        if isinstance(val, dict):
            original[key] = deep_update(original.get(key, {}), val)
        else:
            original[key] = val
    return original
