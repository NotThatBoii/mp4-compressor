## Compressly 0.2.0 — video conversion

Download **Compressly-0.2.0-Setup-x64.exe** below. Close Compressly and run Setup to update. Python and FFmpeg are included; the app works offline.

### New in 0.2.0

- Switch between **Compress** and **Convert** in the same app.
- Convert to **MP4, MOV, MKV, WebM, AVI, WMV, FLV, MPG, TS, M4V and 3GP**.
- **Auto** copies compatible streams and re-encodes others, with a retry if copying fails. **Re-encode** always encodes. **Stream copy only** preserves video/audio quality and rejects incompatible combinations.
- View the conversion plan before starting. Choose whether to keep audio, metadata and MKV subtitles.
- Broader input selection, including an All files option for other FFmpeg-readable formats.
- Unique output names, live progress and safe cancellation; originals stay untouched.

Conversion re-encoding uses CPU and can increase file size. Re-encoded audio becomes stereo; MPG/WMV encoding uses 30 FPS. Only the first video and audio tracks are retained. Subtitles require MKV; HDR remains unsupported. See README for details.

Created by **NotThatBoii**. Compressly's original code is MIT-licensed; bundled components retain their own licenses.

**Supported:** Windows 10 version 1809 or newer / Windows 11, 64-bit Intel or AMD laptops. ARM and 32-bit Windows are not validated for this release.

### Included

- H.264 / H.265 compression, quality presets and approximate target sizes.
- Hardware encoder detection with CPU fallback.
- Live progress, safe cancellation, resizing, audio and subtitle options.
- Start menu shortcut, optional desktop shortcut and Windows uninstaller.
- SHA256SUMS.txt to verify the download.

This release is **unsigned**; Windows may show SmartScreen or Unknown Publisher. Download only from this repository's release page. No HDR support or pause yet; CPU AV1 is unavailable in the bundled essentials build. Hardware availability depends on the laptop's GPU and driver.

The release workflow checks real compression, conversion, GUI operation, installation, packaged startup, reinstallation and uninstallation before publishing. Uninstall preserves your video files. See README.md and THIRD_PARTY.md for usage and bundled-component information.
