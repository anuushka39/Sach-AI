from ddgs import DDGS
import trafilatura
import tldextract
import re
import logging
from urllib.parse import urlparse, urlunparse
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor

# Model Loading
print("Loading Embedding Model...")
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2")
print("Embedding Model Loaded.")

# Authority Database
# Authority scoring - Har .edu trustworthy nahi hota Better is Domain whitelist Domain whitelist
# Whitelist of trusted domains.
# Unknown domains fall back to TLD-based scoring.
AUTHORITY_SCORES = { "gov": 100, "gov.uk":100, "europa.eu":95, "un.org":100, "unesco.org":95, "cdc.gov":100, "fda.gov":100, "edu": 95, "nature.com": 95, "science.org": 95, "sciencedirect.com": 90, "theconversation.com": 85, "elsevier.com": 95, "springer.com": 95, "nih.gov": 100, "ncbi.nlm.nih.gov": 100, "reuters.com": 95, "apnews.com": 95, "who.int": 100, "nasa.gov": 100, "bbc.com": 90, "bbc.co.uk": 90, "britannica.com": 90, "wikipedia.org": 75
}
def get_authority_score(url):
    """
    Returns authority score of a source based on its domain.
    Falls back to TLD-based scoring for unknown domains.
    """
    try:
        ext = tldextract.extract(url)
        # Example:
        # news.bbc.com  -> bbc.com
        # www.nasa.gov  -> nasa.gov
        domain = f"{ext.domain}.{ext.suffix}"
        # Exact whitelist match
        if domain in AUTHORITY_SCORES:
            return AUTHORITY_SCORES[domain]
        # Generic government domains
        if ext.suffix == "gov":
            return 100
        # Educational institutions
        if ext.suffix == "edu":
            return 95
        # Unknown source
        return 35
    except Exception as e:
        logging.warning(f"Authority score failed for {url}: {e}")
        return 35
    
# Search
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
MAX_SEARCH_RESULTS = 5
MIN_CONTENT_LENGTH = 100


#search_sources():
    # DDGS search
    # DDG often returns --Reuters Reuters mirror Yahoo Reuters mirror MSN Reuters mirror--- Consensus artificially skew ho jayega. Need canonical URL/domain deduplication.

def canonicalize_url(url: str) -> str:
    """Removes query parameters, fragments and trailing slash. Used for deduplication."""
    parsed = urlparse(url)
    cleaned = parsed._replace(query="", fragment="")
    url = urlunparse(cleaned)
    return url.rstrip("/")

def search_sources(claim, max_results=MAX_SEARCH_RESULTS):
    """Search DuckDuckGo and return unique URLs."""
    logging.info("Searching DuckDuckGo...")
    sources = []
    seen_urls = set()
    try:
        with DDGS() as ddgs:
            results = ddgs.text(claim, max_results=max_results * 2)
            for item in results:
                url = item.get("href")
                if not url:
                    continue
                canonical = canonicalize_url(url)
                if canonical in seen_urls:
                    continue
                seen_urls.add(canonical)
                sources.append({
                    "title": item.get("title", "").strip(),
                    "url": canonical,
                    "snippet": item.get("body", "").strip()
                })
                if len(sources) >= max_results:
                    break
        logging.info(f"Collected {len(sources)} unique sources.")
        return sources
    except Exception as e:
        logging.error(f"DDG Search Failed : {e}")
        return []

# Cleaning
def clean_text(text):
    # Basic text normalization.
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# Content Extraction
def extract_page(url):
    # "" -->> Downloads webpage. -->> Extracts only the readable article. -->> Cleans whitespace. -->> Returns: -->>     Clean article text -->> Returns empty string if extraction fails.
    # Trafilatura + cleaning
    # Download webpage and extract readable article.

    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            logging.warning(f"Download Failed : {url}")
            return ""
        extracted = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False
        )
        if extracted is None:
            logging.warning(f"Extraction Failed : {url}")
            return ""
        cleaned = clean_text(extracted)
        if len(cleaned) < MIN_CONTENT_LENGTH:
            logging.warning(f"Content Too Short : {url}")
            return ""
        return cleaned
    except Exception as e:
        logging.error(f"Extraction Error ({url}) : {e}")
        return ""

