import json
import requests
import os
import hashlib
import math
from elasticsearch import Elasticsearch, NotFoundError
from datetime import datetime, timedelta
from log_utils import configure_logger, current_time
import time
from metrics_2_usage_convertor import convert_metrics_to_usage
import traceback
from zoneinfo import ZoneInfo


def get_utc_offset():
    tz_name = os.environ.get("TZ", "GMT")
    try:
        local_tz = ZoneInfo(tz_name)
    except Exception:
        local_tz = ZoneInfo("GMT")
    now = datetime.now(local_tz)
    offset_sec = now.utcoffset().total_seconds()
    offset_hours = int(offset_sec // 3600)
    offset_minutes = int((offset_sec % 3600) // 60)
    offset_str = f"{offset_hours:+03}:{abs(offset_minutes):02}"
    return offset_str


class Paras:

    @staticmethod
    def date_str():
        return current_time()[:10]

    # GitHub
    github_pat = os.getenv("GITHUB_PAT")
    organization_slugs = os.getenv("ORGANIZATION_SLUGS")

    # ElasticSearch
    primary_key = os.getenv("PRIMARY_KEY", "unique_hash")
    elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://$ELASTICSEARCH_URL")
    elasticsearch_user = os.getenv("ELASTICSEARCH_USER", None)
    elasticsearch_pass = os.getenv("ELASTICSEARCH_PASS", None)

    # Log path
    log_path = os.getenv("LOG_PATH", "logs")

    @staticmethod
    def get_log_path():
        return os.path.join(Paras.log_path, Paras.date_str())

    # Execution interval HOURS
    execution_interval = int(os.getenv("EXECUTION_INTERVAL", 6))


class Indexes:
    index_seat_info = os.getenv("INDEX_SEAT_INFO", "copilot_seat_info_settings")
    index_seat_assignments = os.getenv(
        "INDEX_SEAT_ASSIGNMENTS", "copilot_seat_assignments"
    )
    index_name_total = os.getenv("INDEX_NAME_TOTAL", "copilot_usage_total")
    index_name_breakdown = os.getenv("INDEX_NAME_BREAKDOWN", "copilot_usage_breakdown")
    index_name_breakdown_chat = os.getenv(
        "INDEX_NAME_BREAKDOWN_CHAT", "copilot_usage_breakdown_chat"
    )
    index_user_metrics = os.getenv("INDEX_USER_METRICS", "copilot_user_metrics")
    index_user_adoption = os.getenv("INDEX_USER_ADOPTION", "copilot_user_adoption")


logger = configure_logger(log_path=Paras.log_path)
logger.info("-----------------Starting-----------------")


# Validate github_pat and organization_slugs, if not present, log an error and exit
if not Paras.github_pat:
    logger.error("GitHub PAT not found, exiting...")
    exit(1)

if not Paras.organization_slugs:
    logger.error("Organization slugs not found, exiting...")
    exit(1)


def github_api_request_handler(url, error_return_value=[]):
    logger.info(f"Requesting URL: {url}")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {Paras.github_pat}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code} error for URL: {url}")
            logger.error(f"Response text: {response.text}")
            return error_return_value
        
        data = response.json()
        logger.info(f"Successfully received data from: {url}")
        
        if isinstance(data, dict) and data.get("status", "200") != "200":
            logger.error(f"Request failed reason: {data}")
            return error_return_value
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception for URL {url}: {e}")
        return error_return_value
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for URL {url}: {e}")
        return error_return_value


def dict_save_to_json_file(
    data, file_name, logs_path=Paras.get_log_path(), save_to_json=True
):
    if not data:
        logger.warning(f"No data to save for {file_name}")
        return
    if save_to_json:
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
        with open(
            f"{logs_path}/{file_name}_{Paras.date_str()}.json", "w", encoding="utf8"
        ) as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Data saved to {logs_path}/{file_name}_{Paras.date_str()}.json")


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


def build_user_adoption_leaderboard(metrics_data, organization_slug, slug_type, top_n=10):
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

        summary = {
            "user_login": login,
            "organization_slug": organization_slug,
            "slug_type": slug_type,
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

    max_active_days = max(entry["active_days"] for entry in summaries)
    for entry in summaries:
        bonus = 0.1 * (entry["active_days"] / max_active_days) if max_active_days else 0.0
        bonus = min(bonus, 0.1)
        entry["consistency_bonus"] = bonus
        entry["adoption_score"] = entry["_base_score"] * (1 + bonus)

    max_score = max(entry["adoption_score"] for entry in summaries)
    for entry in summaries:
        entry["adoption_pct"] = (
            round(entry["adoption_score"] / max_score * 100, 1)
            if max_score
            else 0.0
        )

    summaries.sort(key=lambda e: e["adoption_pct"], reverse=True)
    leaderboard = summaries[:top_n]
    for rank, entry in enumerate(leaderboard, start=1):
        entry["rank"] = rank
        entry["is_top10"] = True

    entries = []
    for entry in leaderboard:
        entry["bucket_type"] = "user"
        entries.append(entry)

    others = summaries[top_n:]
    if others:
        others_count = len(others)
        others_entry = {
            "user_login": "Others",
            "organization_slug": organization_slug,
            "slug_type": slug_type,
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

    for entry in entries:
        entry.pop("_base_score", None)
    return entries

def assign_position_in_tree(nodes):
    # Create a dictionary with node id as key and node data as value
    node_dict = {node["id"]: node for node in nodes}

    # Create sets to store all node ids and child node ids
    all_ids = set(node_dict.keys())
    child_ids = set()

    # Build parent-child relationships
    for node in nodes:
        parent = node.get("parent")
        if parent and "id" in parent:
            parent_id = parent["id"]
            child_ids.add(node["id"])
            # Add child node list to parent node
            parent_node = node_dict.get(parent_id)
            if parent_node:
                parent_node.setdefault("children", []).append(node["id"])

    # Find root nodes (nodes that are not child nodes)
    root_ids = all_ids - child_ids

    # Mark the position of all nodes
    for node_id in all_ids:
        node = node_dict[node_id]
        children = node.get("children", [])
        if not children:
            node["position_in_tree"] = "leaf_team"
        elif node_id in root_ids:
            node["position_in_tree"] = "root_team"
        else:
            node["position_in_tree"] = "trunk_team"

    return nodes


class GitHubEnterpriseManager:

    # Question: Teams under the same Enterprise can be duplicated in different orgs, so isn't there a problem with the API like this?
    # https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-an-enterprise-team

    def __init__(self, token, enterprise_slug, save_to_json=True):
        self.token = token
        self.enterprise_slug = enterprise_slug
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
        }
        self.url = "https://api.github.com/graphql"
        self.orgs = self._fetch_all_organizations(save_to_json=save_to_json)
        self.orgs_slugs = [org["login"] for org in self.orgs]
        self.github_organization_managers = {
            orgs_slug: GitHubOrganizationManager(self.token, orgs_slug)
            for orgs_slug in self.orgs_slugs
        }
        logger.info(
            f"Initialized GitHubEnterpriseManager for enterprise: {enterprise_slug}"
        )

    def _fetch_all_organizations(self, save_to_json=False):

        # GraphQL query
        query = (
            """
        {
            enterprise(slug: "%s") {
                organizations(first: 100) {
                    nodes {
                        login
                        name
                        description
                        email
                        isVerified
                        location
                        websiteUrl
                        createdAt
                        updatedAt
                        membersWithRole {
                            totalCount
                        }
                        teams {
                            totalCount
                        }
                        repositories {
                            totalCount
                        }
                    }
                }
            }
        }
        """
            % self.enterprise_slug
        )

        # Send POST request
        logger.info(
            f"Fetching all organizations for enterprise: {self.enterprise_slug}"
        )
        response = requests.post(self.url, json={"query": query}, headers=self.headers)

        # Check response status code
        if response.status_code == 200:
            data = response.json()
            # print(data)
            if "errors" in data:
                print(f'query failed, error message: {data["errors"][0]["message"]}')
                return {}
            all_orgs = (
                data["data"]
                .get("enterprise", {})
                .get("organizations", {})
                .get("nodes", [])
            )

            dict_save_to_json_file(
                all_orgs,
                f"{self.enterprise_slug}_all_organizations",
                save_to_json=save_to_json,
            )
            logger.info(f"Fetched {len(all_orgs)} organizations")
            return all_orgs
        else:
            print(f"request failed, error code: {response.status_code}")
            logger.error(f"Request failed with status code: {response.status_code}")
            return {}


class GitHubOrganizationManager:

    def __init__(self, organization_slug, save_to_json=True, is_standalone=False):
        self.slug_type = "Standalone" if is_standalone else "Organization"
        self.api_type = "enterprises" if is_standalone else "orgs"
        self.organization_slug = organization_slug
        self.teams = self._fetch_all_teams(save_to_json=save_to_json)
        self.utc_offset = get_utc_offset()
        logger.info(
            f"Initialized GitHubOrganizationManager for {self.slug_type}: {organization_slug}"
        )

    def get_copilot_usages(
        self,
        team_slug="all",
        save_to_json=True,
        position_in_tree="leaf_team",
        usage_or_metrics="metrics",
    ):
        urls = {
            self.organization_slug,
            (
                position_in_tree,
                f"https://api.github.com/{self.api_type}/{self.organization_slug}/copilot/{usage_or_metrics}",
            ),
        }
        if team_slug:
            if team_slug != "all":
                urls = {
                    team_slug: (
                        position_in_tree,
                        f"https://api.github.com/{self.api_type}/{self.organization_slug}/team/{team_slug}/copilot/{usage_or_metrics}",
                    )
                }
            else:
                if self.teams:
                    logger.info(
                        f"Fetching Copilot usages for all teams, team count: {len(self.teams)}"
                    )
                    urls = {
                        team["slug"]: (
                            team["position_in_tree"],
                            f"https://api.github.com/{self.api_type}/{self.organization_slug}/team/{team['slug']}/copilot/{usage_or_metrics}",
                        )
                        for team in self.teams
                    }

                    # add root team in case teams are too small
                    urls.update(
                        {
                            "no-team": (
                                "root_team",
                                f"https://api.github.com/{self.api_type}/{self.organization_slug}/copilot/{usage_or_metrics}",
                            )
                        }
                    )
                else:
                    logger.info(
                        f"No teams found for {self.slug_type}: {self.organization_slug}, fetching {self.slug_type} usage. mock team slug: no-team. strongly recommend to create teams for the {self.slug_type} to get more accurate data."
                    )
                    urls = {
                        "no-team": (
                            "root_team",
                            f"https://api.github.com/{self.api_type}/{self.organization_slug}/copilot/{usage_or_metrics}",
                        )
                    }

        datas = {}
        logger.info(
            f"Fetching Copilot usages for {self.slug_type}: {self.organization_slug}, team: {team_slug}"
        )
        for _team_slug, position_in_tree_and_url in urls.items():
            position_in_tree, url = position_in_tree_and_url
            data = github_api_request_handler(url, error_return_value={})
            dict_save_to_json_file(
                data,
                f"{self.organization_slug}_{_team_slug}_copilot_metrics",
                save_to_json=save_to_json,
            )
            data = convert_metrics_to_usage(data)
            dict_save_to_json_file(
                data,
                f"{self.organization_slug}_{_team_slug}_copilot_usage",
                save_to_json=save_to_json,
            )
            datas[_team_slug] = {
                "position_in_tree": position_in_tree,
                "copilot_usage_data": data,
            }
            logger.info(f"Fetched Copilot usage for team: {_team_slug}")

        if team_slug == "all":
            dict_save_to_json_file(
                datas,
                f"{self.organization_slug}_all_teams_copilot_usage",
                save_to_json=save_to_json,
            )

        return datas

    def get_seat_info_settings_standalone(self, save_to_json=True):
        # only for Standalone
        # todo: no API for Standalone, need to caculate the data from other APIs
        url = f"https://api.github.com/{self.api_type}/{self.organization_slug}/copilot/billing/seats"
        data_seats = github_api_request_handler(url, error_return_value={})
        if not data_seats:
            return data_seats

        data = {
            "seat_management_setting": "assign_selected",
            "public_code_suggestions": "allow",
            "ide_chat": "enabled",
            "cli": "enabled",
            "plan_type": "business",
            "seat_total": data_seats.get("total_seats", 0),
            "seat_added_this_cycle": 0,  # caculated
            "seat_pending_invitation": 0,  # always 0
            "seat_pending_cancellation": 0,  # caculated
            "seat_active_this_cycle": 0,  # caculated
            "seat_inactive_this_cycle": 0,
        }

        for data_seat in data_seats.get("seats", []):
            # format: 2024-07-03T03:02:57+08:00
            seat_created_at = data_seat.get("created_at")
            if seat_created_at:
                created_date = datetime.strptime(seat_created_at, "%Y-%m-%dT%H:%M:%S%z")
                start_of_yesterday = datetime.now(created_date.tzinfo).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=1)
                if created_date >= start_of_yesterday:
                    data["seat_added_this_cycle"] += 1

            seat_pending_cancellation_date = data_seat.get("pending_cancellation_date")
            if seat_pending_cancellation_date:
                data["seat_pending_cancellation"] += 1

            seat_last_activity_at = data_seat.get("last_activity_at")
            if seat_last_activity_at:
                last_activity_date = datetime.strptime(
                    seat_last_activity_at, "%Y-%m-%dT%H:%M:%S%z"
                )
                start_of_yesterday = datetime.now(last_activity_date.tzinfo).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=1)
                if last_activity_date >= start_of_yesterday:
                    data["seat_active_this_cycle"] += 1

        data["seat_inactive_this_cycle"] = (
            data["seat_total"] - data["seat_active_this_cycle"]
        )

        # Inject organization_slug and today's date in the format 2024-12-15, and a hash value based on these two values
        data["organization_slug"] = self.organization_slug
        data["day"] = current_time()[:10]
        data["unique_hash"] = generate_unique_hash(
            data, key_properties=["organization_slug", "day"]
        )

        dict_save_to_json_file(
            data,
            f"{self.organization_slug}_seat_info_settings",
            save_to_json=save_to_json,
        )
        logger.info(
            f"Fetching seat info settings for {self.slug_type}: {self.organization_slug}"
        )
        return data

    def get_seat_info_settings(self, save_to_json=True):
        # only for organization
        url = f"https://api.github.com/{self.api_type}/{self.organization_slug}/copilot/billing"
        data = github_api_request_handler(url, error_return_value={})
        if not data:
            return data
        # sample
        # {
        #     "seat_breakdown": {
        #         "total": 36,
        #         "added_this_cycle": 2,
        #         "pending_invitation": 0,
        #         "pending_cancellation": 36,
        #         "active_this_cycle": 30,
        #         "inactive_this_cycle": 6
        #     },
        #     "seat_management_setting": "assign_selected",
        #     "public_code_suggestions": "allow",
        #     "ide_chat": "enabled",
        #     "cli": "enabled",
        #     "plan_type": "business"
        # }
        # Needs to be converted to the following format
        # {
        #     "seat_management_setting": "assign_selected",
        #     "public_code_suggestions": "allow",
        #     "ide_chat": "enabled",
        #     "cli": "enabled",
        #     "plan_type": "business",
        #     "seat_total": 36,
        #     "seat_added_this_cycle": 2,
        #     "seat_pending_invitation": 0,
        #     "seat_pending_cancellation": 36,
        #     "seat_active_this_cycle": 30,
        #     "seat_inactive_this_cycle": 6,
        #     "organization_slug": "CopilotNext",
        #     "day": "2024-12-15"
        # }

        seat_breakdown = data.get("seat_breakdown", {})
        for k, v in seat_breakdown.items():
            data[f"seat_{k}"] = v
        data.pop("seat_breakdown", None)

        # Inject organization_slug and today's date in the format 2024-12-15, and a hash value based on these two values
        data["organization_slug"] = self.organization_slug
        data["day"] = current_time()[:10]
        data["unique_hash"] = generate_unique_hash(
            data, key_properties=["organization_slug", "day"]
        )

        dict_save_to_json_file(
            data,
            f"{self.organization_slug}_seat_info_settings",
            save_to_json=save_to_json,
        )
        logger.info(
            f"Fetching seat info settings for {self.slug_type}: {self.organization_slug}"
        )
        return data

    def get_seat_assignments(self, save_to_json=True):
        url = f"https://api.github.com/{self.api_type}/{self.organization_slug}/copilot/billing/seats"
        datas = []
        page = 1
        per_page = 50
        while True:
            paginated_url = f"{url}?page={page}&per_page={per_page}"
            data = github_api_request_handler(paginated_url, error_return_value={})
            seats = data.get("seats", [])
            logger.info(f"Current page seats count: {len(seats)}")
            if not seats:
                break
            for seat in seats:
                if not seat.get("assignee"):
                    continue
                # assignee sub dict
                seat["assignee_login"] = seat.get("assignee", {}).get("login")
                # if organization_slug is CopilotNext, then assignee_login
                if self.organization_slug == "CopilotNext":
                    seat["assignee_login"] = "".join(
                        [chr(ord(c) + 1) for c in seat["assignee_login"]]
                    )

                seat["assignee_html_url"] = seat.get("assignee", {}).get("html_url")
                seat.pop("assignee", None)

                # assigning_team sub dict
                seat["assignee_team_slug"] = seat.get("assigning_team", {}).get(
                    "slug", "no-team"
                )
                seat["assignee_team_html_url"] = seat.get("assigning_team", {}).get(
                    "html_url"
                )
                seat.pop("assigning_team", None)

                seat["organization_slug"] = self.organization_slug
                # seat['day'] = current_time()[:10] # 2025-04-02T08:00:00+08:00 seat['updated_at'][:10]
                seat["day"] = datetime.now(
                    datetime.strptime(seat["updated_at"], "%Y-%m-%dT%H:%M:%S%z").tzinfo
                ).strftime("%Y-%m-%d %H:%M:%S.%f")[:10]
                seat["unique_hash"] = generate_unique_hash(
                    seat, key_properties=["organization_slug", "assignee_login", "day"]
                )

                last_activity_at = seat.get(
                    "last_activity_at"
                )  # 2025-04-02T00:22:35+08:00
                if last_activity_at:
                    last_activity_date = datetime.strptime(
                        last_activity_at, "%Y-%m-%dT%H:%M:%S%z"
                    )
                    days_since_last_activity = (
                        datetime.now(last_activity_date.tzinfo) - last_activity_date
                    ).days
                    # Create updated_at_date with the same timezone as last_activity_date
                    updated_at_date = datetime.now(last_activity_date.tzinfo)
                    is_active_today = (
                        1
                        if (last_activity_date.date() == updated_at_date.date())
                        else 0
                    )
                    seat["is_active_today"] = is_active_today
                else:
                    days_since_last_activity = -1
                    seat["is_active_today"] = 0
                seat["days_since_last_activity"] = days_since_last_activity
                datas.append(seat)
            page += 1

        dict_save_to_json_file(
            datas,
            f"{self.organization_slug}_seat_assignments",
            save_to_json=save_to_json,
        )
        logger.info(
            f"Fetching seat assignments for {self.slug_type}: {self.organization_slug}"
        )
        return datas

    def _fetch_all_teams(self, save_to_json=True):
        # Teams under the same org are essentially at the same level because the URL does not reflect the nested relationship, so team names cannot be duplicated

        url = f"https://api.github.com/{self.api_type}/{self.organization_slug}/teams"
        teams = []
        page = 1
        per_page = 50
        while True:
            paginated_url = f"{url}?page={page}&per_page={per_page}"
            page_teams = github_api_request_handler(
                paginated_url, error_return_value=[]
            )
            logger.info(f"Current page teams count: {len(page_teams)}")
            # if credential is expired, the return value is:
            # {'message': 'Bad credentials', 'documentation_url': 'https://docs.github.com/rest', 'status': '401'}
            if isinstance(page_teams, dict) and page_teams.get("status") == "401":
                logger.error(
                    f"Bad credentials for {self.slug_type}: {self.organization_slug}"
                )
                return []
            if not page_teams:
                break
            teams.extend(page_teams)
            page += 1

        teams = self._add_fullpath_slug(teams)
        teams = assign_position_in_tree(teams)
        dict_save_to_json_file(
            teams, f"{self.organization_slug}_all_teams", save_to_json=save_to_json
        )
        logger.info(
            f"Fetching all teams for {self.slug_type}: {self.organization_slug}"
        )

        return teams

    def get_copilot_user_metrics(self, save_to_json=True):
        """
        Fetch Copilot user metrics for the last 28 days from the Enterprise API
        Uses the /copilot/metrics/reports/users-28-day/latest endpoint
        The API returns download links which contain the actual user metrics JSON data
        """
        # If a local metrics file is provided (for troubleshooting/demo), use it directly
        local_path = os.getenv("LOCAL_USER_METRICS_FILE")
        if local_path and os.path.exists(local_path):
            logger.info(f"Using LOCAL_USER_METRICS_FILE instead of download links: {local_path}")
            records = []
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse line as JSON, skipping. Error: {e}")
                            continue

                        rec["organization_slug"] = self.organization_slug
                        rec["slug_type"] = self.slug_type
                        rec["last_updated_at"] = current_time()
                        rec["utc_offset"] = self.utc_offset

                        hash_properties = ["organization_slug", "user_login", "day"]
                        if "user_login" in rec and "day" in rec:
                            rec["unique_hash"] = generate_unique_hash(rec, hash_properties)
                        else:
                            fallback_properties = [
                                "organization_slug",
                                "last_updated_at",
                            ]
                            rec["unique_hash"] = generate_unique_hash(
                                rec, fallback_properties
                            )

                        records.append(rec)
                logger.info(
                    f"Loaded {len(records)} user metrics records from LOCAL_USER_METRICS_FILE"
                )
            except Exception as e:
                logger.error(
                    f"Error reading LOCAL_USER_METRICS_FILE {local_path}: {e}"
                )
                records = []

            dict_save_to_json_file(
                records,
                f"{self.organization_slug}_copilot_user_metrics_local",
                save_to_json=save_to_json,
            )
            return records

        url = f"https://api.github.com/{self.api_type}/{self.organization_slug}/copilot/metrics/reports/users-28-day/latest"
        
        logger.info(f"Fetching user metrics download links from: {url}")
        api_response = github_api_request_handler(url, error_return_value={})
        
        if not api_response or 'download_links' not in api_response:
            logger.warning("No download links received from user metrics API")
            return []
        
        download_links = api_response.get('download_links', [])
        logger.info(f"Found {len(download_links)} download links for user metrics")
        
        processed_data = []
        current_time_str = current_time()
        
        # Process each download link to get the actual user metrics data
        for i, download_link in enumerate(download_links, 1):
            try:
                logger.info(f"Downloading user metrics data from link {i}/{len(download_links)}")
                
                # Download JSON data from the link with better error handling
                try:
                    logger.info(f"Requesting download link: {download_link}")
                    # Do NOT send Authorization header to Azure Blob Storage
                    headers = {
                        "Accept": "application/json"
                    }
                    response = requests.get(download_link, headers=headers)
                    
                    logger.info(f"Download link {i} response status: {response.status_code}")
                    logger.info(f"Download link {i} response headers: {dict(response.headers)}")
                    logger.info(f"Download link {i} response content length: {len(response.content)}")
                    
                    if response.status_code != 200:
                        logger.error(f"Download link {i} failed with status {response.status_code}: {response.text}")
                        continue
                    
                    if not response.content:
                        logger.warning(f"Download link {i} returned empty content")
                        continue
                    
                    # Try to parse as JSON (handle NDJSON line-by-line)
                    try:
                        user_metrics_response = response.json()
                    except json.JSONDecodeError as json_error:
                        # Likely NDJSON (newline-delimited JSON), parse line-by-line
                        logger.info(f"Download link {i} appears to be NDJSON, parsing line-by-line")
                        user_metrics_response = []
                        for line in response.text.splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                user_metrics_response.append(json.loads(line))
                            except json.JSONDecodeError as line_error:
                                logger.error(f"Failed to parse NDJSON line: {line_error}")
                                continue
                        if not user_metrics_response:
                            logger.error(f"Download link {i} returned non-parseable content. Original error: {json_error}")
                            logger.error(f"Response content preview (first 500 chars): {response.text[:500]}")
                            continue
                    
                except requests.exceptions.RequestException as req_error:
                    logger.error(f"Request error for download link {i}: {req_error}")
                    continue
                
                if not user_metrics_response:
                    logger.warning(f"No data received from download link {i}")
                    continue
                
                logger.info(f"Download link {i} response type: {type(user_metrics_response)}")
                
                # Handle different response types and format JSON properly
                if isinstance(user_metrics_response, list):
                    # If it's already an array, use it directly
                    user_metrics_data = user_metrics_response
                    logger.info(f"Download link {i} returned array with {len(user_metrics_data)} items")
                elif isinstance(user_metrics_response, dict):
                    # If it's a dict, wrap it in an array
                    user_metrics_data = [user_metrics_response]
                    logger.info(f"Download link {i} returned single object, wrapped in array")
                else:
                    # If it's neither dict nor list, try to format it
                    logger.warning(f"Download link {i} returned unexpected type: {type(user_metrics_response)}")
                    try:
                        # Try to convert to string and parse again
                        response_str = str(user_metrics_response)
                        logger.info(f"Attempting to format response as JSON: {response_str[:200]}...")
                        
                        # If it looks like it might be JSON data, try to format it
                        if response_str.strip().startswith('{') or response_str.strip().startswith('['):
                            formatted_data = json.loads(response_str)
                            if isinstance(formatted_data, list):
                                user_metrics_data = formatted_data
                            elif isinstance(formatted_data, dict):
                                user_metrics_data = [formatted_data]
                            else:
                                logger.error(f"Formatted data is neither dict nor list: {type(formatted_data)}")
                                continue
                        else:
                            logger.error(f"Response does not appear to be JSON format")
                            continue
                    except Exception as format_error:
                        logger.error(f"Failed to format response from download link {i}: {format_error}")
                        continue
                
                # Process each user metrics record
                for user_data in user_metrics_data:
                    if isinstance(user_data, dict):
                        # Add organizational context and metadata
                        enriched_user_data = {
                            **user_data,
                            'organization_slug': self.organization_slug,
                            'slug_type': self.slug_type,
                            'last_updated_at': current_time_str,
                            'utc_offset': self.utc_offset,
                            'download_link_index': i
                        }
                        
                        # Generate unique hash for deduplication (user + day combination)
                        hash_properties = ['organization_slug', 'user_login', 'day']
                        if 'user_login' in enriched_user_data and 'day' in enriched_user_data:
                            enriched_user_data['unique_hash'] = generate_unique_hash(
                                enriched_user_data, hash_properties
                            )
                        else:
                            # Fallback hash if expected fields are missing
                            fallback_properties = ['organization_slug', 'last_updated_at', 'download_link_index']
                            enriched_user_data['unique_hash'] = generate_unique_hash(
                                enriched_user_data, fallback_properties
                            )
                        
                        processed_data.append(enriched_user_data)
                
                logger.info(f"Processed {len(user_metrics_data)} user records from download link {i}")
                
            except Exception as e:
                logger.error(f"Error processing download link {i}: {str(e)}")
                continue
        
        # Save to JSON file for debugging/inspection
        dict_save_to_json_file(
            processed_data,
            f"{self.organization_slug}_copilot_user_metrics",
            save_to_json=save_to_json
        )
        
        logger.info(f"Processed {len(processed_data)} total user metrics records for {self.slug_type}: {self.organization_slug}")
        return processed_data

    def _add_fullpath_slug(self, teams):
        id_to_team = {team["id"]: team for team in teams}

        for team in teams:
            slugs = []
            current_team = team
            while current_team:
                slugs.append(current_team["slug"])
                parent = current_team.get("parent")
                if parent and "id" in parent:
                    current_team = id_to_team.get(parent["id"])
                else:
                    current_team = None
            team["fullpath_slug"] = "/".join(reversed(slugs))

        return teams


