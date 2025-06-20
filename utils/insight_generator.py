def generate_insights(evaluation_results):
    def avg(scores):
        return sum(scores) / len(scores) if scores else 0.0

    # Determine if we're in single or dual agent mode
    is_dual_agent = all("prodagent" in entry["evaluation"] and "shadagent" in entry["evaluation"] for entry in evaluation_results)
    
    # Initialize metrics containers based on mode
    if is_dual_agent:
        prod_logic = {"completeness": [], "relevance": [], "factuality": []}
        shad_logic = {"completeness": [], "relevance": [], "factuality": []}
        prod_llm = {"completeness": [], "relevance": [], "quality": []}
        shad_llm = {"completeness": [], "relevance": [], "quality": []}
        prod_pii = shad_pii = prod_unsafe = shad_unsafe = 0
        prod_harmfulness_scores = []
        shad_harmfulness_scores = []
    else:
        agent_logic = {"completeness": [], "relevance": [], "factuality": []}
        agent_llm = {"completeness": [], "relevance": [], "quality": []}
        agent_pii = agent_unsafe = 0
        agent_harmfulness_scores = []
    
    # For temporal analysis
    time_ordered_results = sorted(evaluation_results, key=lambda x: x.get("timestamp", 0))
    session_data = {}

    for entry in evaluation_results:
        # Handle dual agent case
        if is_dual_agent:
            prod = entry["evaluation"]["prodagent"]
            shad = entry["evaluation"]["shadagent"]
            
            # Track session data
            session_id = entry.get("session_id", "unknown")
            if session_id not in session_data:
                session_data[session_id] = {
                    "prod_scores": [], 
                    "shad_scores": [],
                    "timestamps": []
                }
                
            # Calculate overall score for this entry
            prod_entry_score = (prod["logic"]["completeness"] + 
                               prod["logic"]["relevance"] + 
                               prod["logic"].get("factuality", 0)) / 3
            shad_entry_score = (shad["logic"]["completeness"] + 
                               shad["logic"]["relevance"] + 
                               shad["logic"].get("factuality", 0)) / 3
                               
            # Add to session tracking
            session_data[session_id]["prod_scores"].append(prod_entry_score)
            session_data[session_id]["shad_scores"].append(shad_entry_score)
            session_data[session_id]["timestamps"].append(entry.get("timestamp", 0))

            # Logic
            prod_logic["completeness"].append(prod["logic"]["completeness"])
            prod_logic["relevance"].append(prod["logic"]["relevance"])
            shad_logic["completeness"].append(shad["logic"]["completeness"])
            shad_logic["relevance"].append(shad["logic"]["relevance"])
            
            # Add factuality if available
            if "factuality" in prod["logic"]:
                prod_logic["factuality"].append(prod["logic"]["factuality"])
            if "factuality" in shad["logic"]:
                shad_logic["factuality"].append(shad["logic"]["factuality"])

            # LLM
            for metric in ["completeness", "relevance", "quality"]:
                prod_llm[metric].append(prod["llm"][metric])
                shad_llm[metric].append(shad["llm"][metric])

            # PII + Unsafe + Harmfulness
            prod_pii += prod["pii_count"]
            shad_pii += shad["pii_count"]
            if prod["unsafe"]: prod_unsafe += 1
            if shad["unsafe"]: shad_unsafe += 1
            prod_harmfulness_scores.append(prod["harmfulness_score"])
            shad_harmfulness_scores.append(shad["harmfulness_score"])
        
        # Handle single agent case
        else:
            agent = entry["evaluation"]["agent"]
            
            # Track session data
            session_id = entry.get("session_id", "unknown")
            if session_id not in session_data:
                session_data[session_id] = {
                    "agent_scores": [],
                    "timestamps": []
                }
                
            # Calculate overall score for this entry
            agent_entry_score = (agent["logic"]["completeness"] + 
                               agent["logic"]["relevance"] + 
                               agent["logic"].get("factuality", 0)) / 3
                               
            # Add to session tracking
            session_data[session_id]["agent_scores"].append(agent_entry_score)
            session_data[session_id]["timestamps"].append(entry.get("timestamp", 0))

            # Logic
            agent_logic["completeness"].append(agent["logic"]["completeness"])
            agent_logic["relevance"].append(agent["logic"]["relevance"])
            
            # Add factuality if available
            if "factuality" in agent["logic"]:
                agent_logic["factuality"].append(agent["logic"]["factuality"])

            # LLM
            for metric in ["completeness", "relevance", "quality"]:
                agent_llm[metric].append(agent["llm"][metric])

            # PII + Unsafe + Harmfulness
            agent_pii += agent["pii_count"]
            if agent["unsafe"]: agent_unsafe += 1
            agent_harmfulness_scores.append(agent["harmfulness_score"])

    # Compute averages based on mode
    if is_dual_agent:
        avg_scores = {
            "prodagent": {
                "logic": {k: round(avg(v), 4) for k, v in prod_logic.items()},
                "llm": {k: round(avg(v), 4) for k, v in prod_llm.items()},
                "avg_harmfulness_score": round(avg(prod_harmfulness_scores), 6)
            },
            "shadagent": {
                "logic": {k: round(avg(v), 4) for k, v in shad_logic.items()},
                "llm": {k: round(avg(v), 4) for k, v in shad_llm.items()},
                "avg_harmfulness_score": round(avg(shad_harmfulness_scores), 6)
            }
        }

        # Compute overall scores (now including factuality if available)
        factuality_weight = 1 if prod_logic.get("factuality") else 0
        prod_score = round(
            avg_scores["prodagent"]["logic"]["completeness"] + 
            avg_scores["prodagent"]["logic"]["relevance"] + 
            (avg_scores["prodagent"]["logic"].get("factuality", 0) * factuality_weight), 
            4
        )
        shad_score = round(
            avg_scores["shadagent"]["logic"]["completeness"] + 
            avg_scores["shadagent"]["logic"]["relevance"] + 
            (avg_scores["shadagent"]["logic"].get("factuality", 0) * factuality_weight), 
            4
        )
        
        # Generate insights text for dual agent
        insights_text = generate_dual_agent_insights(avg_scores, prod_score, shad_score, prod_pii, shad_pii, prod_unsafe, shad_unsafe)
    else:
        avg_scores = {
            "agent": {
                "logic": {k: round(avg(v), 4) for k, v in agent_logic.items()},
                "llm": {k: round(avg(v), 4) for k, v in agent_llm.items()},
                "avg_harmfulness_score": round(avg(agent_harmfulness_scores), 6)
            }
        }

        # Compute overall score (including factuality if available)
        factuality_weight = 1 if agent_logic.get("factuality") else 0
        agent_score = round(
            avg_scores["agent"]["logic"]["completeness"] + 
            avg_scores["agent"]["logic"]["relevance"] + 
            (avg_scores["agent"]["logic"].get("factuality", 0) * factuality_weight), 
            4
        )
        
        # Generate insights text for single agent
        insights_text = generate_single_agent_insights(avg_scores, agent_score, agent_pii, agent_unsafe)
    
    # Analyze temporal trends
    temporal_insights = analyze_temporal_trends(time_ordered_results, is_dual_agent)
    session_insights = analyze_session_performance(session_data, is_dual_agent)

    # Return results based on mode
    if is_dual_agent:
        return {
            "average_scores": avg_scores,
            "pii_violations": {
                "prodagent": prod_pii,
                "shadagent": shad_pii
            },
            "unsafe_responses": {
                "prodagent": prod_unsafe,
                "shadagent": shad_unsafe
            },
            "temporal_analysis": temporal_insights,
            "session_analysis": session_insights,
            "summary": insights_text.strip()
        }
    else:
        return {
            "average_scores": avg_scores,
            "pii_violations": {
                "agent": agent_pii
            },
            "unsafe_responses": {
                "agent": agent_unsafe
            },
            "temporal_analysis": temporal_insights,
            "session_analysis": session_insights,
            "summary": insights_text.strip()
        }

