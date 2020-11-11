from datetime import datetime, timedelta
import json
import requests
from state_data import names, population

__all_states_data = "https://covidtracking.com/api/states/daily"
__all_states_data = requests.get(__all_states_data).json()[::-1]
__state_keys = list(set([d["state"] for d in __all_states_data]))
__state_keys.sort()
__states = {}

with open("docs/index.json", "w+") as index:
    index.write(json.dumps(names))
    index.close()

for state in __state_keys:
    data = [d for d in __all_states_data if d["state"] == state]
    total = data[-1]

    pop = population[state]
    millions = pop / 1_000_000

    csv_lines = [
        "date,projected,deaths,deathsPerMillion,deathIncrease,deathIncreasePerMillion,"
        + "positive,positivePerMillion,positiveIncrease,positiveIncreasePerMillion"
    ]

    for date in data:
        death = date["death"] or 0
        deathIncrease = date["deathIncrease"] or 0
        positive = date["positive"] or 0
        positiveIncrease = date["positiveIncrease"] or 0

        csv_lines.append(
            f"{date['date']},false,{death},{round(death/millions)},{deathIncrease},"
            + f"{round(deathIncrease/millions)},{positive},{round(positive/millions)},"
            + f"{positiveIncrease},{round(positiveIncrease/millions)}"
        )

    avg = (
        (sum([d["deathIncrease"] for d in data[-7:]]))
        - (sum([d["deathIncrease"] for d in data[-14:-7]]))
    ) / 49
    daily_death_increase = (
        1 + (avg / data[-1]["deathIncrease"]) if data[-1]["deathIncrease"] > 0 else 1
    )

    avg = (
        (sum([d["positiveIncrease"] for d in data[-7:]]))
        - (sum([d["positiveIncrease"] for d in data[-14:-7]]))
    ) / 49
    daily_positive_increase = (
        1 + (avg / data[-1]["positiveIncrease"])
        if data[-1]["positiveIncrease"] > 0
        else 1
    )

    date = datetime.strptime(f'{data[-1]["date"]}', "%Y%m%d")
    death = data[-1]["death"] or 0
    deathIncrease = data[-1]["deathIncrease"] or 0
    positive = data[-1]["positive"] or 0
    positiveIncrease = data[-1]["positiveIncrease"] or 0

    for i in range(21):
        date = date + timedelta(1)

        deathIncrease *= daily_death_increase
        positiveIncrease *= daily_positive_increase

        death += deathIncrease
        positive += positiveIncrease

        csv_lines.append(
            f"{int(f'{date:%Y%m%d}')},true,{round(death)},{round(death/millions)},"
            + f"{round(deathIncrease)},{round(deathIncrease/millions)},"
            + f"{round(positive)},{round(positive/millions)},{round(positiveIncrease)},"
            + f"{round(positiveIncrease/millions)}"
        )

    with open(f"docs/{state}.csv", "w") as csv:
        csv.write("\n".join(csv_lines))
        csv.write("\n")
        csv.close()
