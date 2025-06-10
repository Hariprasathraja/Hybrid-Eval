from models import hap_call, presidio_call, llm_judge
from utils import insight_generator
from utils.s3_helper import load_session_data, save_evaluation_results
from metrics.logic_scores import calculate_completeness_score, calculate_relevance_score

def evaluate(session_id, bucket):
    db = load_session_data(session_id, bucket)
    if not db:
        return

    results = []

    for row in db:
        query = row["request"]
        prod_response = row["prodagent_response"]
        shad_response = row["shadagent_response"]  # ⬅️ ADD THIS
        request_id = row["request_id"]

        # HAP + Presidio
        hap_score_prod = hap_call.invoke_hap(prod_response)[0]
        hap_score_shad = hap_call.invoke_hap(shad_response)[0]
        pii_prod = presidio_call.invoke_presidio(prod_response)
        pii_shad = presidio_call.invoke_presidio(shad_response)

        # Logic scores
        logic_score_prod = {
            "completeness": calculate_completeness_score(prod_response),
            "relevance": calculate_relevance_score(query, prod_response)
        }
        logic_score_shad = {
            "completeness": calculate_completeness_score(shad_response),
            "relevance": calculate_relevance_score(query, shad_response)
        }

        # LLM scores
        llm_scores_prod = llm_judge.evaluate_with_llm(query, prod_response)
        llm_scores_shad = llm_judge.evaluate_with_llm(query, shad_response)

        results.append({
            "request_id": request_id,
            "query": query,
            "prod_response": prod_response,
            "shad_response": shad_response,
            "evaluation": {
                "prodagent": {
                    "logic": logic_score_prod,
                    "llm": llm_scores_prod,
                    "safety_score": hap_score_prod,
                    "pii_count": len(pii_prod)
                },
                "shadagent": {
                    "logic": logic_score_shad,
                    "llm": llm_scores_shad,
                    "safety_score": hap_score_shad,
                    "pii_count": len(pii_shad)
                }
            }
        })

    insights = insight_generator.generate_insights(results)

    final_output = {
        "evaluation_results": results,
        "insights": insights
    }
    save_evaluation_results(session_id, final_output, bucket)
    print("Evaluation complete.")
