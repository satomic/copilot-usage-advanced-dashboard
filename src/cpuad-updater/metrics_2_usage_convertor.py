import json


def convert_day(metrics_day):
    # Use the 'date' field in the Metrics API as the 'day' field in the Usage API
    day = metrics_day.get("date")

    # Handle Copilot IDE code completion indicators
    code_completions = metrics_day.get("copilot_ide_code_completions")
    total_suggestions_count = 0
    total_acceptances_count = 0
    total_lines_suggested = 0
    total_lines_accepted = 0

    # breakdown will summarize completion-related metrics by editor and language
    breakdown_dict = {}

    if code_completions:
        editors = code_completions.get("editors", [])
        for editor in editors:
            editor_name = editor.get("name", "unknown")
            for model in editor.get("models", []):
                model_name = model.get("name", "unknown")
                for lang in model.get("languages", []):
                    lang_name = lang.get("name", "unknown")
                    key = (editor_name, model_name, lang_name)
                    if key not in breakdown_dict:
                        breakdown_dict[key] = {
                            "editor": editor_name,
                            "model": model_name,
                            "language": lang_name,
                            "suggestions_count": 0,
                            "acceptances_count": 0,
                            "lines_suggested": 0,
                            "lines_accepted": 0,
                            "active_users": lang.get("total_engaged_users", 0),
                        }
                    breakdown_dict[key]["suggestions_count"] += lang.get(
                        "total_code_suggestions", 0
                    )
                    breakdown_dict[key]["acceptances_count"] += lang.get(
                        "total_code_acceptances", 0
                    )
                    breakdown_dict[key]["lines_suggested"] += lang.get(
                        "total_code_lines_suggested", 0
                    )
                    breakdown_dict[key]["lines_accepted"] += lang.get(
                        "total_code_lines_accepted", 0
                    )

                    total_suggestions_count += lang.get("total_code_suggestions", 0)
                    total_acceptances_count += lang.get("total_code_acceptances", 0)
                    total_lines_suggested += lang.get("total_code_lines_suggested", 0)
                    total_lines_accepted += lang.get("total_code_lines_accepted", 0)

    breakdown_list = list(breakdown_dict.values())

    # Handle Copilot IDE chat indicators
    chat = metrics_day.get("copilot_ide_chat")
    total_chat_acceptances = 0
    total_chat_turns = 0
    total_active_chat_users = 0
    total_chat_copy_events = 0
    total_chat_insertion_events = 0

    breakdown_chat_dict = {}

    if chat:
        total_active_chat_users = chat.get("total_engaged_users", 0)
        for editor in chat.get("editors", []):
            editor_name = editor.get("name", "unknown")
            for model in editor.get("models", []):
                model_name = model.get("name", "unknown")
                key = (editor_name, model_name)
                if key not in breakdown_chat_dict:
                    breakdown_chat_dict[key] = {
                        "editor": editor_name,
                        "model": model_name,
                        "chat_turns": 0,
                        "chat_copy_events": 0,
                        "chat_insertion_events": 0,
                        "chat_acceptances": 0,
                        "active_users": model.get("total_engaged_users", 0),
                    }
                total_chat_copy_events += model.get("total_chat_copy_events", 0)
                total_chat_insertion_events += model.get(
                    "total_chat_insertion_events", 0
                )
                total_chat_acceptances += model.get(
                    "total_chat_insertion_events", 0
                ) + model.get("total_chat_copy_events", 0)
                total_chat_turns += model.get("total_chats", 0)
                breakdown_chat_dict[key]["chat_turns"] += model.get("total_chats", 0)
                breakdown_chat_dict[key]["chat_copy_events"] += model.get(
                    "total_chat_copy_events", 0
                )
                breakdown_chat_dict[key]["chat_insertion_events"] += model.get(
                    "total_chat_insertion_events", 0
                )
                breakdown_chat_dict[key]["chat_acceptances"] += model.get(
                    "total_chat_insertion_events", 0
                ) + model.get("total_chat_copy_events", 0)

    breakdown_chat_list = list(breakdown_chat_dict.values())

    # --- Copilot dotcom chat metrics ---
    dotcom_chat = metrics_day.get("copilot_dotcom_chat", {})
    dotcom_chat_total_engaged_users = dotcom_chat.get("total_engaged_users", 0)
    dotcom_chat_total_chats = 0
    dotcom_chat_breakdown = []
    for model in dotcom_chat.get("models", []):
        model_name = model.get("name", "unknown")
        is_custom_model = model.get("is_custom_model", False)
        custom_model_training_date = model.get("custom_model_training_date")
        total_engaged_users = model.get("total_engaged_users", 0)
        total_chats = model.get("total_chats", 0)
        dotcom_chat_total_chats += total_chats
        dotcom_chat_breakdown.append(
            {
                "model": model_name,
                "is_custom_model": is_custom_model,
                "custom_model_training_date": custom_model_training_date,
                "total_engaged_users": total_engaged_users,
                "total_chats": total_chats,
            }
        )

    # --- Copilot dotcom pull request/code review metrics ---
    dotcom_pr = metrics_day.get("copilot_dotcom_pull_requests", {})
    dotcom_pr_total_engaged_users = dotcom_pr.get("total_engaged_users", 0)
    dotcom_pr_total_summaries = 0
    dotcom_pr_breakdown = []
    for repo in dotcom_pr.get("repositories", []):
        repo_name = repo.get("name", "unknown")
        repo_engaged_users = repo.get("total_engaged_users", 0)
        for model in repo.get("models", []):
            model_name = model.get("name", "unknown")
            is_custom_model = model.get("is_custom_model", False)
            custom_model_training_date = model.get("custom_model_training_date")
            total_pr_summaries_created = model.get("total_pr_summaries_created", 0)
            model_engaged_users = model.get("total_engaged_users", 0)
            dotcom_pr_total_summaries += total_pr_summaries_created
            dotcom_pr_breakdown.append(
                {
                    "repository": repo_name,
                    "repo_engaged_users": repo_engaged_users,
                    "model": model_name,
                    "is_custom_model": is_custom_model,
                    "custom_model_training_date": custom_model_training_date,
                    "total_pr_summaries_created": total_pr_summaries_created,
                    "model_engaged_users": model_engaged_users,
                }
            )

    usage = {
        "day": day,
        "total_suggestions_count": total_suggestions_count,
        "total_acceptances_count": total_acceptances_count,
        "total_lines_suggested": total_lines_suggested,
        "total_lines_accepted": total_lines_accepted,
        "total_active_users": metrics_day.get("total_active_users", 0),
        "total_chat_acceptances": total_chat_acceptances,
        "total_chat_turns": total_chat_turns,
        "total_active_chat_users": total_active_chat_users,
        "total_chat_copy_events": total_chat_copy_events,
        "total_chat_insertion_events": total_chat_insertion_events,
        "breakdown": breakdown_list,
        "breakdown_chat": breakdown_chat_list,
        # --- dotcom metrics ---
        "dotcom_chat_total_engaged_users": dotcom_chat_total_engaged_users,
        "dotcom_chat_total_chats": dotcom_chat_total_chats,
        "dotcom_chat_breakdown": dotcom_chat_breakdown,
        "dotcom_pr_total_engaged_users": dotcom_pr_total_engaged_users,
        "dotcom_pr_total_summaries": dotcom_pr_total_summaries,
        "dotcom_pr_breakdown": dotcom_pr_breakdown,
    }
    return usage


def convert_metrics_to_usage(metrics):
    # metrics is a list, each element is the indicator data for one day
    return [convert_day(day) for day in metrics]


def main():
    # if len(sys.argv) < 3:
    #     print("Usage: python conversion.py input.json output.json")
    #     sys.exit(1)
    input_file = "logs/2025-02-22/nekoaru_level1-team1_copilot_metrics_2025-02-22.json"  # sys.argv[1]
    output_file = "tmp/output.json"  # sys.argv[2]

    with open(input_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    usage = convert_metrics_to_usage(metrics)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(usage, f, indent=2)


if __name__ == "__main__":
    main()
