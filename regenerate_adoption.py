"""
Script to recalculate user adoption from existing metrics in Elasticsearch
"""
from elasticsearch import Elasticsearch
from datetime import datetime
import hashlib
import math

# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])

# Configuration
INDEX_USER_METRICS = "copilot_user_metrics"
INDEX_USER_ADOPTION = "copilot_user_adoption"


def generate_unique_hash(data, key_properties=[]):
    key_elements = []
    for key_property in key_properties:
        value = data.get(key_property)
        key_elements.append(str(value) if value is not None else "")
    key_string = "-".join(key_elements)
    unique_hash = hashlib.sha256(key_string.encode()).hexdigest()
    return unique_hash


def _compute_percentile(sorted_values, percentile):
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (percentile / 100)
    lower = math.floor(k)
    upper = math.ceil(k)
    if lower == upper:
        return float(sorted_values[int(k)])
    lower_value = sorted_values[lower]
    upper_value = sorted_values[upper]
    weight_upper = k - lower
    weight_lower = upper - k
    return float(lower_value) * weight_lower + float(upper_value) * weight_upper


def _robust_scale(value, lower, upper):
    if upper <= lower:
        return 1.0
    return max(0.0, min(1.0, (value - lower) / (upper - lower)))


def fetch_user_metrics():
    """Fetch all user metrics from all organizations"""
    query = {
        "query": {
            "match_all": {}
        },
        "size": 10000,
        "sort": [{"day": {"order": "desc"}}]
    }
    
    result = es.search(index=INDEX_USER_METRICS, body=query)
    metrics = [hit["_source"] for hit in result["hits"]["hits"]]
    print(f"Fetched {len(metrics)} user metrics records")
    return metrics


