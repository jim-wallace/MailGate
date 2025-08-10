from __future__ import annotations
import argparse, email, os
from email import policy
from email.parser import BytesParser
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Input
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from app.storage import Store

def read_text_part(eml_path: str) -> tuple[dict, str]:
    headers, body = {}, ""
    if not eml_path or not os.path.exists(eml_path):
        return headers, body
    with open(eml_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    for k in ("From", "To", "Subject", "Date", "Message-ID"):
        v = msg.get(k)
        if v:
            headers[k] = str(v)

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
        if not body:
            for part in msg.walk():
                if part.get_content_maintype() == "text":
                    body = part.get_content()
                    break
    else:
        if msg.get_content_maintype() == "text":
            body = msg.get_content()

    return headers, body or ""

class SinkTUI(App):
    CSS = """
    #sidebar { width: 62%; }
    #preview { width: 38%; border-left: solid gray; }
    #status { height: 3; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("d", "delete", "Delete"),
        ("e", "export", "Export .eml"),
        ("/", "focus_search", "Search"),
        ("escape", "clear_search", "Clear search"),
        ("tab", "focus_table", "To table"),
        ("shift+tab", "focus_search", "To search"),
    ]

    filter_text: reactive[str] = reactive("")

    def __init__(self, db_path: str, store_dir: str, export_dir: str = "./exports"):
        super().__init__()
        self.store = Store(db_path, store_dir)
        self.export_dir = export_dir
        self.rows_cache: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Input(placeholder="type to filer (subject/from/to)...", id="search")
                t = DataTable(id = "table")
                t.cursor_type = "row"
                t.show_cursor = True
                t.add_columns("Received", "From", "To", "Subject", "Size", "ID")
                yield t
            with Vertical(id="preview"):
                yield Static("Select a message to preview.", id="preview_text")
        yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.load_rows()
        table = self.query_one("#table", DataTable)
        table.focus()
        if table.row_count:
            table.cursor_coordinate = (0, 0)
            cell = table.get_cell_at((0, 5))
            mid = getattr(cell, "value", cell)
            if isinstance(mid, str):
                self.show_preview(mid)

    def action_refresh(self) -> None:
        self.load_rows(status="refreshed")

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_focus_table(self) -> None:
        self.query_one("#table", DataTable).focus()

    def action_clear_search(self) -> None:
        self.filter_text = ""
        search_box = self.query_one("#search", Input)
        search_box.value = ""
        search_box.blur()
        self.query_one("#table", DataTable).focus()
        self.load_rows(status="filter cleared")

    def action_cursor_down(self) -> None:
        tbl = self.query_one("#table", DataTable)
        tbl.cursor_down()

    def action_cursor_up(self) -> None:
        tbl = self.query_one("#table", DataTable)
        tbl.cursor_up()

    def on_input_changed(self, ev: Input.Changed) -> None:
        if ev.input.id == "search":
            self.filter_text = ev.value
            self.load_rows()

    def on_input_submitted(self, ev: Input.Submitted) -> None:
        if ev.input.id == "search":
            self.query_one("#table", DataTable).focus()

    def load_rows(self, status: str | None = None) -> None:
        tbl = self.query_one("#table", DataTable)
        tbl.clear()
        self.rows_cache = list(self.store.list_messages(limit=500))
        rows = self.rows_cache
        ft = self.filter_text.strip().lower()
        if ft:
            def ok(r):
                return (ft in (r["subject"] or "").lower()
                        or ft in (r["from_addr"] or "").lower()
                        or ft in (r["to_addrs"] or "").lower())
            rows = [r for r in rows if ok(r)]
        for r in rows:
            rec = r.get("received_at")
            received_str = rec.strftime("%Y-%m-%d %H:%M:%S") if hasattr(rec, "strftime") else str(rec or "")
            tbl.add_row(
                received_str,
                r.get("from_addr", ""),
                r.get("to_addrs", ""),
                (r.get("subject", "") or "")[:120],
                str(r.get("size", 0)),
                r["id"],
            )
        if status:
            self.set_status(status)
        if rows:
            tbl.cursor_coordinate = (0,0)
            self.show_preview(rows[0]["id"])

    def on_data_table_row_highlighted(self, ev: DataTable.RowHighlighted) -> None:
        tbl = ev.data_table
        cell = tbl.get_cell_at((ev.cursor_row, 5))
        mid = getattr(cell, "value", cell)
        if isinstance(mid, str):
            self.show_preview(mid)

    def on_data_table_row_selected(self, ev: DataTable.RowSelected) -> None:
        tbl = ev.data_table
        idx = ev.row_key if isinstance(ev.row_key, int) else tbl.cursor_row
        cell = tbl.get_cell_at((idx, 5))
        mid = getattr(cell, "value", cell)
        if isinstance(mid, str):
            self.show_preview(mid)

    def show_preview(self, mid: str) -> None:
        info = self.store.get_message(mid)
        preview = self.query_one("#preview_text", Static)
        if not info:
            preview.update("Message not found.")
            return
        headers, body = read_text_part(info["eml_path"])
        header_lines = [f"{k}: {v}" for k, v, in headers.items()]
        header_text = "\n".join(header_lines)
        preview.update(f"[b]ID[/b]: {info['id']}\n{header_text}\n\n[b]Body:[/b]\n{body[:5000]}")

    def action_delete(self) -> None:
        tbl = self.query_one("#table", DataTable)
        if not tbl.row_count: return
        row = tbl.cursor_row
        mid = tbl.get_cell_at((row, 5))
        if isinstance(mid, str) and self.store.delete_message(mid):
            self.set_status(f"deleted {mid}")
            self.load_rows()

    def action_export(self) -> None:
        tbl = self.query_one("#table", DataTable)
        if not tbl.row_count: return
        row = tbl.cursor_row
        mid = tbl.get_cell_at((row, 5))
        if isinstance(mid, str):
            path = self.store.export_message(mid, self.export_dir)
            if path:
                self.set_status(f"exported -> {path}")

    def set_status(self, msg: str) -> None:
        self.query_one("#status", Static).update(msg)

def _parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="./localdata/messages.db")
    ap.add_argument("--store-dir", default="./localdata")
    ap.add_argument("--export-dir", default="./exports")
    return ap.parse_args()

if __name__ == "__main__":
    args=_parse_args()
    Path(args.store_dir).mkdir(parents=True, exist_ok=True)
    SinkTUI(args.db, args.store_dir, args.export_dir).run()