# Security policy and engineering rules

AI Operator processes potentially sensitive patient and appointment data. Security controls are part of the product definition, not a post-MVP add-on.

## Repository rules

- never commit API keys, passwords, access tokens or production certificates;
- use environment/secret-manager references only;
- do not commit production call recordings, transcripts or patient fixtures;
- test fixtures must be synthetic and non-identifying;
- provider errors/logs must be sanitized before persistence.

## Runtime principles

- least privilege for every provider credential;
- encrypt transport to external/internal providers;
- minimize PII sent to STT/LLM/TTS systems;
- separate supervisor/QA/operator/admin permissions;
- audit critical business mutations;
- require explicit patient-verification policy before exposing or modifying existing appointments.

## LLM boundary

Treat LLM output and retrieved documents as untrusted data.

The model must never be given database credentials, API secrets, unrestricted internal networking, SQL execution or administrator scopes.

Prompt injection cannot grant permissions or expand the tool allowlist.

## Reporting

Until a dedicated private vulnerability-reporting channel is configured, do not publish security-sensitive vulnerabilities or credentials in public GitHub issues. Repository maintainers should configure GitHub private vulnerability reporting before production use.
