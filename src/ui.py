import PIL
import ollama
from rich.logging import RichHandler
import logging
import asyncio
import math
from contextlib import asynccontextmanager
from datetime import datetime
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import (
    Horizontal,
    Vertical,
    VerticalScroll,
)
from textual.widget import Widget
from textual.widgets import (
    Button,
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
    Markdown,
    Sparkline,
    TextArea,
)
from textual.binding import Binding
from textual_image.widget import Image
from textual.theme import Theme
from textual_fspicker import FileOpen

import ai_connect
import main

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


class Chat(VerticalScroll):
    def __init__(self):
        super().__init__()

    def on_mount(self) -> None:
        self.id = "chat_window"
        self.classes = "chat"
        self.border_title = "Chat"

    def add_message(self, msg_content: str, member_name: str):
        message_bubble = Vertical(
            Markdown(f"***{member_name}***", classes="name"),
            Markdown(msg_content, classes="message_box", open_links=True),
            classes="message",
        )
        self.mount(message_bubble)
        self.refresh()


class AIChat(App):
    CSS_PATH = "ui.tcss"

    BINDINGS = [
        Binding("ctrl+enter", "send_message", "Send", show=True),
    ]

    log_window = RichLog(auto_scroll=True, highlight=True, markup=True)
    model_name = None
    username = "TheDocingEast"
    chat = Chat()
    img_file_pth = None
    sparkline_widget = None
    animation_task = None

    def on_ready(self) -> None:
        logger.info("Hello World!")
        self.client = ai_connect.OllamaClient()

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
                        yield Sparkline(
                            data=[],
                            summary_function=max,
                            id="generation_sparkline",
                        )
                        with Horizontal(id="chat_input"):
                            yield TextArea(
                                id="prompt",
                                language="markdown",
                                show_line_numbers=False,
                            )
                            yield Button(
                                label="Send",
                                variant="primary",
                                id="send_button",
                            )
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

    async def animate_sparkline(self):
        sparkline = self.query_one("#generation_sparkline", Sparkline)

        data = [0] * 20  # Initialize with 20 zeros
        phase = 0

        while True:
            # Create a smooth sine wave pattern
            for i in range(len(data)):
                # Calculate sine wave value
                wave_value = math.sin((i + phase) * 0.5) * 5 + 6
                data[i] = max(1, int(wave_value))  # Ensure minimum value of 1

            sparkline.data = data.copy()
            phase += 0.5  # Control wave speed
            await asyncio.sleep(0.05)  # Smooth 50ms updates

    @asynccontextmanager
    async def GenerateAnswer(self):
        """Context manager to show animation during answer generation"""
        sparkline = self.query_one("#generation_sparkline", Sparkline)

        self.animation_task = asyncio.create_task(self.animate_sparkline())

        try:
            yield
        finally:
            # Stop animation and hide sparkline
            if self.animation_task:
                self.animation_task.cancel()
                try:
                    await self.animation_task
                except asyncio.CancelledError:
                    pass

            sparkline.data = []

    async def action_send_message(self) -> None:
        """Action to send message (triggered by Ctrl+Enter)"""
        await self.send_prompt_handler()

    async def send_prompt_handler(self) -> None:
        """Handler for sending prompt"""
        try:
            text_area = self.query_one("#prompt", TextArea)
            prompt_text = text_area.text.strip()

            if not prompt_text:
                return

            if self.model_name is None:
                logger.error("No model has been selected, please select model!")
                return

            async with self.GenerateAnswer():
                self.chat.add_message(prompt_text, self.username)
                message = prompt_text
                text_area.clear()

                if self.img_file_pth is not None:
                    response = await self.client.send_message(
                        self.model_name, message, self.img_file_pth
                    )
                    avatar = self.query_one("#img", expect_type=Image)
                    await avatar.remove()
                    self.img_file_pth = None
                else:
                    response = await self.client.send_message(self.model_name, message)

                logger.info(f"Get response from ollama: {response}")
                self.chat.add_message(
                    response["message"]["content"],
                    self.model_name,
                )

        except Exception as e:
            logger.fatal(e)

    @work
    @on(Button.Pressed)
    async def button_action(self, event: Button.Pressed) -> None:
        if event.button.id == "send_button":
            await self.send_prompt_handler()

        elif event.button.id == "choose_file":
            if opened := await self.push_screen_wait(FileOpen()):
                if is_image(str(opened)):
                    logger.info(f"Open image in {str(opened)}")
                    chat_input = self.get_widget_by_id("chat_input")
                    img = Image(image=str(opened), classes="avatar", id="img")
                    await chat_input.mount(img, after="#choose_file")
                    self.img_file_pth = str(opened)
                else:
                    logger.warning(f"File {str(opened)} not image")

        elif event.button.id == "reset_log":
            self.log_window.clear()

    @on(RadioSet.Changed)
    async def set_avatar(self, event: RadioSet.Changed) -> None:
        # Проверяем, что событие от нужного RadioSet
        if event.radio_set.id == "modelset":
            self.model_name = str(event.pressed.label) if event.pressed else "Unknown"
            logger.info(f"Selected model: {self.model_name}")

    @on(Input.Submitted)
    async def handle_nickname_change(self, event: Input.Submitted) -> None:
        """Handle nickname input submission"""
        if event.input.id == "nickname":
            self.username = event.input.value
            logger.info(f"Username successfully changed to {event.input.value}")


def main_entry():
    app = AIChat()
    app.run()


if __name__ == "__main__":
    main_entry()
