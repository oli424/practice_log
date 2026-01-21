from __future__ import annotations

import csv
import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional


DATA_FILE = Path(__file__).with_name("practice_log.json")


@dataclass
class PracticeSession:
    id: str
    date: str               # ISO format: YYYY-MM-DD
    instrument: str
    piece: str
    duration_minutes: int
    notes: str = ""


def _start_of_week(d: date) -> date:
    # Monday = 0, Sunday = 6
    return d - timedelta(days=d.weekday())


def weekly_summary(top_n: int = 5) -> dict:
    today = date.today()
    start = _start_of_week(today)
    sessions = list_sessions(since=start.isoformat())

    total = sum(s.duration_minutes for s in sessions)

    minutes_by_instrument = defaultdict(int)
    minutes_by_piece = defaultdict(int)

    for s in sessions:
        minutes_by_instrument[s.instrument] += s.duration_minutes
        minutes_by_piece[s.piece] += s.duration_minutes

    top_pieces = sorted(minutes_by_piece.items(), key=lambda x: x[1], reverse=True)[:top_n]
    instruments_sorted = sorted(minutes_by_instrument.items(), key=lambda x: x[1], reverse=True)

    return {
        "start_date": start.isoformat(),
        "end_date": today.isoformat(),
        "total_minutes": total,
        "minutes_by_instrument": instruments_sorted,
        "top_pieces": top_pieces,
        "session_count": len(sessions),
    }


def _load_sessions(path: Path = DATA_FILE) -> List[PracticeSession]:
    if not path.exists():
        return []
    
    raw = json.loads(path.read_text(encoding="utf-8"))
    sessions: List[PracticeSession] = []
    changed = False

    for item in raw:
        if "id" not in item or not item["id"]:
            item["id"] = uuid.uuid4().hex
            changed = True
        sessions.append(PracticeSession(**item))

    # Persist ids back to disk so they stay stable
    if changed:
        _save_sessions(sessions, path)

    return sessions


def _save_sessions(sessions: List[PracticeSession], path: Path = DATA_FILE) -> None:
    raw = [asdict(s) for s in sessions]
    path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")


def add_session(
    instrument: str,
    piece: str,
    duration_minutes: int,
    notes: str = "",
    session_date: Optional[str] = None,
) -> PracticeSession:
    if session_date is None:
        session_date = date.today().isoformat()

    try:
        datetime.strptime(session_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError("Date must be in YYYY-MM-DD format.") from e
    
    if duration_minutes <= 0:
        raise ValueError("Duration must be a positive number of minutes.")
    
    session = PracticeSession(
        id=uuid.uuid4().hex,
        date=session_date,
        instrument=instrument.strip(),
        piece=piece.strip(),
        duration_minutes=duration_minutes,
        notes=notes.strip(),
    )

    sessions = _load_sessions()
    sessions.append(session)
    _save_sessions(sessions)

    return session


def list_sessions(
    instrument: Optional[str] = None,
    since: Optional[str] = None,
) -> List[PracticeSession]:
    sessions = _load_sessions()

    if instrument:
        sessions = [s for s in sessions if s.instrument.lower() == instrument.lower()]

    if since:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError("Since-date must be in YYYY-MM-DD format.") from e
        sessions = [
            s for s in sessions
            if datetime.strptime(s.date, "%Y-%m-%d").date() >= since_dt
        ]
    
    sessions.sort(key=lambda s: s.date, reverse=True)
    return sessions


def total_minutes(
    instrument: Optional[str] = None,
    since: Optional[str] = None,
) -> int:
    return sum(s.duration_minutes for s in list_sessions(instrument=instrument, since=since))


def _prompt(text: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{text}{suffix}: ").strip()
    return value if value else (default or "")


def export_csv(path: Optional[Path] = None) -> Path:
    sessions = list_sessions()
    if path is None:
        path = Path(__file__).with_name("practice_export.csv")

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "date", "instrument", "piece", "duration_minutes", "notes"],
        )
        writer.writeheader()
        for s in sessions:
            writer.writerow(asdict(s))

    return path

def get_session(session_id: str) -> PracticeSession:
    sessions = _load_sessions()
    for s in sessions:
        if s.id == session_id:
            return s
    raise ValueError(f"No session found with id: {session_id}")

def update_session(
    session_id: str,
    *,
    session_date: Optional[str] = None,
    instrument: Optional[str] = None,
    piece: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    notes: Optional[str] = None,
) -> PracticeSession:
    sessions = _load_sessions()
    for i, s in enumerate(sessions):
        if s.id == session_id:
            # Validate and apply updates
            if session_date is not None:
                datetime.strptime(session_date, "%Y-%m-%d")
                s.date = session_date

            if instrument is not None:
                s.instrument = instrument.strip()

            if piece is not None:
                s.piece = piece.strip()

            if duration_minutes is not None:
                if duration_minutes <= 0:
                    raise ValueError("Duration must be a positive number of minutes")
                s.duration_minutes = duration_minutes

            if notes is not None:
                s.notes = notes.strip()

            sessions[i] = s
            _save_sessions(sessions)
            return s
        
    raise ValueError(f"No session found with id: {session_id}")