def source_checker():
    # Search
    sources = search_sources(claim)
    # Extract valid sources
    valid_sources = []
    for source in sources:
        content = extract_page(source["url"])
        if not content:
            continue
        source["content"] = content
        valid_sources.append(source)
        
# Paragraph Retrieval
MIN_PARAGRAPH_LENGTH = 120
MAX_PARAGRAPH_LENGTH = 1200
TARGET_CHUNK_SIZE = 900
MAX_CHUNK_SIZE = 1200
MIN_SENTENCES_PER_CHUNK = 3
TOP_K_PARAGRAPHS = 5
MIN_SIMILARITY_FOR_STANCE = 0.45

def prepare_paragraphs(article):
    # Article => Split => Remove tiny paragraph => Remove duplicate => Merge broken paragraph => Clean => Return
    """Prepare article paragraphs for semantic retrieval.
    Steps:
    1. Split article
    2. Clean whitespace
    3. Merge tiny broken paragraphs
    4. Remove duplicates
    5. Remove very short paragraphs
    """
    if not article:
        return []

    article = clean_text(article)

    # Step 1: Split using paragraph breaks
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", article) if p.strip()]

    # Step 2:  If article has very few paragraphs,create semantic chunks using sentences.
    if len(paragraphs) <= 2:
        sentences = re.split(r'(?<=[.!?])\s+', article)
        paragraphs, current_chunk = [], ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            # If adding this sentence would make chunk too large,
            # save current chunk first.
            if (current_chunk and len(current_chunk) + len(sentence) > TARGET_CHUNK_SIZE):
                paragraphs.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " "
                current_chunk += sentence
        if current_chunk:
            paragraphs.append(current_chunk.strip())

    # Step 3: Merge undersized chunks
    merged, i = [], 0
    while i < len(paragraphs):
        current = paragraphs[i]
        if len(current) >= MIN_PARAGRAPH_LENGTH:
            merged.append(current)
            i += 1
            continue
         # Tiny chunk at beginning
        if i == 0 and len(paragraphs) > 1:
            paragraphs[i + 1] = current + " " + paragraphs[i + 1]
         # Tiny chunk at end
        elif i == len(paragraphs) - 1 and merged:
            merged[-1] += " " + current
         # Tiny chunk at middle
        else:
            prev_size = len(merged[-1]) if merged else float("inf")
            next_size = len(paragraphs[i + 1])
            # Merge with smaller neighbour
            if prev_size <= next_size:
                merged[-1] += " " + current
            else:
                paragraphs[i + 1] = current + " " + paragraphs[i + 1]
        i += 1

    # Step 4: Split oversized chunks
    final_chunks = []
    for chunk in merged:
        while len(chunk) > MAX_CHUNK_SIZE:
            split_index = chunk.rfind(".", 0, MAX_CHUNK_SIZE)
            if split_index == -1:
                split_index = chunk.rfind(" ", 0, MAX_CHUNK_SIZE)
            if split_index == -1:
                split_index = MAX_CHUNK_SIZE
            final_chunks.append(chunk[:split_index].strip())
            chunk = chunk[split_index:].strip()
        if chunk:
            final_chunks.append(chunk)

    # Step 5: Remove duplicates
    unique_chunks, seen = [], set()
    for chunk in final_chunks:
        key = chunk.lower()
        if key not in seen:
            seen.add(key)
            unique_chunks.append(chunk)

    return unique_chunks

