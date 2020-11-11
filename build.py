from datetime import datetime, timedelta
import requests
from state_data import population

__all_states_data = "https://covidtracking.com/api/states/daily"
__all_states_data = requests.get(__all_states_data).json()[::-1]
__state_keys = list(set([d["state"] for d in __all_states_data]))
__state_keys.sort()
__states = {}

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

    recent = [d for d in data[-14:]]

    daily_death_increase = round(
        sum([d["deathIncrease"] for d in recent]) / len(recent)
    )
    daily_positive_increase = round(
        sum([d["positiveIncrease"] for d in recent]) / len(recent)
    )

    date = datetime.strptime(f'{data[-1]["date"]}', "%Y%m%d")
    death = recent[-1]["death"] or 0
    positive = recent[-1]["positive"] or 0

    for i in range(21):
        date = date + timedelta(1)

        death += daily_death_increase
        positive += daily_positive_increase

        csv_lines.append(
            f"{int(f'{date:%Y%m%d}')},true,{death},{round(death/millions)},"
            + f"{daily_death_increase},{round(daily_death_increase/millions)},"
            + f"{positive},{round(positive/millions)},{daily_positive_increase},"
            + f"{round(daily_positive_increase/millions)}"
        )

    with open(f"docs/{state}.csv", "w") as csv:
        csv.write("\n".join(csv_lines))
        csv.close()
