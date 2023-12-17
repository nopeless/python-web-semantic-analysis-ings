import os
import json
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timedelta

from src.helpers import read, gaussian, generate_date_intervals

DIRECTORY = "data/3_sentimental_analysis"

SAVE_DIRECTORY = "data/4_aggregate"

SIGMA_BIAS = 2

START_DATE = datetime.strptime("2015-01-01", "%Y-%m-%d")
END_DATE = datetime.strptime("2023-12-31", "%Y-%m-%d")

COLOR_CODES = {
    "reddit.com": "#FF4500",
    "twitter.com": "#1DA1F2",
    None: "#000000",
}

SITE_BIAS_STRAW = {
    "reddit.com": 2,
    "twitter.com": 18,
    None: 1,
}

SITE_BIAS_POLLUTION = {
    "reddit.com": 6,
    "twitter.com": 43,
    None: 1,
}


def resolve_color(site):
    return COLOR_CODES[site]


class SentimentalAnalysis:
    def __init__(
        self,
        query,
        site,
        time_start: datetime,
        time_end: datetime,
        summary: str | None,
        sentiment: int | None,
    ):
        self.query = query
        self.site = site
        self.time_start = time_start
        self.time_end = time_end
        self.summary = summary
        self.sentiment = sentiment

    @staticmethod
    def from_json(j):
        time_start, time_end = j["time_range"].split("..")

        time_start = datetime.strptime(time_start, "%Y-%m-%d")
        time_end = datetime.strptime(time_end, "%Y-%m-%d")

        return SentimentalAnalysis(
            j["query"], j["site"], time_start, time_end, j["summary"], j["sentiment"]
        )


def process_json_files(directory_path):
    sentimental_analysises = []

    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)

            sentimental_analysises.append(
                SentimentalAnalysis.from_json(json.loads(read(file_path)))
            )

    return sentimental_analysises


def populate_plot_data(
    date_start: str, date_end: str, interval: int, data: list[SentimentalAnalysis]
):
    # [date, [pos, neg]]
    plot_points = [
        [date[0], [0, 0]]
        for date in generate_date_intervals(date_start, date_end, interval)
    ]

    for d in data:
        if not d.sentiment:
            continue

        x = (d.time_start + (d.time_end - d.time_start) / 2).timestamp()

        # SD
        sigma = ((d.time_end - d.time_start) / 2).total_seconds() * SIGMA_BIAS

        for date, sentiment in plot_points:
            effect_factor = gaussian(
                x, datetime.strptime(date, "%Y-%m-%d").timestamp(), sigma
            )

            sentiment[0] += (1 + d.sentiment) * effect_factor
            sentiment[1] += (d.sentiment - 1) * effect_factor

            # if d.time_start <= datetime.strptime(date, "%Y-%m-%d") <= d.time_end:
            #     sentiment[0] += 1 + d.sentiment
            #     sentiment[1] += d.sentiment - 1

    return plot_points


import matplotlib.pyplot as plt


def plot_line_charts(data, filter=None, name="line_charts", site_bias=None):
    site_bias = site_bias or (lambda _, q: 1)

    site_query_dict = defaultdict(list)

    for d in data:
        if filter and not filter(d):
            continue
        site_query_dict[(d.site, d.query)].append(d)

    lines = []
    dates = [p[0] for p in populate_plot_data(START_DATE, END_DATE, 30, [])]

    for (site, query), data in site_query_dict.items():
        plot_points = populate_plot_data(START_DATE, END_DATE, 30, data)

        positive_line = [p[1][0] * site_bias(site, query) for p in plot_points]
        negative_line = [p[1][1] * site_bias(site, query) for p in plot_points]

        lines.append((site, query, positive_line))
        lines.append((site, query, negative_line))

    plt.figure(figsize=(40, 10))

    for site, query, plot_points in lines:
        plt.plot(
            dates,
            plot_points,
            color=resolve_color(site),
            linestyle=":" if "pollution" in query else "-",
            label=f"{site or 'General'} - {query}",
        )

    plt.title("Line Charts for Sites and Queries")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.xticks(rotation=45)
    plt.axhline(0, color="black")
    plt.legend()
    plt.savefig(f"{SAVE_DIRECTORY}/{name}.png")


def get_site_bias(x, q):
    if "straw" in q:
        return SITE_BIAS_STRAW[x]
    elif "pollution" in q:
        return SITE_BIAS_POLLUTION[x]
    else:
        return 1


def main():
    for bias_name, bias_algorithm in [
        (" non-biased", lambda x, q: 1),
        ("", get_site_bias),
    ]:
        plot_line_charts(
            process_json_files(DIRECTORY),
            lambda d: "straw" in d.query,
            f"straw{bias_name}",
            bias_algorithm,
        )
        plot_line_charts(
            process_json_files(DIRECTORY),
            lambda d: "pollution" in d.query,
            f"pollution{bias_name}",
            bias_algorithm,
        )

        plot_line_charts(
            process_json_files(DIRECTORY),
            lambda d: True,
            f"everything{bias_name}",
            bias_algorithm,
        )


if __name__ == "__main__":
    main()
