"""Create a compact, day-wise "top-by" index for user drill-down.

Source index: copilot_user_metrics (one doc per user/day)
Dest index:   copilot_user_metrics_top_by_day (one doc per user/day)

Each destination doc stores the TOP item within each nested totals_by_* array
for that user/day.

We compute an internal activity score to select the top item:

    score = code_generation_activity_count + user_initiated_interaction_count + code_acceptance_activity_count

But we do NOT persist the score in the destination document (only the labels).
"""

from __future__ import annotations

import os
import logging
from typing import Any, Iterable

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)


DEFAULT_SOURCE_INDEX = os.getenv("INDEX_USER_METRICS", "copilot_user_metrics")
DEFAULT_DEST_INDEX = os.getenv("INDEX_USER_METRICS_TOP_BY_DAY", "copilot_user_metrics_top_by_day")


def get_es_client() -> Elasticsearch:
    # es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    # es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    # es_url = f"http://{es_host}:{es_port}"
    es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

    es_user = os.getenv("ELASTICSEARCH_USER")
    es_password = os.getenv("ELASTICSEARCH_PASS")

    if es_user and es_password:
        logger.info(f"Connecting to Elasticsearch at {es_url} with authentication")
        return Elasticsearch([es_url], basic_auth=(es_user, es_password))

    logger.info(f"Connecting to Elasticsearch at {es_url} without authentication")
    return Elasticsearch([es_url])


def ensure_dest_index(es: Elasticsearch, index_name: str) -> None:
    if es.indices.exists(index=index_name):
        return

    es.indices.create(
        index=index_name,
        body={
            "mappings": {
                "properties": {
                    "day": {"type": "date"},
                    "user_login": {"type": "keyword"},
                    "organization_slug": {"type": "keyword"},
                    "enterprise_id": {"type": "keyword"},
                    "top_ide": {"type": "keyword"},
                    "top_feature": {"type": "keyword"},
                    "top_language_feature": {"type": "keyword"},
                    "top_language_model": {"type": "keyword"},
                    "top_model_feature": {"type": "keyword"},
                }
            }
        },
    )
    logger.info(f"Created index: {index_name}")


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def activity_score(entry: dict[str, Any]) -> int:
    return (
        _safe_int(entry.get("code_generation_activity_count"))
        + _safe_int(entry.get("user_initiated_interaction_count"))
        + _safe_int(entry.get("code_acceptance_activity_count"))
    )


def _pick_top(entries: Iterable[dict[str, Any]], key_fn) -> str | None:
    best_value: str | None = None
    best_score = -1
    for entry in entries or []:
        value = key_fn(entry)
        if not value:
            continue
        score = activity_score(entry)
        if score > best_score:
            best_score = score
            best_value = value
    return best_value


def build_top_doc(source_doc: dict[str, Any]) -> dict[str, Any] | None:
    day = source_doc.get("day")
    user_login = source_doc.get("user_login")
    if not day or not user_login:
        return None

    base = {
        "day": day,
        "user_login": user_login,
        "organization_slug": source_doc.get("organization_slug"),
        "enterprise_id": str(source_doc.get("enterprise_id")) if source_doc.get("enterprise_id") is not None else None,
    }

    ide = _pick_top(source_doc.get("totals_by_ide", []), lambda e: e.get("ide"))
    feature = _pick_top(source_doc.get("totals_by_feature", []), lambda e: e.get("feature"))
    lang_feat = _pick_top(
        source_doc.get("totals_by_language_feature", []),
        lambda e: f"{e.get('language', 'unknown')}|{e.get('feature', 'unknown')}",
    )
    lang_model = _pick_top(
        source_doc.get("totals_by_language_model", []),
        lambda e: f"{e.get('language', 'unknown')}|{e.get('model', 'unknown')}",
    )
    model_feat = _pick_top(
        source_doc.get("totals_by_model_feature", []),
        lambda e: f"{e.get('model', 'unknown')}|{e.get('feature', 'unknown')}",
    )

    return {
        **base,
        "top_ide": ide or "unknown",
        "top_feature": feature or "unknown",
        "top_language_feature": lang_feat or "unknown|unknown",
        "top_language_model": lang_model or "unknown|unknown",
        "top_model_feature": model_feat or "unknown|unknown",
    }


def create_user_top_by_day(source_index: str = DEFAULT_SOURCE_INDEX, dest_index: str = DEFAULT_DEST_INDEX) -> int:
    es = get_es_client()
    ensure_dest_index(es, dest_index)

    query = {
        "sort": [{"day": "asc"}],
        "query": {"match_all": {}},
    }

    # Use a scroll to handle larger datasets.
    page_size = 500
    resp = es.search(index=source_index, body={**query, "size": page_size}, scroll="2m")
    scroll_id = resp.get("_scroll_id")
    hits = resp.get("hits", {}).get("hits", [])

    total_written = 0

    def flush(actions: list[dict[str, Any]]) -> int:
        if not actions:
            return 0
        ok, _ = bulk(es, actions, raise_on_error=False, request_timeout=60)
        return int(ok)

    actions: list[dict[str, Any]] = []

    while hits:
        for hit in hits:
            source_doc = hit.get("_source", {})
            doc = build_top_doc(source_doc)
            if doc is None:
                continue
            doc_id = f"{doc.get('user_login')}|{doc.get('day')}"
            actions.append({"_op_type": "index", "_index": dest_index, "_id": doc_id, "_source": doc})

            if len(actions) >= 2000:
                total_written += flush(actions)
                actions = []

        resp = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = resp.get("_scroll_id")
        hits = resp.get("hits", {}).get("hits", [])

    if actions:
        total_written += flush(actions)

    try:
        if scroll_id:
            es.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass

    logger.info(f"Created/updated {total_written} top-by-day docs in {dest_index}")
    return total_written


if __name__ == "__main__":
    create_user_top_by_day()