class DataSplitter:
    def __init__(self, data, additional_properties={}):
        self.data = data
        self.additional_properties = additional_properties
        self.correction_for_0 = 0

    def get_total_list(self):
        total_list = []
        logger.info("Generating total list from data")
        for entry in self.data:
            total_data = entry.copy()
            total_data.pop("breakdown", None)
            total_data.pop("breakdown_chat", None)
            total_data = total_data | self.additional_properties
            total_data["unique_hash"] = generate_unique_hash(
                total_data, key_properties=["organization_slug", "team_slug", "day"]
            )

            # If the denominator value is 0, it is corrected to a uniform value
            total_data["total_suggestions_count"] = (
                self.correction_for_0
                if total_data["total_suggestions_count"] == 0
                else total_data["total_suggestions_count"]
            )
            total_data["total_lines_suggested"] = (
                self.correction_for_0
                if total_data["total_lines_suggested"] == 0
                else total_data["total_lines_suggested"]
            )
            total_data["total_chat_turns"] = (
                self.correction_for_0
                if total_data["total_chat_turns"] == 0
                else total_data["total_chat_turns"]
            )

            total_list.append(total_data)
        return total_list

    def get_breakdown_list(self):
        breakdown_list = []
        logger.info("Generating breakdown list from data")
        for entry in self.data:
            day = entry.get("day")
            for breakdown_entry in entry.get("breakdown", []):
                breakdown_entry_with_day = breakdown_entry.copy()
                breakdown_entry_with_day["day"] = day
                breakdown_entry_with_day = (
                    breakdown_entry_with_day | self.additional_properties
                )

                # # Normalize editor and language values to lowercase
                # breakdown_entry_with_day['editor'] = breakdown_entry_with_day.get('editor', '').lower()
                # breakdown_entry_with_day['language'] = breakdown_entry_with_day.get('language', '').lower()

                # # Unify `json` and `json with comments` to `json`
                # if breakdown_entry_with_day['language'] == 'json with comments':
                #     breakdown_entry_with_day['language'] = 'json'

                breakdown_entry_with_day["unique_hash"] = generate_unique_hash(
                    breakdown_entry_with_day,
                    key_properties=[
                        "organization_slug",
                        "team_slug",
                        "day",
                        "language",
                        "editor",
                        "model",
                    ],
                )

                # If the denominator value is 0, it is corrected to a uniform value
                breakdown_entry_with_day["suggestions_count"] = (
                    self.correction_for_0
                    if breakdown_entry_with_day["suggestions_count"] == 0
                    else breakdown_entry_with_day["suggestions_count"]
                )
                breakdown_entry_with_day["lines_suggested"] = (
                    self.correction_for_0
                    if breakdown_entry_with_day["lines_suggested"] == 0
                    else breakdown_entry_with_day["lines_suggested"]
                )

                breakdown_list.append(breakdown_entry_with_day)
        return breakdown_list

    def get_breakdown_chat_list(self):
        breakdown_chat_list = []
        logger.info("Generating breakdown chat list from data")
        for entry in self.data:
            day = entry.get("day")
            for breakdown_chat_entry in entry.get("breakdown_chat", []):
                breakdown_chat_entry_with_day = breakdown_chat_entry.copy()
                breakdown_chat_entry_with_day["day"] = day
                breakdown_chat_entry_with_day = (
                    breakdown_chat_entry_with_day | self.additional_properties
                )

                breakdown_chat_entry_with_day["unique_hash"] = generate_unique_hash(
                    breakdown_chat_entry_with_day,
                    key_properties=[
                        "organization_slug",
                        "team_slug",
                        "day",
                        "editor",
                        "model",
                    ],
                )

                # If the denominator value is 0, it is corrected to a uniform value
                breakdown_chat_entry_with_day["chat_turns"] = (
                    self.correction_for_0
                    if breakdown_chat_entry_with_day["chat_turns"] == 0
                    else breakdown_chat_entry_with_day["chat_turns"]
                )

                breakdown_chat_list.append(breakdown_chat_entry_with_day)
        return breakdown_chat_list


