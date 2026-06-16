
import os
import sys
import numpy as np
import logging

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from signal_processing import GeomagneticSignalProcessor
except ImportError:
    logging.error("Could not import GeomagneticSignalProcessor from src.signal_processing")
    sys.exit(1)

logger = logging.getLogger(__name__)

class Preprocessor:
    """
    Wraps GeomagneticSignalProcessor for pipeline usage.
    """
    def __init__(self, sampling_rate=1.0):
        self.processor = GeomagneticSignalProcessor(sampling_rate=sampling_rate)
        logger.info("Preprocessor initialized.")

    def preprocess(self, h_raw, d_raw, z_raw):
        """
        Applies PC3 bandpass filtering and returns processed components.
        
        Returns:
            dict: { 'h_pc3', 'd_pc3', 'z_pc3', 'zh_ratio_pc3', ... }
        """
        # Ensure data is handled (replace NaNs if needed)
        h = np.nan_to_num(h_raw, nan=0.0)
        d = np.nan_to_num(d_raw, nan=0.0)
        z = np.nan_to_num(z_raw, nan=0.0)
        
        # Process components using existing processor
        processed_data = self.processor.process_components(h, d, z, apply_pc3=True)
        return processed_data

if __name__ == '__main__':
    # Simple test
    logging.basicConfig(level=logging.INFO)
    prep = Preprocessor()
    h_test = np.random.rand(86400) * 100
    d_test = np.random.rand(86400) * 100
    z_test = np.random.rand(86400) * 100
    
    result = prep.preprocess(h_test, d_test, z_test)
    print(f"Preprocessing test successful. Keys: {result.keys()}")
