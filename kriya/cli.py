import argparse

from kriya.approvals import format_pending_actions, list_pending_actions
from kriya.daily_brief import generate_daily_brief
from kriya.email_triage import append_email_triage
from kriya.google_tasks import write_tasks_snapshot
from kriya.inbox import render_inbox
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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
