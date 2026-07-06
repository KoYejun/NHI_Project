def mask_secret(secret_value: str, visible_prefix: int = 4, visible_suffix: int = 4) -> str:
    """
    Secret 원문을 리포트에 저장하지 않기 위해 마스킹한다.

    예:
    AKIA1234567890ABCDEF -> AKIA************CDEF
    ghp_abcdefghijklmnopqrstuvwxyz1234567890 -> ghp_************************7890
    """

    if not secret_value:
        return ""

    secret_length = len(secret_value)

    if secret_length <= visible_prefix + visible_suffix:
        return "*" * secret_length

    prefix = secret_value[:visible_prefix]
    suffix = secret_value[-visible_suffix:]
    masked_body = "*" * (secret_length - visible_prefix - visible_suffix)

    return f"{prefix}{masked_body}{suffix}"


def mask_bearer_token(token_value: str) -> str:
    """
    Bearer Token은 리포트에서 Bearer 접두어는 유지하고 토큰 값만 마스킹한다.
    """

    return f"Bearer {mask_secret(token_value)}"
