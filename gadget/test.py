import os
from pathlib import Path

p = Path(".")
for a in p.glob("*"):
    print(a)
    print(str(a))