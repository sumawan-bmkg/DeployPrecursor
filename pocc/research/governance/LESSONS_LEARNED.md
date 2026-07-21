# Lessons Learned — LAWS V2

## Format
Each lesson: Context → Event → Impact → Lesson → Action

---

## L-001 | CRC32 Module Confusion
- **Context**: Developing validation worker
- **Event**: Used `hashlib.crc32()` instead of `zlib.crc32()`
- **Impact**: Critical production blocker for 3+ days
- **Lesson**: Always verify stdlib module location. CRC32 lives in `zlib`, not `hashlib`. Python stdlib module names can be counterintuitive.
- **Action**: Added to coding standards checklist. Unit test for CRC32 call added.

## L-002 | Hardcoded Dashboard Label
- **Context**: Dashboard API overview endpoint
- **Event**: `"prediction": "MOCK"` hardcoded, never updated
- **Impact**: ORR false negative on predictor status (CF-01)
- **Lesson**: Hardcoded status strings create misleading operational dashboards. Use dynamic checks.
- **Action**: Replaced with `Path.exists()` check. Consider state machine for all status fields.

## L-003 | SCP Password Prompt Hangs
- **Context**: Deploying fixes to Ubuntu from Windows
- **Event**: SCP command waited for password input, blocking deployment
- **Impact**: Deployment delayed, had to switch to paramiko SFTP
- **Lesson**: Windows PowerShell SSH/SCP doesn't support password input via stdin. Use paramiko for scripted deployments.
- **Action**: Created paramiko-based deploy scripts as standard deployment method.

## L-004 | Unicode in Production Logs
- **Context**: Writing logs with Unicode characters (arrows, special symbols)
- **Event**: cp1252 encoding on Windows crashed stdout
- **Impact**: Log display failed, debugging impaired
- **Lesson**: Always use ASCII-safe characters in production log output. Set `PYTHONIOENCODING=utf-8`.
- **Action**: Encoding added to environment setup.

## L-005 | ORR Initial Score Too Aggressive
- **Context**: Initial ORR scoring based on incomplete evidence
- **Event**: Assigned numeric scores (41/100) without verifying if system was production vs staging
- **Impact**: User correctly challenged scoring methodology
- **Lesson**: ORR must verify which environment is being evaluated. Don't score what you haven't verified.
- **Action**: Revised to evidence-based scoring with environment verification.

## L-006 | Dashboard Restart Counter Accumulation
- **Context**: Long-running production system
- **Event**: systemd restart counter reached 7524 across all restarts
- **Impact**: Misleading metric — not all restarts were incidents
- **Lesson**: Track uptime since last restart, not total restart count. Reset counter on planned maintenance.
- **Action**: Add `systemd-analyze` to burn-in monitoring.
