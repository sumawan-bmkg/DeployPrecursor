"""SEOS entry point.

Usage: python -m validation.seos
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from validation.seos.run import run
run()
