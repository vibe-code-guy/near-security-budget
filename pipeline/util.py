"""Small helpers shared by every stage. Standard library only."""
import csv
import gzip
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from . import config


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def day_to_ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_json(path: Path):
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f:
            return json.loads(f.read().decode("utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


def write_bytes(path: Path, b: bytes, gz: bool = False) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if gz:
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as f:  # mtime=0: same bytes every run
            f.write(b)
        b = buf.getvalue()
    path.write_bytes(b)


def write_json(path: Path, obj) -> None:
    write_bytes(path, (json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8"))


def write_csv(path: Path, rows: list, columns: list) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in columns})


def read_csv(path: Path) -> list:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def median(xs: list):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def usd(x) -> str:
    """Fixed formatting so committed CSVs are byte-stable."""
    return "" if x is None else f"{float(x):.2f}"


def rel(path: Path) -> str:
    return Path(path).resolve().relative_to(config.ROOT).as_posix()
