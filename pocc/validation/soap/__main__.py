"""SOAP — Scientific Operational Accreditation Platform.

Usage: python -m validation.soap
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from validation.soap.runner import run
run()
