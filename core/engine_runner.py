from core.engine_registry import get_all


def run(state):

    reports = []

    for engine in get_all():

        report = engine["func"](state)

        reports.append({
            "name": engine["name"],
            "weight": engine["weight"],
            "report": report
        })

    return reports