def build_user_adoption_leaderboard(metrics_data, organization_slug, top_n=10):
    """Calculate adoption scores from metrics data (same logic as main.py)"""
    if not metrics_data:
        return []

    grouped = {}
    report_start_days = set()
    report_end_days = set()

    for record in metrics_data:
        login = record.get("user_login") or "unknown"
        entry = grouped.setdefault(login, {
            "events_logged": 0,
            "volume": 0,
            "code_generation": 0,
            "code_acceptance": 0,
            "loc_added": 0,
            "loc_suggested": 0,
            "agent_usage": 0,
            "chat_usage": 0,
            "days": set(),
        })

        entry["events_logged"] += 1
        entry["volume"] += record.get("user_initiated_interaction_count", 0)
        entry["code_generation"] += record.get("code_generation_activity_count", 0)
        entry["code_acceptance"] += record.get("code_acceptance_activity_count", 0)
        entry["loc_added"] += record.get("loc_added_sum", 0)
        entry["loc_suggested"] += record.get("loc_suggested_to_add_sum", 0)
        if record.get("used_agent"):
            entry["agent_usage"] += 1
        if record.get("used_chat"):
            entry["chat_usage"] += 1
        day_val = record.get("day")
        if day_val:
            entry["days"].add(day_val)

        start_day = record.get("report_start_day")
        if start_day:
            report_start_days.add(start_day)
        end_day = record.get("report_end_day")
        if end_day:
            report_end_days.add(end_day)

    global_start_day = min(report_start_days) if report_start_days else None
    global_end_day = max(report_end_days) if report_end_days else None

    summaries = []
    for login, stats in grouped.items():
        active_days = len(stats["days"])
        interaction_per_day = (
            stats["volume"] / active_days if active_days else 0.0
        )
        acceptance_rate = (
            stats["code_acceptance"] / stats["code_generation"]
            if stats["code_generation"]
            else 0.0
        )
        average_loc_added = (
            stats["loc_added"] / active_days if active_days else 0.0
        )
        feature_breadth = stats["agent_usage"] + stats["chat_usage"]

        # Stamp a day for Grafana time filtering
        stamped_day = (
            global_end_day if global_end_day else datetime.utcnow().strftime("%Y-%m-%d")
        )

        summary = {
            "user_login": login,
            "organization_slug": organization_slug,
            "slug_type": "Standalone",
            "events_logged": stats["events_logged"],
            "volume": stats["volume"],
            "code_generation_activity_count": stats["code_generation"],
            "code_acceptance_activity_count": stats["code_acceptance"],
            "loc_added_sum": stats["loc_added"],
            "loc_suggested_to_add_sum": stats["loc_suggested"],
            "average_loc_added": average_loc_added,
            "interactions_per_day": interaction_per_day,
            "acceptance_rate": acceptance_rate,
            "feature_breadth": feature_breadth,
            "agent_usage": stats["agent_usage"],
            "chat_usage": stats["chat_usage"],
            "active_days": active_days,
            "report_start_day": global_start_day,
            "report_end_day": global_end_day,
            "day": stamped_day,
            "bucket_type": "user",
            "is_top10": False,
            "rank": None,
        }

        summary["unique_hash"] = generate_unique_hash(
            summary,
            key_properties=[
                "organization_slug",
                "user_login",
                "report_start_day",
                "report_end_day",
                "bucket_type",
            ],
        )

        summaries.append(summary)

    if not summaries:
        return []

    # Calculate percentile bounds for robust scaling
    signals = {
        "volume": [entry["volume"] for entry in summaries],
        "interactions_per_day": [entry["interactions_per_day"] for entry in summaries],
        "acceptance_rate": [entry["acceptance_rate"] for entry in summaries],
        "average_loc_added": [entry["average_loc_added"] for entry in summaries],
        "feature_breadth": [entry["feature_breadth"] for entry in summaries],
    }

    bounds = {}
    for key, values in signals.items():
        sorted_values = sorted(values)
        lower = _compute_percentile(sorted_values, 5)
        upper = _compute_percentile(sorted_values, 95)
        bounds[key] = (lower, upper)

    # Calculate base scores with normalized components
    for entry in summaries:
        norm_volume = _robust_scale(entry["volume"], *bounds["volume"])
        norm_interactions = _robust_scale(
            entry["interactions_per_day"], *bounds["interactions_per_day"]
        )
        norm_acceptance = _robust_scale(
            entry["acceptance_rate"], *bounds["acceptance_rate"]
        )
        norm_loc_added = _robust_scale(
            entry["average_loc_added"], *bounds["average_loc_added"]
        )
        norm_feature = _robust_scale(
            entry["feature_breadth"], *bounds["feature_breadth"]
        )

        base_score = (
            0.2 * norm_volume
            + 0.2 * norm_interactions
            + 0.2 * norm_acceptance
            + 0.2 * norm_loc_added
            + 0.2 * norm_feature
        )
        entry["_base_score"] = base_score

    # Add consistency bonus
    max_active_days = max(entry["active_days"] for entry in summaries)
    for entry in summaries:
        bonus = 0.1 * (entry["active_days"] / max_active_days) if max_active_days else 0.0
        bonus = min(bonus, 0.1)
        entry["consistency_bonus"] = bonus
        entry["adoption_score"] = entry["_base_score"] * (1 + bonus)

    # Convert to percentage (0-100)
    max_score = max(entry["adoption_score"] for entry in summaries)
    for entry in summaries:
        entry["adoption_pct"] = (
            round(entry["adoption_score"] / max_score * 100, 1)
            if max_score
            else 0.0
        )

    # Sort and mark top 10
    summaries.sort(key=lambda e: e["adoption_pct"], reverse=True)
    leaderboard = summaries[:top_n]
    for rank, entry in enumerate(leaderboard, start=1):
        entry["rank"] = rank
        entry["is_top10"] = True

    entries = []
    for entry in leaderboard:
        entry["bucket_type"] = "user"
        entries.append(entry)

    # Create "Others" aggregate
    others = summaries[top_n:]
    if others:
        others_count = len(others)
        stamped_day = (
            global_end_day if global_end_day else datetime.utcnow().strftime("%Y-%m-%d")
        )

        others_entry = {
            "user_login": "Others",
            "organization_slug": organization_slug,
            "slug_type": "Standalone",
            "events_logged": sum(o["events_logged"] for o in others),
            "volume": sum(o["volume"] for o in others),
            "code_generation_activity_count": sum(
                o["code_generation_activity_count"] for o in others
            ),
            "code_acceptance_activity_count": sum(
                o["code_acceptance_activity_count"] for o in others
            ),
            "loc_added_sum": sum(o["loc_added_sum"] for o in others),
            "loc_suggested_to_add_sum": sum(
                o["loc_suggested_to_add_sum"] for o in others
            ),
            "average_loc_added": sum(o["average_loc_added"] for o in others) / others_count,
            "interactions_per_day": sum(
                o["interactions_per_day"] for o in others
            )
            / others_count,
            "acceptance_rate": sum(o["acceptance_rate"] for o in others) / others_count,
            "feature_breadth": sum(o["feature_breadth"] for o in others) / others_count,
            "agent_usage": sum(o["agent_usage"] for o in others),
            "chat_usage": sum(o["chat_usage"] for o in others),
            "active_days": sum(o["active_days"] for o in others),
            "report_start_day": global_start_day,
            "report_end_day": global_end_day,
            "day": stamped_day,
            "bucket_type": "others",
            "is_top10": False,
            "rank": None,
            "others_count": others_count,
            "consistency_bonus": 0.0,
        }

        others_entry["adoption_score"] = (
            sum(o["adoption_score"] for o in others) / others_count
        )
        score_scale = max_score if max_score else 1
        others_entry["adoption_pct"] = round(
            others_entry["adoption_score"] / score_scale * 100, 1
        )
        others_entry["unique_hash"] = generate_unique_hash(
            others_entry,
            key_properties=[
                "organization_slug",
                "user_login",
                "report_start_day",
                "report_end_day",
                "bucket_type",
            ],
        )
        entries.append(others_entry)

    # Clean up internal fields
    for entry in entries:
        entry.pop("_base_score", None)
        
    return entries


