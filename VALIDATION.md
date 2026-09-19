# Validation

## Converter 0.2.0 — 2026-09-19

- Local suite: 30 tests, 29 passed and 1 skipped (unavailable CPU SVT-AV1).
- All 11 output formats passed real Auto and Re-encode conversions, followed by decoding the resulting files and checking duration, dimensions and audio presence.
- MP4 → MOV → MP4 with Stream copy only retained identical decoded video frame hashes.
- Verified audio/metadata removal, MP4 timed-text to MKV SRT conversion, rejection of incompatible strict-copy requests, fallback after copy failure, unique output names, unchanged source hashes, and cleanup after cancelling both copying and re-encoding.
- Qt tests exercised switching modes, changing the conversion method, converting to MOV, resetting unsupported subtitle settings, and probing a video with an unlisted extension. The conversion screen was rendered and visually inspected.
- These are short generated SDR clips, not a guarantee for every input codec, container variant, camera or player.

## Original MVP — 2026-09-16

Test environment: Windows 11, CPython 3.12.14, PySide6 6.11.2, FFmpeg 9.0.1 essentials build, PyInstaller 6.22.3.

## Results

- Full local suite: **20 tests run, 19 passed, 1 skipped**, in 17.5 seconds.
- The skipped test was CPU AV1 because this local FFmpeg essentials build does not include `libsvtav1`. The application detects that and explains how to choose another codec/build.
- H.264 CPU two-pass target of 1 MB produced **0.975 MB**.
- H.265 CPU two-pass target of 1 MB produced **0.971 MB**.
- HEVC Intel QSV single-pass target of 1 MB produced **0.985 MB**.
- H.264 and HEVC hardware encoding worked with Intel QSV. NVIDIA and AMD runtime availability checks fell back appropriately on this machine; actual encoding on those vendors has not been validated here.
- Real FFmpeg tests covered progress, audio removal, resizing, FPS conversion, source-metadata removal, SRT preservation, MP4 timed-text conversion, cancellation cleanup, damaged input and invalid output folders.
- Source hashes stayed unchanged after compression and cancellation tests.
- Qt tests verified UI event processing during compression and orderly cancellation when closing the window.
- Desktop layouts were rendered and visually inspected. Output controls and progress remain fixed while settings scroll.
- PyInstaller produced the portable Windows folder successfully. The final windowed EXE passed `--smoke-test` with exit code 0, verifying Qt imports and bundled FFmpeg/ffprobe discovery. A third-party ICU DLL conflict discovered during packaging was fixed by isolating the build search path.

These tests use short generated SDR videos. They do not establish perceptual-quality scores, performance on multi-GB footage, support for every GPU/driver, or byte-exact target sizes. HDR and pause are outside this MVP's supported features. GitHub Actions runs the committed tests separately; this document records local results.
