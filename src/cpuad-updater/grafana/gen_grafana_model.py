import json
import requests
import os
import argparse
from datetime import datetime


data_source_names = [
    "elasticsearch-breakdown",
    "elasticsearch-breakdown-chat",
    "elasticsearch-seat-assignments",
    "elasticsearch-seat-info-settings",
    "elasticsearch-total",
]

grafana_folder = 'grafana'
default_template_path = f'{grafana_folder}/dashboard-template.json'
model_output_path = f'{grafana_folder}/dashboard-model-{datetime.today().strftime("%Y-%m-%d")}.json'
mapping_output_path = f'{grafana_folder}/dashboard-model-data_sources_name_uid_mapping-{datetime.today().strftime("%Y-%m-%d")}.json'

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Generate Grafana dashboard model.')
parser.add_argument('--template', type=str, default=default_template_path, help='Path to the dashboard template JSON file')
args = parser.parse_args()

template_path = args.template

grafana_url = os.getenv('GRAFANA_URL', 'http://$GRAFANA_URL/')
grafana_token = os.getenv('GRAFANA_TOKEN')

if not grafana_token:
    raise ValueError("Please set the GRAFANA_TOKEN environment variable")

headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {grafana_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
response = requests.get(grafana_url.rstrip('/')+'/api/datasources', headers=headers)

# sample data_resources
# data_resources = [
#       {
#     "id": 1,
#     "uid": "ee73owudpbim8f",
#     "orgId": 1,
#     "name": "elastcsearch-breakdown",
#     "type": "elasticsearch",
#     "typeName": "Elasticsearch",
#     "typeLogoUrl": "public/app/plugins/datasource/elasticsearch/img/elasticsearch.svg",
#     "access": "proxy",
#     "url": "http://$ELASTICSEARCH_URL",
#     "user": "",
#     "database": "",
#     "basicAuth": false,
#     "isDefault": true,
#     "jsonData": {
#       "includeFrozen": false,
#       "index": "copilot_usage_breakdown",
#       "logLevelField": "",
#       "logMessageField": "",
#       "maxConcurrentShardRequests": 5,
#       "timeField": "day",
#       "timeInterval": "1d"
#     },
#     "readOnly": false
#   },
# ]
data_resources = response.json()

data_sources_name_uid_mapping = {}
for data_resource in data_resources:
    name = data_resource['name']
    uid = data_resource['uid']
    data_sources_name_uid_mapping[name] = uid

with open(mapping_output_path, 'w', encoding='utf-8') as f:
    json.dump(data_sources_name_uid_mapping, f, indent=4)

with open(template_path, 'r', encoding='utf-8') as template_file:
    template_content = template_file.read()

for data_source_name in data_source_names:
    uid = data_sources_name_uid_mapping.get(data_source_name)
    if not uid:
        print(f"Data source {data_source_name} not found, you must create it first")
        break
    uid_placeholder = f"{data_source_name}-uid"
    template_content = template_content.replace(uid_placeholder, uid)

with open(model_output_path, 'w', encoding='utf-8') as output_file:
    output_file.write(template_content)
    print(f"Model saved to {model_output_path}, please import it to Grafana")