def write_to_adoption_index(adoption_entries):
    """Write adoption entries to Elasticsearch"""
    print(f"Writing {len(adoption_entries)} adoption entries to {INDEX_USER_ADOPTION}...")
    
    for entry in adoption_entries:
        # Add @timestamp for Grafana time filtering
        entry["@timestamp"] = datetime.utcnow().isoformat()
        
        # Use unique_hash as document ID
        doc_id = entry["unique_hash"]
        
        try:
            es.index(index=INDEX_USER_ADOPTION, id=doc_id, document=entry)
            print(f"  ✓ {entry['user_login']}: {entry['adoption_pct']}%")
        except Exception as e:
            print(f"  ✗ Failed to write {entry['user_login']}: {e}")
    
    print(f"Successfully wrote {len(adoption_entries)} adoption entries")


def main():
    print("="*60)
    print("Recalculating User Adoption from Existing Metrics")
    print("="*60)
    
    # Fetch all user metrics
    all_metrics = fetch_user_metrics()
    
    if not all_metrics:
        print("No metrics data found. Cannot calculate adoption.")
        return
    
    # Group by organization
    orgs = {}
    for metric in all_metrics:
        org = metric.get("organization_slug", "unknown")
        if org not in orgs:
            orgs[org] = []
        orgs[org].append(metric)
    
    print(f"Found {len(orgs)} organizations: {', '.join(orgs.keys())}")
    
    # Calculate adoption for each organization
    all_adoption_entries = []
    for org_slug, metrics_data in orgs.items():
        print(f"\nProcessing {org_slug}...")
        adoption_entries = build_user_adoption_leaderboard(
            metrics_data, 
            org_slug,
            top_n=10
        )
        all_adoption_entries.extend(adoption_entries)
    
    if not all_adoption_entries:
        print("No adoption entries generated.")
        return
    
    # Write all to Elasticsearch
    write_to_adoption_index(all_adoption_entries)
    
    print("="*60)
    print("✓ Adoption data regenerated successfully!")
    print(f"  Total entries: {len(all_adoption_entries)}")
    print(f"  Organizations: {len(orgs)}")
    print("="*60)


if __name__ == "__main__":
    main()
