# -*- coding: utf-8 -*-
import sys
from datetime import datetime
from pathlib import Path

Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)
Path(sys.argv[1]).write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
