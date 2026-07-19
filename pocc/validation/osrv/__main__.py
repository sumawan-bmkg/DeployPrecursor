"""
OSRV Framework — Operational Scientific Release Validation
Single command entry point.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from validation.osrv.runner import main
main()
