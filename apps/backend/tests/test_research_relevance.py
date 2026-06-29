from research.relevance import _is_noise_url, filter_relevant_results, score_result


def test_rejects_facebook_and_youtube():
    assert _is_noise_url("https://www.facebook.com/groups/foo") is True
    assert _is_noise_url("https://www.youtube.com/watch?v=abc") is True
    assert _is_noise_url("https://www.justanswer.com/law/foo") is True


def test_scores_strategic_content_higher():
    question = "Should startup accept Fortune 500 enterprise pilot?"
    queries = ["startup enterprise pilot benefits", "SMB vs enterprise focus"]
    good = {
        "url": "https://example.com/blog/enterprise-pilot-case-study",
        "title": "Enterprise pilot case study for B2B startup",
        "content": "Startups often face distraction risk when accepting enterprise pilots...",
    }
    bad = {
        "url": "https://www.demandsage.com/fortune-500-companies",
        "title": "Fortune 500 list",
        "content": "List of companies",
    }
    assert score_result(question, queries, good) > score_result(question, queries, bad)


def test_filter_keeps_relevant_only():
    question = "enterprise pilot startup"
    queries = ["enterprise pilot startup benefits"]
    results = [
        {"url": "https://facebook.com/x", "title": "x", "content": "enterprise pilot"},
        {
            "url": "https://saas.blog/enterprise-pilot",
            "title": "Enterprise pilot guide",
            "content": "B2B startup enterprise pilot reference customer strategy",
        },
    ]
    kept, count = filter_relevant_results(question, queries, results, min_score=0.1, max_keep=5)
    assert count >= 1
    assert all("facebook" not in r.get("url", "") for r in kept)
