# BMKG Acceptance Test — LAWS V2

## 1. Installation Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| INS-01 | Binary existence | `ls -la /opt/pimes/laws/predict_cli.py` | File exists |
| INS-02 | Python venv | `source venv/bin/activate; python --version` | >= 3.11 |
| INS-03 | Dependencies | `pip list \| grep <req>` | All packages |
| INS-04 | DB connection | `psql -U bmkg -d pimes -c "SELECT 1;"` | Returns 1 |

## 2. Startup Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| STT-01 | Dashboard service | `systemctl start pocc-dashboard` | Started |
| STT-02 | Collector service | `systemctl start pocc-collector` | Started |
| STT-03 | Backend API | `curl http://localhost:8500/api/health` | `{"status":"OK"}` |
| STT-04 | Scheduler | `ps -ef \| grep scheduler` | PID exists |

## 3. Recovery Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| REC-01 | Service crash | Kill dashboard PID | Auto-restart within 10s |
| REC-02 | DB restart | `systemctl restart postgresql` | Services reconnect |
| REC-03 | Full restart | `reboot; wait 120s` | All services active |

## 4. Data Collection Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| DAT-01 | New data arrival | Check trigger file creation | New trigger within 5 min |
| DAT-02 | Validation | Check collector.log | No CRC32 errors |
| DAT-03 | Storage | `df -h /opt/pimes` | Usage < 80% |

## 5. Prediction Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| PRD-01 | Predictor status | `curl /api/predictor` | `"status":"loaded"` |
| PRD-02 | Prediction output | `curl /api/overview` | `"prediction":"ACTIVE"` |
| PRD-03 | DB recording | PG query `SELECT count(*) FROM predictions` | Count increasing |

## 6. Logging Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| LOG-01 | Collector log | `ls -la /opt/pimes/pocc/collector/collector.log` | Growing |
| LOG-02 | Dashboard log | `ls -la /opt/pimes/pocc/backend/dashboard.log` | Growing |
| LOG-03 | Log rotation | Trigger logrotate | Files compressed |

## 7. Alert Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| ALR-01 | Advisory alert | P=0.40 event | Non-Warning alert fired |
| ALR-02 | Warning alert | P=0.70 event | Warning alert fired |
| ALR-03 | Storm suppression | Kp>4 sampled data | Alert suppressed |

## 8. Backup/Restore Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| BKP-01 | DB backup | `pg_dump pimes > test.sql` | File created |
| BKP-02 | DB restore | Restore to test DB | 0 errors |
| BKP-03 | Config backup | `tar czf config.tar.gz /opt/pimes/pocc/` | File created |

## 9. Monitoring Verification
| ID | Test | Method | Expected |
|---|---|---|---|
| MON-01 | Health endpoint | `curl /api/health` | OK |
| MON-02 | Overview endpoint | `curl /api/overview` | Complete response |
| MON-03 | Predictor endpoint | `curl /api/predictor` | Complete response |