def delete_session(session_id: str) -> None:
    sessions = _load_sessions()
    new_sessions = [s for s in sessions if s.id != session_id]
    if len(new_sessions) == len(sessions):
        raise ValueError(f"No sesssion found with id: {session_id}")
    _save_sessions(new_sessions)

def _resolve_id_prefix(prefix: str) -> str:
    prefix = prefix.strip()
    sessions = _load_sessions()
    matches = [s for s in sessions if s.id.startswith(prefix)]
    if len(matches) == 0:
        raise ValueError("No session matches that id/prefix.")
    if len(matches) > 1:
        raise ValueError("Multiple sessions match that prefix. Paste full id.")
    return matches[0].id

def run_cli() -> None:
    while True:
        print("\nPractice Log")
        print("1) Add session")
        print("2) List sessions")
        print("3) Total minutes")
        print("4) Exit")
        print("5) Weekly summary")
        print("6) Export CSV")
        print("7) Edit session")
        print("8) Delete session")

        choice = input("Choose: ").strip()

        try:
            if choice == "1":
                d = _prompt("Date (YYYY-MM-DD)", default=date.today().isoformat())
                inst = _prompt("Instrument")
                piece = _prompt("Piece / exercise")
                mins_str = _prompt("Duration (minutes)")
                notes = _prompt("Notes (optional)", default="")

                session = add_session(
                    instrument=inst,
                    piece=piece,
                    duration_minutes=int(mins_str),
                    notes=notes,
                    session_date=d,
                )
                print(f"Saved: {session.date} | {session.instrument} | {session.piece} | {session.duration_minutes} min")

            elif choice == "2":
                inst = _prompt("Filter instrument (blank = all)", default="").strip() or None
                since = _prompt("Since date YYYY-MM-DD (blank = all)", default="").strip() or None
                sessions = list_sessions(instrument=inst, since=since)

                if not sessions:
                    print("No sessions found.")
                else:
                    for s in sessions:
                        notes_part = f" — {s.notes}" if s.notes else ""
                        short_id = s.id[:8]
                        print(f"{short_id} | {s.date} | {s.instrument} | {s.piece} | {s.duration_minutes} min{notes_part}")

            elif choice == "3":
                inst = _prompt("Filter instrument (blank = all)", default="").strip() or None
                since = _prompt("Since date YYYY-MM-DD (blank = all)", default="").strip() or None
                total = total_minutes(instrument=inst, since=since)
                print(f"Total: {total} minutes")

            elif choice == "4":
                break
            
            elif choice ==  "5":
                summary = weekly_summary(top_n=5)
                print(f"\nWeek: {summary['start_date']} to {summary['end_date']}")
                print(f"Sessions: {summary['session_count']}")
                print(f"Total: {summary['total_minutes']} minutes")

                if summary["minutes_by_instrument"]:
                    print("\nBy instrument:")
                    for inst, mins in summary["minutes_by_instrument"]:
                        print(f"- {inst}: {mins} min")

                if summary["top_pieces"]:
                    print("\nTop pieces:")
                    for piece, mins in summary["top_pieces"]:
                        print(f"- {piece}: {mins} min")
                else:
                    print("\nNo sessions logged this week")

            elif choice == "6":
                out_path = export_csv()
                print(f"Exported CSV to : {out_path}")

            elif choice == "7":
                prefix = _prompt("Enter session id (8-char prefix ok if unique)").strip()
                full_id = _resolve_id_prefix(prefix)
                s = next(x for x in _load_sessions() if x.id == full_id)
                
                print(f"Editing: {s.id[:8]} | {s.date} | {s.instrument} | {s.piece} | {s.duration_minutes} min")

                new_date = _prompt("New date (YYYY-MM-DD)", default=s.date).strip()
                new_inst = _prompt("New instrument", default=s.instrument).strip()
                new_piece = _prompt("New piece", default=s.piece).strip()
                new_mins_str = _prompt("New duration (minutes)", default=str(s.duration_minutes)).strip()
                new_notes = _prompt("New notes", default=s.notes).strip()

                updated = update_session(
                    full_id,
                    session_date=new_date,
                    instrument=new_inst,
                    piece=new_piece,
                    duration_minutes=int(new_mins_str),
                    notes=new_notes,
                )
                print(f"Updated: {updated.id[:8]} | {updated.date} | {updated.instrument} | {updated.piece} | {updated.duration_minutes} min")

            elif choice == "8":
                prefix = _prompt("Enter session id (8-char prefix of if unique)").strip()
                full_id = _resolve_id_prefix(prefix)
                s = next(x for x in _load_sessions() if x.id == full_id)

                confirm = _prompt(f"Type YES to delete {s.id[:8]} ({s.date} {s.instrument} {s.piece})", default="NO").strip()
                if confirm == "YES":
                    delete_session(s.id)
                    print("Deleted.")
                else:
                    print("Canceled.")

            else:
                print("Invalid choice.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_cli()
