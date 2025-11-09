import PIL
import os
import ollama
from rich.markdown import Markdown
from rich.logging import RichHandler
import logging
from datetime import datetime
from textual import on, widget, work
from textual.app import App, ComposeResult
from textual.containers import (
    Horizontal,
    Vertical,
    VerticalScroll,
)
from textual.logging import TextualHandler
from textual.widget import Widget
from textual.widgets import (
    Button,
    Static,
    Footer,
    Header,
    RadioSet,
    RadioButton,
    Input,
    TabbedContent,
    TabPane,
    Select,
    SelectionList,
    RichLog,
    Label,
)
from textual_image.widget import Image
from textual.theme import Theme
from textual_fspicker import FileOpen


# import core

nord_dark_theme = Theme(
    name="nord_dark",
    primary="#88C0D0",  # Frost
    secondary="#81A1C1",  # Frost
    accent="#B48EAD",  # Aurora
    foreground="#D8DEE9",  # Snow
    background="#2E3440",  # Polar Night
    success="#A3BE8C",  # Aurora (green)
    warning="#EBCB8B",  # Aurora (yellow)
    error="#BF616A",  # Aurora (red)
    surface="#3B4252",  # Polar Night
    panel="#434C5E",  # Polar Night (lighter)
    dark=True,
)


def current_time():
    return datetime.now().strftime("%H:%M:%S")


class Logging(RichLog):
    file = False
    console: Widget

    def print(self, content):
        self.write(content)


logger = logging.getLogger(__name__)
richHandler = RichHandler(console=Logging(), rich_tracebacks=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%H:%M:%S",
    handlers=[richHandler],
)


def is_image(path: str) -> bool:
    try:
        with PIL.Image.open(path) as img:
            img.verify()  # Проверяет целостность
        return True
    except Exception:
        return False


class Message(Vertical):
    def __init__(
        self, chat: VerticalScroll, img_path: str, message_content: str, nickname: str
    ):
        super().__init__()
        self.member = nickname
        self.message = message_content
        self.chat = chat
        self.classes = "message"
        self.shrink = True

    def compose(self):
        yield Label(Markdown(f"***{self.member}***"), classes="name")
        yield Static(Markdown(self.message), classes="message_box", expand=True)

    def add_message(self):
        self.chat.mount(self)
        self.refresh()


class AIChat(App):
    CSS_PATH = "main.tcss"

    chat = VerticalScroll(id="chat_window", classes="chat")
    log_window = RichLog(auto_scroll=True, highlight=True, markup=True)
    model_name = None
    img_file_pth = None
    username = "TheDocingEast"

    def on_ready(self) -> None:
        logger.info("Hello World!")
        self.ollamaClient = ollama.AsyncClient()

    def on_mount(self) -> None:
        self.register_theme(nord_dark_theme)
        self.theme = "nord_dark"

    def compose(self) -> ComposeResult:
        yield Footer()
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("Chat", id="chat_tab"):
                with Horizontal():
                    with Vertical(classes="info"):
                        with RadioSet(classes="modellist", id="modelset"):
                            for i in ollama.list()["models"]:
                                yield RadioButton(i["model"], classes="modellistitem")

                    with Vertical():
                        yield self.chat
                        with Horizontal(id="chat_input"):
                            yield Input(placeholder="Write prompt", id="prompt")
                            yield Button(
                                label="Choose file",
                                variant="default",
                                id="choose_file",
                            )

            with TabPane("Settings", id="setting_tab"):
                with VerticalScroll(classes="vert"):
                    yield Input(
                        placeholder="Nickname",
                        max_length=25,
                        validators=[],
                        classes="listitem",
                        id="nickname",
                    )
                    yield Select(
                        options=[],
                        prompt="???",
                        type_to_search=True,
                        classes="listitem",
                    )
                    yield SelectionList(
                        *[("First", 1), ("Second", 2)],
                        name="???",
                        classes="listitem",
                    )
                with Horizontal(classes="hort"):
                    yield Button(
                        label="Save setting", variant="success", id="save_setting"
                    )
                    yield Button(
                        label="Reset setting",
                        variant="error",
                        id="reset_setting",
                    )
            with TabPane("Logs", id="log_tab"):
                with VerticalScroll(classes="log"):
                    yield richHandler.console
                    yield Button(label="Clear logs", variant="default", id="reset_log")

    @work
    @on(Button.Pressed)
    async def button_action(self, event: Button.Pressed) -> None:
        if event.button.id == "choose_file":
            if opened := await self.push_screen_wait(FileOpen()):
                if is_image(str(opened)):
                    logger.info(f"Open image in {str(opened)}")
                    chat_input = self.get_widget_by_id("chat_input")
                    img = Image(image=str(opened), classes="avatar", id="img")
                    await chat_input.mount(img, after="#choose_file")
                    self.img_file_pth = str(opened)
                else:
                    logger.warning(f"File {str(opened)} not image")

        if event.button.id == "reset_log":
            self.log_window.clear()

    @on(RadioSet.Changed)
    async def set_avatar(self, event: RadioSet.Changed) -> None:
        # Проверяем, что событие от нужного RadioSet
        if event.radio_set.id == "modelset":
            ava_id = event.index  # индекс выбранной кнопки
            self.model_name = str(event.pressed.label) if event.pressed else "Unknown"
            self.ai_avatar = f"src/img/avatar_{ava_id}.png"
            if os.path.exists(self.ai_avatar):
                logger.info(f"AI avatar changed to {self.model_name} (id {ava_id})")
            else:
                logger.warning(
                    f"Avatar image for {self.model_name} doesn't exist (id {ava_id})"
                )

    @on(Input.Submitted)
    async def send_prompt(self, event: Input.Submitted) -> None:
        match event.input.id:
            case "prompt":
                if event.value is not None:
                    try:
                        if self.model_name is not None:
                            Message(
                                self.chat,
                                "",
                                str(event.value),
                                self.username,
                            ).add_message()
                            message = event.value
                            event.input.clear()
                            event.input.disabled = True
                            if self.img_file_pth is not None:
                                response = await self.ollamaClient.chat(
                                    model=self.model_name,
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": message,
                                            "images": [self.img_file_pth],
                                        }
                                    ],
                                )
                            else:
                                response = await self.ollamaClient.chat(
                                    model=self.model_name,
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": message,
                                        }
                                    ],
                                )
                            event.input.disabled = False

                            Message(
                                self.chat,
                                self.ai_avatar,
                                response["message"]["content"],
                                self.model_name,
                            ).add_message()
                            if self.img_file_pth is not None:
                                avatar = self.query_one("#img", expect_type=Image)
                                await avatar.remove()
                        else:
                            raise Exception(
                                "No model has been selected, please select model!"
                            )
                    except Exception as e:
                        logger.fatal(e)
            case "nickname":
                self.username = event.input.value
                logger.info(f"Username successfully changed to {event.input.value}")


def main_entry():
    app = AIChat()
    app.run()


if __name__ == "__main__":
    main_entry()
