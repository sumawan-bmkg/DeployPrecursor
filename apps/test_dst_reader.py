#!/usr/bin/env python3

import re
import requests

URL = (
    "https://wdc.kugi.kyoto-u.ac.jp/"
    "dst_realtime/presentmonth/index.html"
)

html = requests.get(
    URL,
    timeout=60
).text

m = re.search(
    r"\n16\s+([-\d]+)\s+([-\d]+)",
    html
)

print(m.groups())
