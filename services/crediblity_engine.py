def calculate_score(
    ai_score,
    fact_score,
    source_score
):

    final_score = (
        0.2 * ai_score +
        0.5 * fact_score +
        0.3 * source_score
    )

    return round(final_score, 2)

authority_score =
(
    domain_score * 0.6
) +
(
    relevance_score * 0.2
) +
(
    consensus_score * 0.2
)