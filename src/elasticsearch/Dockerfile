FROM docker.elastic.co/elasticsearch/elasticsearch:8.17.0

# Set environment variables
ENV discovery.type=single-node

COPY elasticsearch.yml /srv/elasticsearch/config/elasticsearch.yml

# Expose the default Elasticsearch port
EXPOSE 9200

# Run Elasticsearch
CMD ["elasticsearch" ]