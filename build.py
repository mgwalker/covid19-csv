from datetime import datetime, timedelta
import json
import requests
from state_data import names, population

__all_us_data = "https://covidtracking.com/api/us/daily"
__all_us_data = requests.get(__all_us_data).json()[::-1]
__all_us_data = [{**d, "state": "US"} for d in __all_us_data]

population["US"] = sum(population.values())
names["US"] = "United States"

__all_states_data = "https://covidtracking.com/api/states/daily"
__all_states_data = requests.get(__all_states_data).json()[::-1]
__all_states_data.extend(__all_us_data)

__state_keys = list(set([d["state"] for d in __all_states_data]))
__state_keys.sort()
__states = {}

with open("docs/index.json", "w+") as index:
    index.write(
        json.dumps(
            {
                k: {
                    "link": f"https://mgwalker.github.io/covid19-csv/v1/{k}.csv",
                    "name": v,
                    "population": population[k],
                }
                for (k, v) in names.items()
            }
        )
    )
    index.close()

for state in __state_keys:
    data = [d for d in __all_states_data if d["state"] == state]
    total = data[-1]

    pop = population[state]
    millions = pop / 1_000_000

    csv_lines = [
        "date,projected,deaths,deathsPerMillion,deathIncrease,deathIncreaseAverage,"
        + "deathIncreasePerMillion,positive,positivePerMillion,positiveIncrease,"
        + "positiveIncreaseAverage,positiveIncreasePerMillion"
    ]

    for i, date in enumerate(data):
        death = date["death"] or 0
        deathIncrease = date["deathIncrease"] or 0
        positive = date["positive"] or 0
        positiveIncrease = date["positiveIncrease"] or 0

        deathIncreaseAvg = (
            round(sum([d["deathIncrease"] for d in data[i - 7 : i]]) / 7)
            if i > 7
            else deathIncrease
        )
        positiveIncreaseAvg = (
            round(sum([d["positiveIncrease"] for d in data[i - 7 : i]]) / 7)
            if i > 7
            else positiveIncrease
        )

        date["deathIncreaseAverage"] = deathIncreaseAvg
        date["positiveIncreaseAverage"] = positiveIncreaseAvg

        csv_lines.append(
            f"{date['date']},false,{death},{round(death/millions)},{deathIncrease},"
            + f"{deathIncreaseAvg},{round(deathIncrease/millions)},{positive},"
            + f"{round(positive/millions)},{positiveIncrease},{positiveIncreaseAvg},"
            + f"{round(positiveIncrease/millions)}"
        )

    avg = (
        (sum([d["deathIncreaseAverage"] for d in data[-7:]]))
        - (sum([d["deathIncreaseAverage"] for d in data[-14:-7]]))
    ) / 49
    daily_death_increase = (
        1 + (avg / data[-1]["deathIncrease"]) if data[-1]["deathIncrease"] > 0 else 1
    )

    avg = (
        (sum([d["positiveIncreaseAverage"] for d in data[-7:]]))
        - (sum([d["positiveIncreaseAverage"] for d in data[-14:-7]]))
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

    for i in range(14):
        date = date + timedelta(1)

        deathIncrease *= daily_death_increase
        positiveIncrease *= daily_positive_increase

        death += deathIncrease
        positive += positiveIncrease

        csv_lines.append(
            f"{int(f'{date:%Y%m%d}')},true,{round(death)},{round(death/millions)},"
            + f"{round(deathIncrease)},{round(deathIncrease)},"
            + f"{round(deathIncrease/millions)},{round(positive)},"
            + f"{round(positive/millions)},{round(positiveIncrease)},"
            + f"{round(positiveIncrease)},{round(positiveIncrease/millions)}"
        )

    with open(f"docs/v1/{state}.csv", "w") as csv:
        csv.write("\n".join(csv_lines))
        csv.write("\n")
        csv.close()
