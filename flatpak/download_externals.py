import functools
import re
import subprocess
import sys
from pathlib import Path

# noinspection RegExpRepeatedSpace
json_pattern = re.compile(
    """\{
            "type": "file",
            "url": "([^"]*)",
            "sha256": "([^"]*)"
        }""",
    re.MULTILINE,
)

# noinspection RegExpRepeatedSpace
yaml_pattern = re.compile(
    """      - type: file
        url: "([^"]*)"
        sha256: "([^"]*)\"""",
    re.MULTILINE,
)


def process_file(path: Path):
    orig = path.read_text()

    def repl(template, match):
        url = match.group(1)
        sha256 = match.group(2)
        filename = url.rpartition("/")[2]
        ext_file = Path(path.parent) / "externals" / filename
        if not ext_file.exists():
            print(f"Downloading {url}...")
            ext_file.parent.mkdir(parents=True, exist_ok=True)
            subprocess.call(["curl", "-L", "-o", str(ext_file), url])
            actual_sha256 = subprocess.check_output(["sha256sum", str(ext_file)]).decode()[:64]

            if actual_sha256 != sha256:
                raise Exception(
                    f"SHA256 mismatch for {url}\nExpected {sha256}, got {actual_sha256}"
                )
        else:
            print(f"Using cached {url}...")
        return template.format(filename)

    if path.name.endswith(".json"):
        pattern = json_pattern
        repl = functools.partial(
            repl,
            '{{\n            "type": "file",\n            "path": "externals/{}"\n        }}',
        )
    elif path.name.endswith(".yaml") or path.name.endswith(".yml"):
        pattern = yaml_pattern
        repl = functools.partial(
            repl,
            '      - type: file\n        path: "externals/{}"',
        )
    else:
        return

    new = re.sub(pattern, repl, orig)
    path.write_text(new)


def main():
    for path in sys.argv[1:]:
        process_file(Path(path))


if __name__ == "__main__":
    main()
