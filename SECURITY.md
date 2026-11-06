# Security Policy

## Supported versions

| Branch / release | Security updates |
| ---------------- | ---------------- |
| `main` (latest)  | :white_check_mark: |
| Older tags / forks | :x: (please upgrade to `main`) |

## Reporting a vulnerability

**Do not open a public GitHub issue for active credential leaks, session theft, or unpatched RCE.**

Preferred reporting channels (in order):

1. **GitHub Security Advisories** for this repository (Private vulnerability reporting), if enabled.
2. Contact the repository owner (`vvChu`) via a private channel you already use for CCBA ops.

Please include:

- Affected paths / packages
- Reproduction steps (without pasting live secrets)
- Impact assessment
- Whether the issue is already public

### Expected response

- Acknowledgement within **7 days**
- Status update within **14 days**
- Fix or mitigation targeted as soon as practical for Critical/High findings

If a secret was committed:

1. Rotate / revoke the credential immediately
2. Remove it from the tree
3. Scrub git history (`git filter-repo` / BFG) and coordinate with collaborators before force-pushing

## Hardening baselines

- Never commit `.env`, Chrome profiles, `cookies.json`, or API keys
- Prefer `AI_GATEWAY_URL` / env placeholders over hard-coded Tailscale IPs
- Prefer `subprocess` with `shell=False` and argv lists in harness code
