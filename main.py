import json
import requests
import os
import hashlib
from elasticsearch import Elasticsearch, NotFoundError
from datetime import datetime
from log_utils import *
import time


def current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


class Paras:

    date_str = current_time()[:10]

    # GitHub
    github_pat = os.getenv('GITHUB_PAT')
    organization_slugs = os.getenv('ORGANIZATION_SLUGS')

    # ElasticSearch
    primary_key = os.getenv('PRIMARY_KEY', 'unique_hash')
    elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    
    # Log path
    log_path = os.path.join(os.getenv('LOG_PATH', 'logs'), date_str)

    # Execution interval HOURS
    execution_interval = int(os.getenv('EXECUTION_INTERVAL', 6))


class Indexes:
    index_seat_info = os.getenv('INDEX_SEAT_INFO', 'copilot_seat_info_settings')
    index_seat_assignments = os.getenv('INDEX_SEAT_ASSIGNMENTS', 'copilot_seat_assignments')
    index_name_total = os.getenv('INDEX_NAME_TOTAL', 'copilot_usage_total')
    index_name_breakdown = os.getenv('INDEX_NAME_BREAKDOWN', 'copilot_usage_breakdown')



logger = configure_logger(log_path=Paras.log_path)
logger.info('-----------------Starting-----------------')


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
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    # logger.info(f"Response received: {data}")

    if isinstance(data, dict) and data.get('status', '200') == '404':
        logger.warning(f"URL not found: {url}")
        return error_return_value
    return data