def retrieve_evidence(claim_embedding, chunks,  top_k=TOP_K_PARAGRAPHS):
      # mini lm Authority scoring #split article - para embeedings -- most relevan para-, (take top 10 para(what if thing is in more bara/ or be smart enought to capture all relevant para , not whole article..)) nli , MiniLM supports batch encoding..( 8 chunks -> 1 modle call , instead of 8), chunk id, text , similarity). Retrieve most relevant evidence paragraphs.
      # retrieve_evidence() becomes responsible for retrieval + similarity computation.
    #   '''
    #   Retrieve Top-K semantic evidence chunks.
    #   Uses MiniLM batch embeddings.
    #   Parameters
    #     ----------
    #   claim_embedding : Tensor
    #     Precomputed embedding of the user claim.

    #   chunks : List[str]
    #     Semantic chunks produced by prepare_paragraphs()

    #    and  Return  List[Dict] 
    #    [{
    #         "chunk_id": 1,
    #         "text": "...",
    #         "similarity": 0.8745,
    #         "length": 812
    #     }
    #   Retrieve Top-K semantic evidence chunks using MiniLM batch embeddings, and return chunk_id, text and similarity.'''
    if not chunks:
        return []
    # Encode ALL chunks together
    chunk_embeddings = embedding_model.encode(
        chunks, convert_to_tensor=True, show_progress_bar=False
    )
    # # Encode all chunks (one forward pass)
    # chunk_embeddings = embedding_model.encode(
    #     chunks, convert_to_tensor=True, show_progress_bar=False
    # )
    # Cosine similarity
    similarities = util.cos_sim(claim_embedding, chunk_embeddings)[0]
    evidence = []
    for idx, score in enumerate(similarities):
        evidence.append({
            "chunk_id": idx + 1,
            "text": chunks[idx],
            "similarity": round(float(score), 4),
            "length": len(chunks[idx]),
            "rank": None
        })
    evidence.sort(key=lambda x: x["similarity"], reverse=True)
    for rank, chunk in enumerate(evidence, start=1):
       chunk["rank"] = rank
    return evidence[:top_k]

# Embeddings
def calculate_relevance(evidence_chunks):
    ... # MiniLM embeddings
    #split article - para embeedings -- most relevan para-nli.. aggregate those similarity scores into a single article-level relevance value., it dont call mini lm, and simply uses similarity from previous function..
    '''
    Calculate overall article relevance.

    Uses already computed similarities.

    Returns relevance score (0-100).
    update-Calculate overall article relevance using
    weighted similarity.

    Higher-ranked evidence contributes more.'''
    if not evidence_chunks:
        return 0
    n = len(evidence_chunks)
    # Dynamic weights
    weights = list(range(n, 0, -1))
    total_weight = sum(weights)
    weighted_sum = 0
    for weight, chunk in zip(weights, evidence_chunks):
        weighted_sum += weight * chunk["similarity"]
    relevance = weighted_sum / total_weight
    return round(relevance * 100, 2)


