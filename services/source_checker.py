from ddgs import DDGS
import trafilatura
import tldextract
from sentence_transformers import SentenceTransformer, util
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

AUTHORITY_SCORES = {
    "gov": 100,
    "edu": 95,
    "nature.com": 95,
    "science.org": 95,
    "sciencedirect.com": 90,
    "theconversation.com": 85,
    "elsevier.com": 95,
    "springer.com": 95,
    "nih.gov": 100,
    "ncbi.nlm.nih.gov": 100,
    "reuters.com": 95,
    "apnews.com": 95,
    "who.int": 100,
    "nasa.gov": 100,
    "bbc.com": 90,
    "bbc.co.uk": 90,
    "britannica.com": 90,
    "wikipedia.org": 75
}
# LOAD MODEL
print("Loading Sentence Transformer Model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model Loaded Successfully!")

# SEARCH SOURCES
def search_sources(claim, max_results=25):
    with DDGS() as ddgs:
        search_results = list(ddgs.text(claim, max_results=max_results))

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("href", ""),
            "snippet": item.get("body", "")
        }
        for item in search_results
    ]

# CONTENT EXTRACTION
def extract_page_content(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text or ""
    except Exception:
        return ""


# AUTHORITY SCORE
def get_authority_score(url):
    try:
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}"

        if domain in AUTHORITY_SCORES:
            return AUTHORITY_SCORES[domain]

        if ext.suffix == "gov":
            return 100

        if ext.suffix == "edu":
            return 95

        return 50

    except Exception:
        return 50


# RELEVANCE SCORE
def get_relevance_score(claim_embedding, title, snippet, content):
    try:
        text = f"{title} {snippet} {content[:2000]}"

        content_embedding = model.encode(
            text,
            convert_to_tensor=True
        )

        similarity = util.cos_sim(
            claim_embedding,
            content_embedding
        )

        return round(float(similarity[0][0]) * 100, 2)

    except Exception:
        return 0

# ANALYZE ONE SOURCE
def analyze_source(claim_embedding, claim, source):

    content = extract_page_content(
        source["url"]
    )

    authority_score = get_authority_score(
        source["url"]
    )

    relevance_score = get_relevance_score(
        claim_embedding,
        source["title"],
        source["snippet"],
        content
    )

    stance = get_stance(
        claim,
        content
    )

    rank = round(
        authority_score * 0.4 +
        relevance_score * 0.6,
        2
    )

    return {

        "title": source["title"],

        "url": source["url"],

        "authority_score": authority_score,

        "relevance_score": relevance_score,

        "stance": stance,

        "rank": rank,

        "content": content[:1000]
    }


genai.configure(api_key=GEMINI_API_KEY)

gemini_model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

def get_stance(claim, content):

    try:

        prompt = f"""
Claim:
{claim}

Article:
{content[:3000]}

Classify the article's stance towards the claim.

Possible labels:

SUPPORTS
REFUTES
NEUTRAL

Return ONLY ONE WORD.
"""

        response = gemini_model.generate_content(prompt)

        stance = response.text.strip().upper()

        if stance not in [
            "SUPPORTS",
            "REFUTES",
            "NEUTRAL"
        ]:
            stance = "NEUTRAL"

        return stance

    except Exception as e:

        print("STANCE ERROR:", e)

        return "NEUTRAL"
    
def get_consensus_score(analyzed_sources):

    supports = 0
    refutes = 0
    neutral = 0

    for source in analyzed_sources:

        weight = source["authority_score"]

        if source["stance"] == "SUPPORTS":

            supports += weight

        elif source["stance"] == "REFUTES":

            refutes += weight

        else:

            neutral += weight

    total = supports + refutes + neutral

    if total == 0:

        return {
            "verdict": "UNKNOWN",
            "score": 0
        }

    scores = {

        "SUPPORTS": supports,
        "REFUTES": refutes,
        "NEUTRAL": neutral
    }

    verdict = max(
        scores,
        key=scores.get
    )

    confidence = round(
        scores[verdict] /
        total * 100,
        2
    )

    return {

        "verdict": verdict,

        "score": confidence,

        "supports_weight": supports,

        "refutes_weight": refutes,

        "neutral_weight": neutral
    }

# MAIN PIPELINE
def source_checker(claim):
    print("\nSearching Sources...\n")
    sources = search_sources(claim, max_results=25)
    print(f"Found {len(sources)} sources\n")
    claim_embedding = model.encode(
        claim,
        convert_to_tensor=True
    )
    analyzed_sources = []
    for idx, source in enumerate(sources, start=1):
        print(f"Processing Source {idx}")
        analyzed_sources.append(analyze_source(claim_embedding, claim, source))
    analyzed_sources.sort(key=lambda x: x["rank"],reverse=True)
    consensus = get_consensus_score(
    analyzed_sources
)
    mean_relevance = round(
        sum(source["relevance_score"] for source in analyzed_sources) / len(analyzed_sources), 2)
    return {
        "mean_relevance": mean_relevance,
        "consensus": consensus,
        "sources": analyzed_sources
    }

if __name__ == "__main__":

    claim = input("Enter Claim: ")

    result = source_checker(claim)

    print("\nCONSENSUS RESULT")
    print(result["consensus"])

