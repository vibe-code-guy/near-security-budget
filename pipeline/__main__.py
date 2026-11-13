"""Entry point: python -m pipeline <command>. The Makefile is a thin wrapper around this."""
import sys


def main(argv: list) -> int:
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "data":
        from . import fetch
        fetch.main(argv[2] if len(argv) > 2 else "all")
    elif cmd == "bounties-template":
        from . import universe
        print("written" if universe.write_bounty_template() else "data/bounties.csv exists; left alone")
    elif cmd == "build":
        from . import build
        build.main()
    else:
        print("usage: python -m pipeline [data [defillama|near] | bounties-template | build]")
        return 2 if cmd != "help" else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
