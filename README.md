# tool-use

Tools to simplify life with AI. Brought to you by the hosts of [ToolUse](https://www.youtube.com/@ToolUseAI).

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

**Note:** After `ai do`, you can input natural language without quotation marks.

```bash
ai do Your command description here
```

### 2. RSS CLI (`tooluse`)

Fetches and displays podcast episodes from a specified RSS feed, allowing you to interact with them.

```bash
tooluse
```

### 3. Contact Form (`tooluse contact`)

Provides a contact form to submit feedback, requests or just to say hi.

```bash
tooluse contact
```

### 4. Calendar Manager (`cal`)

Manages Google Calendar events, including creating, editing, searching, and deleting events.

```bash
ai cal
```

### 5. Convert anything (`convert`)

Converts anything to anything using Open Interpreter.

```bash
ai convert "/path/to/file.txt to pdf"
```

### 6. Obsidian Plugin Generator (`make-obsidian-plugin`)

Generates a customizable Obsidian plugin based on user input and AI-driven code generation.


```bash
ai make-obsidian-plugin "Plugin Name"
```


### 7. Activity Tracker (`ai log`)

Tracks and analyzes your daily activities with AI-powered categorization.

```bash
ai log <activity>          # Start tracking an activity
ai log                     # Stop current activity or start new one
ai log tell <query>        # Query your activity history
ai log category <command>  # Manage activity categories
```

Examples:

```bash
ai log working on python project
ai log tell me how long I coded today
ai log tell me what I did yesterday
ai log category list
```

### 8. Prioritize Tasks (`ai prioritize`)

Prioritizes your tasks based on urgency and importance, helping you focus on what matters most.

```bash
ai prioritize "List of tasks to prioritize"
