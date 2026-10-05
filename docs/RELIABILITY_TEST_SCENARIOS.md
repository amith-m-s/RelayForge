# Reliability Test Scenarios

These scenarios provide a reproducible checklist for local validation.

## Idempotent ingestion

Send the same event with the same organization-scoped idempotency key twice.

Expected: one logical event is created and the duplicate request does not create another event record.

## Retry behavior

Send an event to a receiver that returns HTTP 429 or 5xx.

Expected: the delivery enters retry scheduling with bounded exponential backoff and jitter.

## Dead-letter behavior

Allow a delivery to exhaust its configured retry attempts.

Expected: the failed delivery is represented as a dead-letter record and is available for replay.

## Replay

Replay a dead-letter event after correcting the downstream failure.

Expected: a new delivery attempt is queued without rewriting the historical audit record.

## Signature verification

Verify an outbound payload using the configured HMAC-SHA256 secret.

Expected: a valid signature is accepted and a modified payload fails verification.

## Rate limiting

Exceed the configured Redis fixed-window limit.

Expected: requests beyond the limit are rejected until the window resets.

These checks are local engineering scenarios; they are not claims about verified external production traffic.
