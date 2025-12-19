#!/usr/bin/env python3

def calculate_top_values(user_data):
    """Calculate top model, language, and feature from user metrics data"""
    
    # Initialize counters
    model_counts = {}
    language_counts = {}
    feature_counts = {}
    
    print(f"DEBUG: Processing user data for {user_data.get('user_login', 'unknown')}")
    
    # Extract from totals_by_language_model
    for entry in user_data.get('totals_by_language_model', []):
        language = entry.get('language', 'unknown')
        model = entry.get('model', 'unknown')
        activity_count = entry.get('code_generation_activity_count', 0)
        
        print(f"DEBUG: Found language={language}, model={model}, activity={activity_count}")
        
        language_counts[language] = language_counts.get(language, 0) + activity_count
        model_counts[model] = model_counts.get(model, 0) + activity_count
    
    # Extract from totals_by_feature
    for entry in user_data.get('totals_by_feature', []):
        feature = entry.get('feature', 'unknown')
        activity_count = entry.get('code_generation_activity_count', 0) + entry.get('user_initiated_interaction_count', 0)
        
        print(f"DEBUG: Found feature={feature}, activity={activity_count}")
        
        feature_counts[feature] = feature_counts.get(feature, 0) + activity_count
    
    # Extract from totals_by_language_feature (additional language data)
    for entry in user_data.get('totals_by_language_feature', []):
        language = entry.get('language', 'unknown')
        activity_count = entry.get('code_generation_activity_count', 0)
        
        print(f"DEBUG: Found additional language={language}, activity={activity_count}")
        
        language_counts[language] = language_counts.get(language, 0) + activity_count
    
    print(f"DEBUG: Final counts - models: {model_counts}")
    print(f"DEBUG: Final counts - languages: {language_counts}")
    print(f"DEBUG: Final counts - features: {feature_counts}")
    
    # Find top values (most used)
    top_model = max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else 'unknown'
    top_language = max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else 'unknown'
    top_feature = max(feature_counts.items(), key=lambda x: x[1])[0] if feature_counts else 'unknown'
    
    # Map feature names to more user-friendly names
    feature_mapping = {
        'chat_panel_ask_mode': 'Chat',
        'chat_panel_agent_mode': 'Agent',
        'agent_edit': 'Agent',
        'code_completion': 'Code Completion',
        'inline_chat': 'Inline Chat'
    }
    
    top_feature = feature_mapping.get(top_feature, top_feature)
    
    result = {
        'top_model': top_model,
        'top_language': top_language, 
        'top_feature': top_feature
    }
    
    print(f"DEBUG: Calculated result: {result}")
    
    return result

# Test data from the actual logs
test_user_data = {
    'user_login': 'sombaner_octocps',
    'totals_by_language_model': [
        {
            'language': 'bash',
            'model': 'unknown',
            'code_generation_activity_count': 2
        },
        {
            'language': 'python',
            'model': 'unknown', 
            'code_generation_activity_count': 1
        }
    ],
    'totals_by_feature': [
        {
            'feature': 'chat_panel_ask_mode',
            'user_initiated_interaction_count': 1,
            'code_generation_activity_count': 3
        }
    ],
    'totals_by_language_feature': [
        {
            'language': 'python',
            'feature': 'chat_panel_ask_mode',
            'code_generation_activity_count': 1
        },
        {
            'language': 'bash',
            'feature': 'chat_panel_ask_mode', 
            'code_generation_activity_count': 2
        }
    ]
}

print("Testing calculate_top_values function with real data...")
result = calculate_top_values(test_user_data)
print(f"\nFinal result: {result}")