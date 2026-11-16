"""Run registered finite experiments and checkpoint complete/incomplete/failed JSON."""
import argparse
import json
from pathlib import Path
from common import BudgetExceeded, Context, write_json
from experiments import STAGES


def run(args):
    names = args.stages.split(",") if args.stages else list(STAGES)
    if not names or len(set(names)) != len(names) or any(name not in STAGES for name in names):
        raise ValueError(f"choose unique implemented stages from {list(STAGES)}")
    try:
        ctx = Context(args,names)
    except Exception as exc:
        report = {"schema_version":1,"algorithm":"Interlock-128","status":"failed",
                  "phase":"initialization","error":{"type":type(exc).__name__,"message":str(exc)}}
        write_json(args.output,report)
        print(json.dumps(report,sort_keys=True))
        return 1
    current = None
    ctx.flush()
    try:
        for current in names:
            ctx.deadline.check()
            data = STAGES[current](ctx)
            ctx.checkpoint(current,data,"complete")
        ctx.deadline.check()
        ctx.report["status"] = "complete"
    except BudgetExceeded as exc:
        ctx.report["status"] = "incomplete"
        ctx.report["reason"] = str(exc)
        if current is not None:
            entry = ctx.report["experiments"].setdefault(current,{"data": {}})
            entry["status"] = "incomplete"
    except Exception as exc:
        ctx.report["status"] = "failed"
        ctx.report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        if current is not None:
            entry = ctx.report["experiments"].setdefault(current,{"data": {}})
            entry["status"] = "failed"
    ctx.flush()
    print(json.dumps({"status": ctx.report["status"], "profile": args.profile,
                      "stages": {k:v["status"] for k,v in ctx.report["experiments"].items()},
                      "elapsed_seconds": ctx.report["elapsed_seconds"], "output": str(args.output)}, sort_keys=True))
    return {"complete":0,"failed":1,"incomplete":2}[ctx.report["status"]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--driver", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-dir",type=Path)
    parser.add_argument("--openssl-version",default="unspecified")
    parser.add_argument("--profile", choices=("smoke","full"), default="smoke")
    parser.add_argument("--stages", default="")
    parser.add_argument("--budget-seconds", type=float)
    parser.add_argument("--compiler-id", default="unspecified")
    parser.add_argument("--compiler-version", default="unspecified")
    parser.add_argument("--config", default="unspecified")
    args = parser.parse_args()
    if args.budget_seconds is None:
        args.budget_seconds = 120 if args.profile == "smoke" else 1200
    if not 0 <= args.budget_seconds <= 1200:
        parser.error("budget must be 0..1200 seconds; no automatic extension")
    raise SystemExit(run(args))
