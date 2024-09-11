import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent

env = os.environ.copy()
env["PYTHONPATH"] = BASE_DIR
