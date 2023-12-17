from duckduckgo_search import DDGS
from src.helpers import (
    generate_date_intervals,
    filename_safe,
    read,
    write,
    words_before_limit,
    ddgs_ratelimit_wrapper,
    get_random_user_agent,
)
from src.sentimental_analysis import (
    generate_readable,
    check_relevance,
    sentimental_analysis,
)
from itertools import product
import shutil
import os
import json
import time
import httpx

# Half a year
DATE_INTERVAL = 182
DATE_START = "2015-01-01"
DATE_END = "2023-12-31"
SEARCH_BATCH_SIZE = 20

SEARCH_OBJECTS_DIR = "data/1_search_objects"
SCRAPED_WEBSITES_DIR = "data/2_scraped_websites"
SENTIMENTAL_ANALYSIS_DIR = "data/3_sentimental_analysis"
AGGREGATE_DIR = "data/4_aggregate"

# Explicit website searches
WEBSITES = [
    None,
    "reddit.com",
    "twitter.com",
]
QUERIES = ["plastic straws", "plastic pollution"]

ANALYSIS_TOPIC_GUARD = (
    "plastic straws' impact on daily life, industry, or the environment"
)
ANALYSIS_SENTIMENT_EVALUATION = "banning plastic straws"

# Limit to 8000 characters for openai api
CHAR_LIMIT = 8000


HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://duckduckgo.com/",
}


# Purge all directories
def pipeline_purge():
    for dir in [
        SEARCH_OBJECTS_DIR,
        SCRAPED_WEBSITES_DIR,
        SENTIMENTAL_ANALYSIS_DIR,
        AGGREGATE_DIR,
    ]:
        shutil.rmtree(dir, ignore_errors=True)
        os.mkdir(dir)


# Fetch all searches
def pipeline_search():
    existing_files = [
        json.loads(read(f"{SEARCH_OBJECTS_DIR}/{filename}"))
        for filename in os.listdir(SEARCH_OBJECTS_DIR)
    ]

    for s, e in generate_date_intervals(DATE_START, DATE_END, DATE_INTERVAL):
        with DDGS() as ddgs:
            search = ddgs_ratelimit_wrapper(ddgs.text)

            for website, query in product(WEBSITES, QUERIES):
                # time.sleep(2)

                # Force refresh client to avoid rate limiting
                ddgs._client = httpx.Client(
                    headers={**HEADERS, "User-Agent": get_random_user_agent()},
                    proxies=None,
                    timeout=10,
                    http2=True,
                    verify=False,
                )

                site_query = ""

                if website:
                    site_query = f"site:{website} "

                # if exists, skip
                if any(
                    result["query"] == query
                    and result["site"] == website
                    and result["time_range"] == f"{s}..{e}"
                    for result in existing_files
                ):
                    print("Skipping: ", query, website, f"{s}..{e}")
                    continue

                for result in search(
                    f"{site_query}{query}",
                    max_results=SEARCH_BATCH_SIZE,
                    timelimit=f"{s}..{e}",
                ):
                    write(
                        f"{SEARCH_OBJECTS_DIR}/{s}_{e} {words_before_limit(filename_safe(result['title']), 40).strip()}.json",
                        json.dumps(
                            {
                                "query": query,
                                "site": website,
                                "time_range": f"{s}..{e}",
                                **result,
                            },
                            indent=2,
                        ),
                    )


def pipeline_scrape():
    os.system(f"node src/scraper.js {SEARCH_OBJECTS_DIR} {SCRAPED_WEBSITES_DIR}")


def pipeline_sentimental_analysis():
    existing_files = [
        json.loads(read(f"{SENTIMENTAL_ANALYSIS_DIR}/{filename}"))
        for filename in os.listdir(SENTIMENTAL_ANALYSIS_DIR)
        if filename.endswith(".json")
    ]

    for filename in os.listdir(SCRAPED_WEBSITES_DIR):
        web_info = json.loads(read(f"{SCRAPED_WEBSITES_DIR}/{filename}"))

        # if exists, skip
        if any(exist["href"] == web_info["href"] for exist in existing_files):
            print("Skipping: ", filename)
            continue

        if not web_info["textContent"]:
            print(f"No text content found for {filename}, skipping...")
            continue

        summary = None
        sentiment = None

        readable_content = generate_readable(web_info["textContent"][:CHAR_LIMIT])

        if check_relevance(readable_content, ANALYSIS_TOPIC_GUARD):
            packed = sentimental_analysis(
                readable_content, ANALYSIS_SENTIMENT_EVALUATION
            )

            if not packed:
                print(f"Skipping {filename} due to failed parse")
                continue

            summary, sentiment = packed

        del web_info["textContent"]

        write(
            f"{SENTIMENTAL_ANALYSIS_DIR}/{filename}",
            json.dumps(
                {
                    **web_info,
                    "readable_content": readable_content,
                    "summary": summary,
                    "sentiment": sentiment,
                },
                indent=2,
            ),
        )

        print(f"Completed {filename}")


# Write all searches to file
# pipeline_purge()
# pipeline_search()
# pipeline_scrape()
# pipeline_sentimental_analysis()
