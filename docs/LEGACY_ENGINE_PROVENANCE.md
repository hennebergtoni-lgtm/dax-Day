# Legacy V11.2 engine provenance

This file records the exact source lineage used for Gate 1 parity. The legacy sources are frozen evidence and must not be reformatted or edited.

## Exact candidate notebook
- Drive title: `NEXT_ENGINE_V3_5_4_FIX2_EXACT_ENGINE_PARITY_GATE.ipynb`
- Drive file id: `17FGfy6L67fa-PomRuBlmJbER_AiKf5yY`
- notebook size at retrieval: 73,929 bytes
- full notebook SHA-256: `9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887`
- extracted embedded engine length: 51,501 characters
- extracted engine SHA-256: `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`

## V11.2 oracle notebook
- Drive title: `V11_2_ONE_CLICK.ipynb`
- Drive file id: `1-ILFNP53cFEVJ_KRY7qGDRqEathvH_Y1`
- notebook size at retrieval: 45,666 bytes
- full notebook SHA-256 at retrieval: `20cac1ce714a2af664d5c39e730c7949bf554399a518a3b9dcf9b9be73d24495`
- extracted embedded engine length: 35,819 characters
- extracted engine SHA-256: `62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f`

## V2.8.18 runner
- Drive title: `DAX_V11_2_V2_8_18_FAST_FULL_RESEARCH_ONE_CLICK.ipynb`
- Drive file id: `1nhqCKKJ-bOGp6ZPJj66Lzid4Ir6LVzYk`
- notebook size at retrieval: 25,824 bytes

The runner establishes the data/session gate used for the new-lab parity reconstruction: 1,673 days, 172,319 M5 session rows, 103 bars/day, Europe/Berlin 09:00–17:30, 144 variants, 81 WFs, and the normal / stress_1.5x / stress_2x cost models.

## Preservation rule
The byte-exact extracted engine sources are stored losslessly as gzip/base64 chunks under `src/daxlab/reference/legacy_payload/`. `legacy_loader.py` decompresses them, verifies the original SHA-256 before every module load, and only then compiles the recovered source. Any hash drift is a Gate 1 failure.
