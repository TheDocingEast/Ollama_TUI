### Ollama TUI

This is TUI (Text-based User Interface) for work with LLM model, which serve by Ollama server.
**WIP** - new updates on work

## Features

- Image send
- Multi-model work
- ....

## Installation

1. Clone the repo:

```bash
git clone https://github.com/TheDocingEast/Ollama_TUI.git
cd Ollama_TUI
```

2. Create env and install dependencies:

```bash
# For python-venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# For uv
uv init
uv sync
```

3. To run use:

```bash
# For python-venv
source venv/bin/activate
textual run src/main.py
# or
venv/bin/python src/main.py

# For uv
uv run textual run src/main.py
# or
uv run python src/main.py
```

#### Bugs, issues and new features

If you find any bug, problem or have suggestions for ideas, write them in the issues thread, please)

Licensed by:
[MIT](https://en.wikipedia.org/wiki/MIT_License)

Creator:
[TheDocingEast](https://github.com/TheDocingEast)
