import sys
from subprocess import check_call


def fatal(msg: str):
    print(msg, file=sys.stderr)
    exit(1)


def main():
    print("Installing lefthook hooks...")
    check_call(["lefthook", "install"])
    print()
    print("Remember to:")
    print(" - Add a license file for {{ cookiecutter.license }}")


if __name__ == "__main__":
    main()
