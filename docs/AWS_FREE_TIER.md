# AWS Free-Tier Guide (Optional)

AutoHedge runs **fully locally by default**. AWS is optional and only used to store analysis artifacts.

## What you can do on free tier

1. Create an S3 bucket in your AWS account (S3 free tier / always-free requests apply within Amazon's current free-tier limits).
2. Store `analysis.json` / `report.md` objects under a prefix such as `autohedge/simulations/`.
3. Optionally inspect logs with CloudWatch if you later wrap the CLI in Lambda (advanced; not required).

## Required when enabling AWS

- `REQUIRED: AWS_ACCESS_KEY_ID`
- `REQUIRED: AWS_SECRET_ACCESS_KEY`
- `REQUIRED: S3 bucket name` in `configs/default.yaml` → `aws.s3_bucket`

Free alternative: keep `aws.enabled: false` and read files under `./outputs`.

## Setup steps

1. Install optional dependency:
   ```bash
   pip install boto3
   ```
2. Configure credentials using the free AWS CLI / shared credentials file (do **not** commit secrets):
   ```bash
   aws configure
   ```
3. Edit `configs/default.yaml`:
   ```yaml
   aws:
     enabled: true
     region: us-east-1
     s3_bucket: your-free-tier-bucket-name
     s3_prefix: autohedge/simulations
   ```
4. Run an analysis:
   ```bash
   autohedge analyze --portfolio configs/portfolios/balanced.yaml --scenario risk_off
   ```

## Cost safety

- Keep objects small (JSON/Markdown reports only).
- Disable uploads anytime by setting `aws.enabled: false`.
- Never commit access keys.
- This project does **not** require SageMaker endpoints, paid LLM APIs, or always-on EC2.

## Not used (to stay free)

- Managed vector DBs
- Paid market-data vendors
- Hosted LLM APIs
- Emergent or other paid app platforms
