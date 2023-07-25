# NOTE: This file is *not* substituted with cookiecutter...

PROJECT_DIR := "{{cookiecutter.project_slug}}"

build: convert-config && check-format

# Check for formatting errors
check-format: && (format "--check")
    # Checking formatting!

TOML_FILES := replace(`python3 ./build_helper.py find-glob "**/*.toml"`, "\n", " ")
OUR_PYTHON_FILES := replace(`python3 build_helper.py find-glob --exclude '{{cookiecutter.project_slug}}/**' '**/*.py'`, "\n", " ")

convert-config *flags:
    # Convert the config file from TOML to JSON
    python3 build_helper.py convert-config-file {{ flags }}

format *flags:
    # Formatting toml files with taplo
    @echo "Running 'taplo format {{ flags }} -- "{{ TOML_FILES }}"'"
    @RUST_LOG=warning taplo format {{ flags }} -- "{{ TOML_FILES }}"
    # Formatting Justfiles
    @python3 ./build_helper.py format-justfile {{ flags }} -- 'Justfile' '{{ PROJECT_DIR }}/Justfile'
    # Formatting the template project
    just '{{ PROJECT_DIR }}/format' {{ flags }}
    # Format our python scripts
    isort --profile=black {{ flags }} -- {{ OUR_PYTHON_FILES }}
    black {{ flags }} -- {{ OUR_PYTHON_FILES }}
