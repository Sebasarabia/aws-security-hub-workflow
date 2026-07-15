# Schema compatibility

| Mode | Service | Format | EventBridge detail type | Use |
|---|---|---|---|---|
| `ocsf` | Security Hub | OCSF 1.6 | `Findings Imported V2` | Default/current path |
| `asff` | Security Hub CSPM | ASFF | `Security Hub Findings - Imported` | Compatibility |
| `dual` | Both | Both adapters | Two separate rules | Teaching/migration only |

Both documented events contain exactly one finding. The handler nevertheless rejects
zero, multiple, or non-object findings. Source-specific access stays in adapters.
Unknown severities normalize to `UNKNOWN` and are rejected by the default policy.

Dual mode does not prove the two services are independent signal sources; depending on
account integrations, one underlying issue can appear through both families. DynamoDB
keys include the schema family, so this implementation prevents transport duplicates,
not cross-schema semantic duplicates.

