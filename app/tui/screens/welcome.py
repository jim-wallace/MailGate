from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Center, Vertical, Horizontal

class WelcomeScreen(Screen):
    BINDINGS = [("e", "open_emails", "Open Emails"), ("q", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="welcome_box"):
                yield Static("[b]MailSink[/b]\n\nA dev/testing tool for capturing emails.\n", id="welcome_title")
                with Horizontal():
                    yield Button("Open Emails (E)", id="open_emails", variant="primary")
                    yield Button("Quit (Q)", id="quit_app")
        yield Footer()

    def on_button_pressed(self, ev: Button.Pressed) -> None:
        if ev.button.id == "open_emails":
            self.app.push_screen("emails")
        elif ev.button.id == "quit_app":
            self.app.exit()

    def action_open_emails(self) -> None:
        self.app.push_screen("emails")
