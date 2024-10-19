# src/tool_use/rss_cli.py
import feedparser
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from prompt_toolkit import prompt
import webbrowser
import subprocess
import os
import inquirer

console = Console()

def fetch_rss_feed(url):
    return feedparser.parse(url)

def display_episodes(feed):
    table = Table(title="Podcast Episodes", box=box.ROUNDED)
    table.add_column("Title", style="cyan", no_wrap=True)
    table.add_column("Date", style="magenta")
    table.add_column("Duration", style="green")

    for entry in feed.entries:
        table.add_row(
            entry.title,
            entry.published,
            entry.itunes_duration if hasattr(entry, 'itunes_duration') else "N/A"
        )

    console.print(table)

def select_episode(feed):
    choices = [inquirer.List('episode',
                             message="Select an episode",
                             choices=[(entry.title, i) for i, entry in enumerate(feed.entries)])]
    result = inquirer.prompt(choices)
    
    if result:
        return feed.entries[result['episode']]
    return None

def display_episode_options(episode):
    panel = Panel(
        f"[bold cyan]{episode.title}[/bold cyan]\n\n"
        f"[magenta]Published:[/magenta] {episode.published}\n"
        f"[green]Duration:[/green] {episode.itunes_duration if hasattr(episode, 'itunes_duration') else 'N/A'}\n\n"
        "[yellow]Options:[/yellow]\n"
        "1. Play in Spotify\n"
        "2. Play in Apple Podcasts\n"
        "3. Watch on YouTube\n"
        "4. Play MP3 in CLI\n"
        "5. Back to episode list",
        title="Episode Details",
        expand=False
    )
    console.print(panel)

def handle_option(episode, option):
    if option == "1":
        webbrowser.open(f"https://open.spotify.com/search/{episode.title}")
    elif option == "2":
        webbrowser.open(f"https://podcasts.apple.com/search?term={episode.title}")
    elif option == "3":
        webbrowser.open(f"https://www.youtube.com/results?search_query={episode.title}")
    elif option == "4":
        play_mp3(episode.enclosures[0].href)
    elif option == "5":
        return True
    return False

def play_mp3(url):
    try:
        subprocess.run(["mpv", url], check=True)
    except subprocess.CalledProcessError:
        console.print("[bold red]Error:[/bold red] Failed to play MP3. Make sure you have mpv installed.")
    except FileNotFoundError:
        console.print("[bold red]Error:[/bold red] mpv not found. Please install mpv to play MP3s in the CLI.")

def main():
    rss_url = "https://anchor.fm/s/fb2a98a0/podcast/rss"
    feed = fetch_rss_feed(rss_url)

    while True:
        console.clear()
        display_episodes(feed)
        episode = select_episode(feed)

        if episode is None:
            break

        while True:
            console.clear()
            display_episode_options(episode)
            option = prompt("Enter your choice (1-5): ")
            if handle_option(episode, option):
                break

if __name__ == "__main__":
    main()
