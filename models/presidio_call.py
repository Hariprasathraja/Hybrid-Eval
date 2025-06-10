from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()

def invoke_presidio(text):
    results = analyzer.analyze(text=text,
                           entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD", "IP_ADDRESS", "DATE_TIME", "PERSON", "LOCATION", "URL"],
                           language='en')
    return results
