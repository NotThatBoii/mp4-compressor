# Working on Compressly

- Keep each major change in a separate, descriptive Git commit. The owner wants progress committed incrementally and published to the requested GitHub branch when updates are authorized.
- Keep GUI, media processing and worker code separate. Never block the Qt GUI thread with FFmpeg or ffprobe.
- Run the relevant unit tests and real FFmpeg tests for engine changes. Verify the original file stays unchanged and cancellation removes temporary output.
- Check a packaged Windows build when changing packaging or bundled-resource discovery; a successful PyInstaller build alone does not prove the executable launches.
- Never commit virtual environments, media test files, logs, FFmpeg binaries or build output. Keep setup and limitations in README.md current.
