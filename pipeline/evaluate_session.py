from models import hap_call, presidio_call, llm_judge
from utils import insight_generator
from utils.s3_helper import load_session_data, save_evaluation_results
from metrics.logic_scores import calculate_completeness_score, calculate_relevance_score
from metrics.factuality_scores import calculate_factuality_score  # Add this import

def evaluate(session_id, bucket):
    db = load_session_data(session_id, bucket)
    if not db:
        return

    results = []

    for row in db:
        query = row["request"]
        request_id = row["request_id"]
        
        # Add timestamp and session_id to results for temporal tracking
        timestamp = row.get("unix_timestamp")
        readable_time = row.get("readable_timestamp")

        # Determine if we're in single or dual agent mode
        is_dual_agent = "prodagent_response" in row and "shadagent_response" in row

        if is_dual_agent:
            # Dual agent evaluation
            prod_response = row["prodagent_response"]
            shad_response = row["shadagent_response"]

            # HAP evaluation
            hap_result_prod = hap_call.invoke_hap(prod_response)[0]
            hap_result_shad = hap_call.invoke_hap(shad_response)[0]

            # Presidio PII detection
            pii_prod = presidio_call.invoke_presidio(prod_response)
            pii_shad = presidio_call.invoke_presidio(shad_response)

            # Logic scores
            logic_score_prod = {
                "completeness": calculate_completeness_score(prod_response),
                "relevance": calculate_relevance_score(query, prod_response),
                "factuality": calculate_factuality_score(query, prod_response)
            }
            logic_score_shad = {
                "completeness": calculate_completeness_score(shad_response),
                "relevance": calculate_relevance_score(query, shad_response),
                "factuality": calculate_factuality_score(query, shad_response)
            }

            # LLM scores
            llm_scores_prod = llm_judge.evaluate_with_llm(query, prod_response)
            llm_scores_shad = llm_judge.evaluate_with_llm(query, shad_response)

            # Combine results
            results.append({
                "request_id": request_id,
                "session_id": row.get("session_id"),
                "timestamp": timestamp,
                "readable_timestamp": readable_time,
                "query": query,
                "prod_response": prod_response,
                "shad_response": shad_response,
                "evaluation": {
                    "prodagent": {
                        "logic": logic_score_prod,
                        "llm": llm_scores_prod,
                        "harmfulness_score": hap_result_prod["score"],
                        "unsafe": bool(hap_result_prod["unsafe"]),
                        "pii_count": len(pii_prod)
                    },
                    "shadagent": {
                        "logic": logic_score_shad,
                        "llm": llm_scores_shad,
                        "harmfulness_score": hap_result_shad["score"],
                        "unsafe": bool(hap_result_shad["unsafe"]),
                        "pii_count": len(pii_shad)
                    }
                }
            })
        else:
            # Single agent evaluation
            agent_response = row["agent_response"]

            # HAP evaluation
            hap_result = hap_call.invoke_hap(agent_response)[0]

            # Presidio PII detection
            pii = presidio_call.invoke_presidio(agent_response)

            # Logic scores
            logic_score = {
                "completeness": calculate_completeness_score(agent_response),
                "relevance": calculate_relevance_score(query, agent_response),
                "factuality": calculate_factuality_score(query, agent_response)
            }

            # LLM scores
            llm_scores = llm_judge.evaluate_with_llm(query, agent_response)

            # Combine results
            results.append({
                "request_id": request_id,
                "session_id": row.get("session_id"),
                "timestamp": timestamp,
                "readable_timestamp": readable_time,
                "query": query,
                "agent_response": agent_response,
                "evaluation": {
                    "agent": {
                        "logic": logic_score,
                        "llm": llm_scores,
                        "harmfulness_score": hap_result["score"],
                        "unsafe": bool(hap_result["unsafe"]),
                        "pii_count": len(pii)
                    }
                }
            })

    # Generate high-level insights across all entries
    insights = insight_generator.generate_insights(results)

    final_output = {
        "evaluation_results": results,
        "insights": insights
    }

    save_evaluation_results(session_id, final_output, bucket)
    print("Evaluation complete.")
    print("Summary:", insights["summary"])
