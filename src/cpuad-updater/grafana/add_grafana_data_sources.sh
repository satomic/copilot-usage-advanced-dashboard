curl -X POST http://$GRAFANA_URL/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-breakdown",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://$ELASTICSEARCH_URL",
  "basicAuth": false,
  "withCredentials": false,
  "isDefault": false,
  "jsonData": {
    "includeFrozen": false,
    "index": "copilot_usage_breakdown",
    "logLevelField": "",
    "logMessageField": "",
    "maxConcurrentShardRequests": 5,
    "timeField": "day",
    "timeInterval": "1d"
  }
}'


curl -X POST http://$GRAFANA_URL/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-breakdown-chat",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://$ELASTICSEARCH_URL",
  "basicAuth": false,
  "withCredentials": false,
  "isDefault": false,
  "jsonData": {
    "includeFrozen": false,
    "index": "copilot_usage_breakdown_chat",
    "logLevelField": "",
    "logMessageField": "",
    "maxConcurrentShardRequests": 5,
    "timeField": "day",
    "timeInterval": "1d"
  }
}'


curl -X POST http://$GRAFANA_URL/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-total",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://$ELASTICSEARCH_URL",
  "basicAuth": false,
  "withCredentials": false,
  "isDefault": false,
  "jsonData": {
    "includeFrozen": false,
    "index": "copilot_usage_total",
    "logLevelField": "",
    "logMessageField": "",
    "maxConcurrentShardRequests": 5,
    "timeField": "day",
    "timeInterval": "1d"
  }
}'


curl -X POST http://$GRAFANA_URL/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-seat-info-settings",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://$ELASTICSEARCH_URL",
  "basicAuth": false,
  "withCredentials": false,
  "isDefault": false,
  "jsonData": {
    "includeFrozen": false,
    "index": "copilot_seat_info_settings",
    "logLevelField": "",
    "logMessageField": "",
    "maxConcurrentShardRequests": 5,
    "timeField": "day",
    "timeInterval": "1d"
  }
}'

curl -X POST http://$GRAFANA_URL/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-seat-assignments",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://$ELASTICSEARCH_URL",
  "basicAuth": false,
  "withCredentials": false,
  "isDefault": false,
  "jsonData": {
    "includeFrozen": false,
    "index": "copilot_seat_assignments",
    "logLevelField": "",
    "logMessageField": "",
    "maxConcurrentShardRequests": 5,
    "timeField": "day",
    "timeInterval": "1d"
  }
}'

