"""
Quick start example demonstrating the Advanced TODO System.
Run this to see the system in action.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from todo_advanced import api
from todo_advanced.cli import print_colored, print_task, print_tasks, Colors, print_info, print_success


def main():
    """Run quick start demo."""
    print()
    print_colored("=" * 70, Colors.BOLD)
    print_colored("Advanced TODO System - Quick Start Demo", Colors.BOLD)
    print_colored("=" * 70, Colors.RESET)
    print()

    # 1. Add some tasks
    print_info("1. Adding tasks...")
    api.add_todo("Fix critical bug in auth system", ["urgent", "work", "bug"])
    api.add_todo("Buy groceries", ["personal", "shopping"])
    api.add_todo("Review team proposals", ["work", "review"])
    api.add_todo("Call dentist", ["personal", "health"])
    api.add_todo("Deploy to production", ["work", "deployment", "urgent"])
    print_success("5 tasks added")
    print()

    # 2. List all tasks
    print_info("2. All tasks:")
    tasks = api.list_todos()
    for i, task in enumerate(tasks):
        print_task(task, index=i)
    print()

    # 3. Create structured tags
    print_info("3. Creating structured tags with metadata...")
    api.add_structured_tag(
        "work",
        description="Work-related tasks",
        color="#FF0000",
        aliases=["office", "job"],
    )
    api.add_structured_tag(
        "urgent",
        description="Needs immediate attention",
        color="#FF5500",
    )
    api.add_structured_tag(
        "personal",
        description="Personal tasks",
        color="#0066FF",
    )
    print_success("3 structured tags created")
    print()

    # 4. Show tag statistics
    print_info("4. Tag statistics:")
    stats = api.show_tag_stats()
    for tag, count in sorted(stats.items()):
        print(f"  {tag}: {count} tasks")
    print()

    # 5. Filter by tags
    print_info("5. Filter work tasks:")
    work_tasks = api.filter_by_tags(["work"])
    print_tasks(work_tasks, show_index=False, prefix="  ")
    print()

    # 6. Complex filter (AND logic)
    print_info("6. Urgent work tasks:")
    urgent_work = api.filter_by_tags(["work", "urgent"], match_all=True)
    print_tasks(urgent_work, show_index=False, prefix="  ")
    print()

    # 7. DSL queries
    print_info("7. DSL Query: 'tag:work AND urgent'")
    dsl_results = api.query_tasks_dsl("tag:work AND urgent")
    print_tasks(dsl_results, show_index=False, prefix="  ")
    print()

    # 8. Tag recommendations
    print_info("8. Recommend tags for: 'Database migration on server'")
    recommendations = api.recommend_tags(
        "Database migration on server",
        existing_tags=["work"],
        limit=3,
    )
    if recommendations:
        for tag, score in recommendations:
            print(f"  {tag}: {score:.2f}")
    else:
        print("  (No recommendations found)")
    print()

    # 9. Get tag metadata
    print_info("9. Tag metadata for 'work':")
    metadata = api.get_tag_metadata("work")
    if metadata:
        print(f"  Name: {metadata['name']}")
        print(f"  Description: {metadata['description']}")
        print(f"  Color: {metadata['color']}")
        print(f"  Aliases: {', '.join(metadata['aliases'])}")
        print(f"  Usage: {metadata['usage_count']} tasks")
    print()

    # 10. Get related tags
    print_info("10. Tags related to 'work':")
    related = api.get_related_tags("work", limit=3)
    if related:
        for tag, count in related:
            print(f"  {tag}: co-occurred {count} time(s)")
    else:
        print("  (No related tags found)")
    print()

    # 11. Complete a task
    print_info("11. Marking task 0 as completed...")
    api.complete_task(0)
    print_success("Task marked as completed")
    print()

    # 12. Show final state
    print_info("12. Final task list:")
    final_tasks = api.list_todos()
    for i, task in enumerate(final_tasks):
        print_task(task, index=i)
    print()

    # Summary
    print_colored("=" * 70, Colors.BOLD)
    print_colored("✓ Quick Start Demo Complete!", Colors.GREEN)
    print_colored("=" * 70, Colors.RESET)
    print()
    print("Key features demonstrated:")
    print("  ✓ Task management (CRUD operations)")
    print("  ✓ Tag-based filtering (OR and AND logic)")
    print("  ✓ Structured tags with metadata")
    print("  ✓ Tag recommendations based on content")
    print("  ✓ DSL queries for advanced filtering")
    print("  ✓ Tag statistics and relationships")
    print()
    print("For more information, see:")
    print("  - README.md for usage documentation")
    print("  - FEATURE_SPEC.md for detailed feature list")
    print("  - tests/test_advanced_todo.py for test examples")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_colored(f"Error: {e}", Colors.RED)
        sys.exit(1)
