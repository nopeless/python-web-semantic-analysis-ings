from datetime import datetime, timedelta
import math
import duckduckgo_search
import time
import random


def is_relevant_and_meaningful(body, topic):
    ...


from datetime import datetime, timedelta


def generate_date_intervals(
    start: str | datetime, end: str | datetime, interval: int
) -> [str, str]:
    if isinstance(start, str):
        start_date = datetime.strptime(start, "%Y-%m-%d")
    else:
        start_date = start

    if isinstance(end, str):
        end_date = datetime.strptime(end, "%Y-%m-%d")
    else:
        end_date = end

    while start_date < end_date:
        yield start_date.strftime("%Y-%m-%d"), (
            start_date + timedelta(days=interval)
        ).strftime("%Y-%m-%d")
        start_date += timedelta(days=interval)


def gaussian(x: float, mu: float, sigma: float) -> float:
    """
    explanation:

    example: gaussian(0, 0, 1) = 0.3989422804014327
    """
    return 1 / (sigma * (2 * math.pi) ** 0.5) * math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def filename_safe(s: str) -> str:
    return "".join([c for c in s if c.isalpha() or c.isdigit() or c == " "]).rstrip()


def words_before_limit(s: str, limit: int) -> str:
    """
    Doesn't split in between words
    """
    words = s.split(" ")
    output = ""
    for word in words:
        if not word:
            continue
        if len(output) + len(word) > limit:
            return output
        else:
            output += word + " "
    return output[:-1]


def write(filename: str, content: str):
    with open(filename, "w") as file:
        file.write(content)


def read(filename: str) -> str:
    with open(filename, "r") as file:
        return file.read()


def ddgs_ratelimit_wrapper(func):
    SLEEP_TIME = 0
    MAX_TRIES = 1

    def wrapper(*args, **kwargs):
        tries = 0
        while True:
            if tries >= MAX_TRIES:
                # give up for now
                print("Giving up query: ", args[0])
                return []

            try:
                tries += 1
                return list(func(*args, **kwargs))
            except duckduckgo_search.exceptions.RateLimitException as e:
                print(f"Rate limit exceeded ({tries}). Waiting {SLEEP_TIME} seconds...")
                print("query: ", args[0])
                time.sleep(SLEEP_TIME)

                if isinstance(args, tuple):
                    args = [*args]
                args[0] = args[0] + " "  # Hacky way to avoid rate limiting

    return wrapper


def get_random_user_agent():
    USERAGENTS = [
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,119)}.0.0.0 Safari/537.36",
        f"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,119)}.0.0.0 Safari/537.36",
        f"Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,119)}.0.0.0 Safari/537.36",
        f"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,119)}.0.0.0 Safari/537.36",
    ]

    return random.choice(USERAGENTS)
