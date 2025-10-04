import os
import csv
import datetime
import time
import shutil
from rich import print as rprint
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.console import Console
from rich.columns import Columns

DATA_FILE = "tasks.csv"
MOTIVATIONS = [
    "You are closer to your goals than you think!",
    "Every small step counts—finish a task now!",
    "Success is built by finishing today’s tasks.",
    "Keep going! Your effort matters.",
    "Small wins lead to big changes."
]

STATUS_LIST = ['todo', 'done']

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_tasks():
    tasks = []
    try:
        with open(DATA_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row['id'] = int(row['id'])
                    row['time_tracked'] = int(row['time_tracked']) if row['time_tracked'] else 0
                    tasks.append(row)
                except Exception as e:
                    print(f"Skipping corrupt task row: {e}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error loading tasks: {e}")
    return tasks

def save_tasks(tasks):
    with open(DATA_FILE, 'w', newline='') as f:
        fieldnames = ['id', 'desc', 'status', 'notes', 'created_at', 'updated_at', 'time_tracked']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            writer.writerow(task)

def print_stats(tasks):
    done = sum(1 for t in tasks if t['status'] == 'done')
    todo = sum(1 for t in tasks if t['status'] == 'todo')
    total = len(tasks)

    rprint("\n[bold]Task Summary:[/bold]")
    rprint(f"Total: {total} | Pending: {todo} | Completed: {done}")

def ascii_bar_chart(done, pending, width=40):
    total = done + pending
    if total == 0:
        rprint("No tasks to display.")
        return

    done_len = int((done / total) * width)
    pending_len = width - done_len

    done_bar = "[green]" + "█" * done_len + "[/green]"
    pending_bar = "[red]" + "█" * pending_len + "[/red]"

    rprint(f"Completed: {done_bar} {done} | Pending: {pending_bar} {pending}\n")

def get_message_panel(todo_count):
    if todo_count > 0:
        message = "YOU HAVE WORK TO DO"
    else:
        message = "YAY WORK IS DONE CONGRATS"

    text = Text(message, style="bold green")
    panel = Panel.fit(text)
    return panel

def print_menu(tasks):
    console = Console()
    menu_lines = [
        "--- Personal Tracker CLI ---",
        "1. Add Task",
        "2. List Tasks",
        "3. Update Task",
        "4. Delete Task",
        "5. Search Tasks",
        "6. Filter Tasks",
        "7. Show Stats (Bar Chart)",
        "8. Export Tasks to CSV",
        "9. Time Track Task",
        "0. Exit"
    ]

    todo_count = sum(1 for t in tasks if t['status'] == 'todo')
    message_panel = get_message_panel(todo_count)

    menu_text = "\n".join(menu_lines)

    console.print(Columns([menu_text, message_panel], expand=True))


def show_tasks(tasks, filter_status=None, search_kw=None):
    filtered = tasks
    if filter_status:
        filtered = [t for t in filtered if t['status'] == filter_status]
    if search_kw:
        filtered = [t for t in filtered if search_kw.lower() in t['desc'].lower()]
    if not filtered:
        rprint("[yellow]No tasks found.[/yellow]")
        return

    rprint("\n[bold]Tasks:[/bold]")
    for t in filtered:
        rprint(f"[{t['id']}] {t['desc']}")
        rprint(f"  Status: {t['status']}")
        rprint(f"  Notes: {t['notes'] or '-'}")
        rprint("-" * 40)

def add_task(tasks):
    desc = input("Task description: ").strip()
    if not desc:
        print("Description cannot be empty.")
        return

    notes = input("Additional notes or leave blank: ").strip()

    now = datetime.datetime.now().isoformat()
    tid = max([t['id'] for t in tasks], default=0) + 1
    new_task = {
        'id': tid,
        'desc': desc,
        'status': 'todo',
        'notes': notes,
        'created_at': now,
        'updated_at': now,
        'time_tracked': 0
    }
    tasks.append(new_task)
    rprint("[green]Task added![/green] " + MOTIVATIONS[tid % len(MOTIVATIONS)])

def update_task(tasks):
    try:
        tid = int(input("Task ID to update: "))
    except ValueError:
        rprint("[red]Invalid input.[/red]")
        return
    task = next((t for t in tasks if t['id'] == tid), None)
    if not task:
        rprint("[red]Task not found.[/red]")
        return

    print("Leave input blank to keep existing values.")

    desc = input(f"Description [{task['desc']}]: ").strip()
    if desc:
        task['desc'] = desc

    status = input(f"Status (todo/done) [{task['status']}]: ").lower()
    if status in STATUS_LIST:
        task['status'] = status

    notes = input(f"Notes [{task.get('notes', '')}]: ").strip()
    if notes:
        task['notes'] = notes

    task['updated_at'] = datetime.datetime.now().isoformat()
    rprint("[green]Task updated![/green] " + MOTIVATIONS[tid % len(MOTIVATIONS)])

def delete_task(tasks):
    try:
        tid = int(input("Task ID to delete: "))
    except ValueError:
        rprint("[red]Invalid input.[/red]")
        return
    for i, t in enumerate(tasks):
        if t['id'] == tid:
            confirm = input(f"Confirm delete task [{t['desc']}]? (y/n): ").lower()
            if confirm == 'y':
                del tasks[i]
                rprint("[green]Task deleted.[/green]")
            else:
                rprint("[yellow]Delete cancelled.[/yellow]")
            return
    rprint("[red]Task not found.[/red]")

def search_tasks(tasks):
    kw = input("Enter keyword to search in descriptions: ").strip()
    show_tasks(tasks, search_kw=kw)

def filter_tasks(tasks):
    rprint("Filter by status options:")
    rprint("1. todo (pending)")
    rprint("2. done (completed)")
    choice = input("Choose filter type (1-2): ").strip()
    if choice == '1':
        show_tasks(tasks, filter_status='todo')
    elif choice == '2':
        show_tasks(tasks, filter_status='done')
    else:
        rprint("[red]Invalid choice.[/red]")

def export_tasks_csv(tasks):
    filename = input("Enter export CSV filename [tasks_export.csv]: ").strip() or "tasks_export.csv"
    with open(filename, "w", newline='') as f:
        fieldnames = ['id', 'desc', 'status', 'notes', 'created_at', 'updated_at', 'time_tracked']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tasks)
    rprint(f"[green]Tasks exported to {filename}[/green]")

