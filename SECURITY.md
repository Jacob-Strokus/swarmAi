# Security & Responsible Use

swamAi includes capabilities that touch networked systems. Use them only where
you are legally authorized to do so.

## Authorized use only

The `offensive` capability pack is intended for:

- Assets **you own**, or
- Engagements where you have **written authorization** (a signed scope / rules
  of engagement).

Unauthorized scanning or access of systems you do not own or control may be
illegal in your jurisdiction (e.g. the U.S. Computer Fraud and Abuse Act and
equivalents elsewhere).

## Controls built into the framework

- **Scope enforcement in code.** Every active action is checked against
  `ScopeGuard`, constructed from the mission's explicit `scope` list. An empty
  scope refuses all active actions. There is no override flag.
- **No weaponization.** The project deliberately excludes exploitation payloads,
  malware, C2, and delivery mechanisms. Recon primitives are limited to standard
  passive/light techniques (DNS resolution, HTTP service fingerprinting).

## Reporting a vulnerability

Open a private security advisory on the GitHub repository, or email the
maintainer. Please do not file public issues for undisclosed vulnerabilities.
