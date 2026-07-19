import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Check TemplateResponse signature
_, o, _ = c.exec_command('''/opt/pimes/laws/runtime/.venv/bin/python3 << 'EOF'
import inspect
from starlette.templating import Jinja2Templates
print(inspect.signature(Jinja2Templates.TemplateResponse))
EOF''')
print(o.read().decode()[:500])

# Also test direct import
_, o, _ = c.exec_command('''/opt/pimes/laws/runtime/.venv/bin/python3 << 'EOF'
from starlette.templating import Jinja2Templates
print(type(Jinja2Templates))
EOF''')
print(o.read().decode()[:200])

c.close()
