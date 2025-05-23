import os
import requests
import base64
import time
import logging
from datetime import datetime
import json

# # load environment variables from .env file
# from dotenv import load_dotenv
# load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

elasticsearch_url = os.getenv("ELASTICSEARCH_URL")

if not elasticsearch_url:
    raise ValueError("Please set the ELASTICSEARCH_URL environment variable")

grafana_username = os.getenv("GRAFANA_USERNAME")

if not grafana_username:
    raise ValueError("Please set the GRAFANA_USERNAME environment variable")

grafana_url = os.getenv("GRAFANA_URL", "http://$GRAFANA_URL/")

if not grafana_url:
    raise ValueError("Please set the GRAFANA_URL environment variable")

grafana_password = os.getenv("GRAFANA_PASSWORD")

if not grafana_password:
    raise ValueError("Please set the GRAFANA_PASSWORD environment variable")

service_account_name = "sa-for-cpuad"


def poll_for_elasticsearch():
    """
    Polls the Elasticsearch server until it is reachable.

    Raises:
        ValueError: If the Elasticsearch server is not reachable.
    """
    while True:
        try:
            response = requests.get(f"{elasticsearch_url.rstrip('/')}/_cluster/health")
            if response.status_code == 200:
                logging.info("Elasticsearch is up and running.")
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Elasticsearch is not reachable: {e}")
        time.sleep(5)


def poll_for_grafana():
    """
    Polls the Grafana server until it is reachable.

    Raises:
        ValueError: If the Grafana server is not reachable.
    """
    while True:
        try:
            response = requests.get(f"{grafana_url.rstrip('/')}/api/health")
            if response.status_code == 200:
                # read the response content
                content = response.json()
                logging.info(f"Grafana health status: {content}")

                if content.get("database") != "ok":
                    logging.error("Grafana database is not healthy.")
                    raise ValueError("Grafana database is not healthy.")

                logging.info("Grafana is up and running.")
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Grafana is not reachable: {e}")
        time.sleep(5)

def safe_request(method, url, headers=None, json=None, max_retries=3, retry_interval=5):
    """General purpose HTTP request handler with retries"""
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, headers=headers, json=json)
            if response.status_code in [200,201,404]:
                return response
            else:
                logging.error(f"Request failed with status code {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request exception: {e}")
        time.sleep(retry_interval)
    raise ValueError(f"Unable to complete request after {max_retries} retries: {url}")

def get_existing_grafana_service_account_id(headers):
    """
    Retrieves the existing Grafana service account.

    Returns:
        The service account ID if it exists, None otherwise.
    """
    result = safe_request(
        "GET",
        f"{grafana_url.rstrip('/')}/api/serviceaccounts/search?query={service_account_name}",
        headers=headers,
    )
    # time.sleep(1)  # Add a 1-second delay

    if result.status_code != 200:
        logging.error(
            f"Failed to retrieve service accounts: {result.status_code} - {result.text}"
        )
        raise ValueError(
            f"Failed to retrieve service accounts - {result.status_code} - {result.text}"
        )

    service_accounts = result.json().get("serviceAccounts", [])

    if not service_accounts:
        logging.info("No existing service accounts found.")
        return None

    for account in service_accounts:
        if account.get("name") == service_account_name:
            logging.info(f"Service account {service_account_name} already exists.")
            return account.get("id")

    logging.info(f"Service account {service_account_name} not found.")
    return None


def delete_existing_grafana_service_account(headers, service_account_id):
    """
    Deletes the existing Grafana service account.

    Args:
        service_account_id: The ID of the service account to delete.
    """
    result = requests.delete(
        f"{grafana_url.rstrip('/')}/api/serviceaccounts/{service_account_id}",
        headers=headers,
    )
    time.sleep(1)  # Add a 1-second delay

    if result.status_code != 200:
        logging.error(
            f"Failed to delete service account: {result.status_code} - {result.text}"
        )
        raise ValueError(
            f"Failed to delete service account - {result.status_code} - {result.text}"
        )
    logging.info("Service account deleted successfully.")


