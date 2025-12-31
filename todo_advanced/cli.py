"""
CLI interface for the advanced TODO system.
"""

import sys
from typing import List, Optional


class Colors:
    """ANSI color codes for CLI output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def colorize(text: str, color: str) -> str:
    """Apply ANSI color to text."""
    if not sys.stdout.isatty():
        return text
    return f"{color}{text}{Colors.RESET}"


def print_colored(text: str, color: str) -> None:
    """Print colored text."""
    print(colorize(text, color))


def print_task(task: dict, index: int = None, prefix: str = "") -> None:
    """Print a task in formatted output."""
    status = "✓" if task.get("completed") else "○"
    status_color = Colors.GREEN if task.get("completed") else Colors.BLUE

    index_str = f"{index + 1:3}. " if index is not None else ""
    task_text = task.get("task", "")
    tags = task.get("tags", [])

    output = f"{prefix}{colorize(status, status_color)} {index_str}{task_text}"

    if tags:
        tags_str = " ".join([f"#{tag}" for tag in tags])
        output += f" {colorize(tags_str, Colors.CYAN)}"

    print(output)


def print_tasks(tasks: List[dict], show_index: bool = True, prefix: str = "") -> None:
    """Print multiple tasks in formatted output."""
    for i, task in enumerate(tasks):
        print_task(task, i if show_index else None, prefix)


def print_tag(tag: dict, show_usage: bool = False, show_description: bool = False) -> None:
    """Print a tag with metadata."""
    name = tag.get("name", "")
    color = tag.get("color", "#CCCCCC")

    # Convert hex color to ASCII approximation
    color_code = Colors.WHITE

    output = f"  {colorize(name, color_code)}"

    if show_usage:
        usage = tag.get("usage_count", 0)
        output += f" {colorize(f'[{usage}]', Colors.DIM)}"

    if show_description and tag.get("description"):
        output += f" - {tag.get('description')}"

    print(output)


def print_tags(tags: List[dict], show_usage: bool = False, show_description: bool = False) -> None:
    """Print multiple tags in formatted output."""
    for tag in tags:
        print_tag(tag, show_usage, show_description)


def print_error(message: str) -> None:
    """Print an error message."""
    print_colored(f"Error: {message}", Colors.RED)


def print_success(message: str) -> None:
    """Print a success message."""
    print_colored(f"✓ {message}", Colors.GREEN)


def print_info(message: str) -> None:
    """Print an info message."""
    print_colored(f"ℹ {message}", Colors.CYAN)


def paginate(items: List[str], page_size: int = 10) -> None:
    """Print items with pagination."""
    total_pages = (len(items) + page_size - 1) // page_size

    for page in range(total_pages):
        start = page * page_size
        end = min(start + page_size, len(items))
        page_items = items[start:end]

        for item in page_items:
            print(item)

        if page < total_pages - 1:
            try:
                input(f"Page {page + 1}/{total_pages} - Press Enter for next page...")
            except KeyboardInterrupt:
                break


def fuzzy_search(query: str, items: List[str], threshold: float = 0.6) -> List[str]:
    """Fuzzy search for items."""
    from difflib import SequenceMatcher

    results = []
    query_lower = query.lower()

    for item in items:
        item_lower = item.lower()
        ratio = SequenceMatcher(None, query_lower, item_lower).ratio()
        if ratio >= threshold:
            results.append((item, ratio))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return [item for item, _ in results]
