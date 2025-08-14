from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Center, Vertical, Horizontal
from textual.widgets import DataTable, Input
from textual.reactive import reactive

from app.utils.utils import read_text_part


class EmailsScreen(Screen):
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("d", "delete", "Delete"),
        ("e", "export", "Export .eml"),
        ("/", "focus_search", "Search"),
        ("escape", "clear_search", "Clear search"),
        ("tab", "focus_table", "To table"),
        ("shift+tab", "focus_search", "To search"),
        ("w", "to_welcome", "Welcome"),
    ]

    filter_text: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Input(placeholder="type to filter (subject/from/to)...", id="search")
                t = DataTable(id="table")
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
            mid = self._get_cell((0, 5))
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

    def on_input_changed(self, ev: Input.Changed) -> None:
        if ev.input.id == "search":
            self.filter_text = ev.value
            self.load_rows()

    def on_input_submitted(self, ev: Input.Submitted) -> None:
        if ev.input.id == "search":
            self.query_one("#table", DataTable).focus()

    def on_data_table_row_highlighted(self, ev: DataTable.RowHighlighted) -> None:
        mid = self._get_cell((ev.cursor_row, 5), ev.data_table)
        if isinstance(mid, str):
            self.show_preview(mid)

    def on_data_table_row_selected(self, ev: DataTable.RowSelected) -> None:
        tbl = ev.data_table
        idx = ev.row_key if isinstance(ev.row_key, int) else tbl.cursor_row
        mid = self._get_cell((idx, 5), tbl)
        if isinstance(mid, str):
            self.show_preview(mid)

    def action_delete(self) -> None:
        tbl = self.query_one("#table", DataTable)
        if not tbl.row_count:
            return
        row = tbl.cursor_row
        mid = self._get_cell((row, 5))
        if isinstance(mid, str) and self.app.store.delete_message(mid):
            self.set_status(f"deleted {mid}")
            self.load_rows()

    def action_export(self) -> None:
        tbl = self.query_one("#table", DataTable)
        if not tbl.row_count:
            return
        row = tbl.cursor_row
        mid = self._get_cell((row, 5))
        if isinstance(mid, str):
            path = self.app.store.export_message(mid, self.app.export_dir)
            if path:
                self.set_status(f"exported -> {path}")

    def action_to_welcome(self) -> None:
        self.app.pop_screen()

    def _get_cell(self, coord, tbl: DataTable | None = None):
        tbl = tbl or self.query_one("#table", DataTable)
        cell = tbl.get_cell_at(coord)
        return getattr(cell, "value", cell)

    def load_rows(self, status: str | None = None) -> None:
        tbl = self.query_one("#table", DataTable)
        tbl.clear()
        rows = list(self.app.store.list_messages(limit=500))
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
                r.get("from_addr", "") or "",
                r.get("to_addrs", "") or "",
                (r.get("subject", "") or "")[:120],
                str(r.get("size", 0)),
                r["id"],
            )

        if status:
            self.set_status(status)
        if rows:
            tbl.cursor_coordinate = (0, 0)
            self.show_preview(rows[0]["id"])

    def show_preview(self, mid: str) -> None:
        info = self.app.store.get_message(mid)
        preview = self.query_one("#preview_text", Static)
        if not info:
            preview.update("Message not found.")
            return
        headers, body = read_text_part(info["eml_path"])
        header_text = "\n".join(f"{k}: {v}" for k, v in headers.items())
        preview.update(f"[b]ID[/b]: {info['id']}\n{header_text}\n\n[b]Body:[/b]\n{body[:5000]}")

    def set_status(self, msg: str) -> None:
        self.query_one("#status", Static).update(msg)
