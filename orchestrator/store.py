from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Store:
    """Local control plane. Case artifacts never accept caller-selected paths."""

    def __init__(self, root=None):
        self.root = Path(root or os.getenv("TENDER_CASE_ROOT", "outputs")).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.root / "workbench.sqlite3", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, data TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
          CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
            BEGIN SELECT RAISE(ABORT, 'Audit entries are append-only'); END;
          CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
            BEGIN SELECT RAISE(ABORT, 'Audit entries are append-only'); END;
        """)
        self.db.commit()

    def case_path(self, case_id, *parts):
        if not re.fullmatch(r"case_[a-f0-9]{16}", case_id):
            raise ValueError("Invalid case identifier")
        base = self.root / case_id
        path = base.joinpath(*parts)
        # Reject symlink/junction escapes for both the case and the requested file.
        if not base.resolve().is_relative_to(self.root) or not path.resolve().is_relative_to(base.resolve()):
            raise ValueError("Path leaves the case workspace")
        for parent in [path, *path.parents]:
            if parent == self.root:
                break
            if parent.is_symlink():
                raise ValueError("Symlink paths are not permitted")
        return path

    def write(self, case_id, relative, data):
        path = self.case_path(case_id, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise ValueError("Versioned artifacts cannot be overwritten")
        path.write_bytes(data if isinstance(data, bytes) else canonical(data).encode())
        return path

    def save(self, case):
        with self.lock, self.db:
            self.db.execute("INSERT INTO cases VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                            (case["id"], canonical(case)))

    def get(self, case_id):
        self.case_path(case_id)
        row = self.db.execute("SELECT data FROM cases WHERE id=?", (case_id,)).fetchone()
        if not row:
            raise ValueError("Case not found")
        return json.loads(row[0])

    def list(self):
        return [json.loads(r[0]) for r in self.db.execute("SELECT data FROM cases ORDER BY rowid DESC")]

    def event(self, tool, case_id, inputs, outputs, status, call_id=None, started_at=None, **extra):
        payload = dict(tool=tool, case_id=case_id, inputs=inputs, outputs=outputs,
                       status=status, call_id=call_id or uuid.uuid4().hex,
                       started_at=started_at or now(), timestamp=now(), **extra)
        with self.lock, self.db:
            last = self.db.execute("SELECT event_hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            previous = last[0] if last else "0" * 64
            event_hash = digest({"previous_hash": previous, "payload": payload})
            self.db.execute("INSERT INTO audit(payload,previous_hash,event_hash) VALUES (?,?,?)",
                            (canonical(payload), previous, event_hash))
        return event_hash

    def events(self, case_id=None):
        rows = self.db.execute("SELECT * FROM audit ORDER BY seq").fetchall()
        return [dict(seq=r["seq"], previous_hash=r["previous_hash"], event_hash=r["event_hash"],
                     **json.loads(r["payload"])) for r in rows
                if not case_id or json.loads(r["payload"])["case_id"] == case_id]

    def verify_audit(self):
        previous = "0" * 64
        for r in self.db.execute("SELECT * FROM audit ORDER BY seq"):
            payload = json.loads(r["payload"])
            if r["previous_hash"] != previous or r["event_hash"] != digest({"previous_hash": previous, "payload": payload}):
                return False
            previous = r["event_hash"]
        return True
