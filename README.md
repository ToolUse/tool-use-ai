# tool-use

Tools to simplify life with AI

## Installation

You can install the package using pip:

```bash
pip install tool-use-ai
```

## Available Tools

The repository includes the following tools to simplify your interactions with AI:

**Note:** Use `ai` for general tools and `tooluse` specifically for the RSS CLI tool.

### 1. AI CLI Tool (`ai do`)

Generates and executes terminal commands based on natural language input using AI assistance.

```bash
ai do Your command description here
```

### 2. RSS CLI (`tooluse`)

Fetches and displays podcast episodes from a specified RSS feed, allowing you to interact with them.

```bash
tooluse "https://example.com/rss-feed.xml"
```

### 3. Calendar Manager (`cal`)

Manages Google Calendar events, including creating, editing, searching, and deleting events.

```bash
ai cal
```

### 4. Obsidian Plugin Generator (`make-obsidian-plugin`)

Generates a customizable Obsidian plugin based on user input and AI-driven code generation.

**Note:** Quotation marks are not required. You can input natural language directly after the command.

```bash
ai make-obsidian-plugin "Plugin Name"
```

### 5. Scriptomatic (`scriptomatic`)

Creates scripts by specifying the desired functionality, leveraging AI to generate the code.

```bash
ai scriptomatic "Your script description here"
```

### 6. Script1 (`script1`)

Processes text files using AI to extract key insights and display them in a user-friendly format.

```bash
ai script1 input_file.txt --output output_file.txt
```

**Note:** After `ai do`, you can input natural language without quotation marks.
