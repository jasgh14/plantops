# Models Directory

This directory contains model assets used by PlantOps inference.

## Current state

- `stub_model/` is the default model package used for local development and testing.
- Inference currently relies on deterministic filename rules + hash fallback (via `StubClassifier`).

## Expected structure for a real model package (future)

A production-ready model package should typically include:

- model weights/artifacts (framework-specific)
- label map file
- model metadata (version, training date, metrics, class definitions)
- optional preprocessing metadata

Example (future):

```text
models/
└─ production_model/
   ├─ model.onnx
   ├─ labels.yaml
   └─ metadata.yaml
```

## Integration notes

To switch from stub to real model:

1. Add model files under `models/`.
2. Update config (`model_path`, `label_map_path`, `use_stub_model: false`).
3. Extend `src/inference/model_loader.py` to instantiate the real classifier.
4. Keep output contract unchanged to preserve pipeline/report compatibility.