print("Loading DeBERTa Stance Model...")
stance_model = pipeline(
    task="text-classification",
    model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
)
print("DeBERTa Loaded.")
# Stance Detection
def get_stance( claim, source_title, evidence_chunks):
    # DeBERTa NLI , maye its stance--instead of sratr/end 2000 chars, give it most relevant paragraph+title
    '''
    befor this we also added rank thing in retrieve evidence--DeBERTa can prioritize the highest-ranked evidence first.
    Consensus can give slightly more importance to     higher-ranked evidence if you choose.
    The final report can naturally say:
    Top Evidence #1 (Reuters): Government has not announced  any such free laptop scheme...'''
    """
    Determine article stance using Top-K evidence chunks.
    Parameters
    ----------
    claim : str
    source_title : str
    evidence_chunks : output of retrieve_evidence()
    Returns
    -------
    {
        "stance": "...",
        "confidence": 92.5,
        "chunk_results":[...]
    }
    third change-- Determine article stance using Top-K evidence chunks.
    Premise    : Source Title + Evidence Chunk
    Hypothesis : User Claim
    Chunk Weight = Similarity × NLI Confidence
    """
    if not evidence_chunks:
        return {
            "stance": "NEUTRAL",
            "confidence": 0,
            "chunk_results": []
        }
    chunk_results = []
    stance_weights = {
        "SUPPORTS": 0.0,
        "REFUTES": 0.0,
    }
    for evidence in evidence_chunks:
        if evidence["similarity"] < MIN_SIMILARITY_FOR_STANCE:
           continue
        premise =( f"Title: {source_title}\n\n"
        f"Evidence: {evidence['text']}" )
        try:
            result = stance_model(
                {
                    "text": premise,
                    "text_pair": claim
                }
            )
            label = result["label"].upper()
            confidence = float(result["score"])
            # Map HF labels to project labels
            if label == "ENTAILMENT":
                stance = "SUPPORTS"
            elif label == "CONTRADICTION":
                stance = "REFUTES"
            else:
                  continue
            chunk_results.append({
                "rank": evidence["rank"],
                "chunk_id": evidence["chunk_id"],
                "stance": stance,
                "confidence": round(confidence * 100, 2),
                "similarity": evidence["similarity"]
            })
            # Evidence Weight
            weight = evidence["similarity"] * confidence
            stance_weights[stance] += weight
        except Exception as e:
            print(f"STANCE ERROR [{evidence['chunk_id']}] : {e}")
    # Final Article Stance
    total = sum(stance_weights.values())
    if total == 0:
        return {
        "stance": "NEUTRAL",
        "confidence": 0,
        "chunk_results": chunk_results
    }
    final_stance = max(
    stance_weights,
    key=stance_weights.get
)
    final_confidence = round(
            stance_weights[final_stance] /
            total * 100,
            2
        )
    return {
        "stance": final_stance,
        "confidence": final_confidence,
        "chunk_results": chunk_results
    }

def analyze_source(claim_embedding, claim, source):
    """
    Analyze one source completely.
    Returns a fully analyzed source object that can be directly
    consumed by the consensus engine.
    """
    # Extract Content
    content = extract_page(source["url"])

    if not content:
        return {
         "title": source["title"],
         "url": source["url"],   
    "status": "FAILED",
    "reason": "CONTENT_EXTRACTION_FAILED"
}
    # Authority
    authority = get_authority_score(source["url"])
    # Prepare Semantic Chunks
    paragraphs = prepare_paragraphs(content)

    if not paragraphs:
        return {
         "title": source["title"],
         "url": source["url"],   
    "status": "FAILED",
    "reason": "NO_PARAGRAPH_FOUND"
}
    # Retrieve Evidence
    evidence = retrieve_evidence(
        claim_embedding,
        paragraphs
    )
    if not evidence:
        return {
         "title": source["title"],
         "url": source["url"],   
         "status": "FAILED",
         "reason": "NO_RELEVANT_EVIDENCE"
}
    # Overall Semantic Relevance
    relevance = calculate_relevance(
        evidence
    )
    # Article Stance
    stance = get_stance(
        claim,
        source["title"],
        evidence
    )
    # Return Complete Source Object
    return {
        "title": source["title"],
        "url": source["url"],
        "authority_score": authority,
        "relevance_score": relevance,
        "stance_label": stance["stance"],
        "stance_confidence": stance["confidence"],
        "top_evidence": stance["chunk_results"]
    }
