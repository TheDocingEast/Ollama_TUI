from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual.widgets import (
    Button,
    Static,
    Footer,
    Header,
    ProgressBar,
    Label, RadioSet,
    RadioButton,
    Input,
    TabbedContent,
    TabPane,
    OptionList,
    Select,
    SelectionList,
    Log

)
from textual_image.widget import Image
from textual.theme import Theme
from textual_fspicker import FileOpen
import ollama
import os

# import core



nord_dark_theme = Theme(
    name="nord_dark",
    primary="#88C0D0",     # Frost
    secondary="#81A1C1",   # Frost
    accent="#B48EAD",      # Aurora
    foreground="#D8DEE9",  # Snow
    background="#2E3440",  # Polar Night
    success="#A3BE8C",     # Aurora (green)
    warning="#EBCB8B",     # Aurora (yellow)
    error="#BF616A",       # Aurora (red)
    surface="#3B4252",     # Polar Night
    panel="#434C5E",       # Polar Night (lighter)
    dark=True,
)

class Message(Static):
    def compose(self) -> ComposeResult:
        with Horizontal():
            pass



class AIChat(App):
    CSS_PATH = "main.tcss"

    BINDINGS = [
        ("left", "previous_tab", "Previous tab"),
        ("right", "next_tab", "Next tab"),
    ]
    log_window = Log(
        auto_scroll=True,
        highlight=True,
    )

    chat = Log(
        auto_scroll=True,
        id='chat_log',

    )

    def on_ready(self) -> None:
        self.log_window.write_line("Hello, World!")


    def on_mount(self) -> None:
        self.register_theme(nord_dark_theme)
        self.theme = "nord_dark"



    def compose(self) -> ComposeResult:
        yield Footer()
        yield Header()
        with TabbedContent():
            with TabPane("Chat", id='chat_tab'):
                with Horizontal():
                    with Vertical(classes="info"):
                        with RadioSet(classes="modellist", id='modelset'):
                            for i in ollama.list()['models']:
                                yield RadioButton(
                                    i['model'],
                                    classes="modellistitem"
                                )

                    with Vertical():
                        with VerticalScroll(classes="chat", id='chat_window'):
                            yield self.chat
                        with Horizontal():
                            yield Input(
                                placeholder="Write prompt",
                                id='prompt'
                            )
                            with Container():
                                yield Button(
                                    label="Choose file",
                                    variant="default",
                                    id='choose_file',
                                )

            with TabPane("Settings", id='setting_tab'):
                with VerticalScroll(classes='vert'):
                    yield Select(
                        options=[],
                        prompt='???',
                        type_to_search=True,
                        classes='listitem'
                    )
                    yield SelectionList(
                        *[('First', 1), ('Second', 2)],
                        name='???',
                        classes='listitem',
                    )
                with Horizontal(classes='hort'):
                    yield Button(
                        label="Save setting",
                        variant='success',
                        id='save_setting'
                    )
                    yield Button(
                        label="Reset setting",
                        variant='error',
                        id='reset_setting',
                    )
            with TabPane("Logs", id="log_tab"):
                with VerticalScroll(classes='log'):
                    yield self.log_window
                    yield Button(
                        label='Clear logs',
                        variant='default',
                        id='reset_log'
                    )


    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'choose_file':
            await self.push_screen(FileOpen())
        if event.button.id == 'reset_log':
            self.log_window.clear()

    @on(RadioSet.Changed)
    async def set_avatar(self, event: RadioSet.Changed) -> None:
        # Проверяем, что событие от нужного RadioSet
        if event.radio_set.id == "modelset":
            ava_id = event.index  # индекс выбранной кнопки
            model_name = event.pressed.label if event.pressed else "Unknown"
            ai_avatar = f"img/avatar_{ava_id}.png"
            if os.path.exists(ai_avatar):
                self.log_window.write_line(f"AI avatar changed to {model_name} (id {ava_id})")
                chat_win = self.get_widget_by_id('chat_window')
                chat_win.mount(Image(image=ai_avatar,classes='avatar'))
            else:
                self.log_window.write_line(f"Avatar image for {model_name} doesn't exist (id {ava_id})")

    @on(Input.Submitted)
    async def send_prompt(self, event: Input.Submitted) -> None:
        chat = self.get_widget_by_id('chat_log')
        user_name = "TheDocingEast"
        if event.value is not None:
            chat.write_line(f"{user_name}: {event.value}")



def main_entry():
    app = AIChat()
    app.run()


if __name__ == "__main__":
    main_entry()