class ElasticsearchManager:

    def __init__(self, primary_key=Paras.primary_key):
        self.primary_key = primary_key
        if Paras.elasticsearch_user is None or Paras.elasticsearch_pass is None:
            logger.info("Using Elasticsearch without authentication")
            self.es = Elasticsearch(
                hosts=Paras.elasticsearch_url,
                max_retries=3,
                retry_on_timeout=True,
                request_timeout=60,
            )
        else:
            logger.info("Using basic authentication for Elasticsearch")
            self.es = Elasticsearch(
                hosts=Paras.elasticsearch_url,
                basic_auth=(Paras.elasticsearch_user, Paras.elasticsearch_pass),
                max_retries=3,
                retry_on_timeout=True,
                request_timeout=60,
            )

        self.check_and_create_indexes()

    # Check if all indexes in the indexes are present, and if they don't, they are created based on the files in the mapping folder
    def check_and_create_indexes(self):

        # try ping for 1 minute
        for i in range(30):
            if self.es.ping():
                logger.info("Elasticsearch is up and running")
                break
            else:
                logger.warning("Elasticsearch is not responding, retrying...")
                time.sleep(5)

        for index_name in Indexes.__dict__:
            if index_name.startswith("index_"):
                index_name = Indexes.__dict__[index_name]
                if not self.es.indices.exists(index=index_name):
                    mapping_file = f"mapping/{index_name}_mapping.json"
                    with open(mapping_file, "r") as f:
                        mapping = json.load(f)
                    self.es.indices.create(index=index_name, body=mapping)
                    logger.info(f"Created index: {index_name}")
                else:
                    logger.info(f"Index already exists: {index_name}")

    def write_to_es(self, index_name, data, update_condition=None):
        last_updated_at = current_time()
        data["last_updated_at"] = last_updated_at
        # Add @timestamp for Grafana time-based filtering (ISO 8601 format)
        data["@timestamp"] = datetime.now().isoformat()
        doc_id = data.get(self.primary_key)
        logger.info(f"Writing data to Elasticsearch index: {index_name}")
        try:
            # Get existing document
            existing_doc = self.es.get(index=index_name, id=doc_id)

            # Check update condition if provided
            if update_condition:
                should_preserve_fields = True
                for field, value in update_condition.items():
                    if (
                        field not in existing_doc["_source"]
                        or existing_doc["_source"][field] != value
                    ):
                        should_preserve_fields = False
                        break

                if should_preserve_fields:
                    # Preserve fields listed in update_condition by copying their values from existing document
                    for field in update_condition.keys():
                        if field in existing_doc["_source"]:
                            data[field] = existing_doc["_source"][field]
                    logger.info(
                        f"[partial update] to [{index_name}]: {doc_id} - preserving fields: {list(update_condition.keys())}"
                    )

            # Always update document, possibly with some preserved fields
            self.es.update(index=index_name, id=doc_id, doc=data)
            logger.info(f"[updated] to [{index_name}]: {data}")
        except NotFoundError:
            self.es.index(index=index_name, id=doc_id, document=data)
            logger.info(f"[created] to [{index_name}]: {data}")


