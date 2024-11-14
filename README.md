# tool-use

Tools to simplify life with AI. Brought to you by [Tool Use](https://www.youtube.com/@ToolUseAI).
You can install the package via [PyPI](https://pypi.org/project/tool-use-ai/).

## Installation

```bash
pip install tool-use-ai
```

## Command Structure

This toolkit provides two main command interfaces:

- `ai`: General-purpose AI tools for everyday tasks
- `tooluse`: Specific tools for podcast and community interaction

## AI Tools (`ai` command)

### 1. Command Generation (`ai do`)

Generate and execute terminal commands from natural language.

```bash
ai do <your optional command description>
```

### 2. Calendar Manager (`ai cal`)

Manage Google Calendar events.

```bash
ai cal
```

### 3. File Converter (`ai convert`)

Convert between file formats using Open Interpreter.

```bash
ai convert "/path/to/file.txt to pdf"
```

### 4. Obsidian Plugin Generator (`ai make-obsidian-plugin`)

Create custom Obsidian plugins with AI assistance.

```bash
ai make-obsidian-plugin "Plugin Name"
```

### 5. Activity Tracker (`ai log`)

Track and analyze daily activities.

```bash
ai log <activity>          # Start tracking an activity
ai log                     # Stop current activity or start new one
ai log tell <query>       # Query your activity history
ai log category <command> # Manage activity categories
```

Examples:

```bash
ai log working on python project
ai log tell me how long I coded today
ai log tell me what I did yesterday
ai log category list
```

### 6. Task Prioritizer (`ai prioritize`)

Voice-based task organization tool that:

- Organizes tasks by priority level
- Provides empathetic analysis
- Suggests concrete next steps

**Note:** You input your tasks using voice commands for a hands-free experience after running the script

```bash
ai prioritize
```

### 7. Marketing Plan Generator (`ai marketing-plan`)

Use a swarm of AI agents to generate a marketing plan for your business.

```bash
ai marketing-plan
```

## Tool Use Tools (`tooluse` command)

### 1. Podcast RSS Reader (`tooluse`)

Fetch and interact with podcast episodes from RSS feeds.

```bash
tooluse
```

### 2. Contact Form (`tooluse contact`)

Submit feedback, requests, or general messages.

```bash
tooluse contact
```
