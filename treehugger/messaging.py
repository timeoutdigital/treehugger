import sys


def die(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)
