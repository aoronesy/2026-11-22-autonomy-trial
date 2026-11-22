import importlib
import pkgutil
import sys

from tcli import commands


def available_commands():
    """tcli/commands/ のモジュール名をコマンド名として返す（中央の登録表は持たない）。"""
    return sorted(m.name for m in pkgutil.iter_modules(commands.__path__) if not m.name.startswith("_"))


def usage():
    lines = ["usage: python -m tcli <command> [args...]", "", "commands:"]
    for name in available_commands():
        module = importlib.import_module(f"tcli.commands.{name}")
        lines.append(f"  {name:<10} {getattr(module, 'HELP', '')}")
    return "\n".join(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(usage())
        return 0 if argv else 2
    name, args = argv[0], argv[1:]
    if name not in available_commands():
        print(f"unknown command: {name}", file=sys.stderr)
        print(usage(), file=sys.stderr)
        return 2
    module = importlib.import_module(f"tcli.commands.{name}")
    return module.run(args)


if __name__ == "__main__":
    sys.exit(main())
