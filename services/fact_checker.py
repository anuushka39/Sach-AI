def check_fact(claim):

    claim = claim.lower()

    if "earth is flat" in claim:

        return {
            "verdict": "False",
            "fact_score": 15
        }

    elif "water boils at 100" in claim:

        return {
            "verdict": "True",
            "fact_score": 95
        }

    else:

        return {
            "verdict": "Unknown",
            "fact_score": 60
        }