#!/usr/bin/env python3

# Test script for the calculate_top_values function
import sys
import os

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'cpuad-updater'))

from main import calculate_top_values

# Test data similar to what we see in the logs
test_user_data = {
    'user_login': 'test_user',
    'totals_by_language_model': [
        {
            'language': 'python',
            'model': 'gpt-4',
            'code_generation_activity_count': 10
        },
        {
            'language': 'javascript',
            'model': 'gpt-3.5',
            'code_generation_activity_count': 5
        },
        {
            'language': 'python',
            'model': 'gpt-3.5',
            'code_generation_activity_count': 3
        }
    ],
    'totals_by_feature': [
        {
            'feature': 'code_completion',
            'code_generation_activity_count': 8,
            'user_initiated_interaction_count': 2
        },
        {
            'feature': 'chat_panel_ask_mode',
            'code_generation_activity_count': 5,
            'user_initiated_interaction_count': 3
        }
    ],
    'totals_by_language_feature': [
        {
            'language': 'python',
            'feature': 'code_completion',
            'code_generation_activity_count': 6
        },
        {
            'language': 'javascript',
            'feature': 'code_completion',
            'code_generation_activity_count': 4
        }
    ]
}

print("Testing calculate_top_values function...")
print("Input data:")
print(f"  totals_by_language_model: {test_user_data['totals_by_language_model']}")
print(f"  totals_by_feature: {test_user_data['totals_by_feature']}")

result = calculate_top_values(test_user_data)
print(f"\nResult: {result}")

print(f"\nExpected values:")
print(f"  top_model: 'gpt-4' (10 activity)")
print(f"  top_language: 'python' (10+6=16 activity)")
print(f"  top_feature: 'code_completion' -> 'Code Completion' (8+2=10 activity)")