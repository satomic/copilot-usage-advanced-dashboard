FROM docker.elastic.co/elasticsearch/elasticsearch:8.17.0

# USER root

# # Install dependencies
# RUN apt-get update && \
#     apt-get install -y libcap2-bin && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# RUN setcap 'cap_net_bind_service=+ep' /usr/share/elasticsearch/bin/elasticsearch

# USER elasticsearch

COPY elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml

# Expose the default Elasticsearch port
EXPOSE 9200

# Run Elasticsearch
CMD ["elasticsearch"]