def setup_grafana_service_account():
    """
    Creates a Grafana service account using basic authentication.

    Returns:
        A dictionary containing the headers for the request.
    """
    headers = get_grafana_basic_credentials_headers()

    # Check if the service account already exists
    existing_service_account_id = get_existing_grafana_service_account_id(
        headers=headers
    )

    if existing_service_account_id:
        delete_existing_grafana_service_account(
            headers=headers, service_account_id=existing_service_account_id
        )

    service_account_id = create_service_account(headers=headers)

    grafana_api_token = create_grafana_access_token(
        headers=headers, service_account_id=service_account_id
    )

    return grafana_api_token


def create_grafana_access_token(headers, service_account_id):
    result = safe_request(
        "POST",
        f"{grafana_url.rstrip('/')}/api/serviceaccounts/{service_account_id}/tokens",
        headers=headers,
        json={"name": "sa-for-cpuad-key", "secondsToLive": 0},
    )

    if result.status_code != 200:
        logging.error(
            f"Failed to create Grafana API token: {result.status_code} - {result.text}"
        )
        raise ValueError("Failed to create Grafana API token")

    logging.info("Grafana API token created successfully.")

    grafana_api_token = result.json().get("key")

    if not grafana_api_token:
        logging.error("Failed to retrieve Grafana API token")
        raise ValueError("Failed to retrieve Grafana API token")

    return grafana_api_token


def get_grafana_basic_credentials_headers():
    credentials = f"{grafana_username}:{grafana_password}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }

    return headers


def create_service_account(headers):
    result = safe_request(
        "POST",
        f"{grafana_url.rstrip('/')}/api/serviceaccounts",
        headers=headers,
        json={"name": service_account_name, "role": "Admin", "isDisabled": False},
    )
    # time.sleep(1)  # Add a 1-second delay

    if result.status_code != 201:
        logging.error(
            f"Failed to create service account: {result.status_code} - {result.text}"
        )
        raise ValueError(
            f"Failed to create service account - {result.status_code} - {result.text}"
        )

    logging.info(f"Service account {result.json().get('name')} created successfully.")

    service_account_id = result.json().get("id")
    return service_account_id


def import_grafana_dashboard(dashboard_model, grafana_token):
    """
    Imports a Grafana dashboard using the Grafana API.

    Args:
        dashboard_model_path: Path to the dashboard model JSON file.
    """
    template_content = dashboard_model

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {grafana_token}",
    }

    # write the template content to a file
    with open("dashboard-template-test.json", "w") as f:
        f.write(template_content)

    result = requests.post(
        f"{grafana_url.rstrip('/')}/api/dashboards/db",
        headers=headers,
        data=template_content,
    )

    if result.status_code != 200:
        logging.error(
            f"Failed to import dashboard: {result.status_code} - {result.text}"
        )
        raise ValueError(
            f"Failed to import dashboard - {result.status_code} - {result.text}"
        )
    else:
        logging.info("Dashboard imported successfully.")