# Add new helper functions for generating insights text
def generate_dual_agent_insights(avg_scores, prod_score, shad_score, prod_pii, shad_pii, prod_unsafe, shad_unsafe):
    insights_text = f"""# Overall Performance Comparison
- Production Agent Overall Score: {prod_score}
- Shadow Agent Overall Score: {shad_score}
- The {"Shadow" if shad_score > prod_score else "Production"} Agent performed better overall by {abs(shad_score - prod_score):.2f} points.

# Metric-Specific Performance

## Completeness
- Production Agent: {avg_scores["prodagent"]["logic"]["completeness"]}
- Shadow Agent: {avg_scores["shadagent"]["logic"]["completeness"]}
- {"Shadow" if avg_scores["shadagent"]["logic"]["completeness"] > avg_scores["prodagent"]["logic"]["completeness"] else "Production"} Agent performed better in completeness by {abs(avg_scores["prodagent"]["logic"]["completeness"] - avg_scores["shadagent"]["logic"]["completeness"]):.2f} points.

## Relevance
- Production Agent: {avg_scores["prodagent"]["logic"]["relevance"]}
- Shadow Agent: {avg_scores["shadagent"]["logic"]["relevance"]}
- {"Shadow" if avg_scores["shadagent"]["logic"]["relevance"] > avg_scores["prodagent"]["logic"]["relevance"] else "Production"} Agent performed better in relevance by {abs(avg_scores["prodagent"]["logic"]["relevance"] - avg_scores["shadagent"]["logic"]["relevance"]):.2f} points.
"""

    # Add factuality section if available
    if "factuality" in avg_scores["prodagent"]["logic"] and "factuality" in avg_scores["shadagent"]["logic"]:
        insights_text += f"""
## Factuality
- Production Agent: {avg_scores["prodagent"]["logic"]["factuality"]}
- Shadow Agent: {avg_scores["shadagent"]["logic"]["factuality"]}
- {"Shadow" if avg_scores["shadagent"]["logic"]["factuality"] > avg_scores["prodagent"]["logic"]["factuality"] else "Production"} Agent performed better in factuality by {abs(avg_scores["prodagent"]["logic"]["factuality"] - avg_scores["shadagent"]["logic"]["factuality"]):.2f} points.
"""

    insights_text += f"""
## Safety
- Production Agent Harmfulness Score (avg): {avg_scores["prodagent"]["avg_harmfulness_score"]}
- Shadow Agent Harmfulness Score (avg): {avg_scores["shadagent"]["avg_harmfulness_score"]}
- Both agents performed similarly in terms of safety.

## Sensitivity (PII Detection)
- Production Agent PII Violations: {prod_pii}
- Shadow Agent PII Violations: {shad_pii}
- Both agents had {("similar" if prod_pii == shad_pii else "different")} sensitivity detection performance.

# Response Safety
- Unsafe Production Responses: {prod_unsafe}
- Unsafe Shadow Responses: {shad_unsafe}

# Recommendations
- Production Agent should focus on improving completeness (current score: {avg_scores["prodagent"]["logic"]["completeness"]}).
- Shadow Agent should focus on improving relevance (current score: {avg_scores["shadagent"]["logic"]["relevance"]}).
- Consider aligning the response patterns between the two agents for a consistent experience.
"""

    return insights_text

