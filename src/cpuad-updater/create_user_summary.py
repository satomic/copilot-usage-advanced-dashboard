"""
Script to create aggregated user summary with overall top_model, top_language, top_feature
"""
import os
from elasticsearch import Elasticsearch
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

def get_es_client():
    """Initialize Elasticsearch client"""
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_url = f"http://{es_host}:{es_port}"
    
    es_user = os.getenv("ELASTICSEARCH_USER")
    es_password = os.getenv("ELASTICSEARCH_PASSWORD")
    
    if es_user and es_password:
        es = Elasticsearch([es_url], http_auth=(es_user, es_password))
        logger.info(f"Connecting to Elasticsearch at {es_url} with authentication")
    else:
        es = Elasticsearch([es_url])
        logger.info("Using Elasticsearch without authentication")
    
    return es

def create_user_summaries():
    """Aggregate user metrics and create summary documents"""
    es = get_es_client()
    
    # Get all user metrics
    query = {
        "size": 10000,
        "query": {"match_all": {}}
    }
    
    response = es.search(index="copilot_user_metrics", body=query)
    
    # Group by user
    user_data = {}
    for hit in response['hits']['hits']:
        doc = hit['_source']
        user_login = doc.get('user_login')
        
        if user_login not in user_data:
            user_data[user_login] = {
                'models': [],
                'languages': [],
                'features': [],
                'organization_slug': doc.get('organization_slug')
            }
        
        if doc.get('top_model'):
            user_data[user_login]['models'].append(doc['top_model'])
        if doc.get('top_language'):
            user_data[user_login]['languages'].append(doc['top_language'])
        if doc.get('top_feature'):
            user_data[user_login]['features'].append(doc['top_feature'])
    
    # Calculate most frequent values and write to new index
    summary_index = "copilot_user_metrics_summary"
    
    # Create index if it doesn't exist
    if not es.indices.exists(index=summary_index):
        es.indices.create(index=summary_index, body={
            "mappings": {
                "properties": {
                    "user_login": {"type": "keyword"},
                    "top_model": {"type": "keyword"},
                    "top_language": {"type": "keyword"},
                    "top_feature": {"type": "keyword"},
                    "organization_slug": {"type": "keyword"},
                    "@timestamp": {"type": "date"}
                }
            }
        })
        logger.info(f"Created index: {summary_index}")
    
    # Write summary documents
    for user_login, data in user_data.items():
        # Get most common values
        top_model = Counter(data['models']).most_common(1)[0][0] if data['models'] else 'unknown'
        top_language = Counter(data['languages']).most_common(1)[0][0] if data['languages'] else 'unknown'
        top_feature = Counter(data['features']).most_common(1)[0][0] if data['features'] else 'unknown'
        
        from datetime import datetime
        doc = {
            'user_login': user_login,
            'top_model': top_model,
            'top_language': top_language,
            'top_feature': top_feature,
            'organization_slug': data['organization_slug'],
            '@timestamp': datetime.utcnow().isoformat()
        }
        
        # Use user_login as document ID to enable updates
        es.index(index=summary_index, id=user_login, body=doc)
        logger.info(f"Updated summary for user: {user_login}")
    
    logger.info(f"Created/updated {len(user_data)} user summary documents")
    return len(user_data)

if __name__ == "__main__":
    count = create_user_summaries()
    logger.info(f"Total user summaries created: {count}")
    
    logger.info(f"Created/updated {len(user_data)} user summaries")

if __name__ == "__main__":
    create_user_summaries()
