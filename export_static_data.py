import json
import random
import os
import math


def generate_mock_data():
    random.seed(42)
    n_respondents = 150
    n_items = 25

    # Groups
    group_membership = {}
    for i in range(n_respondents):
        resp_id = f"resp_{i}"
        group_membership[resp_id] = "M" if i < 75 else "F"

    # Items
    items = []
    for i in range(n_items):
        items.append(
            {
                "id": f"item_{i + 1:02d}",
                "title": f"Question {i + 1}",
                "type": "multiple_choice",
            }
        )

    # Responses
    responses = {}
    for item in items:
        item_id = item["id"]
        # Add some bias to item 5
        is_biased = item_id == "item_05"

        item_responses = {}
        for resp_id, group in group_membership.items():
            if is_biased and group == "F":
                # Female group performs worse on item 5
                prob = 0.35
            else:
                prob = 0.75 - (random.random() * 0.2)

            item_responses[resp_id] = 1 if random.random() < prob else 0
        responses[item_id] = item_responses

    # Calculate scores
    total_scores = {}
    for resp_id in group_membership:
        score = sum(responses[item_id][resp_id] for item_id in responses)
        total_scores[resp_id] = score

    # Analytics
    item_performance = []
    for item in items:
        item_id = item["id"]
        resps = list(responses[item_id].values())
        difficulty = sum(resps) / len(resps)

        # Simple discrimination
        scores = [total_scores[r] for r in responses[item_id]]
        # Point-biserial approx
        avg_total = sum(scores) / len(scores)

        item_performance.append(
            {
                "id": item_id,
                "title": item["title"],
                "difficulty": round(difficulty, 3),
                "discrimination": round(0.4 + (random.random() * 0.2), 3),
                "response_count": n_respondents,
            }
        )

    # DIF Analysis (Simplified MH)
    dif_results = {}
    for item in items:
        item_id = item["id"]
        ref_group = [
            responses[item_id][r] for r, g in group_membership.items() if g == "M"
        ]
        foc_group = [
            responses[item_id][r] for r, g in group_membership.items() if g == "F"
        ]

        p_ref = sum(ref_group) / len(ref_group)
        p_foc = sum(foc_group) / len(foc_group)

        diff = p_ref - p_foc
        classification = "no_DIF"
        if abs(diff) > 0.25:
            classification = "severe_DIF"
        elif abs(diff) > 0.15:
            classification = "moderate_DIF"

        dif_results[item_id] = {
            "chi_square": round(diff * 10, 3),
            "p_value": 0.001 if abs(diff) > 0.2 else 0.5,
            "classification": classification,
            "reference_pass_rate": round(p_ref, 3),
            "focal_pass_rate": round(p_foc, 3),
        }

    # Final Export
    export_data = {
        "item_performance": {
            "assessment_id": "demo-001",
            "items": item_performance,
            "summary": {"mean_difficulty": 0.68, "reliability": 0.84},
        },
        "fairness_report": {
            "assessment_id": "demo-001",
            "group_attribute": "gender",
            "dif_results": dif_results,
            "summary": {"biased_items_count": 1, "impact_score": 95.0},
        },
    }

    os.makedirs("docs/analytics/data", exist_ok=True)
    with open("docs/analytics/data/demo.json", "w") as f:
        json.dump(export_data, f, indent=2)
    print("Exported mock data to docs/analytics/data/demo.json")


if __name__ == "__main__":
    generate_mock_data()
