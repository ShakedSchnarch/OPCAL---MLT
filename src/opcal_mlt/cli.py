def dev_main():
    import argparse, json, sys
    from pathlib import Path as _P

    parser = argparse.ArgumentParser(prog="opcal-mlt-dev", description="Developer CLI for OPCAL-MLT")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info")

    p = sub.add_parser("start-session")
    p.add_argument("--input", required=True)
    p.add_argument("--out", default="session.json")

    args = parser.parse_args()

    if args.cmd == "info":
        print(json.dumps({"package":"opcal-mlt","python":sys.version.split()[0]}, indent=2))
        return

    if args.cmd == "start-session":
        _P(args.out).write_text(json.dumps({
            "params":{"input":str(_P(args.input).resolve())},
            "labels":{}
        }, indent=2))
        print(f"Wrote session to {args.out}")
