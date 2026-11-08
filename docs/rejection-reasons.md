# Rejection codes in `seen.json`

Every dropped ad carries a `code` from this closed list and a one-line `reason`. If the cause is location, the reason quotes the ad's own line. Never reuse a code for a different cause: use `other` and explain.

| Code | Use when |
|---|---|
| `not-research` | Title matched but the role is another discipline (security, engineering, economics, product management) |
| `commercial-role` | Sales or go-to-market leadership, not the role you want |
| `onsite-required` | Ad requires office presence beyond your limit (quote the line) |
| `region-excluded` | Ad's country list excludes your place (quote the line) |
| `wrong-level` | Level below what you want |
| `usability-led` | Role is led by a discipline you excluded |
| `below-floor` | Stated pay clearly under your floor |
| `excluded-company` | Company is on your exclusion list |
| `already-applied` | You applied or approached already |
| `other` | Anything else; the reason must say what |

Entry format (one per ad URL):

```json
"<url>": {"status": "dropped", "code": "onsite-required", "reason": "\"We are an office-first company.\"",
          "company": "Example", "title": "Senior Researcher", "first_seen": "2026-01-05", "policy_hash": "optional"}
```

`status` is `reported` or `dropped`. A reported ad that disappears from its board gets `closed: <date>`.
