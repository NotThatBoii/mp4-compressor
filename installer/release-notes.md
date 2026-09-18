## Install Compressly on Windows

Download **Compressly-0.1.0-Setup-x64.exe** below and run it. Setup installs Compressly for your Windows account and adds a Start menu shortcut. Python and FFmpeg are included; no separate installation is needed.

**Supported:** Windows 10 version 1809 or newer / Windows 11, 64-bit Intel or AMD laptops. ARM and 32-bit Windows are not validated for this release.

### Included

- H.264 / H.265 compression, quality presets and approximate target sizes.
- Hardware encoder detection with CPU fallback.
- Live progress, safe cancellation, resizing, audio and subtitle options.
- Start menu shortcut, optional desktop shortcut and Windows uninstaller.
- SHA256SUMS.txt to verify the download.

This initial release is **unsigned**; Windows may show SmartScreen or Unknown Publisher. Download only from this repository's release page. No HDR support or pause yet; CPU AV1 is unavailable in the bundled essentials build. Hardware availability depends on the laptop's GPU and driver.

The release workflow checks real compression, installation, packaged startup, reinstallation and uninstallation before publishing. Uninstall preserves your video files. See README.md and THIRD_PARTY.md for usage and bundled-component information.
