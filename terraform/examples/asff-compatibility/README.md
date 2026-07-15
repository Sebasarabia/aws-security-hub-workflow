# Security Hub CSPM ASFF compatibility

Set `finding_schema_mode = "asff"` only when Security Hub CSPM is already enabled in
the selected Region. The Terraform does not enable it. Use `dual` only during a
deliberate migration or teaching exercise because logical duplicates can result.

