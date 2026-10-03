# core/engine_helpers.py
import logging

def safe_engine_output(state, attr_name):
    """
    Return the engine output as a dictionary, or an empty dict if it is missing
    or not a dictionary.  A warning is logged when the output is unusable,
    so integration bugs are never silently hidden.
    """
    obj = getattr(state, attr_name, None)

    if obj is None:
        logging.warning("%s engine output missing – no attribute on state", attr_name)
        return {}

    if not isinstance(obj, dict):
        logging.warning(
            "%s engine output is not a dictionary (type=%s) – returning {}",
            attr_name,
            type(obj).__name__,
        )
        return {}

    return obj