# Consensus
def consensus(analyzed_sources):
    # Consensus logic
    #maybe ranking come here-- Ranking formula--Fixed weights.bad ---Production systems usually normalize first.
    #consensus score = weighted sum of stance confidence,  authority and relevance# DeBERTa
    # across all article.. source weight=authority(new information.)+article relivance(new information.)*stance confidence
    # or in layman ,inside one article ..evidnece wt= similarity*nli confidence
    """
    Aggregate stance across all analyzed sources.

    Source Weight =
        Authority × Relevance × Stance Confidence
    """
    if not analyzed_sources:
        return {
            "verdict": "UNKNOWN",
            "confidence": 0,
            "supports_weight": 0,
            "refutes_weight": 0
        }
    supports = 0.0
    refutes = 0.0
    valid_sources = 0
    for source in analyzed_sources:
        # Skip failed analyses
        if source.get("status") == "FAILED":
            continue
        authority = source["authority_score"] / 100
        relevance = source["relevance_score"] / 100
        confidence = source["stance_confidence"] / 100
        source_weight = (
            authority *
            relevance *
            confidence
        )
        # Save for later reporting
        source["source_weight"] = round(source_weight, 4)
        if source["stance_label"] == "SUPPORTS":
            supports += source_weight
            valid_sources += 1
        elif source["stance_label"] == "REFUTES":
            refutes += source_weight
            valid_sources += 1
    total = supports + refutes
    if total == 0:
        return {
            "verdict": "NEUTRAL",
            "confidence": 0,
            "supports_weight": 0,
            "refutes_weight": 0,
            "sources_used": valid_sources
        }
    if supports >= refutes:
        verdict = "SUPPORTS"
        confidence = supports / total
    else:
        verdict = "REFUTES"
        confidence = refutes / total
    return {
        "verdict": verdict,
        "confidence": round(confidence * 100, 2),
        "supports_weight": round(supports, 4),
        "refutes_weight": round(refutes, 4),
        "sources_used": valid_sources
    }


def additional_utils():
    ...# Additional utility functions
      # Optional caching
      # Shared helpers, parallel fetching..
      #25 websites ↓ , ek ke baad ek. , CPU idle rehta hai. , Internet wait karta rehta hai. , Ye sab , ThreadPoolExecutor , se parallel hona chahiye.

      # Abhi MiniLM use ho raha hai Ranking ke liye Good. But Stance ke liye DeBERTa Good. Par Content extraction ke baad same article dobara DeBERTa dobara MiniLM dobara. --No pipeline optimization.

      #Very weak error handling. Tumne except     return "" likh diya. Ab pata hi nahi chalega Problem Internet? 403? 404? SSL? Timeout?-- "Instead of silently swallowing exceptions, I would log structured errors so failures can be analyzed and retried."

      #Imagine claim--COVID restrictions today--Aur article--2020--High relevance--High authority--
      # Wrong evidence.--Need publication date extraction., in working like today latest etc, eg if clain is moon landing 1969, aur article 2020, then it should be considered relevant. But if claim is COVID restrictions today, aur article 2020, then it should be considered irrelevant. --Need publication date extraction., means should be smart enough to understand claim and article date, and then decide relevance. --


# Pipeline
# Pipeline orchestration

def test_consensus_pipeline(claim):

    claim_embedding = embedding_model.encode(
        claim,
        convert_to_tensor=True,
        show_progress_bar=False
    )

    sources = search_sources(claim)

    analyzed_sources = []

    for source in sources:
        print(f"Analyzing {len(analyzed_sources)+1}/{len(sources)} : {source['title']}")
        result = analyze_source(
            claim_embedding,
            claim,
            source
        )

        if result.get("status") == "FAILED":
            continue

        analyzed_sources.append(result)

    print()
    print("=" * 80)
    print(f"Successfully Analyzed : {len(analyzed_sources)} Sources")
    print("=" * 80)

    result = consensus(analyzed_sources)

    print()
    print("CONSENSUS RESULT")
    print("-" * 80)

    print("Verdict          :", result["verdict"])
    print("Confidence       :", result["confidence"])
    print("Supports Weight  :", result["supports_weight"])
    print("Refutes Weight   :", result["refutes_weight"])
    print("Sources Used     :", result["sources_used"])

if __name__ == "__main__":
    claim = input("Enter Claim : ")
    test_consensus_pipeline(claim)