def add_grafana_data_sources(grafana_token, max_retries=3, retry_interval=5):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {grafana_token}",
    }

    # Data sources to add
    data_sources = [
        {
            "name": "elasticsearch-breakdown",
            "index": "copilot_usage_breakdown",
        },
        {
            "name": "elasticsearch-breakdown-chat",
            "index": "copilot_usage_breakdown_chat",
        },
        {
            "name": "elasticsearch-total",
            "index": "copilot_usage_total",
        },
        {
            "name": "elasticsearch-seat-info-settings",
            "index": "copilot_seat_info_settings",
        },
        {
            "name": "elasticsearch-seat-assignments",
            "index": "copilot_seat_assignments",
        },
    ]

    # Template for the payload
    def create_payload(name, index):
        return {
            "name": name,
            "type": "elasticsearch",
            "access": "proxy",
            "url": f"{elasticsearch_url.rstrip('/')}",
            "basicAuth": False,
            "withCredentials": False,
            "isDefault": False,
            "jsonData": {
                "includeFrozen": False,
                "index": index,
                "logLevelField": "",
                "logMessageField": "",
                "maxConcurrentShardRequests": 5,
                "timeField": "day",
                "timeInterval": "1d",
            },
        }

    # Add each data source
    for ds in data_sources:
        logging.info(f"Checking if data source {ds['name']} already exists...")
        check_resp = safe_request(
            "GET",
            f"{grafana_url.rstrip('/')}/api/datasources/name/{ds['name']}",
            headers=headers
        )
        if check_resp.status_code == 200:
            logging.info(f"Data source {ds['name']} already exists, skipping.")
            continue

        payload = create_payload(ds["name"], ds["index"])
        logging.info(f"Creating data source: {ds['name']}...")

        response = safe_request(
            "POST",
            f"{grafana_url.rstrip('/')}/api/datasources",
            headers=headers,
            json=payload,
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        verify_resp = safe_request(
            "GET",
            f"{grafana_url.rstrip('/')}/api/datasources/name/{ds['name']}",
            headers=headers,
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        if verify_resp.status_code == 200:
            logging.info(f"Data source verified: {ds['name']}")
        else:
            raise ValueError(f"Data source verification failed: {ds['name']}")


def generate_grafana_model(grafana_token):
    data_source_names = [
        "elasticsearch-breakdown",
        "elasticsearch-breakdown-chat",
        "elasticsearch-seat-assignments",
        "elasticsearch-seat-info-settings",
        "elasticsearch-total",
    ]

    default_template_path = "dashboard-template.json"
    model_output_path = f'dashboard-model-{datetime.today().strftime("%Y-%m-%d")}.json'
    mapping_output_path = f'dashboard-model-data_sources_name_uid_mapping-{datetime.today().strftime("%Y-%m-%d")}.json'

    template_path = default_template_path

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {grafana_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    grafana_url_stripted = grafana_url.rstrip("/")
    response = requests.get(f"{grafana_url_stripted}/api/datasources", headers=headers)
    time.sleep(1)  # Add a 1-second delay

    if response.status_code != 200:
        logging.error(
            f"Failed to get data sources: {response.status_code} - {response.text}"
        )
        raise ValueError(
            f"Failed to get data sources - {response.status_code} - {response.text}"
        )

    data_resources = response.json()

    data_sources_name_uid_mapping = {}
    for data_resource in data_resources:
        name = data_resource["name"]
        uid = data_resource["uid"]
        data_sources_name_uid_mapping[name] = uid

    with open(mapping_output_path, "w") as f:
        json.dump(data_sources_name_uid_mapping, f, indent=4)

    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    for data_source_name in data_source_names:
        uid = data_sources_name_uid_mapping.get(data_source_name)
        if not uid:
            logging.error(
                f"Data source {data_source_name} not found, you must create it first"
            )
            break
        uid_placeholder = f"{data_source_name}-uid"
        template_content = template_content.replace(uid_placeholder, uid)

    # load template content as json
    try:
        dashboard = json.loads(template_content)
        # get the id
        dashboard_id = dashboard.get("dashboard", {}).get("id")
        # get title
        dashboard_title = dashboard.get("dashboard", {}).get("title")
        logging.info(f"Dashboard ID: {dashboard_id}")
        logging.info(f"Dashboard Title: {dashboard_title}")

        # change id to null
        dashboard["dashboard"]["id"] = None

        # updated template content
        template_content = json.dumps(dashboard, indent=4)

        with open(model_output_path, "w") as output_file:
            output_file.write(template_content)

        return template_content

    except json.JSONDecodeError as e:
        logging.error(f"Failed to load template content as JSON: {e}")
        raise ValueError("Failed to load template content as JSON")


if __name__ == "__main__":

    poll_for_grafana()

    grafana_token = setup_grafana_service_account()

    logging.info("Adding Grafana data sources...")

    add_grafana_data_sources(grafana_token=grafana_token)

    logging.info("Successfully added Grafana data sources.")

    logging.info("Generating Grafana dashboard model...")

    python_script_path = "gen_grafana_model.py"

    dashboard_model = generate_grafana_model(grafana_token=grafana_token)

    logging.info("Successfully generated Grafana dashboard model.")

    logging.info("Importing Grafana dashboard...")

    import_grafana_dashboard(
        dashboard_model=dashboard_model, grafana_token=grafana_token
    )

    logging.info("Successfully imported Grafana dashboard.")
