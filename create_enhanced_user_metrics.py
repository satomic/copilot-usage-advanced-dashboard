#!/usr/bin/env python3
"""Download the latest Copilot user metrics and summarize the returned records."""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from typing import Mapping, Sequence

import requests
import json


def get_download_links(api_url: str, github_token: str) -> Sequence[str]:
	headers = {
		"Accept": "application/vnd.github+json",
		"Authorization": f"Bearer {github_token}",
		"X-GitHub-Api-Version": "2022-11-28",
	}
	response = requests.get(api_url, headers=headers, timeout=30)
	response.raise_for_status()
	payload = response.json()
	return payload.get("download_links", [])


def parse_ndjson(payload: str, link: str) -> Sequence[Mapping]:
	records: list[Mapping] = []
	for line in payload.splitlines():
		if not line.strip():
			continue
		records.append(json.loads(line))
	if not records:
		raise ValueError(f"download link {link} returned no valid records")
	return records


def fetch_metrics(json_url: str) -> Sequence[Mapping]:
	response = requests.get(json_url, headers={"Accept": "application/json"}, timeout=30)
	response.raise_for_status()
	text = response.text.strip()
	if not text:
		raise ValueError(f"download link {json_url} returned empty payload")
	try:
		data = json.loads(text)
	except json.JSONDecodeError:
		return parse_ndjson(text, json_url)
	if isinstance(data, list):
		return data
	if isinstance(data, dict):
		return [data]
	raise ValueError(f"download link {json_url} returned unexpected payload {type(data)}")


def build_doc_id(record: Mapping) -> str:
	if (unique := record.get("unique_hash")):
		return unique
	day = record.get("day", "").replace(" ", "_")
	user = record.get("user_login", "unknown")
	return f"{user}::{day}"


def write_to_es(es_url: str, index: str, records: Sequence[Mapping]) -> None:
	es_url = es_url.rstrip("/")
	headers = {"Content-Type": "application/json"}
	for record in records:
		doc_id = build_doc_id(record)
		record["last_updated_at"] = datetime.now(timezone.utc).isoformat()
		url = f"{es_url}/{index}/_doc/{doc_id}"
		resp = requests.put(url, headers=headers, json=record, timeout=30)
		resp.raise_for_status()


def summarize(records: Sequence[Mapping]) -> Mapping[str, object]:
	total = 0
	usernames = set()
	last_updated = None
	for row in records:
		total += 1
		if (user := row.get("user_login")):
			usernames.add(user)
		last_updated = row.get("last_updated_at") or last_updated
	return {
		"total_records": total,
		"unique_users": len(usernames),
		"usernames": sorted(usernames),
		"last_updated_at": last_updated,
	}


def load_token(prm_token: str | None) -> str:
	if prm_token:
		return prm_token
	token = os.environ.get("GITHUB_TOKEN")
	if not token:
		raise SystemExit("GitHub token must be provided via --token or GITHUB_TOKEN environment variable")
	return token


def main() -> None:
	logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
	parser = argparse.ArgumentParser(description="Download latest Copilot user metrics data")
	parser.add_argument(
		"--org",
		default="octodemo-copilot-standalone",
		help="Enterprise slug for the API endpoint",
	)
	parser.add_argument(
		"--token",
		help="GitHub token with Copilot metrics permission (defaults to GITHUB_TOKEN env var)",
	)
	parser.add_argument(
		"--insert-to-es",
		action="store_true",
		help="Also insert the fetched records into Elasticsearch",
	)
	parser.add_argument(
		"--es-url",
		default="http://localhost:9200",
		help="Elasticsearch endpoint (default http://localhost:9200)",
	)
	parser.add_argument(
		"--es-index",
		default="copilot_user_metrics",
		help="Elasticsearch index to write to",
	)
	args = parser.parse_args()

	api_url = (
		f"https://api.github.com/enterprises/{args.org}/copilot/metrics/reports/users-28-day/latest"
	)
	token = load_token(args.token)
	download_links = get_download_links(api_url, token)
	if not download_links:
		logging.warning("No download links returned from the user metrics API")
		raise SystemExit(1)

	all_records: list[Mapping] = []
	for idx, link in enumerate(download_links, start=1):
		logging.info("downloading link %d/%d", idx, len(download_links))
		batch = fetch_metrics(link)
		logging.info("link %d returned %d records", idx, len(batch))
		all_records.extend(batch)

	summary = summarize(all_records)
	print("\nUser Metrics Summary")
	print(f"  API URL:      {api_url}")
	print(f"  Records:      {summary['total_records']}")
	print(f"  Unique users: {summary['unique_users']}")
	if summary["last_updated_at"]:
		print(f"  Last update:  {summary['last_updated_at']}")
	print("  Usernames:")
	for username in summary["usernames"]:
		print(f"    - {username}")

	if args.insert_to_es:
		logging.info("Writing %d records into Elasticsearch", summary["total_records"])
		write_to_es(args.es_url, args.es_index, all_records)
		logging.info("Finished inserting records into %s/%s", args.es_url, args.es_index)


if __name__ == "__main__":
	main()
