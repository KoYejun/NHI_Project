import hashlib


def mask_secret(
    secret_value: str,
    visible_prefix: int = 4,
    visible_suffix: int = 4,
) -> str:
    """
    Secret 원문을 리포트에 직접 저장하지 않기 위해 마스킹한다.

    기본 정책:
    - 앞 4자와 뒤 4자만 노출
    - 길이가 짧은 값은 전체 마스킹
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


def fingerprint_secret(secret_value: str) -> str:
    """
    Secret 원문을 저장하지 않고도 동일 Secret의 반복 노출을 계산하기 위한 fingerprint를 만든다.
    """

    return hashlib.sha256(secret_value.encode("utf-8")).hexdigest()


def mask_line_content(
    line_content: str,
    raw_secret: str,
    masked_secret: str,
) -> str:
    """
    라인 전체를 저장할 때도 Secret 원문이 남지 않도록 해당 구간을 마스킹한다.
    """

    if not raw_secret:
        return line_content

    return line_content.replace(raw_secret, masked_secret)
