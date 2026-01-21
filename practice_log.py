from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional


DATA_FILE = Path(__file__).with_name("practice_log.json")


@dataclass
class PracticeSession:
    date: str               # ISO format: YYYY-MM-DD
    instrument: str
    piece: str
    duration_minutes: int
    notes: str = ""


def _load_sessions(path: Path = DATA_FILE) -> List[PracticeSession]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-b"))
    return [PracticeSession(**item) for item in raw]


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


def run_cli() -> None:
    while True:
        print("\nPractice Log")
        print("1) Add session")
        print("2) List sessions")
        print("3) Total minutes")
        print("4) Exit")

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
                        print(f"{s.date} | {s.instrument} | {s.piece} | {s.duration_minutes} min{notes_part}")

            elif choice == "3":
                inst = _prompt("Filter instrument (blank = all)", default="").strip() or None
                since = _prompt("Since date YYYY-MM-DD (blank = all)", default="").strip() or None
                total = total_minutes(instrument=inst, since=since)
                print(f"Total: {total} minutes")

            elif choice == "4":
                break
            else:
                print("Invalid choice.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_cli()
