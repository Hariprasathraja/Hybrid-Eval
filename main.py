from pipeline.evaluate_session import evaluate
import sys

if __name__ == "__main__":
    print("Running main.py...")

    if len(sys.argv) < 3:
        print("Usage: python main.py <session_id> <bucket>")
    else:
        session_id = sys.argv[1]
        bucket = sys.argv[2]
        print(f"Starting evaluation for session_id: {session_id}, bucket: {bucket}")
        evaluate(session_id, bucket)
