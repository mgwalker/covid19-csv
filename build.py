from datetime import datetime, timedelta
import json
from math import floor, log10
import requests
import numpy
from scipy import stats
from state_data import names, population


def approximate(number):
    if number > 0:
        return round(round(number, 2 - int(floor(log10(number)))))
    return round(number)


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
        + "deathIncreasePerMillion,deathIncreaseAveragePerMillion,positive,"
        + "positivePerMillion,positiveIncrease,positiveIncreaseAverage,"
        + "positiveIncreasePerMillion,positiveIncreaseAveragePerMillion"
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
            + f"{deathIncreaseAvg},{round(deathIncrease/millions)},"
            + f"{round(deathIncreaseAvg/millions)},{positive},"
            + f"{round(positive/millions)},{positiveIncrease},{positiveIncreaseAvg},"
            + f"{round(positiveIncrease/millions)},"
            + f"{round(positiveIncreaseAvg/millions)}"
        )

    def createIncreaseCalculator(field):
        __days = 14
        lastDays = numpy.array([d[field] for d in data[-__days:]])
        (m, b, _, _, _) = stats.linregress(range(__days), lastDays)

        x = __days - 1

        def nextValue():
            nonlocal x
            x += 1
            return round(max(0, m * x + b))

        return nextValue

    nextDeathIncrease = createIncreaseCalculator("deathIncreaseAverage")
    nextPositiveIncrease = createIncreaseCalculator("positiveIncreaseAverage")

    date = datetime.strptime(f'{data[-1]["date"]}', "%Y%m%d")
    death = data[-1]["death"] or 0
    positive = data[-1]["positive"] or 0

    for i in range(14):

        date = date + timedelta(1)

        deathIncrease = nextDeathIncrease()
        positiveIncrease = nextPositiveIncrease()

        death += deathIncrease
        positive += positiveIncrease

        csv_lines.append(
            f"{int(f'{date:%Y%m%d}')},"
            + "true,"
            + f"{approximate(death)},"
            + f"{approximate(death/millions)},"
            + f"{approximate(deathIncrease)},"
            + f"{approximate(deathIncrease)},"
            + f"{approximate(deathIncrease/millions)},"
            + f"{approximate(deathIncrease/millions)},"
            + f"{approximate(positive)},"
            + f"{approximate(positive/millions)},"
            + f"{approximate(positiveIncrease)},"
            + f"{approximate(positiveIncrease)},"
            + f"{approximate(positiveIncrease/millions)},"
            + f"{approximate(positiveIncrease/millions)}"
        )

    with open(f"docs/v1/{state}.csv", "w") as csv:
        csv.write("\n".join(csv_lines))
        csv.write("\n")
        csv.close()
