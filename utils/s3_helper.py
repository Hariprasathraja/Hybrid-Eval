import boto3, json

S3_KEY_PREFIX = "interactions/"
session = boto3.Session(profile_name="hari-work")
s3_client = session.client("s3")

def load_session_data(session_id, bucket_name):
    s3_key = f"{S3_KEY_PREFIX}{session_id}/session.json"
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except Exception as e:
        print(f"Error loading session: {e}")
        return None

def save_evaluation_results(session_id, data, bucket_name):
    s3_key = f"{S3_KEY_PREFIX}{session_id}/evaluation_results.json"
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )
    except Exception as e:
        print(f"Error saving results: {e}")
