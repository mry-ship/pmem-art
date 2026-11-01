# p2_aspect fixture

Self-contained mini `.memory-art/` used by `tests/test_p2_session_and_aspect.py`.
The tests copy `memory/` into a temp project as `.memory-art/` and generate the
PNG assets they need with Pillow, so they no longer depend on the live
`.memory-art/` demo library (which changes as the user works).

Module contracts mirror the historical demo library (before commit a66373f
dropped the old Astra / case-study entries).
