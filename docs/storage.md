# Storage and migration

Archledger derives its storage topology from Ledgercore. The shared project
manifest is `.ledger/ledger.toml`; the Archledger tool configuration is
`.ledger/archledger/config.toml`; and authoritative source data is under
`.ledger/archledger/data`. Do not infer paths from old `archledger_dir` values.

Inspect the effective topology without writes:

```bash
archledger --json storage where
archledger --json storage validate
```

`storage set` changes the manifest or local override only. It does not move
authoritative data. A topology change that needs data movement must be planned
and applied through the canonical migration handler:

```bash
archledger --json storage set data --storage external \
  --storage-root ../archledger-data --reason "use shared data volume"
archledger --json migrate plan storage-layout \
  --storage external --external-root ../archledger-data
archledger --json migrate apply storage-layout \
  --reason "activate reviewed storage plan"
```

Plans are strict, hashed, tied to the project root and source fingerprint, and
must be recreated after topology or data changes. The source remains preserved
until a successful activation receipt exists. Never copy or move the data
directory manually.

The installed Ledgercore release reports its migration capabilities in plan,
status, and apply results. When schema-3 execution hooks or resume/rollback
recovery are unavailable, Archledger reports `manual-intervention` and does
not attempt an unsafe move.
