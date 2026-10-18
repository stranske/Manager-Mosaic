# Contract audit guard evidence

Full119testsPASS at93.84percent coverage. Removing both real fact-key registry loader calls makes the unchanged packaged-resource consumer guard fail; exact-byte restoration returns alltestsGREEN. The finalsrc/manager_mosaic diff is empty. The report/catalog enumerate public definitions and package resources, distinguish mandatory and intentionally opt-in rules, and link only existing96/97/98/101 owners. No new production fixes, issue uploads or shared schema/script changes. Presence guards track audit coverage; the named behavioral tests remain the semantic evidence.

Current behavioral gate: `registry-behavior-red.txt` captures two failures after
bypassing `validate_fact_keys` in `src/manager_mosaic/fact_keys.py`;
`registry-behavior-green.txt` captures two passes after exact-byte restoration.
The probe checks that adding/removing keys in the default registry affects
explicit validation, strict thesis evaluation and strict discrepancy detection,
including both flag spellings. These transcripts supplement the earlier static
loader-call gate; they do not represent a committed production-code change.
