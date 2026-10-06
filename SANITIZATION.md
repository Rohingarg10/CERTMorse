# Public release sanitization

The owner approved rewriting a separate public clone; the private original and
its accepted draft remain private. Private specifications, agent handoffs,
status notes and one-time process scripts are private working documents.
The approved inventory removes 28 paths: 24 from reachable Git history and
four artifact-only paths. All 12 commits remain, including three that become
empty. Both tags point to their mapped commits; [COMMIT-MAP.md](COMMIT-MAP.md)
records the one-to-one mapping. `main` starts from the mapped `v0.1`; `v1.8`
is retained. Public documentation commits follow that scientific release.

All discovered home-prefix spellings become `<HOME>`, hostname fields become
`<HOST>`, and identifying pytest directories become `pytest-of-<USER>`.
The owner explicitly retained the existing author, committer and tagger
identity. Identity metadata is the sole approved exception to anonymization;
the zero-match content audit excludes those metadata fields.

Power-event messages contain event types only. Their timestamps and the three
related recovery metadata timestamps are exact elapsed seconds from the first
event. UTC and local offsets agree, with Decimal precision retained; naive
archived timestamps use the originally declared +05:30 zone. Associated archive
directory names and references use elapsed-offset names. The two raw-data file
sets were merged into existing destinations with zero overlapping paths and
zero overwrites; the two existing manifest files in each destination are kept.

Specification and handoff links in prose and report templates now point to the
public [method](docs/METHOD.md). Literal private paths in old provenance use
numbered `PRIVATE_DOCUMENT` markers. Historical rule/version labels remain
where they identify the interpretation of saved records. Every stored hash
value in historical evidence remains unchanged; redacted provenance is not a
new hash claim about METHOD.

The proposed normalization of 24,046 saved text files was declined. Existing
encoding, BOM and line-ending bytes remain unchanged except for approved
substitutions. New documentation and tools use UTF-8 and LF. Scientific source,
binary measurements, caps, seeds and thresholds are unchanged; no completed
count, sampling or probe unit is rerun. The 43-file scientific source set is
checked byte-for-byte against the private baseline.

The dry-run inventory listed 136 potentially affected gate hash checks.
[The complete inventory](docs/public-hash-checks.csv) now records 133 unchanged
checks and three old report hashes blocked by approved identifier/path edits.
Their original digests are retained. The public gate records unavailable private
inputs and other approved cleanup discrepancies separately, and executes every
remaining assertion. A public result with blocked checks is not a full PASS.
[public-policy.json](docs/public-policy.json) lists the independently verified
approved byte changes and removals without publishing private file names.

Raw results and historical archives remain outside Git. Release archives omit
test scratch directories and private working documents, list changed files and
have new SHA-256 manifests for their cleaned bytes. Old manifests remain evidence
about their original bytes. No push is part of this preparation.

The private-state guard checks HEAD, ordinary branches/tags, index, clean status,
the accepted draft and all scientific source hashes. Codex-owned temporary refs
are recorded separately because their names rotate between tool sessions; they
are never imported into public history.
