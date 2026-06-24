from transformers import pipeline

detector = pipeline(
    "text-classification",
    model="roberta-base-openai-detector"
)

def detect_ai_text(text):

    result = detector(text)

    print("MODEL OUTPUT:", result)

    label = result[0]["label"]
    score = result[0]["score"]

    if label.upper() in ["FAKE", "AI", "GENERATED"]:
        ai_probability = score * 100
    else:
        ai_probability = (1 - score) * 100

    return {
        "label": label,
        "ai_probability": round(ai_probability, 2)
    }