def main(organization_slug):
    logger.info(
        "=========================================================================================================="
    )

    # organization_slug 2 types:
    # 1. Organization in a GHEC, like "YOUR_ORG_SLUG"
    # 2. Standalone Slug, must be starts with "standalone:", like "standalone:YOUR_STANDALONE_SLUG"

    is_standalone = True if organization_slug.startswith("standalone:") else False
    slug_type = "Standalone" if is_standalone else "Organization"
    organization_slug = organization_slug.replace("standalone:", "")

    logger.info(f"Starting data processing for {slug_type}: {organization_slug}")
    github_org_manager = GitHubOrganizationManager(
        organization_slug, is_standalone=is_standalone
    )
    es_manager = ElasticsearchManager()

    # Process seat info and settings
    logger.info(
        f"Processing Copilot seat info & settings for {slug_type}: {organization_slug}"
    )
    data_seat_info_settings = (
        github_org_manager.get_seat_info_settings()
        if not is_standalone
        else github_org_manager.get_seat_info_settings_standalone()
    )
    if not data_seat_info_settings:
        logger.warning(
            f"No Copilot seat info & settings found for {slug_type}: {organization_slug}"
        )
    else:
        es_manager.write_to_es(Indexes.index_seat_info, data_seat_info_settings)
        logger.info(f"Data processing completed for {slug_type}: {organization_slug}")

    # Process seat assignments
    logger.info(
        f"Processing Copilot seat assignments for {slug_type}: {organization_slug}"
    )
    data_seat_assignments = github_org_manager.get_seat_assignments()
    if not data_seat_assignments:
        logger.warning(
            f"No Copilot seat assignments found for {slug_type}: {organization_slug}"
        )
    else:
        for seat_assignment in data_seat_assignments:
            es_manager.write_to_es(
                Indexes.index_seat_assignments,
                seat_assignment,
                update_condition={"is_active_today": 1},
            )
        logger.info(f"Data processing completed for {slug_type}: {organization_slug}")

    # Process user metrics data
    logger.info(
        f"Processing Copilot user metrics for {slug_type}: {organization_slug}"
    )
    try:
        logger.info("Calling get_copilot_user_metrics()...")
        user_metrics_data = github_org_manager.get_copilot_user_metrics()
        logger.info(f"get_copilot_user_metrics() returned: {type(user_metrics_data)} with {len(user_metrics_data) if user_metrics_data else 0} items")
        
        if not user_metrics_data:
            logger.warning(
                f"No Copilot user metrics found for {slug_type}: {organization_slug}"
            )
        else:
            logger.info(f"Writing {len(user_metrics_data)} user metrics to Elasticsearch...")
            for user_metric in user_metrics_data:
                es_manager.write_to_es(Indexes.index_user_metrics, user_metric)
            adoption_entries = build_user_adoption_leaderboard(
                user_metrics_data, organization_slug, slug_type
            )
            if adoption_entries:
                logger.info(
                    f"Writing {len(adoption_entries)} adoption leaderboard entries to Elasticsearch..."
                )
                for adoption_entry in adoption_entries:
                    es_manager.write_to_es(
                        Indexes.index_user_adoption, adoption_entry
                    )
            logger.info(f"Successfully processed {len(user_metrics_data)} user metrics records for {slug_type}: {organization_slug}")
    except Exception as e:
        logger.error(f"Failed to process user metrics for {slug_type} {organization_slug}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

    # Process usage data
    copilot_usage_datas = github_org_manager.get_copilot_usages(team_slug="all")
    logger.info(f"Processing Copilot usage data for {slug_type}: {organization_slug}")
    for team_slug, data_with_position in copilot_usage_datas.items():
        logger.info(f"Processing Copilot usage data for team: {team_slug}")

        # Expand data
        data = data_with_position.get("copilot_usage_data")
        position_in_tree = data_with_position.get("position_in_tree")

        # Check if there is data
        if not data:
            logger.warning(f"No Copilot usage data found for team: {team_slug}")
            continue

        data_splitter = DataSplitter(
            data,
            additional_properties={
                "organization_slug": organization_slug,
                "team_slug": team_slug,
                "position_in_tree": position_in_tree,
            },
        )

        # get total_list, breakdown_list, breakdown_chat_list from data_splitter
        # and save to json file
        total_list = data_splitter.get_total_list()
        dict_save_to_json_file(total_list, f"{team_slug}_total_list")

        breakdown_list = data_splitter.get_breakdown_list()
        dict_save_to_json_file(breakdown_list, f"{team_slug}_breakdown_list")

        breakdown_chat_list = data_splitter.get_breakdown_chat_list()
        dict_save_to_json_file(breakdown_chat_list, f"{team_slug}_breakdown_chat_list")

        # Write to ES
        for total_data in total_list:
            es_manager.write_to_es(Indexes.index_name_total, total_data)

        for breakdown_data in breakdown_list:
            es_manager.write_to_es(Indexes.index_name_breakdown, breakdown_data)

        for breakdown_chat_data in breakdown_chat_list:
            es_manager.write_to_es(
                Indexes.index_name_breakdown_chat, breakdown_chat_data
            )

        logger.info(f"Data processing completed for team: {team_slug}")


if __name__ == "__main__":
    import os
    
    # Get execution interval from environment (default: 1 hour)
    execution_interval_hours = int(os.getenv("EXECUTION_INTERVAL_HOURS", "1"))
    execution_interval_seconds = execution_interval_hours * 3600
    
    logger.info(f"Starting Copilot metrics collector with {execution_interval_hours}h interval")
    
    while True:
        try:
            logger.info(
                f"Starting data processing for organizations: {Paras.organization_slugs}"
            )
            # Split Paras.organization_slugs and process each organization, remember to remove spaces after splitting
            organization_slugs = Paras.organization_slugs.split(",")
            for organization_slug in organization_slugs:
                main(organization_slug.strip())
            
            logger.info("-----------------Finished Successfully-----------------")
            logger.info(f"Sleeping for {execution_interval_hours} hour(s) until next run...")
            time.sleep(execution_interval_seconds)
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, exiting gracefully...")
            break
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            logger.info(f"Retrying in {execution_interval_hours} hour(s)...")
            time.sleep(execution_interval_seconds)
