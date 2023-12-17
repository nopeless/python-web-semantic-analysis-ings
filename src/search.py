from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = [r for r in ddgs.text("plastic straws reddit", max_results=5)]
    print(results)
