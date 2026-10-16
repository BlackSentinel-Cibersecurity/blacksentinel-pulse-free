# Security Policy — BlackSentinel Pulse (OSS)

BlackSentinel builds security products; we hold our own code to the same bar.

## Reporting a vulnerability

**Please do not open public issues for security problems.**

Report privately through one of:

1. **GitHub private vulnerability reporting** (preferred): this repository's
   **Security** tab → **Report a vulnerability** (a private advisory visible
   only to the maintainers).
2. The security contact published at **https://blacksentinel.com** if you
   cannot use GitHub.

Include: affected version/commit, description and impact, and reproduction
steps or a proof of concept.

## Our commitment

- Acknowledgement within **3 business days**.
- Triage assessment within **10 business days**.
- Coordinated disclosure, with credit to reporters who wish to be named.

## Supported versions

Security fixes land on the default branch and the latest tagged release;
older releases are supported on a best-effort basis.

## Scope

In scope: this repository's source, build and deployment configuration.
Out of scope: issues requiring a compromised host, findings against
placeholder credentials in `*.example` files, and DoS from unrealistic load.
