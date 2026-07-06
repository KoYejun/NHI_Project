from app.scanner.masking import mask_bearer_token, mask_secret


def test_mask_secret_preserves_prefix_and_suffix():
    raw_secret = "AKIA1234567890ABCDEF"

    masked = mask_secret(raw_secret)

    assert masked == "AKIA************CDEF"
    assert raw_secret not in masked


def test_mask_short_secret_fully_masks_value():
    raw_secret = "short"

    masked = mask_secret(raw_secret)

    assert masked == "*****"


def test_mask_bearer_token_keeps_bearer_prefix():
    raw_token = "sampleBearerToken1234567890abcdef"

    masked = mask_bearer_token(raw_token)

    assert masked.startswith("Bearer ")
    assert raw_token not in masked
    assert "sampleBearerToken1234567890abcdef" not in masked
