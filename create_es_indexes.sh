curl -X PUT "http://localhost:9200/copilot_usage_total" -H 'Content-Type: application/json' -d @mapping/copilot_usage_total_mapping.json
curl -X PUT "http://localhost:9200/copilot_usage_breakdown" -H 'Content-Type: application/json' -d @mapping/copilot_usage_breakdown_mapping.json
curl -X PUT "http://localhost:9200/copilot_seat_info_settings" -H 'Content-Type: application/json' -d @mapping/copilot_seat_info_settings_mapping.json
curl -X PUT "http://localhost:9200/copilot_seat_assignments" -H 'Content-Type: application/json' -d @mapping/copilot_seat_assignments_mapping.json