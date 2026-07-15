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

