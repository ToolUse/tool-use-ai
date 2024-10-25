# tool-use

Tools to simplify life with AI

## Installation

You can install the package using pip:

```bash
pip install tool-use-ai
```

## Available Tools

The repository includes the following tools to simplify your interactions with AI:

### 1. AI CLI Tool (`ai_cli`)

Generates and executes terminal commands based on natural language input using AI assistance.

```bash
python -m tool_use.cli ai_cli "Your command description here"
```

### 2. RSS CLI (`rss_cli`)

Fetches and displays podcast episodes from a specified RSS feed, allowing you to interact with them.

```bash
python -m tool_use.cli rss_cli
```

### 3. Calendar Manager (`cal`)

Manages Google Calendar events, including creating, editing, searching, and deleting events.

```bash
python -m tool_use.cli cal
```

### 4. Obsidian Plugin Generator (`make-obsidian-plugin`)

Generates a customizable Obsidian plugin based on user input and AI-driven code generation.

```bash
python -m tool_use.cli make-obsidian-plugin "Plugin Name"
```

### 5. Scriptomatic (`scriptomatic`)

Creates scripts by specifying the desired functionality, leveraging AI to generate the code.

```bash
python -m tool_use.cli scriptomatic "Your script description here"
```

### 6. Script1 (`script1`)

Processes text files using AI to extract key insights and display them in a user-friendly format.

```bash
python -m tool_use.cli script1 input_file.txt --output output_file.txt
```
