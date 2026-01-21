from __future__ import annotations

from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

from practice_log import add_session, list_sessions, weekly_summary, export_csv


def run_gui() -> None:
    root = tk.Tk()
    root.title("Practice Log")
    root.geometry("1000x600")

    # --- Layout frames ---
    main = ttk.Frame(root, padding=12)
    main.pack(fill="both", expand=True)

    left = ttk.Frame(main)
    left.pack(side="left", fill="y")

    right = ttk.Frame(main)
    right.pack(side="right", fill="both", expand=True, padx=(12, 0))

    # --- Form variables ---
    var_date = tk.StringVar(value=date.today().isoformat())
    var_instrument = tk.StringVar()
    var_piece = tk.StringVar()
    var_minutes = tk.StringVar()
    var_notes = tk.StringVar()

    # --- Filter variables --
    var_filter_instrument = tk.StringVar()
    var_filter_since = tk.StringVar()

    # --- Helpers ---
    def refresh_list() -> None:
        sessions = list_sessions(
            instrument=var_filter_instrument.get().strip() or None,
            since=var_filter_since.get().strip() or None,
        )

        session_list.delete(*session_list.get_children())
        for s in sessions[:200]: # keep UI responsive
            session_list.insert(
                "",
                "end",
                values=(s.date, s.instrument, s.piece, s.duration_minutes, s.notes),
            )

        # Weekly summary (always based on calendar week, no filters)
        try:
            summary = weekly_summary(top_n=5)
            weekly_label.config(
                text=(
                    f"Week {summary['start_date']} → {summary['end_date']} | "
                    f"{summary['total_minutes']} min | {summary['session_count']} sessions"
                )
            )
        except Exception:
            weekly_label.config(text="Week summary unavailable.")

    def on_add() -> None:
        try:
            d = var_date.get().strip()
            inst = var_instrument.get().strip()
            piece = var_piece.get().strip()
            mins = int(var_minutes.get().strip() or "0")
            notes = var_notes.get().strip()

            if not inst:
                raise ValueError("Instrument is required.")
            if not piece:
                raise ValueError("Piece / exercise is required.")
            
            add_session(
                instrument=inst,
                piece=piece,
                duration_minutes=mins,
                notes=notes,
                session_date=d,
            )

            # Clear only what you typically re-enter
            var_piece.set("")
            var_minutes.set("")
            var_notes.set("")

            refresh_list()
        except Exception as e:
            messagebox.showerror("Could not add session", str(e))
    
    def on_export() -> None:
        try:
            out_path = export_csv()
            messagebox.showinfo("Export complete", f"Exported CSV to:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    # --- Left: Add form ---
    ttk.Label(left, text="Add practice session", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 8))

    form = ttk.Frame(left)
    form.pack(fill="x")

    def field(label: str, var: tk.StringVar) -> ttk.Entry:
        ttk.Label(form, text=label).pack(anchor="w", pady=(6, 0))
        e = ttk.Entry(form, textvariable=var)
        e.pack(fill="x")
        return e
    
    field("Date (YYYY-MM-DD)", var_date)
    field("Instrument", var_instrument)
    field("Piece / exercise", var_piece)
    field("Duration (minutes)", var_minutes)
    field("Notes (optional)", var_notes)

    ttk.Button(left, text="Add session", command=on_add).pack(fill="x", pady=(12, 0))

    ttk.Separator(left).pack(fill="x", pady=12)

    ttk.Label(left, text="Filters", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 8))
    field("Filter instrument (exact match)", var_filter_instrument)
    field("Since date (YYYY-MM-DD)", var_filter_since)

    ttk.Button(left, text="Apply filters / Refresh", command=refresh_list).pack(fill="x", pady=(12, 0))
    ttk.Button(left, text="Export CSV", command=on_export).pack(fill="x", pady=(8, 0))

    # --- Right: Sessions table + weekly summary ---
    weekly_label = ttk.Label(right, text="", font=("TkDefaultFont", 10, "bold"))
    weekly_label.pack(anchor="w", pady=(0, 8))

    columns = ("date", "instrument", "piece", "minutes", "notes")
    session_list = ttk.Treeview(right, columns=columns, show="headings", height=18)
    session_list.pack(fill="both", expand=True)

    headings = {
        "date": "Date",
        "instrument": "Instrument",
        "piece": "Piece",
        "minutes": "Minutes",
        "notes": "Notes",
    }
    for c in columns:
        session_list.heading(c, text=headings[c])
        session_list.column(c, width=120 if c != "notes" else 360, anchor="w")

    # Inital load
    refresh_list()
    root.mainloop()



if __name__ == "__main__":
    run_gui()