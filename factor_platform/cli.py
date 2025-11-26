from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Sequence

from .factor_store import DEFAULT_DB_PATH, FactorStore


def _parse_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Factor platform command-line tools")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"Path to the registry SQLite database (default: {DEFAULT_DB_PATH})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init-db", help="Initialize the registry database")
    init_cmd.add_argument("--seed", help="Optional factors.json path for seeding")

    reg_cmd = sub.add_parser("register-factor", help="Register or update a factor")
    reg_cmd.add_argument("code", help="Factor code")
    reg_cmd.add_argument("expression", help="Expression (QLib-like or Python). Use $close, Ref(), Mean(), etc., or provide a Python callable string")
    reg_cmd.add_argument("--name", help="Display name")
    reg_cmd.add_argument("--category", help="Factor category label")
    reg_cmd.add_argument("--owner", help="Factor owner")
    reg_cmd.add_argument("--tags", help="Comma-separated tags")
    reg_cmd.add_argument("--description", help="Long form description")
    reg_cmd.add_argument("--note", help="Version note")

    sub.add_parser("list-factors", help="Show active factors")

    job_cmd = sub.add_parser("submit-job", help="Submit an evaluation job")
    job_cmd.add_argument("code", help="Factor code")
    job_cmd.add_argument("--start", dest="start_date", required=True, help="Start date YYYY-MM-DD")
    job_cmd.add_argument("--end", dest="end_date", required=True, help="End date YYYY-MM-DD")
    job_cmd.add_argument("--freq", default="day", help="Frequency (day/week/month/5min...)")
    job_cmd.add_argument("--instruments", required=True, help="Comma separated list or pools (csi300,000001.SZ)")
    job_cmd.add_argument("--priority", type=int, default=5, help="Lower value = higher priority (default 5)")
    job_cmd.add_argument("--owner", help="Override job owner")
    job_cmd.add_argument("--tags", help="Override tags (comma separated)")
    job_cmd.add_argument("--callback", help="Webhook for job completion")
    job_cmd.add_argument("--version", type=int, help="Specific factor version")
    job_cmd.add_argument("--context", help="JSON string with custom context")

    list_jobs_cmd = sub.add_parser("list-jobs", help="List jobs")
    list_jobs_cmd.add_argument("--status", choices=["PENDING", "RUNNING", "SUCCESS", "FAILED"])
    list_jobs_cmd.add_argument("--limit", type=int, default=20)

    return parser


def _load_tags(value: str | None) -> Sequence[str] | None:
    if not value:
        return None
    return _parse_list(value)


def run_cli(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = FactorStore(Path(args.db))

    if args.command == "init-db":
        store.ensure_seed_factors(Path(args.seed) if args.seed else None)
        print(f"Registry initialized at {store.db_path}")
        return 0

    if args.command == "register-factor":
        payload = store.register_factor(
            code=args.code,
            expression=args.expression,
            name=args.name,
            category=args.category,
            owner=args.owner,
            tags=_load_tags(args.tags),
            description=args.description,
            note=args.note,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "list-factors":
        factors = store.list_factors()
        print(json.dumps(factors, ensure_ascii=False, indent=2))
        return 0

    if args.command == "submit-job":
        context = json.loads(args.context) if args.context else None
        payload = store.submit_job(
            factor_code=args.code,
            start_date=args.start_date,
            end_date=args.end_date,
            freq=args.freq,
            instruments=_parse_list(args.instruments),
            priority=args.priority,
            owner=args.owner,
            tags=_load_tags(args.tags),
            callback_url=args.callback,
            context=context,
            version=args.version,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "list-jobs":
        jobs = store.list_jobs(status=args.status, limit=args.limit)
        print(json.dumps(jobs, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"Unsupported command {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
