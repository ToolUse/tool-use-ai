from pathlib import Path
import sqlite3
import time
import datetime
from typing import Optional, Tuple, List
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
  ai log category rename "Coding" "Programming"
  ai log category merge "Dev" "Programming"
  ai log category show "Programming"
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
        example_templates = {
            "time_period": """
                -- Shows totals for a time period
                SELECT category, SUM(duration) as total_duration 
                FROM activities 
                WHERE date(start_time) = date('now', '-1 day', 'localtime')  -- or other date conditions
                GROUP BY category
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

        # Get initial SQL query
        prompt = f"""Given this natural language query: "{query}"

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
Respond with just the SQL query, nothing else."""

        sql_query = self.ai_service.query(prompt).strip()
        print(f"Generated SQL: {sql_query}")  # Debug print

        # Validate and correct if needed
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Test the query
            cursor.execute("BEGIN")
            cursor.execute(sql_query)
            cursor.execute("ROLLBACK")
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

        # Execute the (possibly corrected) query
        try:
            cursor.execute(sql_query)
            results = [dict(row) for row in cursor.fetchall()]
            print(f"Query results: {results}")  # Debug print
        except sqlite3.Error as e:
            print(f"Error executing query: {e}")
            results = []

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
            print(f"Error renaming category: {e}")
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
            print(f"Error merging categories: {e}")
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
                print("No categories found")
                return
            for name, usage_count, activity_count, total_duration in categories:
                duration_str = manager.format_duration(total_duration)
                print(
                    f"{name}: {activity_count} activities, {duration_str} total ({usage_count} uses)"
                )

        elif cmd == "rename" and len(args) == 4:
            old_name, new_name = args[2], args[3]
            if manager.rename_category(old_name, new_name):
                print(f"Renamed category '{old_name}' to '{new_name}'")
            else:
                print("Failed to rename category")

        elif cmd == "merge" and len(args) == 4:
            from_cat, into_cat = args[2], args[3]
            if manager.merge_categories(from_cat, into_cat):
                print(f"Merged category '{from_cat}' into '{into_cat}'")
            else:
                print("Failed to merge categories")

        elif cmd == "show" and len(args) == 3:
            category = args[2]
            activities = manager.show_category(category)
            if not activities:
                print(f"No activities found in category '{category}'")
                return
            for activity in activities:
                start_time = datetime.datetime.fromisoformat(
                    str(activity["start_time"])
                )
                duration = (
                    manager.format_duration(activity["duration"])
                    if activity["duration"]
                    else "In progress"
                )
                print(
                    f"{start_time.strftime('%Y-%m-%d %H:%M')}: {activity['name']} ({duration})"
                )
        else:
            print(CATEGORY_HELP_TEXT)
        return

    # Case 2: No arguments - Stop if running, prompt if not
    if not args:
        current_activity = manager.stop_activity()
        if current_activity:
            name, duration, category = current_activity
            print(f"Stopped tracking: {name}")
            print(f"Duration: {duration}")
            print(f"Category: {category}")
        else:
            activity = input("What activity would you like to start?: ").strip()
            if activity:
                manager.start_activity(activity)
                print(f"Started tracking: {activity}")
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
            print("No activities found for your query.")
            return

        for result in results:
            if "total_duration" in result:
                category = result.get("category", "Uncategorized")
                duration = manager.format_duration(result["total_duration"])
                print(f"{category}: {duration}")
            else:
                start_time = datetime.datetime.fromisoformat(str(result["start_time"]))
                duration = (
                    manager.format_duration(result["duration"])
                    if result["duration"]
                    else "In progress"
                )
                name = result.get("name", "Unknown activity")
                print(f"{start_time.strftime('%Y-%m-%d %H:%M')}: {name} ({duration})")
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
            print(f"Started tracking: {activity_name}")
    else:
        manager.start_activity(activity_name)
        print(f"Started tracking: {activity_name}")


def main(args: List[str]) -> None:
    """Entry point for the activity tracker script"""
    process_command(args)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
