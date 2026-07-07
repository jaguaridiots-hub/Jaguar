ENGINES = []


def register(name, func, weight=1.0):

    ENGINES.append({
        "name": name,
        "func": func,
        "weight": weight
    })


def get_all():

    return ENGINES
