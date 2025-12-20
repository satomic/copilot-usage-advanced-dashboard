curl -X PUT "http://$ELASTICSEARCH_URL/copilot_usage_total" -H 'Content-Type: application/json' -d @mapping/copilot_usage_total_mapping.json
curl -X PUT "http://$ELASTICSEARCH_URL/copilot_usage_breakdown" -H 'Content-Type: application/json' -d @mapping/copilot_usage_breakdown_mapping.json
curl -X PUT "http://$ELASTICSEARCH_URL/copilot_usage_breakdown_chat" -H 'Content-Type: application/json' -d @mapping/copilot_usage_breakdown_chat_mapping.json
curl -X PUT "http://$ELASTICSEARCH_URL/copilot_seat_info_settings" -H 'Content-Type: application/json' -d @mapping/copilot_seat_info_settings_mapping.json
curl -X PUT "http://$ELASTICSEARCH_URL/copilot_seat_assignments" -H 'Content-Type: application/json' -d @mapping/copilot_seat_assignments_mapping.json
curl -X PUT "http://$ELASTICSEARCH_URL/copilot_user_adoption" -H 'Content-Type: application/json' -d @mapping/copilot_user_adoption_mapping.json
curl -X PUT "http://$ELASTICSEARCH_URL/copilot_user_metrics" -H 'Content-Type: application/json' -d @mapping/copilot_user_metrics_mapping.json