#!/usr/bin/env bash
# Pre-commit quality gate: syntax-check Pinokio launcher scripts and app Python. Exit 2 blocks the commit.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 2
fail=0
for f in *.js; do node --check "$f" 2>&1 || fail=1; done
py=python
[ -x app/env/Scripts/python.exe ] && py=app/env/Scripts/python.exe
for f in app/*.py app/ultratex_gui/*.py app/tools/*.py; do
  "$py" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read(), sys.argv[1])" "$f" 2>&1 || fail=1
done
if [ $fail -ne 0 ]; then echo "Pre-commit check failed: fix the syntax errors above before committing." >&2; exit 2; fi
exit 0
