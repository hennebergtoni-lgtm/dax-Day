# Verified legacy engine payloads

This directory stores the exact recovered V11.2 source payloads in compressed form so the repository can reconstruct and execute the historically verified engines without depending on Google Colab at runtime.

- `oracle_v11_2.py.zlib.b64` -> frozen V11.2 oracle source, SHA-256 `62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f` after decompression.
- `exact_candidate_v11_2.py.zlib.b64` -> V3.5.4 exact-parity candidate source, SHA-256 `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888` after decompression.

The original parity-gate notebook itself is independently pinned by SHA-256 `9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887`.

Compressed storage is provenance-preserving; runtime reconstruction must always verify the decompressed SHA before import.