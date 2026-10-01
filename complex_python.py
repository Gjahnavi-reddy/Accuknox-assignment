"""A non-trivial Python example: resilient concurrent API pipeline."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from statistics import fmean
from time import sleep
from typing import Callable, Iterable

import requests


@dataclass(frozen=True)
class EndpointResult:
    url: str
    item_count: int
    numeric_average: float | None


def get_json_with_retry(
    url: str,
    attempts: int = 3,
    timeout: int = 10
) -> object:
    """Get JSON while retrying temporary failures."""

    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()

        except (requests.RequestException, ValueError) as error:
            last_error = error

            if attempt < attempts - 1:
                sleep(min(2 ** attempt, 4))

    raise RuntimeError(f"Could not fetch {url}: {last_error}")


def inspect_endpoint(
    url: str,
    numeric_field: str | None = None
) -> EndpointResult:

    payload = get_json_with_retry(url)

    items = (
        payload.get("products", [])
        if isinstance(payload, dict)
        else payload
    )

    if not isinstance(items, list):
        raise ValueError(f"Expected a list-like response from {url}")

    values = [
        float(item[numeric_field])
        for item in items
        if numeric_field and numeric_field in item
    ]

    return EndpointResult(
        url,
        len(items),
        fmean(values) if values else None
    )


def run_pipeline(
    tasks: Iterable[tuple[str, str | None]],
    worker: Callable = inspect_endpoint
) -> list[EndpointResult]:

    """Process API inspections concurrently."""

    results: list[EndpointResult] = []

    with ThreadPoolExecutor(max_workers=4) as pool:

        futures = {
            pool.submit(worker, url, field): url
            for url, field in tasks
        }

        for future in as_completed(futures):

            url = futures[future]

            try:
                results.append(future.result())

            except Exception as error:
                print(f"Skipped {url}: {error}")

    return sorted(results, key=lambda result: result.url)


if __name__ == "__main__":

    tasks = [
        ("https://dummyjson.com/products?limit=10", "price"),
        ("https://dummyjson.com/users?limit=10", None)
    ]

    for result in run_pipeline(tasks):
        print(result)