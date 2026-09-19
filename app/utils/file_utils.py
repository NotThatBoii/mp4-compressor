from pathlib import Path


def format_size(size):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1000 or unit == "TB":
            return f"{size:,.2f} {unit}"
        size /= 1000


def format_time(seconds):
    if seconds is None:
        return "—"
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}" if hours else f"{minutes:02}:{seconds:02}"


def output_path(source, folder, suffix=".mp4", label="compressed"):
    source, folder = Path(source).resolve(), Path(folder).resolve()
    index = 1
    while True:
        ending = "" if index == 1 else f"_{index}"
        candidate = folder / f"{source.stem}_{label}{ending}{suffix}"
        if not candidate.exists() and candidate != source:
            return candidate
        index += 1
