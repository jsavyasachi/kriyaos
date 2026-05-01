import argparse

from kriya.approvals import approve_action, format_pending_actions, list_pending_actions, reject_action
from kriya.daily_brief import generate_daily_brief
from kriya.email_triage import append_email_triage
from kriya.google_tasks import write_tasks_snapshot
from kriya.inbox import render_inbox
from kriya.memory import add as memory_add
from kriya.memory import get_all as memory_get_all
from kriya.poll import format_poll_result, run_poll


def build_parser():
    parser = argparse.ArgumentParser(prog="kriya")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily-brief", help="Generate the daily brief")
    daily.add_argument("--state-dir", default="state")
    daily.add_argument("--date")
    daily.add_argument("--force", action="store_true")

    triage = subparsers.add_parser("email-triage", help="Append unread email triage to state/inbox.md")
    triage.add_argument("--state-dir", default="state")
    triage.add_argument("--date")
    triage.add_argument("--max-results", type=int, default=10)
    triage.add_argument("--force", action="store_true")

    tasks = subparsers.add_parser("tasks", help="Write a read-only Google Tasks snapshot")
    tasks.add_argument("--state-dir", default="state")
    tasks.add_argument("--date")
    tasks.add_argument("--max-lists", type=int, default=10)
    tasks.add_argument("--max-tasks-per-list", type=int, default=20)

    approvals = subparsers.add_parser("approvals", help="List pending approval-gated actions")
    approvals.add_argument("--state-dir", default="state")

    poll = subparsers.add_parser("poll", help="Run a bounded read-only polling cycle")
    poll.add_argument("--state-dir", default="state")
    poll.add_argument("--date")
    poll.add_argument("--force", action="store_true")

    inbox = subparsers.add_parser("inbox", help="Render local Kriya OS state")
    inbox.add_argument("--state-dir", default="state")

    memories = subparsers.add_parser("memories", help="List or add stored memories")
    memories.add_argument("--add", metavar="TEXT", help="Store a new memory")

    approve = subparsers.add_parser("approve", help="Approve and execute a pending action")
    approve.add_argument("id", help="Approval ID")
    approve.add_argument("--state-dir", default="state")

    reject = subparsers.add_parser("reject", help="Reject a pending action")
    reject.add_argument("id", help="Approval ID")
    reject.add_argument("--state-dir", default="state")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "daily-brief":
        generate_daily_brief(state_dir=args.state_dir, today=args.date, force=args.force)
        return 0
    if args.command == "email-triage":
        append_email_triage(
            state_dir=args.state_dir,
            today=args.date,
            max_results=args.max_results,
            force=args.force,
        )
        return 0
    if args.command == "tasks":
        write_tasks_snapshot(
            state_dir=args.state_dir,
            today=args.date,
            max_lists=args.max_lists,
            max_tasks_per_list=args.max_tasks_per_list,
        )
        return 0
    if args.command == "approvals":
        print(format_pending_actions(list_pending_actions(args.state_dir)), end="")
        return 0
    if args.command == "poll":
        print(format_poll_result(run_poll(state_dir=args.state_dir, today=args.date, force=args.force)), end="")
        return 0
    if args.command == "inbox":
        print(render_inbox(args.state_dir), end="")
        return 0
    if args.command == "approve":
        from kriya.execute import execute_action
        try:
            approve_action(args.id, args.state_dir)
            item = execute_action(args.id, args.state_dir)
            print(f"Executed: {item['tool']} ({item['id']})")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0
    if args.command == "reject":
        try:
            reject_action(args.id, args.state_dir)
            print(f"Rejected: {args.id}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0
    if args.command == "memories":
        if args.add:
            ok = memory_add(args.add)
            print("Remembered." if ok else "Memory store unavailable.")
        else:
            all_mems = memory_get_all()
            if not all_mems:
                print("No memories stored.")
            else:
                for m in all_mems:
                    print(f"- {m['memory']}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
