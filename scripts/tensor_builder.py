
import os
import sys
import numpy as np
import logging

# Path to tensor_generator module
TENSOR_GEN_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dataset_scalogram', 'src'))
sys.path.insert(0, TENSOR_GEN_PATH)

try:
    from tensor_generator import TensorGenerator
except ImportError:
    logging.error(f"Could not import TensorGenerator from {TENSOR_GEN_PATH}")
    sys.exit(1)

logger = logging.getLogger(__name__)

class TensorBuilder:
    """
    Wraps TensorGenerator to produce (3, 128, 1440) input tensor.
    """
    def __init__(self):
        self.generator = TensorGenerator()
        logger.info("TensorBuilder initialized.")

    def build(self, h_processed, d_processed, z_processed):
        """
        Builds the input tensor from processed components.
        Output shape: (3, 128, 1440)
        """
        # Ensure array shape (86400,)
        tensor = self.generator.build_tensor(h_processed, d_processed, z_processed)
        return tensor.astype(np.float32)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    builder = TensorBuilder()
    
    h_data = np.random.rand(86400)
    d_data = np.random.rand(86400)
    z_data = np.random.rand(86400)
    
    tensor = builder.build(h_data, d_data, z_data)
    print(f"Tensor shape: {tensor.shape}")
