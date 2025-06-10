import boto3
import json
import re

# Use the 'hari-work' named profile
session = boto3.Session(profile_name="hari-work", region_name="us-east-1")
bedrock = session.client("bedrock-runtime")

MODEL_ID = "amazon.titan-text-premier-v1:0"

def extract_json(text):
    """
    Extract the first valid JSON object from the model's output.
    """
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            raise ValueError("Matched text is not valid JSON.")
    else:
        raise ValueError("No JSON object found in output.")

def evaluate_with_llm(prompt, response):
    """
    Use Titan LLM to evaluate the response on relevance, completeness, and quality.
    Scores range from 0.0 to 1.0.
    """
    eval_prompt = f"""
You are an expert evaluator.

Return only a valid JSON object. No explanation or comments. Score the agents response to the request.

### Prompt:
{prompt}

### Response:
{response}

Score from 0.0 to 1.0 in the following format:
{{
  "relevance": 0.00,
  "completeness": 0.00,
  "quality": 0.00
}}
"""

    try:
        payload = {
            "inputText": eval_prompt,
            "textGenerationConfig": {
                "temperature": 0.3,
                "maxTokenCount": 400,
                "topP": 1,
                "stopSequences": []
            }
        }

        # Invoke Titan model
        response = bedrock.invoke_model(
            body=json.dumps(payload),
            modelId=MODEL_ID,
            accept="application/json",
            contentType="application/json"
        )

        # Extract output text from Bedrock response
        output = json.loads(response["body"].read())
        result_text = output.get("results", [{}])[0].get("outputText", "").strip()

        # Extract and parse only the JSON portion
        return extract_json(result_text)

    except Exception as e:
        print(f"Bedrock LLM judge error: {e}")
        return {"relevance": 0.0, "completeness": 0.0, "quality": 0.0}
