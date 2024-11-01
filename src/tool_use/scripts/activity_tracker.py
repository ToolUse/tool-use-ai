from pathlib import Path
import sqlite3
import time
import datetime
from typing import Optional, Tuple, List
from rich.console import Console
from rich.table import Table
from ..utils.ai_service import AIService

HELP_TEXT = """Usage: ai log [command] [args]

Commands:
  <activity>           Start tracking an activity
  (no arguments)       Stop current activity or prompt to start one
  tell <query>         Query your activity history in natural language
  category <command>   Manage activity categories
  help                Show this help message

Examples:
  ai log working on python project
  ai log tell me how long I coded today
  ai log tell me what I did yesterday
  ai log category list

For more details on a command, use: ai log <command> help
"""

CATEGORY_HELP_TEXT = """Usage: ai log category <command> [args]

Commands:
  list              List all categories with usage counts
  rename <old> <new> Rename a category
  merge <from> <into> Merge one category into another
  show <name>       List activities in a category
  help              Show this help message

Examples:
  ai log category list
  ai log category rename "<old name>" "<new name>"
  ai log category merge "<source name>" "<target name>"
  ai log category show "<category name>"
"""


class ActivityManager:
    def __init__(self):
        # Create data directory in user's home
        self.data_dir = Path.home() / ".tool-use" / "ai_activity"
        self.data_dir.mkdir(exist_ok=True)

        # Initialize database
        self.db_path = self.data_dir / "activities.db"
        self.init_database()

        # State file to track current activity
        self.state_file = self.data_dir / "current_activity.txt"

        # Initialize AI service
        self.ai_service = AIService()

        self.console = Console()

    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Activities table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER,
                category TEXT
            )
        """
        )

        # Categories table for tracking AI categorization
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                count INTEGER DEFAULT 1
            )
        """
        )

        conn.commit()
        conn.close()

    def get_current_activity(self) -> Optional[Tuple[int, str, float]]:
        """Return current activity if exists: (id, name, start_time)"""
        if not self.state_file.exists():
            return None

        with open(self.state_file, "r") as f:
            try:
                activity_id, name, start_time = f.read().strip().split("|")
                return int(activity_id), name, float(start_time)
            except (ValueError, IndexError):
                return None

    def get_existing_categories(self) -> List[str]:
        """Get list of existing categories ordered by usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY count DESC")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories

    def start_activity(self, activity_name: str) -> bool:
        """Start tracking a new activity"""
        current = self.get_current_activity()

        if current:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_time = time.time()
        cursor.execute(
            "INSERT INTO activities (name, start_time) VALUES (?, ?)",
            (activity_name, datetime.datetime.fromtimestamp(start_time)),
        )
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Save current activity state
        with open(self.state_file, "w") as f:
            f.write(f"{activity_id}|{activity_name}|{start_time}")

        return True

    def categorize_activity(self, activity_name: str) -> str:
        """Use AI to categorize the activity"""
        existing_categories = self.get_existing_categories()

        prompt = f"""Given these existing categories: {', '.join(existing_categories) if existing_categories else 'None yet'},
        what category best fits this activity: '{activity_name}'?
        If none fit well, suggest a new category name.
        It is important that these activities are categorized for reporting and analysis, so do not put activities into unrelated categories.
        Respond with just the category name, nothing else."""

        category = self.ai_service.query(prompt).strip()

        # Update categories table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO categories (name, count) 
            VALUES (?, 1)
            ON CONFLICT(name) DO UPDATE SET count = count + 1
        """,
            (category,),
        )
        conn.commit()
        conn.close()

        return category

    def stop_activity(self) -> Optional[Tuple[str, str, str]]:
        """Stop current activity and return (name, duration_str, category)"""
        current = self.get_current_activity()
        if not current:
            return None

        activity_id, name, start_time = current
        end_time = time.time()
        duration = end_time - start_time

        # Get AI categorization
        category = self.categorize_activity(name)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE activities SET end_time = ?, duration = ?, category = ? WHERE id = ?",
            (
                datetime.datetime.fromtimestamp(end_time),
                duration,
                category,
                activity_id,
            ),
        )
        conn.commit()
        conn.close()

        if self.state_file.exists():
            self.state_file.unlink()

        duration_str = self.format_duration(duration)
        return name, duration_str, category

    def process_query(self, query: str) -> List[dict]:
        """Process natural language queries about activities with validation and correction"""
        console = Console()
        example_templates = {
            "today": """
                -- Shows activities from today
                SELECT name, start_time, duration, category
                FROM activities 
                WHERE date(start_time) = date('now', 'localtime')
                ORDER BY start_time DESC
            """,
            "yesterday": """
                -- Shows activities from yesterday
                SELECT name, start_time, duration, category
                FROM activities 
                WHERE date(start_time) = date('now', '-1 day', 'localtime')
                ORDER BY start_time DESC
            """,
            "time_summary": """
                -- Shows total time by category for a period
                SELECT category, SUM(duration) as total_duration, COUNT(*) as activity_count
                FROM activities 
                WHERE date(start_time) = date('now', '-1 day', 'localtime')
                GROUP BY category
                ORDER BY total_duration DESC
            """,
            "longest_activities": """
                -- Shows activities ordered by duration
                SELECT name, start_time, duration, category
                FROM activities
                WHERE date(start_time) = date('now', '-1 day', 'localtime')
                ORDER BY duration DESC
            """,
            "comparison": """
                -- Compares two time periods
                SELECT category,
                    SUM(CASE WHEN date(start_time) = date('now', 'localtime') THEN duration ELSE 0 END) as today,
                    SUM(CASE WHEN date(start_time) = date('now', '-1 day', 'localtime') THEN duration ELSE 0 END) as yesterday
                FROM activities
                GROUP BY category
            """,
            "activity_list": """
                -- Lists activities with times
                SELECT name, start_time, duration, category
                FROM activities
                WHERE date(start_time) >= date('now', '-7 days', 'localtime')
                ORDER BY start_time DESC
            """,
        }

        # Update the prompt to be more explicit about natural language interpretation
        prompt = f"""Convert this natural language question into a SQL query: "{query}"
        The user is asking about their activity history - interpret the meaning, don't use the exact words as search terms.
        For example:
        - "what did I do today" → show all activities from today
        - "how long did I code yesterday" → show coding-related activities from yesterday
        - "show me my activities this week" → show all activities from the past 7 days
        - "what did I do the most today" → show today's activities ordered by duration DESC

        Here are some example query patterns (but feel free to modify or write your own):
{example_templates}

        Database schema:
        CREATE TABLE activities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration INTEGER,
            category TEXT
        );

        Write a SQL query that best answers the user's question.
        IMPORTANT: 
        - Always include name, start_time, duration, and category in the SELECT clause
        - Do not use parameter placeholders (?)
        - Write the complete query with all conditions included
        - For "today", use date(start_time) = date('now', 'localtime')
        - For duration-based queries, order by duration DESC
        Respond with just the SQL query, nothing else."""

        sql_query = self.ai_service.query(prompt).strip()
        # print(f"Generated SQL: {sql_query}")  # TODO: remove after testing

        # Validate and correct if needed
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Test the query
            cursor.execute("BEGIN")
            cursor.execute(sql_query)
            cursor.execute("ROLLBACK")

            # Execute the actual query and get results
            cursor.execute(sql_query)
            results = [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"SQL Error: {e}")  # Debug print
            correction_prompt = f"""The SQL query:
{sql_query}
Failed with error: {str(e)}

Here are valid example patterns:
{example_templates}

Please provide a corrected SQL query that will work."""

            sql_query = self.ai_service.query(correction_prompt).strip()
            print(f"Corrected SQL: {sql_query}")  # Debug print

            # Execute the corrected query
            cursor.execute(sql_query)
            results = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return results

    def list_categories(self) -> List[Tuple[str, int, int, float]]:
        """List all categories with their usage counts and activity stats
        Returns: List of (name, usage_count, activity_count, total_duration)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.name, 
                  c.count as usage_count,
                  COUNT(a.id) as activity_count,
                  COALESCE(SUM(a.duration), 0) as total_duration
            FROM categories c
            LEFT JOIN activities a ON a.category = c.name
            GROUP BY c.name
            ORDER BY c.count DESC
        """
        )
        results = cursor.fetchall()
        conn.close()
        return results

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Rename a category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN")
            # Update activities table
            cursor.execute(
                "UPDATE activities SET category = ? WHERE category = ?",
                (new_name, old_name),
            )
            # Update categories table
            cursor.execute(
                "UPDATE categories SET name = ? WHERE name = ?", (new_name, old_name)
            )
            cursor.execute("COMMIT")
            return True
        except sqlite3.Error as e:
            self.console.print(f"[red]Error renaming category: {e}[/red]")
            cursor.execute("ROLLBACK")
            return False
        finally:
            conn.close()

    def merge_categories(self, from_cat: str, into_cat: str) -> bool:
        """Merge one category into another"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN")
            # Update activities table
            cursor.execute(
                "UPDATE activities SET category = ? WHERE category = ?",
                (into_cat, from_cat),
            )
            # Get the count from the source category
            cursor.execute("SELECT count FROM categories WHERE name = ?", (from_cat,))
            from_count = cursor.fetchone()[0]
            # Update the count in the target category
            cursor.execute(
                "UPDATE categories SET count = count + ? WHERE name = ?",
                (from_count, into_cat),
            )
            # Delete the source category
            cursor.execute("DELETE FROM categories WHERE name = ?", (from_cat,))
            cursor.execute("COMMIT")
            return True
        except sqlite3.Error as e:
            self.console.print(f"[red]Error merging categories: {e}[/red]")
            cursor.execute("ROLLBACK")
            return False
        finally:
            conn.close()

    def show_category(self, category_name: str) -> List[dict]:
        """Show activities in a category"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name, start_time, duration, end_time
            FROM activities
            WHERE category = ?
            ORDER BY start_time DESC
        """,
            (category_name,),
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human readable string"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


def process_command(args: list[str]) -> None:
    """Process command line arguments"""
    manager = ActivityManager()
    console = Console()

    # Handle help command

    if len(args) == 1 and args[0].lower() == "help":
        print(HELP_TEXT)
        return

    # Case 1: Category management
    if len(args) > 0 and args[0].lower() == "category":
        if len(args) == 1 or (len(args) == 2 and args[1].lower() == "help"):
            print(CATEGORY_HELP_TEXT)
            return

        cmd = args[1].lower()
        if cmd == "list":
            categories = manager.list_categories()
            if not categories:
                console.print("[red]No categories found[/red]")
                return
            table = Table(title="Activity Categories")
            table.add_column("Category", style="cyan")
            table.add_column("Activities", justify="right")
            table.add_column("Total Time", justify="right")
            table.add_column("Uses", justify="right")

            for name, usage_count, activity_count, total_duration in categories:
                duration_str = manager.format_duration(total_duration)
                table.add_row(name, str(activity_count), duration_str, str(usage_count))

            console.print(table)
            return

        elif cmd == "rename":
            if len(args) != 4:
                console.print(
                    "[red]Error:[/red] rename requires old and new category names"
                )
                return
            old_name, new_name = args[2], args[3]
            if manager.rename_category(old_name, new_name):
                console.print(
                    f"[green]Renamed category '{old_name}' to '{new_name}'[/green]"
                )
            else:
                console.print("[red]Failed to rename category[/red]")
            return

        elif cmd == "merge":
            if len(args) != 4:
                console.print(
                    "[red]Error:[/red] merge requires source and target category names"
                )
                return
            from_cat, into_cat = args[2], args[3]
            if manager.merge_categories(from_cat, into_cat):
                console.print(
                    f"[green]Merged category '{from_cat}' into '{into_cat}'[/green]"
                )
            else:
                console.print("[red]Failed to merge categories[/red]")
            return

        elif cmd == "show":
            if len(args) != 3:
                console.print("[red]Error:[/red] Please specify a category name")
                return
            category = args[2]
            activities = manager.show_category(category)
            if not activities:
                console.print(
                    f"[red]No activities found in category '{category}'[/red]"
                )
                return

            # Create and display table (indent fixed)
            table = Table(title=f"Activities in {category}")
            table.add_column("Date", style="cyan")
            table.add_column("Activity")
            table.add_column("Duration", justify="right")

            for activity in activities:
                start_time = datetime.datetime.fromisoformat(
                    str(activity["start_time"])
                )
                duration = (
                    manager.format_duration(activity["duration"])
                    if activity["duration"]
                    else "[yellow]In progress[/yellow]"
                )
                table.add_row(
                    start_time.strftime("%Y-%m-%d %H:%M"),
                    activity["name"],
                    duration,
                )
            console.print(table)
            return

        else:
            console.print(f"[red]Unknown category command: {cmd}[/red]")
            print(CATEGORY_HELP_TEXT)
            return

    # Case 2: No arguments - Stop if running, prompt if not
    if not args:
        current_activity = manager.stop_activity()
        if current_activity:
            name, duration, category = current_activity
            console.print()
            console.print(f"[bold green]Stopped tracking:[/bold green] {name}")
            console.print(
                f"[bold green]Duration:[/bold green] [yellow]{duration}[/yellow]"
            )
            console.print(f"[bold green]Category:[/bold green] [blue]{category}[/blue]")
        else:
            activity = input("What activity would you like to start?: ").strip()
            if activity:
                manager.start_activity(activity)
                console.print(f"[bold green]Started tracking:[/bold green] {activity}")
        return

    # Case 2: Command starts with "tell" - Handle query
    if args[0].lower() == "tell":
        if len(args) < 2:
            print("Please specify what you want to know. For example:")
            print("  ai log tell me how long I coded today")
            print("  ai log tell me my activities from yesterday")
            return

        query = " ".join(args[1:])
        results = manager.process_query(query)

        if not results:
            console.print("[red]No activities found for your query.[/red]")
            return

        if "total_duration" in results[0]:
            # Summary table for aggregated results
            table = Table(title="Activity Summary")
            table.add_column("Category", style="cyan")
            table.add_column("Duration", justify="right")

            for result in results:
                category = result.get("category", "Uncategorized")
                duration = manager.format_duration(result["total_duration"])
                table.add_row(category, duration)
        else:
            # Detailed activity list table
            table = Table(title="Activities")
            table.add_column("Time", style="cyan")
            table.add_column("Activity")
            table.add_column("Duration", justify="right")
            table.add_column("Category", style="blue")

            for result in results:
                start_time = datetime.datetime.fromisoformat(str(result["start_time"]))
                duration = (
                    manager.format_duration(result["duration"])
                    if result["duration"]
                    else "[yellow]In progress[/yellow]"
                )
                table.add_row(
                    start_time.strftime("%H:%M"),
                    result["name"],
                    duration,
                    result.get("category", "Uncategorized"),
                )

        console.print(table)
        return

    # Case 3: Start new activity
    activity_name = " ".join(args)
    current = manager.get_current_activity()

    if current:
        _, current_name, _ = current
        response = (
            input(
                f"Activity '{current_name}' in progress. Stop and start '{activity_name}'? [Y/n]: "
            )
            .strip()
            .lower()
        )
        if response in ("y", "yes", ""):
            manager.stop_activity()
            manager.start_activity(activity_name)
            console.print(f"[green]Started tracking:[/green] {activity_name}")

    else:
        manager.start_activity(activity_name)
        console.print(f"[green]Started tracking:[/green] {activity_name}")


def main(args: List[str]) -> None:
    """Entry point for the activity tracker script"""
    process_command(args)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
