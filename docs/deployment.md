# Deployment guide

## Impact and prerequisites

Deployment creates billable regional resources but enables no account-level security
service. Confirm the selected Region supports current Security Hub or Security Hub CSPM,
and confirm the chosen capability is already enabled and producing findings. Choose an
authorized sandbox account, set `allowed_aws_account_ids`, and review IAM and costs.

## Local state demo

```bash
make setup
make check
cp terraform/terraform.tfvars.example terraform/demo.auto.tfvars
# Replace 000000000000 and select the intended schema mode.
make package
terraform -chdir=terraform init
terraform -chdir=terraform plan -out=reviewed.tfplan
# Review every resource and cost/account impact before any manual apply.
```

No apply is hidden in the Makefile. Do not commit `.tfvars`, plans, state, `.terraform/`,
or the package. Subscribe endpoints to the output topic manually only after considering
recipient authorization and message handling.

## Read-only post-deployment verification

After apply, use the Terraform outputs and run the verifier with the exact deployed
names. The verifier performs read-only API calls and exits nonzero on a mismatch:

```bash
python scripts/verify_deployment.py \
  --function-name security-hub-workflow-demo-processor \
  --table-name security-hub-workflow-demo-idempotency \
  --topic-arn <terraform-sns-topic-arn> \
  --rule-name security-hub-workflow-demo-ocsf-findings \
  --dlq-url <terraform-dlq-url> \
  --region us-east-1 \
  --schema-mode ocsf \
  --expect-no-subscriptions \
  --package build/finding-processor.zip
```

Pass the matching timeout, retention, retry, idempotency, log-level, or SNS KMS options
when overriding their Terraform defaults. In `dual` mode, run the verifier once for each
rule name; each rule must contain one of the two documented detail types.

If `sns_kms_key_arn` is set, its key policy must allow the processor role to generate
data keys and decrypt. Terraform adds the exact symmetric data-key actions and
`kms:Decrypt` to the role policy, scoped to the supplied key, but it does not modify an
externally managed key policy. Amazon SNS supports symmetric KMS keys only.

Adding `--expect-idempotency-record` after a deliberate synthetic Lambda invocation also
confirms that the deployed concurrency store contains a record. The verifier does not
create findings, publish events, invoke Lambda, or prove Security Hub delivery.

## Team backend

Use an **existing**, separately governed S3 bucket. Enable versioning and encryption,
use least-privilege access and partial backend configuration, and set `use_lockfile =
true`. S3 lockfile-based locking replaces deprecated DynamoDB locking. Do not create the
bucket from the state it stores, and do not pass credentials in backend arguments.

## Future GitHub deployment

If the owner later adds deployment, use GitHub OIDC, a repository- and environment-scoped
IAM trust policy, protected environments, manual `workflow_dispatch`, reviewed plan
artifacts, explicit approval before apply, and a separately explicit destroy operation.
Never use long-lived AWS keys or expose credentials to pull requests.