def generate_single_agent_insights(avg_scores, agent_score, agent_pii, agent_unsafe):
    insights_text = f"""# Overall Performance
- Agent Overall Score: {agent_score}

# Metric-Specific Performance

## Completeness
- Agent Score: {avg_scores["agent"]["logic"]["completeness"]}

## Relevance
- Agent Score: {avg_scores["agent"]["logic"]["relevance"]}
"""

    # Add factuality section if available
    if "factuality" in avg_scores["agent"]["logic"]:
        insights_text += f"""
## Factuality
- Agent Score: {avg_scores["agent"]["logic"]["factuality"]}
"""

    insights_text += f"""
## Safety
- Agent Harmfulness Score (avg): {avg_scores["agent"]["avg_harmfulness_score"]}

## Sensitivity (PII Detection)
- Agent PII Violations: {agent_pii}

# Response Safety
- Unsafe Agent Responses: {agent_unsafe}

# Recommendations
- Agent should focus on improving {"completeness" if avg_scores["agent"]["logic"]["completeness"] < avg_scores["agent"]["logic"]["relevance"] else "relevance"} (current score: {min(avg_scores["agent"]["logic"]["completeness"], avg_scores["agent"]["logic"]["relevance"])}).
"""

    return insights_text

def analyze_temporal_trends(time_ordered_results, is_dual_agent=True):
    """
    Analyze how agent performance changes over time within the dataset.
    """
    if not time_ordered_results or len(time_ordered_results) < 2:
        return "Insufficient data for temporal analysis."
        
    # Initialize tracking variables
    if is_dual_agent:
        prod_scores = []
        shad_scores = []
    else:
        agent_scores = []
    timestamps = []
    
    # Extract scores over time
    for entry in time_ordered_results:
        if is_dual_agent:
            prod = entry["evaluation"]["prodagent"]
            shad = entry["evaluation"]["shadagent"]
            
            # Calculate overall score for this entry (average of logic metrics)
            prod_logic = prod["logic"]
            shad_logic = shad["logic"]
            
            metrics_count = len(prod_logic)
            prod_entry_score = sum(prod_logic.values()) / metrics_count
            shad_entry_score = sum(shad_logic.values()) / metrics_count
            
            prod_scores.append(prod_entry_score)
            shad_scores.append(shad_entry_score)
        else:
            agent = entry["evaluation"]["agent"]
            
            # Calculate overall score for this entry (average of logic metrics)
            agent_logic = agent["logic"]
            
            metrics_count = len(agent_logic)
            agent_entry_score = sum(agent_logic.values()) / metrics_count
            
            agent_scores.append(agent_entry_score)
            
        timestamps.append(entry.get("readable_timestamp", "Unknown"))
    
    # Analyze for trends
    if is_dual_agent:
        prod_trend = "improving" if prod_scores[-1] > prod_scores[0] else "declining"
        shad_trend = "improving" if shad_scores[-1] > shad_scores[0] else "declining"
        
        # Check for consistency
        prod_consistency = calculate_consistency(prod_scores)
        shad_consistency = calculate_consistency(shad_scores)
        
        # Generate insights
        insights = f"""- Production Agent performance is {prod_trend} over time (consistency: {prod_consistency:.2f}/1.0)
- Shadow Agent performance is {shad_trend} over time (consistency: {shad_consistency:.2f}/1.0)"""
        
        # Add specific insights about performance changes
        if len(prod_scores) >= 3:
            prod_early = sum(prod_scores[:len(prod_scores)//3]) / (len(prod_scores)//3)
            prod_late = sum(prod_scores[-len(prod_scores)//3:]) / (len(prod_scores)//3)
            shad_early = sum(shad_scores[:len(shad_scores)//3]) / (len(shad_scores)//3)
            shad_late = sum(shad_scores[-len(shad_scores)//3:]) / (len(shad_scores)//3)
            
            insights += f"\n- Production Agent: {abs(prod_late - prod_early):.2f} point {'improvement' if prod_late > prod_early else 'decline'} from early to late interactions"
            insights += f"\n- Shadow Agent: {abs(shad_late - shad_early):.2f} point {'improvement' if shad_late > shad_early else 'decline'} from early to late interactions"
    else:
        agent_trend = "improving" if agent_scores[-1] > agent_scores[0] else "declining"
        
        # Check for consistency
        agent_consistency = calculate_consistency(agent_scores)
        
        # Generate insights
        insights = f"""- Agent performance is {agent_trend} over time (consistency: {agent_consistency:.2f}/1.0)"""
        
        # Add specific insights about performance changes
        if len(agent_scores) >= 3:
            agent_early = sum(agent_scores[:len(agent_scores)//3]) / (len(agent_scores)//3)
            agent_late = sum(agent_scores[-len(agent_scores)//3:]) / (len(agent_scores)//3)
            
            insights += f"\n- Agent: {abs(agent_late - agent_early):.2f} point {'improvement' if agent_late > agent_early else 'decline'} from early to late interactions"
    
    return insights

def analyze_session_performance(session_data, is_dual_agent=True):
    """
    Analyze performance across different sessions.
    """
    if not session_data:
        return "No session data available."
    
    insights = []
    
    for session_id, data in session_data.items():
        if is_dual_agent:
            prod_scores = data["prod_scores"]
            shad_scores = data["shad_scores"]
            
            if not prod_scores or not shad_scores:
                continue
                
            prod_avg = sum(prod_scores) / len(prod_scores)
            shad_avg = sum(shad_scores) / len(shad_scores)
            
            # Check for performance drift within session
            prod_drift = "stable"
            shad_drift = "stable"
            
            if len(prod_scores) >= 3:
                prod_early = sum(prod_scores[:len(prod_scores)//2]) / (len(prod_scores)//2)
                prod_late = sum(prod_scores[len(prod_scores)//2:]) / (len(prod_scores) - len(prod_scores)//2)
                
                if abs(prod_late - prod_early) > 0.1:
                    prod_drift = "improving" if prod_late > prod_early else "degrading"
                    
                shad_early = sum(shad_scores[:len(shad_scores)//2]) / (len(shad_scores)//2)
                shad_late = sum(shad_scores[len(shad_scores)//2:]) / (len(shad_scores) - len(shad_scores)//2)
                
                if abs(shad_late - shad_early) > 0.1:
                    shad_drift = "improving" if shad_late > shad_early else "degrading"
            
            insights.append(f"Session {session_id}:\n- Production Agent: {prod_avg:.2f} avg score ({prod_drift})\n- Shadow Agent: {shad_avg:.2f} avg score ({shad_drift})")
        else:
            agent_scores = data["agent_scores"]
            
            if not agent_scores:
                continue
                
            agent_avg = sum(agent_scores) / len(agent_scores)
            
            # Check for performance drift within session
            agent_drift = "stable"
            
            if len(agent_scores) >= 3:
                agent_early = sum(agent_scores[:len(agent_scores)//2]) / (len(agent_scores)//2)
                agent_late = sum(agent_scores[len(agent_scores)//2:]) / (len(agent_scores) - len(agent_scores)//2)
                
                if abs(agent_late - agent_early) > 0.1:
                    agent_drift = "improving" if agent_late > agent_early else "degrading"
            
            insights.append(f"Session {session_id}:\n- Agent: {agent_avg:.2f} avg score ({agent_drift})")
    
    return "\n\n".join(insights)

def calculate_consistency(scores):
    """
    Calculate consistency score (0-1) based on variance in performance.
    Lower variance = higher consistency.
    """
    if not scores or len(scores) < 2:
        return 1.0  # Default perfect consistency with insufficient data
        
    # Calculate variance and normalize to 0-1 scale
    mean = sum(scores) / len(scores)
    variance = sum((x - mean) ** 2 for x in scores) / len(scores)
    
    # Convert variance to consistency score (inverse relationship)
    # Higher variance = lower consistency
    consistency = max(0, 1 - min(variance * 5, 1))  # Scale factor of 5 to make differences more apparent
    
    return consistency
