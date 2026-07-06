from app.policy.policy_retriever import retrieve_policy_evidence


def test_retrieve_policy_evidence_returns_policy_matches():
    risk_results = [
        {
            "finding_id": "finding_001",
            "secret_type": "AWS_ACCESS_KEY_ID",
            "file_path": "data/sample_project/.env",
            "risk_level": "Critical",
        }
    ]

    context_results = [
        {
            "finding_id": "finding_001",
            "environment_hint": "production",
            "context_keywords": ["cloud", "aws", "access_key"],
        }
    ]

    evidence = retrieve_policy_evidence(
        risk_results=risk_results,
        context_results=context_results,
        policy_dir="not_existing_policy_dir",
    )

    assert len(evidence) == 1
    assert evidence[0]["finding_id"] == "finding_001"
    assert len(evidence[0]["matched_policies"]) >= 1
    assert "policy_id" in evidence[0]["matched_policies"][0]
    assert "summary" in evidence[0]["matched_policies"][0]
