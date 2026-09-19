# COMPRESSLY

Created by [NotThatBoii](https://github.com/NotThatBoii) · [MIT License](LICENSE)

A Windows 10/11 desktop video compressor and converter built with Python, PySide6 and real FFmpeg processing. Compress with a quality preset or target size, or convert between video formats. The original stays untouched.

## Download and install

**[Download the Windows installer](https://github.com/NotThatBoii/mp4-compressor/releases/latest)** — choose `Compressly-0.2.0-Setup-x64.exe` under Assets.

Run the downloaded EXE and follow Setup. Python and FFmpeg are included, and the installed app works offline. It installs for your Windows account without an administrator password, adds a Start menu entry, and optionally creates a desktop shortcut. Uninstall through **Windows Settings → Apps → Compressly**. Your video files are preserved.

Requires **64-bit Intel/AMD Windows 10 version 1809 or newer, or Windows 11**. ARM and 32-bit Windows are not validated. GPU drivers are optional: unsupported hardware falls back to CPU.

The first installer is unsigned, so Windows may display SmartScreen or Unknown Publisher. Download only from this repository's Releases page. Each release includes `SHA256SUMS.txt`; compare it with `Get-FileHash .\Compressly-0.2.0-Setup-x64.exe -Algorithm SHA256` if you want to verify the file.

## Features

- Dark desktop interface with drag and drop, file selection, video information and an output folder picker.
- H.265 by default, plus H.264 for compatibility and AV1 through `libsvtav1` when available.
- High Quality, Balanced and Small File presets; approximate Target File Size with CPU H.264/H.265 two-pass encoding.
- NVIDIA NVENC, Intel QSV and AMD AMF, including AV1 when supported by FFmpeg, the GPU and its driver. Auto tests real encoding before selecting hardware and falls back to CPU.
- Original, 4K, 1440p, 1080p, 720p or custom resolution bounds; original/60/30/24 FPS; AAC audio or No Audio.
- Metadata removal, subtitle preservation, progress percentage, encoding FPS, speed, elapsed time, ETA, encoded size and cancellation.
- Unique output names, temporary-file cleanup, final size and space saved, and an Open Output Folder button.

The file picker includes MP4, MOV, MKV, AVI, WebM, M4V, WMV, FLV, MPG/MPEG, TS/MTS/M2TS, 3GP/3G2, VOB, OGV, MXF, F4V and ASF. **All files** and drag-and-drop also accept other extensions for FFmpeg to inspect. Actual support depends on the streams and available decoders; every video format is not guaranteed.

## Convert video formats

1. Select or drop a video, then switch **Compress** to **Convert**.
2. Choose an output format and method. The app shows the expected video/audio handling.
3. Choose the output folder and click **Convert Video**.

**Output formats:** MP4, MOV, MKV, WebM, AVI, WMV, FLV, MPG, TS, M4V and 3GP. MP4 → MOV and MOV → MP4 are supported. Files use names such as `video_converted.mov`; repeated conversions get unique names.

| Method | Behavior |
| --- | --- |
| Auto | Copies compatible video/audio streams without re-encoding and encodes incompatible streams. If copying fails, retries once by re-encoding both selected streams. |
| Re-encode | Always encodes with codecs selected for the output container. Quality can decrease and size can increase. |
| Stream copy only | Copies selected video/audio streams without quality loss. Rejects incompatible combinations; never silently switches to re-encoding. |

Conversion does not target a smaller file. Use **Compress** for quality presets, resizing, hardware acceleration or a target size. Conversion re-encoding uses CPU: H.264/AAC for MP4, MOV, MKV, TS, M4V and 3GP; VP9/Opus for WebM; MPEG-4/MP3 for AVI; WMV2/WMA2 for WMV; FLV1/MP3 for FLV; MPEG-2/MP2 for MPG. Required encoders are included in the Windows installer.

Only the first non-cover-art video and first audio track are selected. **Keep audio** can be turned off. Re-encoded audio is 128 kbps stereo; copied audio retains its original channels. Re-encoded video uses even dimensions and 8-bit SDR; MPG and WMV encoding uses 30 FPS. HDR sources remain unsupported. Container support does not guarantee compatibility with every old device or player.

Metadata and chapters are retained only where the destination supports them. Subtitles are removed by default; choose MKV to preserve subtitles and font attachments. MP4 timed text becomes SRT, potentially losing styling, and requires Auto or Re-encode. Damaged, encrypted or unusual streams may fail with a readable error.

## License

Compressly's original application code is licensed under the **MIT License**, copyright (c) 2026 **NotThatBoii**. See [LICENSE](LICENSE) for the full terms.

Bundled Python, Qt/PySide, FFmpeg and installer components retain their own licenses; the MIT license does not relicense those components. See [THIRD_PARTY.md](THIRD_PARTY.md) and the installed `licenses` folder. The installer displays Compressly's license and includes a copy in the application folder.

## Run from source on Windows (developers)

1. Install **64-bit CPython 3.10 or newer** from [python.org](https://www.python.org/downloads/windows/). Python 3.12 is a good development choice. Enable the Python launcher during installation. Use Windows CPython, not MSYS2 Python.
2. Open PowerShell and run:

```powershell
git clone https://github.com/NotThatBoii/mp4-compressor.git
cd mp4-compressor
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If you installed another Python version, replace `py -3.12` with its launcher version or `python` pointing to Windows CPython. No virtual-environment activation or PowerShell policy change is required.

3. Install FFmpeg using one of the options below.
4. Launch:

```powershell
.\.venv\Scripts\python.exe main.py
```

### FFmpeg setup

Get a Windows build through [FFmpeg's download page](https://ffmpeg.org/download.html#build-windows). Extract **both** `ffmpeg.exe` and `ffprobe.exe` from the same build into:

```text
resources/ffmpeg/ffmpeg.exe
resources/ffmpeg/ffprobe.exe
```

Alternatively, add the build's `bin` directory to PATH and restart Compressly. Bundled executables take priority over PATH. There are no computer-specific paths in the app. FFmpeg executables are not committed to Git. Keep the build's license and redistribution materials if you distribute it.

The app explains how to fix missing tools at startup. Codec availability depends on the build; choose a build containing `libx264`, `libx265` and optionally `libsvtav1`.

## Compression modes

| Mode | H.264 CRF | H.265 CRF | AV1 CRF |
| --- | ---: | ---: | ---: |
| High Quality | 19 | 22 | 24 |
| Balanced | 23 | 26 | 32 |
| Small File | 27 | 30 | 40 |

Lower CRF generally means higher quality and larger files within one encoder. Values are not equivalent between codecs. Hardware uses corresponding encoder-specific quality controls and can produce different sizes and quality. AV1 CPU encoding can be substantially slower. Already compressed videos can become larger: the result screen reports this honestly.

CRF output size cannot be reliably predicted without analyzing or encoding representative content, so the interface explicitly marks its estimate as unavailable. Target mode displays the requested approximate size.

### Target File Size

Sizes use decimal units: 1 MB = 1,000,000 bytes. Audio bitrates use 1 kbps = 1,000 bits/second.

```text
video bits/second = (target MB × 1,000,000 × 8 × 0.98 / duration seconds)
                   − selected audio bits/second
```

Audio is omitted from the budget if the source has none or No Audio is selected. The 2% margin allows for container overhead and encoder variation. Impossible settings are rejected. A resolution/FPS-based heuristic warns when the available video bitrate is likely to give very poor quality; you can adjust settings or explicitly continue.

CPU H.264 and H.265 analyze the video in pass one and encode it in pass two. The progress bar covers both passes; ETA is approximate because they can run at different speeds. Pass logs live in a private temporary directory and are deleted after success, failure or cancellation. Hardware and SVT-AV1 use single-pass bitrate control. **No byte-perfect size is promised**, and simple content may undershoot. Copied subtitles, attachments and metadata can also affect the final size.

### Hardware acceleration

Auto tries NVIDIA, Intel, then AMD for the selected codec. Detection first checks FFmpeg's encoder list, then encodes six test frames to verify the device and driver. This runs off the UI thread. A requested but unavailable vendor falls back to the selected codec's CPU encoder. A hardware failure on the actual source is retried once on CPU. A missing CPU encoder produces a clear error.

Hardware testing can take a few seconds. NVIDIA, Intel and AMD hardware cannot all be validated on one computer; driver and GPU support varies. See the Activity area for the encoder actually used.

## File and stream handling

- Outputs use `video_compressed.mp4`, then `video_compressed_2.mp4`, etc. Existing files and the source are never overwritten.
- Encoding writes inside `.compressly-*` in the output folder. The final name is reserved exclusively only after success, then the output is moved into place on the same drive.
- Cancel asks FFmpeg to quit, then kills it if it does not exit within three seconds. Temporary output and pass logs are removed. Closing during encoding cancels and closes after cleanup.
- The first non-cover-art video and first audio stream are kept. Other audio tracks, extra video angles and data streams are not retained in this MVP.
- AAC audio is copied in quality modes when its known bitrate is already at or below the selected limit; otherwise it is encoded as AAC. Target mode encodes audio at the selected bitrate for budgeting.
- Preserving subtitles switches to MKV when subtitle streams exist. Compatible subtitles and font attachments are copied; MP4 timed text (`mov_text`) is converted to SRT, which can lose styling. Remove subtitles produces MP4.
- Resolution choices are bounding boxes, without upscaling, maintaining aspect ratio and using even dimensions. Portrait videos fit inside the chosen bounds. Original FPS preserves timing; selecting an FPS duplicates or drops frames.
- Remove metadata drops source tags and chapters. Technical tags written by the container/encoder may remain; this is not a forensic anonymization tool.

## Known MVP limitations

- One local file at a time; no batch queue, trimming, preview comparison or resumable jobs.
- HDR sources (PQ/HLG) are rejected to avoid silently damaging their colors. Output is 8-bit SDR; tone mapping, Dolby Vision and HDR preservation need dedicated support.
- Pause is omitted because reliable portable suspension and recovery are not implemented. Cancel is supported.
- Free-space checks run before encoding and during progress. An operating-system crash or forced process termination can leave a `.compressly-*` directory; remove it only after confirming no job is using it.
- Subtitle container limitations, heavily corrupted files and unusual stream combinations may still fail with a readable error. Target-size estimates are approximate.
- Large videos are streamed through FFmpeg, not loaded into Python memory. There is no app-imposed file-size limit, but sufficient free disk space is required.

## Logs

Development: `logs/compressly.log` in the project directory. Packaged app: `%LOCALAPPDATA%\Compressly\logs\compressly.log`, so installation in a read-only location works. Logs rotate at 2 MB with three backups. They contain file paths, selected command arguments and technical FFmpeg errors.

## Tests

Fast unit tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Real-video integration tests (requires FFmpeg and ffprobe):

```powershell
$env:COMPRESSLY_INTEGRATION = "1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:COMPRESSLY_INTEGRATION
```

The integration suite generates short videos, tests all 11 output formats with Auto and Re-encode, decodes the outputs, checks a lossless MP4/MOV round trip, and exercises the Qt conversion controls. It also checks compression, two-pass size tolerance, resizing/audio/metadata/subtitles, cancellation cleanup, and unchanged source hashes. AV1 is skipped if the build lacks SVT-AV1. These tests do not represent an exhaustive multi-GB or multi-GPU benchmark.

## Build a Windows executable

Put FFmpeg and ffprobe in `resources/ffmpeg/` first, with the build's license material, then run:

```powershell
.\build.bat
```

The script installs PyInstaller in `.venv` and produces:

```text
dist/Compressly/Compressly.exe
```

The spec isolates the build's DLL search path from unrelated developer tools to prevent incompatible libraries from entering the bundle. For a diagnostic console build, set `$env:COMPRESSLY_DEBUG_CONSOLE = "1"` before building; remove that environment variable to restore the normal desktop build.

Check the executable's Qt imports and bundled FFmpeg discovery without opening a window:

```powershell
$check = Start-Process .\dist\Compressly\Compressly.exe -ArgumentList '--smoke-test' -Wait -PassThru
$check.ExitCode  # 0 means startup passed
```

Distribute the **entire `dist/Compressly` folder**, usually as a ZIP. This is a one-folder portable build: users do not need Python or FFmpeg separately. Copying just the EXE is insufficient. The build is not signed and Windows may show a reputation prompt. Check FFmpeg and Qt/PySide redistribution obligations before public distribution; no binary license is supplied by this repository on their behalf.

### Build the installable Setup EXE

Install [Inno Setup 6](https://jrsoftware.org/isdl.php), create `.venv` as above, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts/fetch-ffmpeg.py
.\scripts\build-installer.ps1
```

The FFmpeg download uses a pinned version and SHA-256 check. The output is `dist/installer/Compressly-0.2.0-Setup-x64.exe`, with `SHA256SUMS.txt`. Unlike the portable EXE, this **single Setup EXE** contains the complete application and its dependencies. Bundled license texts and notices are installed with the app.

Pass `-Compiler 'C:\path\to\ISCC.exe'` for a custom compiler location or `-SkipAppBuild` to package an already-built app. Close running Compressly instances before updating; Setup does not force-stop compression jobs.

### Publish a release

Update `VERSION` and `installer/release-notes.md`, commit the change, and push to `main`. The Windows release workflow builds the installer, runs real FFmpeg/GUI tests, installs it in a fresh directory, checks packaged startup, reinstalls it, and verifies uninstall preserves a user-created file. Only then does it create a versioned GitHub Release and upload the installer and checksum. Existing versions are never silently replaced; increment `VERSION` for another release. The workflow can also be started manually from GitHub Actions.

## Project layout

```text
main.py                      Application startup
app/main_window.py           GUI orchestration
app/widgets/                 Drop zone, settings, information and progress
app/core/                    Tool detection, probing, bitrate/command planning, encoding
app/workers/                 QThread adapters
app/utils/                   Output names, formatting and logging
resources/ffmpeg/            Optional bundled tools
tests/                       Unit and actual FFmpeg integration tests
Compressly.spec              PyInstaller configuration
build.bat                    Windows build entry point
```

FFmpeg uses argument lists with no shell interpolation. Analysis, hardware tests and compression run in workers; Qt widgets are updated through signals. See the [FFmpeg command documentation](https://ffmpeg.org/ffmpeg.html) and [encoder documentation](https://ffmpeg.org/ffmpeg-codecs.html) for underlying options.
