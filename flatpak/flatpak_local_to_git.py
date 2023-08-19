import functools
import re
import subprocess
import sys
from pathlib import Path

# noinspection RegExpRepeatedSpace
yaml_pattern = re.compile(
    r"""    sources:
      - type: dir
        path: "\.\."
""",
    re.MULTILINE,
)


def process_file(path: Path):
    orig = path.read_text()

    def repl(template, _match):
        git_commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        try:
            git_tag = (
                subprocess.check_output(["git", "describe", "--tags", "--exact-match", "--dirty"])
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError:
            print("ERROR: No git tag found, did you forget to tag the commit?", file=sys.stderr)
            raise

        if "dirty" in git_tag:
            print("WARNING: Git is dirty, please commit your changes first", file=sys.stderr)

        return template.format(git_tag=git_tag, git_commit_hash=git_commit_hash)

    if path.name.endswith(".yaml") or path.name.endswith(".yml"):
        pattern = yaml_pattern
        repl = functools.partial(
            repl,
            """    sources:
      - type: git
        tag: "{git_tag}"
        commit: "{git_commit_hash}"
""",
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
