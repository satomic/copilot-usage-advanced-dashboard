curl -X POST http://localhost:3000/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-breakdown",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://localhost:9200",
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

curl -X POST http://localhost:3000/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-total",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://localhost:9200",
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


curl -X POST http://localhost:3000/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-seat-info-settings",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://localhost:9200",
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

curl -X POST http://localhost:3000/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-seat-assignments",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://localhost:9200",
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

