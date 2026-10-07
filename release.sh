#!/usr/bin/env bash
#
# Increase the package version, commit the change and create the release tag.
#
set -euo pipefail

PROG="$(basename "$0")"

usage() {
    cat <<EOF
Usage: $PROG <version> [--push]

Increase the package version to <version>, commit the change and create an
annotated git tag named <version>.

Arguments:
  <version>   New version in x.y.z form (e.g. 2.0.3)
  --push, -p  Also push the commit and the tag to 'origin'

Examples:
  $PROG 2.0.3
  $PROG 2.0.3 --push
EOF
    exit 1
}

PUSH=0
VERSION=""
for arg in "$@"; do
    case "$arg" in
        --push|-p) PUSH=1 ;;
        -h|--help) usage ;;
        -*) echo "Unknown option: $arg" >&2; usage ;;
        *) if [ -n "$VERSION" ]; then usage; fi; VERSION="$arg" ;;
    esac
done

[ -n "$VERSION" ] || usage

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: version must be in x.y.z form (got '$VERSION')." >&2
    exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
    echo "Error: tag '$VERSION' already exists." >&2
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: working tree has other uncommitted changes; only the version files will be committed." >&2
fi

echo "Setting version to $VERSION"

echo $VERSION > VERSION
git commit -a -m "Release v$VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION"

echo "Created tag $VERSION"

if [ "$PUSH" -eq 1 ]; then
    git push origin HEAD
    git push origin "v$VERSION"
    echo "Pushed commit and tag v$VERSION to origin"
else
    echo "Run 'git push origin HEAD && git push origin v$VERSION' to publish the release."
fi
