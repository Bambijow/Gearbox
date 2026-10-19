# Independent peer review receipt

Persist a machine-readable receipt at `final_review.peer_receipt` with `peer_outcome` (`folded|fallback|failed|not_required`), `requested_provider`, `verified_provider`, `peer_evidence_ref`, and `fallback_reason` (null if inapplicable).

`folded` requires a received independent result, verified provider identity, inspectable evidence, and centrally reconciled findings. `fallback` means an explicit replacement route was used when an independent peer was unavailable; `failed` means the requested peer failed or returned unusable output; `not_required` means the route requested no peer.

Launching a peer job is not receiving its report; unverifiable identity must never be marked `folded`. In `full` + `hybrid`, a non-folded receipt cannot support claims of completed independent review and requires explicit adjudication. Never silently downgrade to local-only PASS. This receipt is provenance, not gate evidence.

Evaluate success, peer unavailable, launched with no usable result, and unverifiable identity.
