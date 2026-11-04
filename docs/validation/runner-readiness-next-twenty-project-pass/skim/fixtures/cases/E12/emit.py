from pathlib import Path
import sys
sys.stdout.buffer.write(Path("items.txt").read_bytes())
