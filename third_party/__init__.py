"""
third_party: holds external git submodules.
We automatically push each submodule root onto sys.path
so its packages (e.g. `music2emo`) are importable project-wide.
"""
import sys, pathlib, importlib.util

HERE = pathlib.Path(__file__).parent

for sub in HERE.iterdir():
    if sub.is_dir() and any(p.suffix == ".py" for p in sub.rglob("*.py")):
        if str(sub) not in sys.path:
            sys.path.append(str(sub))
