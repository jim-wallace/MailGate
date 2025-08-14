from __future__ import annotations
from pathlib import Path
from textual.app import App
from app.storage import Store
from .screens.welcome import WelcomeScreen
from .screens.emails import EmailsScreen

class SinkTUI(App):
    CSS_PATH = Path(__file__).with_name("sink.tcss")

    def __init__(self, db_path: str, store_dir: str, export_dir: str = "./exports"):
        super().__init__()
        self.store = Store(db_path, store_dir)
        self.export_dir = export_dir

    def on_mount(self) -> None:
        self.install_screen(WelcomeScreen(), name="welcome")
        self.install_screen(EmailsScreen(),  name="emails")
        self.push_screen("welcome")

def _parse_args():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="./localdata/messages.db")
    ap.add_argument("--store-dir", default="./localdata")
    ap.add_argument("--export-dir", default="./exports")
    return ap.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    Path(args.store_dir).mkdir(parents=True, exist_ok=True)
    SinkTUI(args.db, args.store_dir, args.export_dir).run()
