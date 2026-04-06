# Stub Model

The PlantOps stub model is a deterministic classifier used to validate the full pipeline before integrating real model weights.

## Behavior summary

Given an input filename (lowercased basename):

1. If it contains `healthy`:
   - `predicted_class = healthy`
   - high confidence (~0.97)
   - `source_type = stub_rule`
2. Else if it contains known keywords:
   - `blight` -> `blight`
   - `rust` -> `rust`
   - `spot` -> `leaf_spot`
   - `mildew` -> `powdery_mildew`
   - `rot` -> `root_rot`
   - `scab` -> `scab`
   - confidence (~0.88), `source_type = stub_rule`
3. Else:
   - deterministic hash fallback picks class + bounded confidence
   - `source_type = stub_hash`

## Why this exists

- Ensures repeatable behavior in tests and CI.
- Enables end-to-end system validation with no ML runtime dependencies.
- Provides a safe baseline while model training/deployment work is pending.

## Replacing with a real model

When real model artifacts are available:

- leave this stub package intact for smoke testing
- add a new model package under `models/`
- update loader/config to route production calls accordingly
