def generate_insights(evaluation_results):
    def avg(scores):
        return sum(scores) / len(scores) if scores else 0.0

    prod_logic = {"completeness": [], "relevance": []}
    shad_logic = {"completeness": [], "relevance": []}
    prod_llm = {"completeness": [], "relevance": [], "quality": []}
    shad_llm = {"completeness": [], "relevance": [], "quality": []}
    prod_pii = shad_pii = prod_unsafe = shad_unsafe = 0

    for entry in evaluation_results:
        prod = entry["evaluation"]["prodagent"]
        shad = entry["evaluation"]["shadagent"]

        # Collect scores
        prod_logic["completeness"].append(prod["logic"]["completeness"])
        prod_logic["relevance"].append(prod["logic"]["relevance"])
        shad_logic["completeness"].append(shad["logic"]["completeness"])
        shad_logic["relevance"].append(shad["logic"]["relevance"])

        prod_llm["completeness"].append(prod["llm"]["completeness"])
        prod_llm["relevance"].append(prod["llm"]["relevance"])
        prod_llm["quality"].append(prod["llm"]["quality"])
        shad_llm["completeness"].append(shad["llm"]["completeness"])
        shad_llm["relevance"].append(shad["llm"]["relevance"])
        shad_llm["quality"].append(shad["llm"]["quality"])

        prod_pii += prod["pii_count"]
        shad_pii += shad["pii_count"]

        if prod["safety_score"] > 0.5:
            prod_unsafe += 1
        if shad["safety_score"] > 0.5:
            shad_unsafe += 1

    # Build summary
    insights = {
        "average_scores": {
            "prodagent": {
                "logic": {k: round(avg(v), 4) for k, v in prod_logic.items()},
                "llm": {k: round(avg(v), 4) for k, v in prod_llm.items()},
            },
            "shadagent": {
                "logic": {k: round(avg(v), 4) for k, v in shad_logic.items()},
                "llm": {k: round(avg(v), 4) for k, v in shad_llm.items()},
            },
        },
        "pii_violations": {
            "prodagent": prod_pii,
            "shadagent": shad_pii,
        },
        "unsafe_responses": {
            "prodagent": prod_unsafe,
            "shadagent": shad_unsafe,
        },
        "summary": ""
    }

    # Add summary
    if avg(shad_llm["quality"]) > avg(prod_llm["quality"]):
        insights["summary"] = "Shadow agent provides higher-quality responses based on LLM scores."
    elif avg(shad_llm["quality"]) < avg(prod_llm["quality"]):
        insights["summary"] = "Production agent provides more consistent high-quality responses."
    else:
        insights["summary"] = "Both agents perform similarly based on average quality."

    return insights
