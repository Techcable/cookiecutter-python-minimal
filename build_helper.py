from __future__ import annotations

import dataclasses as dc
import json
import sys
from collections.abc import Collection, Iterator
from pathlib import Path
from subprocess import CalledProcessError, check_call
from typing import NoReturn

try:
    import tomllib
except:
    import tomli as tomllib

COMMAND_INVOKE_START = f"python ./{Path(__file__).name}"


def fatal(msg: str, *, recommend_help: bool = False) -> NoReturn:
    print(msg, file=sys.stderr)
    if recommend_help:
        print(f"Run `{COMMAND_INVOKE_START} help` for more details.", file=sys.stderr)
    exit(1)


SRC_CONFIG = Path("cookiecutter.toml")
GENERATED_WARNING_HEADER = {
    "_WARNING": f"THIS FILE HAS BEEN AUTOMATICALLY GENERATED FROM `{SRC_CONFIG}`. DO NOT MODIFY!!"
}
GENERATED_CONFIG_FILE = Path("cookiecutter.json")


def convert_config_file(*, check: bool = False):
    with open(SRC_CONFIG, "rb") as orig_file:
        toml_data = tomllib.load(orig_file)

    assert isinstance(toml_data, dict), type(toml_data)
    root_keys = set(toml_data.keys())
    if root_keys != {"cookiecutter"}:
        fatal(
            f"The config file `{SRC_CONFIG}` should only have one top level entry (cookiecutter), but instead got {root_keys!r}"
        )
    # Now convert to json (NOTE: The warning header must come first in the `|` to come first in the ordering of the dict)
    json_data = GENERATED_WARNING_HEADER | toml_data["cookiecutter"]
    expected_json_data = json.dumps(json_data, indent=2)
    if check:
        actual_json_data = GENERATED_CONFIG_FILE.read_text()
        if expected_json_data != actual_json_data:
            fatal(f"Generated config `{GENERATED_CONFIG_FILE}` is out of date.")
    else:
        GENERATED_CONFIG_FILE.write_text(expected_json_data)


def find_glob(pattern: str, *, exclude_globs: Collection[str] = ()) -> None:
    for res in Path(".").glob(pattern):
        should_exclude = any(res.match(ex) for ex in exclude_globs)
        if not should_exclude:
            print(res)


def format_justfile(targets: list[str], *, check: bool = False) -> None:
    # Keep this warning as long as it requires an --unstable flags
    print("**WARNING**: Justfile formating is currently unstable", file=sys.stderr)
    command_flags = ["--unstable"]
    if check:
        command_flags.append("--check")
    command_flags.append("--fmt")
    for target in map(Path, targets):
        if not target.is_file():
            fatal(f"File does not exist: {target}")
        print("Running", "just", " ".join(command_flags), "-f", repr(str(target)))
        try:
            check_call(["just", *command_flags, "-f", target])
        except CalledProcessError as e:
            fatal(f"Formatting {target.name!r} failed with exit code {e.returncode}")


@dc.dataclass
class FlagHelp:
    usage: str
    desc: str


@dc.dataclass
class SubcommandHelp:
    usage: str
    desc: str
    flags: tuple[FlagHelp, ...] = ()


SUBCOMMAND_HELP = {
    "help": SubcommandHelp("help", "Shows this help message"),
    "find-glob": SubcommandHelp(
        "find-glob [flags] <pattern>",
        "Finds all paths matching the specified glob pattern",
        flags=(
            FlagHelp(
                "--exclude <pattern>", "Specifies a glob pattern of paths to exclude"
            ),
        ),
    ),
    "format-justfile": SubcommandHelp(
        "format-justfile [flags] <targets+>",
        "Formats the specified justfiles",
        flags=(
            FlagHelp(
                "--check", "Check for formatting issues without modifying the source."
            ),
        ),
    ),
    "convert-config-file": SubcommandHelp(
        "convert-config-file [flags]",
        "Converts the main config (cookiecutter.toml) into JSON that cookiecutter understands",
        flags=(FlagHelp("--check", "Checks that the generated file is up to date"),),
    ),
}
HELP_DESC_INDENT = 60
SPACE = " "


def print_generic_help() -> NoReturn:
    print(f"Usage: {COMMAND_INVOKE_START} <subcommand> ")
    print()
    print("Available subcommands:")
    for idx, subcommand in enumerate(SUBCOMMAND_HELP.values()):
        if idx != 0:
            print()
        print(
            f"{SPACE * 2}{subcommand.usage: <{HELP_DESC_INDENT - 2}}",
            subcommand.desc,
            sep="",
        )
        for flag in subcommand.flags:
            print(
                f"{SPACE * 4}{flag.usage: <{HELP_DESC_INDENT - 4}}", flag.desc, sep=""
            )
    exit(0)


def parse_flags(
    args: list[str], *, valid: Collection[str], has_value: Collection[str] = ()
) -> Iterator[str | tuple[str, str]]:
    valid = set(valid)
    has_value = set(has_value)
    assert all(
        flag.startswith("-") for flag in valid
    ), f"All flags must start with `-` {valid=}"
    assert has_value <= valid, f"{has_value=} must be subset of {valid=}"
    while args and args[0].startswith("-"):
        flag = args.pop(0)
        if flag == "--":
            break
        elif flag in valid:
            if flag in has_value:
                if args:
                    flag_value = args.pop(0)
                    yield flag, flag_value
                else:
                    fatal(f"Expected a value for flag {flag!r}")
            else:
                yield flag
        else:
            fatal(f"Unsupported flag: {flag!r}")


def helper(args: list[str]) -> None:
    """Runs various helper commands in a cross-platform manner"""
    for flag in parse_flags(args, valid={"--help"}):
        assert flag == "--help", flag  # Only one valid flag
        print_generic_help()

    subcommand_name = args.pop(0) if args else None

    match subcommand_name:
        case None | "help":
            print_generic_help()
        case "find-glob":
            exclude_globs = list()
            for flag in parse_flags(args, valid={"--exclude"}, has_value={"--exclude"}):
                match flag:
                    case ("--exclude", exclude_pattern):
                        exclude_globs.append(exclude_pattern)
                    case _:
                        raise AssertionError(f"Bad flag {flag=}")
            match args:
                case [str(pattern)]:
                    find_glob(pattern, exclude_globs=exclude_globs)
                case _:
                    fatal(
                        "The `find-glob` command expects exactly one argument: The pattern to use.",
                        recommend_help=True,
                    )
        case "format-justfile":
            check = False
            for flag in parse_flags(args, valid={"--check"}):
                assert flag == "--check", f"Unexpected flag {flag=}"
                if check:
                    fatal("Already specified `--check` flag.")
                check = True
            if not args:
                fatal("Must specify at least one file to format.")
            format_justfile(args[:], check=check)
        case "convert-config-file":
            check = False
            for flag in parse_flags(args, valid={"--check"}):
                assert flag == "--check", f"Unexpected flag {flag=}"
                if check:
                    fatal("Already specified `--check` flag.")
                check = True
            if args:
                fatal("This command takes no positional args")
            convert_config_file(check=check)
        case other:
            fatal(f"Unexpected subcommand {other!r}", recommend_help=True)


if __name__ == "__main__":
    helper(sys.argv[1:])
