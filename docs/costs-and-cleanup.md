# Costs and cleanup

Prices and regional availability change; use current AWS pricing pages before deploying.
This stack can incur Lambda invocation/compute, EventBridge events, DynamoDB on-demand
requests/storage, SNS publication/delivery, SQS requests/storage, and CloudWatch logs,
metrics, and alarms. Optional existing customer-managed KMS keys have request/key costs;
future S3 records would add storage/request/lifecycle costs.

Security Hub, Security Hub CSPM, GuardDuty, Inspector, Macie, and AWS Config can create
material costs independently of this Terraform state. The stack neither enables nor
disables them. Free tiers and trials are account- and time-dependent. Estimate from the
expected finding rate, duplicate rate, log volume/retention, notification subscribers,
and alarm count, using the official pricing calculators/pages.

Current official pages: [Security Hub](https://aws.amazon.com/security-hub/pricing/),
[GuardDuty](https://aws.amazon.com/guardduty/pricing/),
[Inspector](https://aws.amazon.com/inspector/pricing/), [Macie](https://aws.amazon.com/macie/pricing/),
[AWS Config](https://aws.amazon.com/config/pricing/), [Lambda](https://aws.amazon.com/lambda/pricing/),
[EventBridge](https://aws.amazon.com/eventbridge/pricing/),
[DynamoDB](https://aws.amazon.com/dynamodb/pricing/), [SNS](https://aws.amazon.com/sns/pricing/),
[SQS](https://aws.amazon.com/sqs/pricing/), [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/),
[KMS](https://aws.amazon.com/kms/pricing/), and [S3](https://aws.amazon.com/s3/pricing/).

## Cleanup

1. In the same working directory/backend, review `terraform plan -destroy`, obtain
   approval, and manually run `terraform destroy` for state-managed resources.
2. Verify the SNS topic, Lambda, both possible EventBridge rules, SQS DLQ, DynamoDB table,
   alarms, and explicit log group are gone in the selected Region.
3. Inspect resources created manually, including topic subscriptions and any synthetic
   findings. Suppress/archive custom CSPM synthetic findings according to current service
   procedures; this project does not import them in v1.
4. If an existing customer-managed key was supplied, inspect it separately. Terraform
   does not own or schedule deletion of that key.
5. Confirm pre-existing account-level services remain in their intended state; Terraform
   does not disable Security Hub, CSPM, GuardDuty, Inspector, Macie, or Config.
6. After confirming remote/state needs and from the repository root, `make clean`; remove
   local state/backend files manually and carefully. Never delete a team backend bucket
   as generic cleanup.
