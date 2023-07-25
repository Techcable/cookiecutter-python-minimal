import re
import shutil
import sys
from pathlib import Path
from subprocess import check_call

# NOTE: No spaces permitted in {{cookiecutter.project_name}}
VALID_NAME_PATTERN = re.compile("[-_\w]+")
VALID_SLUG_PATTERN = re.compile("\w+")


def fatal(msg: str):
    print(msg, file=sys.stderr)
    exit(1)


REQUIRED_COMMANDS = (
    "lefthook",
    "python3",
    "just",
    "pytest",
    "mypy",
    "black",
    "isort",
)


def main():
    if (
        VALID_NAME_PATTERN.fullmatch(project_name := "{{ cookiecutter.project_name }}")
        is None
    ):
        fatal(f"Invalid project name {project_name!r} (Does it contain spaces?)")
    if (
        VALID_NAME_PATTERN.fullmatch(project_slug := "{{ cookiecutter.project_slug }}")
        is None
    ):
        fatal(
            f"Invalid project slug {project_slug!r}, must be a valid python identifier."
        )
    # Check for required commands
    for requirement in REQUIRED_COMMANDS:
        if not shutil.which("lefthook"):
            fatal(f"Missing required command: {requirement!r}. Please install it!!")

    match "{{ cookiecutter.init_git }}".lower():
        case "true":
            if Path(".git").is_dir():
                fatal("Git repository already initialized!")
            else:
                print("Initializing git repository...")
                check_call(["git", "init"])
        case "false":
            if Path(".git").is_dir():
                pass
            else:
                fatal("Git repository not found and automatic init is disabled")
        case text:
            raise AssertionError(f"Unexpected value for init_git {text=}")


if __name__ == "__main__":
    main()
