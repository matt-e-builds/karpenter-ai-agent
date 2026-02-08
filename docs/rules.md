# Rules and severities

Rules are deterministic. Each finding has a rule ID, severity, message, and
(optional) patch snippet. Rule IDs are stable strings used for evaluation and
explanations.

## EC2NodeClass rules (SecurityAgent)
- security:missing-ami-selectors (high)
- security:overly-broad-ami-selectors (medium)
- security:missing-security-groups (high)
- security:missing-subnets (high)
- security:invalid-iam-settings (high)
- security:ambiguous-iam-settings (medium)

## NodePool ↔ EC2NodeClass rules (SecurityAgent)
- security:missing-nodeclass (high)
- security:missing-nodeclass-ref (medium)

## Legacy rule IDs
Cost and reliability rules are generated from the issue message using this
pattern: <agent>:<message-slug>. Examples: cost:missing-spot, reliability:ttl

## Patch behavior
- Patch snippets are only provided when a safe, generic example is possible.
- Patches are suggestions for human review and are never applied automatically.
- If a safe patch cannot be generated, the finding includes guidance only.
