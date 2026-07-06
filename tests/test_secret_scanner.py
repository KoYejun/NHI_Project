from app.scanner.secret_scanner import scan_directory
from tests.sample_data_factory import RAW_SECRETS, create_sample_project


def test_scan_directory_detects_expected_secret_types(tmp_path):
    sample_project = create_sample_project(tmp_path)

    findings = scan_directory(str(sample_project))

    secret_types = {finding["secret_type"] for finding in findings}

    assert len(findings) == 4
    assert "AWS_ACCESS_KEY_ID" in secret_types
    assert "GITHUB_TOKEN" in secret_types
    assert "GENERIC_CLIENT_SECRET" in secret_types
    assert "BEARER_TOKEN" in secret_types


def test_scan_directory_does_not_return_raw_secret_values(tmp_path):
    sample_project = create_sample_project(tmp_path)

    findings = scan_directory(str(sample_project))
    findings_text = str(findings)

    for raw_secret in RAW_SECRETS:
        assert raw_secret not in findings_text

    assert "raw_secret" not in findings_text
    assert "masked_secret" in findings_text
