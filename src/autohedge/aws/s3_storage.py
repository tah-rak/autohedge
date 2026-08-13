"""Optional AWS free-tier helpers (disabled by default)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("autohedge.aws")


def upload_outputs_to_s3(
    local_dir: str | Path,
    bucket: str,
    prefix: str = "autohedge/simulations",
    region: str = "us-east-1",
) -> list[str]:
    """
    Upload output artifacts to S3.

    REQUIRED when enabled: AWS credentials (env AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
    or shared credentials file) and an S3 bucket in your account.

    Free alternative: keep aws.enabled=false and use local ./outputs.
    """
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is not installed. Install with `pip install boto3` or disable AWS uploads."
        ) from exc

    if not bucket:
        raise ValueError("s3_bucket is empty; set configs/default.yaml aws.s3_bucket or disable AWS.")

    local_dir = Path(local_dir)
    client = boto3.client("s3", region_name=region)
    uploaded: list[str] = []
    for path in local_dir.rglob("*"):
        if path.is_file():
            key = f"{prefix.rstrip('/')}/{path.relative_to(local_dir).as_posix()}"
            client.upload_file(str(path), bucket, key)
            uploaded.append(f"s3://{bucket}/{key}")
            logger.info("Uploaded %s", uploaded[-1])
    return uploaded


def maybe_upload(config: dict[str, Any], output_dir: str | Path) -> list[str]:
    aws_cfg = config.get("aws", {})
    if not aws_cfg.get("enabled"):
        return []
    return upload_outputs_to_s3(
        output_dir,
        bucket=str(aws_cfg.get("s3_bucket", "")),
        prefix=str(aws_cfg.get("s3_prefix", "autohedge/simulations")),
        region=str(aws_cfg.get("region", "us-east-1")),
    )