def dict_save_to_json_file(data, file_name, logs_path=Paras.log_path, save_to_json=True):
    if save_to_json:
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
        with open(f'{logs_path}/{file_name}_{Paras.date_str}.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Data saved to {logs_path}/{file_name}_{Paras.date_str}.json")

def generate_unique_hash(data, key_properties=[]):
    key_string = '-'.join([data.get(key_propertie) for key_propertie in key_properties])
    unique_hash = hashlib.sha256(key_string.encode()).hexdigest()
    return unique_hash

def assign_position_in_tree(nodes):
    # Create a dictionary with node id as key and node data as value
    node_dict = {node['id']: node for node in nodes}

    # Create sets to store all node ids and child node ids
    all_ids = set(node_dict.keys())
    child_ids = set()

    # Build parent-child relationships
    for node in nodes:
        parent = node.get('parent')
        if parent and 'id' in parent:
            parent_id = parent['id']
            child_ids.add(node['id'])
            # Add child node list to parent node
            parent_node = node_dict.get(parent_id)
            if parent_node:
                parent_node.setdefault('children', []).append(node['id'])

    # Find root nodes (nodes that are not child nodes)
    root_ids = all_ids - child_ids

    # Mark the position of all nodes
    for node_id in all_ids:
        node = node_dict[node_id]
        children = node.get('children', [])
        if not children:
            node['position_in_tree'] = 'leaf_team'
        elif node_id in root_ids:
            node['position_in_tree'] = 'root_team'
        else:
            node['position_in_tree'] = 'trunk_team'

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
        self.url = 'https://api.github.com/graphql'
        self.orgs = self._fetch_all_organizations(save_to_json=save_to_json)
        self.orgs_slugs = [org['login'] for org in self.orgs]
        self.github_organization_managers = {orgs_slug: GitHubOrganizationManager(self.token, orgs_slug) for orgs_slug in self.orgs_slugs}
        logger.info(f"Initialized GitHubEnterpriseManager for enterprise: {enterprise_slug}")

    def _fetch_all_organizations(self, save_to_json=False):
        
        # GraphQL query
        query = '''
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
        ''' % self.enterprise_slug

        # Send POST request
        logger.info(f"Fetching all organizations for enterprise: {self.enterprise_slug}")
        response = requests.post(self.url, json={'query': query}, headers=self.headers)

        # Check response status code
        if response.status_code == 200:
            data = response.json()
            # print(data)
            if 'errors' in data:
                print(f'query failed, error message: {data["errors"][0]["message"]}')
                return {}
            all_orgs = data["data"].get("enterprise", {}).get("organizations", {}).get("nodes", [])

            dict_save_to_json_file(all_orgs, f'{self.enterprise_slug}_all_organizations', save_to_json=save_to_json)
            logger.info(f"Fetched {len(all_orgs)} organizations")
            return all_orgs
        else:
            print(f'request failed, error code：{response.status_code}')
            logger.error(f"Request failed with status code: {response.status_code}")
            return {}


class GitHubOrganizationManager:

    def __init__(self, organization_slug, save_to_json=True):
        self.organization_slug = organization_slug
        self.teams = self._fetch_all_teams(save_to_json=save_to_json)
        logger.info(f"Initialized GitHubOrganizationManager for organization: {organization_slug}")

    def get_copilot_usages(self, team_slug='all', save_to_json=True, position_in_tree='leaf_team'):
        urls = { self.organization_slug, (position_in_tree, f"https://api.github.com/orgs/{self.organization_slug}/copilot/usage") }
        if team_slug:
            if team_slug != 'all':
                urls = { team_slug: (position_in_tree, f"https://api.github.com/orgs/{self.organization_slug}/teams/{team_slug}/copilot/usage") }
            else:
                urls = { team['slug']: (team['position_in_tree'], f"https://api.github.com/orgs/{self.organization_slug}/teams/{team['slug']}/copilot/usage") for team in self.teams }
        
        datas = {}
        logger.info(f"Fetching Copilot usages for organization: {self.organization_slug}, team: {team_slug}")
        for _team_slug, position_in_tree_and_url in urls.items():
            position_in_tree, url = position_in_tree_and_url
            data = github_api_request_handler(url, error_return_value={})
            dict_save_to_json_file(data, f'{self.organization_slug}_{_team_slug}_copilot_usage', save_to_json=save_to_json)
            datas[_team_slug] = {
                'position_in_tree': position_in_tree,
                'copilot_usage_data': data
            }
            logger.info(f"Fetched Copilot usage for team: {_team_slug}")

        if team_slug == 'all':
            dict_save_to_json_file(datas, f'{self.organization_slug}_all_teams_copilot_usage', save_to_json=save_to_json)

        return datas
    
    def get_seat_info_settings(self, save_to_json=True):
        url = f"https://api.github.com/orgs/{self.organization_slug}/copilot/billing"
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

        seat_breakdown = data.get('seat_breakdown', {})
        for k, v in seat_breakdown.items():
            data[f'seat_{k}'] = v
        data.pop('seat_breakdown', None)

        # Inject organization_slug and today's date in the format 2024-12-15, and a hash value based on these two values
        data['organization_slug'] = self.organization_slug
        data['day'] = current_time()[:10]
        data['unique_hash'] = generate_unique_hash(
            data, 
            key_properties=['organization_slug', 'day']
        )

        dict_save_to_json_file(data, f'{self.organization_slug}_seat_info_settings', save_to_json=save_to_json)
        logger.info(f"Fetching seat info settings for organization: {self.organization_slug}")
        return data

    def get_seat_assignments(self, save_to_json=True):
        url = f"https://api.github.com/orgs/{self.organization_slug}/copilot/billing/seats"
        data = github_api_request_handler(url, error_return_value={})
        datas = []
        seats = data.get('seats', [])
        for seat in seats:

            # assignee sub dict
            seat['assignee_login'] = seat.get('assignee', {}).get('login')
            seat['assignee_html_url'] = seat.get('assignee', {}).get('html_url')
            seat.pop('assignee', None)

            # assigning_team sub dict
            seat['assignee_team_slug'] = seat.get('assigning_team', {}).get('slug')
            seat['assignee_team_html_url'] = seat.get('assigning_team', {}).get('html_url')
            seat.pop('assigning_team', None)
            
            seat['organization_slug'] = self.organization_slug
            seat['day'] = current_time()[:10]
            seat['unique_hash'] = generate_unique_hash(
                seat, 
                key_properties=['organization_slug', 'day', 'assignee_login']
            )
            
            last_activity_at = seat.get('last_activity_at')
            if last_activity_at:
                last_activity_date = datetime.strptime(last_activity_at, '%Y-%m-%dT%H:%M:%S%z')
                days_since_last_activity = (datetime.now(last_activity_date.tzinfo) - last_activity_date).days
            else:
                days_since_last_activity = -1
            seat['days_since_last_activity'] = days_since_last_activity

            datas.append(seat)

        dict_save_to_json_file(datas, f'{self.organization_slug}_seat_assignments', save_to_json=save_to_json)
        logger.info(f"Fetching seat assignments for organization: {self.organization_slug}")
        return datas

    def _fetch_all_teams(self, save_to_json=True):
        # Teams under the same org are essentially at the same level because the URL does not reflect the nested relationship, so team names cannot be duplicated
        
        url = f"https://api.github.com/orgs/{self.organization_slug}/teams"
        teams = github_api_request_handler(url, error_return_value=[])
        # if credential is expired, the return value is:
        # {'message': 'Bad credentials', 'documentation_url': 'https://docs.github.com/rest', 'status': '401'}
        if isinstance(teams, dict) and teams.get('status') == '401':
            logger.error(f"Bad credentials for organization: {self.organization_slug}")
            return []
        
        teams = self._add_fullpath_slug(teams)
        teams = assign_position_in_tree(teams)
        dict_save_to_json_file(teams, f'{self.organization_slug}_all_teams', save_to_json=save_to_json)
        logger.info(f"Fetching all teams for organization: {self.organization_slug}")

        return teams

    def _add_fullpath_slug(self, teams):
        id_to_team = {team['id']: team for team in teams}

        for team in teams:
            slugs = []
            current_team = team
            while current_team:
                slugs.append(current_team['slug'])
                parent = current_team.get('parent')
                if parent and 'id' in parent:
                    current_team = id_to_team.get(parent['id'])
                else:
                    current_team = None
            team['fullpath_slug'] = '/'.join(reversed(slugs))

        return teams



class DataSplitter:
    def __init__(self, data, additional_properties={}):
        self.data = data
        self.additional_properties = additional_properties
        self.correction_for_0 = 0

    def get_total_list(self):
        total_list = []
        logger.info(f"Generating total list from data")
        for entry in self.data:
            total_data = entry.copy()
            total_data.pop('breakdown', None)
            total_data = total_data | self.additional_properties
            total_data['unique_hash'] = generate_unique_hash(
                total_data, 
                key_properties=['organization_slug', 'team_slug', 'day']
            )

            # If the denominator value is 0, it is corrected to a uniform value
            total_data['total_suggestions_count'] = self.correction_for_0 if total_data['total_suggestions_count'] == 0 else total_data['total_suggestions_count']
            total_data['total_lines_suggested'] = self.correction_for_0 if total_data['total_lines_suggested'] == 0 else total_data['total_lines_suggested']
            total_data['total_chat_turns'] = self.correction_for_0 if total_data['total_chat_turns'] == 0 else total_data['total_chat_turns']

            total_list.append(total_data)
        return total_list

    def get_breakdown_list(self):
        breakdown_list = []
        logger.info(f"Generating breakdown list from data")
        for entry in self.data:
            day = entry.get('day')
            for breakdown_entry in entry.get('breakdown', []):
                breakdown_entry_with_day = breakdown_entry.copy()
                breakdown_entry_with_day['day'] = day
                breakdown_entry_with_day = breakdown_entry_with_day | self.additional_properties
                breakdown_entry_with_day['unique_hash'] = generate_unique_hash(
                    breakdown_entry_with_day, 
                    key_properties=['organization_slug', 'team_slug', 'day', 'language', 'editor']
                )

                # If the denominator value is 0, it is corrected to a uniform value
                breakdown_entry_with_day['suggestions_count'] = self.correction_for_0 if breakdown_entry_with_day['suggestions_count'] == 0 else breakdown_entry_with_day['suggestions_count']
                breakdown_entry_with_day['lines_suggested'] = self.correction_for_0 if breakdown_entry_with_day['lines_suggested'] == 0 else breakdown_entry_with_day['lines_suggested']

                breakdown_list.append(breakdown_entry_with_day)
        return breakdown_list



class ElasticsearchManager:

    def __init__(self, primary_key=Paras.primary_key):
        self.primary_key = primary_key
        self.es = Elasticsearch(
            Paras.elasticsearch_url
        )
        self.check_and_create_indexes()

    # Check if all indexes in the indexes are present, and if they don't, they are created based on the files in the mapping folder
    def check_and_create_indexes(self):
        for index_name in Indexes.__dict__:
            if index_name.startswith('index_'):
                index_name = Indexes.__dict__[index_name]
                if not self.es.indices.exists(index=index_name):
                    mapping_file = f'mapping/{index_name}_mapping.json'
                    with open(mapping_file, 'r') as f:
                        mapping = json.load(f)
                    self.es.indices.create(index=index_name, body=mapping)
                    logger.info(f"Created index: {index_name}")
                else:
                    logger.info(f"Index already exists: {index_name}")

    def write_to_es(self, index_name, data):
        last_updated_at = current_time()
        data['last_updated_at'] = last_updated_at
        doc_id = data.get(self.primary_key)
        logger.info(f"Writing data to Elasticsearch index: {index_name}")
        try:
            self.es.get(index=index_name, id=doc_id)
            self.es.update(index=index_name, id=doc_id, doc=data)
            logger.info(f'[updated] to [{index_name}]: {data}')
        except NotFoundError:
            self.es.index(index=index_name, id=doc_id, document=data)
            logger.info(f'[created] to [{index_name}]: {data}') 
 

def main(organization_slug):
    logger.info(f"==========================================================================================================")
    logger.info(f"Starting data processing for organization: {organization_slug}")
    github_org_manager = GitHubOrganizationManager(organization_slug) 
    es_manager = ElasticsearchManager()


    # Process seat info and settings
    logger.info(f"Processing Copilot seat info & settings for organization: {organization_slug}")
    data_seat_info_settings = github_org_manager.get_seat_info_settings()
    if not data_seat_info_settings:
        logger.warning(f"No Copilot seat info & settings found for organization: {organization_slug}")
    else:
        es_manager.write_to_es(Indexes.index_seat_info, data_seat_info_settings)
        logger.info(f"Data processing completed for organization: {organization_slug}")

    # Process seat assignments
    logger.info(f"Processing Copilot seat assignments for organization: {organization_slug}")
    data_seat_assignments = github_org_manager.get_seat_assignments()
    if not data_seat_assignments:
        logger.warning(f"No Copilot seat assignments found for organization: {organization_slug}")
    else:
        for seat_assignment in data_seat_assignments:
            es_manager.write_to_es(Indexes.index_seat_assignments, seat_assignment)
        logger.info(f"Data processing completed for organization: {organization_slug}")

    # Process usage data
    copilot_usage_datas = github_org_manager.get_copilot_usages(team_slug='all')
    logger.info(f"Processing Copilot usage data for organization: {organization_slug}")
    for team_slug, data_with_position in copilot_usage_datas.items():
        logger.info(f"Processing Copilot usage data for team: {team_slug}")

        # Expand data
        data = data_with_position.get('copilot_usage_data')
        position_in_tree = data_with_position.get('position_in_tree')

        # Check if there is data
        if not data:
            logger.warning(f"No Copilot usage data found for team: {team_slug}")
            continue

        data_splitter = DataSplitter(data, additional_properties={
            'organization_slug': organization_slug,
            'team_slug': team_slug,
            'position_in_tree': position_in_tree
        })

        total_list = data_splitter.get_total_list()
        dict_save_to_json_file(total_list, f'{team_slug}_total_list')
        breakdown_list = data_splitter.get_breakdown_list()
        dict_save_to_json_file(breakdown_list, f'{team_slug}_breakdown_list')

        
        for total_data in total_list:
            es_manager.write_to_es(Indexes.index_name_total, total_data)
        
        for breakdown_data in breakdown_list:
            es_manager.write_to_es(Indexes.index_name_breakdown, breakdown_data)
        logger.info(f"Data processing completed for team: {team_slug}")



if __name__ == '__main__':
    
    while True:
        try:
            # Split Paras.organization_slugs and process each organization, remember to remove spaces after splitting
            organization_slugs = Paras.organization_slugs.split(',')
            for organization_slug in organization_slugs:
                main(organization_slug.strip())
            logger.info(f"Sleeping for {Paras.execution_interval} hours before next execution...")
            for _ in range(Paras.execution_interval * 3600 // 3600):
                logger.info("Heartbeat: still running...")
                time.sleep(3600)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            time.sleep(5)
        finally:
            logger.info('-----------------Finished-----------------')
