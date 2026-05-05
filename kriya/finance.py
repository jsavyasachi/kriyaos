import datetime
import os
import subprocess

from kriya.utils.audit import log_tool_call
from kriya.utils.errors import log_error


DEFAULT_F5E_REPO = "/Users/savya/projects/f5e"


def f5e_repo() -> str:
    return os.environ.get("KRIYA_F5E_REPO", DEFAULT_F5E_REPO)


def get_networth_report(
    display: str = "USD",
    inr_per_usd: float | None = None,
    state_dir: str = "state",
) -> str:
    cmd = ["uv", "run", "python", "-m", "f5e.analyze.networth", "--display", display]
    if inr_per_usd is not None:
        cmd += ["--inr-per-usd", str(inr_per_usd)]

    args = {"display": display}
    if inr_per_usd is not None:
        args["inr_per_usd"] = inr_per_usd

    try:
        result = subprocess.run(cmd, cwd=f5e_repo(), capture_output=True, text=True, check=True)
        log_tool_call("f5e.networth", args, "ok", {"bytes": len(result.stdout)}, state_dir=state_dir)
        return result.stdout.rstrip()
    except subprocess.CalledProcessError as e:
        log_error("finance", "f5e networth failed", {"stderr": e.stderr}, state_dir=state_dir)
        log_tool_call("f5e.networth", args, "error", error=str(e), state_dir=state_dir)
        return ""
    except OSError as e:
        log_error("finance", "f5e networth unavailable", {"error": str(e)}, state_dir=state_dir)
        log_tool_call("f5e.networth", args, "error", error=str(e), state_dir=state_dir)
        return ""


def format_finance(report: str, today: str | None = None) -> str:
    today = today or datetime.date.today().isoformat()
    if not report:
        return f"# Finance {today}\n\n_unavailable_\n"
    return f"# Finance {today}\n\n{report.rstrip()}\n"


def format_finance_section(report: str) -> str:
    if not report:
        return "Finance unavailable.\n"
    return report.rstrip() + "\n"


def write_finance_snapshot(
    state_dir: str = "state",
    today: str | None = None,
    display: str = "USD",
    inr_per_usd: float | None = None,
) -> str:
    today = today or datetime.date.today().isoformat()
    os.makedirs(state_dir, exist_ok=True)
    report = get_networth_report(display=display, inr_per_usd=inr_per_usd, state_dir=state_dir)
    path = os.path.join(state_dir, f"finance-{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(format_finance(report, today))
    print(f"Finance snapshot written to {path}")
    return path