def time_track(tasks):
    try:
        tid = int(input("Enter task ID to track time for: "))
    except ValueError:
        rprint("[red]Invalid input.[/red]")
        return
    task = next((t for t in tasks if t['id'] == tid), None)
    if not task:
        rprint("[red]Task not found.[/red]")
        return
    rprint("[yellow]Starting timer. Press Enter to stop.[/yellow]")
    start = time.time()
    input()
    elapsed = int(time.time() - start)
    task['time_tracked'] += elapsed
    task['updated_at'] = datetime.datetime.now().isoformat()
    rprint(f"[green]Tracked {elapsed} seconds. Total time on task: {task['time_tracked']} seconds.[/green]")

def show_menu():
    tasks = load_tasks()
    while True:
        clear_screen()
        print_menu(tasks)

        choice = input("\nChoose option: ").strip()

        if choice == "1":
            add_task(tasks)
        elif choice == "2":
            show_tasks(tasks)
        elif choice == "3":
            update_task(tasks)
        elif choice == "4":
            delete_task(tasks)
        elif choice == "5":
            search_tasks(tasks)
        elif choice == "6":
            filter_tasks(tasks)
        elif choice == "7":
            done = sum(1 for t in tasks if t['status'] == 'done')
            todo = sum(1 for t in tasks if t['status'] == 'todo')
            print_stats(tasks)
            ascii_bar_chart(done, todo, width=40)
            input("Press Enter to continue...")
        elif choice == "8":
            export_tasks_csv(tasks)
            input("Press Enter to continue...")
        elif choice == "9":
            time_track(tasks)
            input("Press Enter to continue...")
        elif choice == "0":
            save_tasks(tasks)
            rprint("[bold green]Thank you for using Personal Tracker. Stay productive![/bold green]")
            break
        else:
            rprint("[red]Invalid choice. Try again.[/red]")
            input("Press Enter to continue...")

        save_tasks(tasks)

if __name__ == "__main__":
    show_menu()
