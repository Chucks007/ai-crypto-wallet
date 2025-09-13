# Security & Compliance — Standards

## Secrets management
- Use environment variables (`.env` for dev) and never commit secrets.
- Scope API keys per environment (1inch, Tenderly, RPC providers).
- Rotate keys on schedule and on incident.

## Key handling
- No production private keys on server; use browser wallet or Safe.
- Dev/test: burner EOA only, limited funds, restricted to `EXECUTION_ALLOWED_CHAIN_IDS`.
- Audit logging of all signing events (who/when/what) with tx hashes.

## Approvals
- Prefer Permit2. If standard ERC‑20 approvals are used:
  - Bound approval amounts (no unlimited allowances).
  - Revoke/update on strategy or spender change.

## Audit logging depth
- Log inputs and outputs of trades: quotes, chosen route, minOut, gas caps, simulation results, broadcast hash, receipt.
- Include user decisions (approve/reject) and thresholds at decision time.

## Transport & storage
- HTTPS everywhere in prod.
- Encrypt at rest for any stored credentials (if unavoidable), but avoid storing keys.

## Dependency hygiene
- Pin versions; run periodic `npm audit` / `pip audit` and review findings.

## Incident response
- Emergency stop flag halts execution immediately.
- On failure bursts or suspicious activity: rotate keys, revoke approvals, and pause execution.
