from __future__ import annotations

from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

from practice_log import add_session, list_sessions, weekly_summary, export_csv, update_session, delete_session


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

    # --- UI state ---
    selected_id = tk.StringVar(value="") # full session id (stable)
    status_text = tk.StringVar(value="Ready.")

    # --- Helpers ---
    def set_status(msg: str) -> None:
        status_text.set(msg)

    def set_mode_ui() -> None:
        """Update action buttons based on whether a session is selected"""
        in_edit_mode = bool(selected_id.get().strip())

        if in_edit_mode:
            # Edit mode
            btn_add.state(["disabled"])
            btn_save.state(["!disabled"])
            btn_delete.state(["!disabled"])

            btn_clear.config(text="Cancel edit")
            btn_save.config(text="Save changes")

            set_status(f"Edit mode: {selected_id.get()[:8]}")
        else:
            # Add mode
            btn_add.state(["!disabled"])
            btn_save.state(["disabled"])
            btn_delete.state(["disabled"])

            btn_clear.config(text="Clear form")
            btn_save.config(text="Save changes")

    def update_mode_label() -> None:
        if selected_id.get().strip():
            mode_label.config(text=f"Mode: Edit ({selected_id.get()[:8]})")
        else:
            mode_label.config(text="Mode: Add")


    def clear_form(keep_date: bool = True) -> None:
        if not keep_date:
            var_date.set(date.today().isoformat())
        var_instrument.set("")
        var_piece.set("")
        var_minutes.set("")
        var_notes.set("")
        selected_id.set("")
        set_status("Ready.")

        update_mode_label()
        set_mode_ui()

    def refresh_list() -> None:
        sessions = list_sessions(
            instrument=var_filter_instrument.get().strip() or None,
            since=var_filter_since.get().strip() or None,
        )

        session_list.delete(*session_list.get_children())

        # Use iid=session.id so selection gives us the stable id
        for s in sessions[:500]: # keep UI responsive
            session_list.insert(
                "",
                "end",
                iid=s.id,
                values=(s.date, s.instrument, s.piece, s.duration_minutes, s.notes),
            )

        # Weekly summary (calendar week, no filters)
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

        # If current selected id no longer exists, clear selection
        sid = selected_id.get().strip()
        if sid and not session_list.exists(sid):
            selected_id.set("")
            set_status("Selection cleared (session no longer present).")
        
        update_mode_label()
        set_mode_ui()

    def current_selection_id() -> str:
        # Prefer internal selected_id; fall back to Treeview selection
        sid = selected_id.get().strip()
        if sid:
            return sid
        sel = session_list.selection()
        if not sel:
            return ""
        return sel[0] # iid id the id

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
            
            s = add_session(
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
            selected_id.set("")
            update_mode_label()
            set_mode_ui()
            set_status(f"Added session {s.id[:8]}.")

            refresh_list()
        except Exception as e:
            messagebox.showerror("Could not add session", str(e))

    def on_save_changes() -> None:
        sid = current_selection_id()
        if not sid:
            messagebox.showinfo("No selection", "Select a session row to edit, then click 'Save changes'")
            return
        
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
            
            updated = update_session(
                sid,
                session_date=d,
                instrument=inst,
                piece=piece,
                duration_minutes=mins,
                notes=notes,
            )
            set_status(f"Updated session {updated.id[:8]}.")
            refresh_list()

            # Keep selection on the updated row
            if session_list.exists(sid):
                session_list.selection_set(sid)
                session_list.focus(sid)
        except Exception as e:
            messagebox.showerror("Could not save changes", str(e))
        # Optional: stay in edit mode (current behavior) OR return to add mode:
        # selected_id.set("")
        # session_list.selection_remove(session_list.selection())
        # clear_form(keep_date=True)
        # refresh_list()

    def on_delete() -> None:
        sid = current_selection_id()
        if not sid:
            messagebox.showinfo("No selection", "Select a session row to delete.")
            return
        
        # Get a friendly description from the row values
        try:
            vals = session_list.item(sid, "values")
            desc = f"{vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} mins"
        except Exception:
            desc = sid[:8]

        if not messagebox.askyesno("Confirm delete", f"Delete this session?\n\n{desc}"):
            return
        
        try:
            delete_session(sid)
            set_status(f"Deleted session {sid[:8]}.")
            clear_form(keep_date=True)
            refresh_list()
        except Exception as e:
            messagebox.showerror("Could not delete session", str(e))

    
    def on_export() -> None:
        try:
            out_path = export_csv()
            messagebox.showinfo("Export complete", f"Exported CSV to:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def on_row_selected(_event=None) -> None:
        sel = session_list.selection()
        if not sel:
            return
        sid = sel[0]
        selected_id.set(sid)

        vals = session_list.item(sid, "values")
        # values: (date, instrument, piece, duration_minutes, notes)
        var_date.set(vals[0])
        var_instrument.set(vals[1])
        var_piece.set(vals[2])
        var_minutes.set(str(vals[3]))
        var_notes.set(vals[4])
        set_status(f"Editing session {sid[:8]} (selected).")

        update_mode_label()
        set_mode_ui()

    # --- Left: Add/edit form ---
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

    ttk.Separator(left).pack(fill="x", pady=12)

    ttk.Label(left, text="Actions", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 8))

    btn_add = ttk.Button(left, text="Add new session", command=on_add)
    btn_add.pack(fill="x", pady=(0, 6))

    btn_save = ttk.Button(left, text="Save changes", command=on_save_changes)
    btn_save.pack(fill="x", pady=(0, 6))

    btn_delete = ttk.Button(left, text="Delete", command=on_delete)
    btn_delete.pack(fill="x", pady=(0, 6))

    btn_clear = ttk.Button(left, text="Clear form / Cancel edit", command=lambda: clear_form(keep_date=True))
    btn_clear.pack(fill="x")

    ttk.Separator(left).pack(fill="x", pady=12)

    ttk.Label(left, text="Filters", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 8))
    field("Filter instrument (exact match)", var_filter_instrument)
    field("Since date (YYYY-MM-DD)", var_filter_since)

    ttk.Button(left, text="Apply filters / Refresh", command=refresh_list).pack(fill="x", pady=(12, 0))
    ttk.Button(left, text="Export CSV", command=on_export).pack(fill="x", pady=(8, 0))

    ttk.Separator(left).pack(fill="x", pady=12)

    ttk.Label(left, text="Status", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 8))
    ttk.Label(left, textvariable=status_text, wraplength=320).pack(anchor="w")

    mode_label = ttk.Label(left, text="Mode: Add", font=("TkDefaultFont", 10, "bold"))
    mode_label.pack(anchor="w", pady=(0, 6))

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
    widths = {"date": 110, "instrument": 140, "piece": 260, "minutes": 80, "notes": 420}

    for c in columns:
        session_list.heading(c, text=headings[c])
        session_list.column(c, width=widths[c], anchor="w")

    # Selection event
    session_list.bind("<Double-1>", on_row_selected)

    set_mode_ui()
    update_mode_label()

    # Inital load
    refresh_list()
    root.mainloop()



if __name__ == "__main__":
    run_gui()