
import argparse
import logging
import os
import sys
from datetime import datetime
import json
import numpy as np
import torch

# Add necessary paths for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dataset_scalogram', 'src')))


# --- Import custom modules ---
# SCN Parser
try:
    from scn_parser import SCNParser
except ImportError:
    logging.error("Failed to import SCNParser. Ensure scn_parser.py is in the correct path.")
    sys.exit(1)

# Preprocessor
try:
    from preprocessing import Preprocessor
except ImportError:
    logging.error("Failed to import Preprocessor. Ensure preprocessing.py is in the correct path.")
    sys.exit(1)

# Tensor Builder
try:
    from tensor_builder import TensorBuilder
except ImportError:
    logging.error("Failed to import TensorBuilder. Ensure tensor_builder.py is in the correct path.")
    sys.exit(1)

# Inference Service
# Using the content obtained from the earlier checkpoint directly as a class
class InferenceService:
    def __init__(self, model_path, device='cpu'):
        self.device = device
        self.model = torch.load(model_path, map_location=device)
        self.model.eval()
        logging.info(f"Model loaded from {model_path}")

    def predict(self, tensor):
        """
        Run inference on (3, 128, 1440) tensor.
        Returns: {probability, alert, magnitude, azimuth}
        """
        if not isinstance(tensor, torch.Tensor):
            tensor = torch.from_numpy(tensor).float()
        
        if len(tensor.shape) == 3:
            tensor = tensor.unsqueeze(0) # Add batch dim
            
        tensor = tensor.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(tensor)
            # Assuming model returns (prob, magnitude, azimuth) or similar
            # Logic here depends on actual model head
            prob = torch.sigmoid(outputs[0]).item()
            alert = prob > 0.5
            
            # Placeholder for regression outputs
            mag = outputs[1].item() if len(outputs) > 1 else 0.0
            azi = outputs[2].item() if len(outputs) > 2 else 0.0
            
        return {
            'probability': prob,
            'alert': alert,
            'magnitude': mag,
            'azimuth': azi
        }


# --- PostgreSQL Setup (Placeholder) ---
# In a production environment, use proper configuration management (e.g., environment variables, a config file)
# and a connection pool.
class PostgreSQLSaver:
    def __init__(self, db_config=None):
        # Dummy config for now
        self.db_config = db_config or {
            "host": "localhost",
            "database": "pimes_db",
            "user": "pimes_user",
            "password": "pimes_password",
        }
        logging.info("PostgreSQLSaver initialized (using dummy config).")

    def save_prediction(self, station, date, prediction_results):
        # In a real scenario, this would connect to PostgreSQL and insert data.
        # For now, it just logs the intent.
        try:
            # import psycopg2
            # conn = psycopg2.connect(**self.db_config)
            # cur = conn.cursor()
            # cur.execute("""
            #     INSERT INTO predictions (station, date, probability, alert, magnitude, azimuth, created_at)
            #     VALUES (%s, %s, %s, %s, %s, %s, %s)
            # """, (
            #     station,
            #     date.strftime('%Y-%m-%d'),
            #     prediction_results['probability'],
            #     prediction_results['alert'],
            #     prediction_results['magnitude'],
            #     prediction_results['azimuth'],
            #     datetime.now()
            # ))
            # conn.commit()
            # cur.close()
            # conn.close()
            logging.info(f"[DB SAVE - MOCKED]: Prediction for {station} on {date.strftime('%Y-%m-%d')}: "
                         f"{json.dumps(prediction_results)}")
            return True
        except Exception as e:
            logging.error(f"Failed to save prediction to DB: {e}", exc_info=True)
            return False

# --- Main Inference Runner Logic ---
def main():
    parser = argparse.ArgumentParser(description="Run earthquake precursor inference.")
    parser.add_argument(
        "--station", type=str, required=True, help="Station code (e.g., SCN)"
    )
    parser.add_argument(
        "--date", type=str, required=True, help="Date in YYYY-MM-DD format (e.g., 2026-06-11)"
    )
    parser.add_argument(
        "--model-path", 
        type=str,
        default="D:\\multi\\scalogramv3\\checkpoints\\v3_v8_conv_fpr_best_weights.pth", # Use discovered path
        help="Path to the trained model checkpoint (.pth)"
    )
    parser.add_argument(
        "--raw-data-path-prefix",
        type=str,
        default="D:\\multi\\data\\raw", # Assuming a raw data folder
        help="Prefix path to raw SCN.gz files. E.g., /opt/pimes/data/raw/"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )
    
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()), 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("InferenceRunner")

    logger.info(f"Starting inference for station {args.station} on {args.date}")

    try:
        # 1. Parse SCN file
        file_date = datetime.strptime(args.date, '%Y-%m-%d')
        yy = file_date.strftime('%y')
        mm = file_date.strftime('%m')
        dd = file_date.strftime('%d')
        
        scn_filepath = os.path.join(
            args.raw_data_path_prefix,
            args.station,
            f"S{yy}{mm}{dd}.{args.station}.gz"
        )
        
        parser = SCNParser()
        raw_data = parser.parse_scn_file(scn_filepath, args.station)
        
        if raw_data is None:
            logger.error(f"Failed to parse SCN file: {scn_filepath}")
            print(json.dumps({"status": "error", "message": "Failed to parse SCN file"}))
            sys.exit(1)

        h_raw, d_raw, z_raw = raw_data['H'], raw_data['D'], raw_data['Z']
        logger.info("SCN file parsed successfully.")

        # 2. Preprocess data
        preprocessor = Preprocessor()
        processed_data = preprocessor.preprocess(h_raw, d_raw, z_raw)
        
        # Use PC3 filtered data for tensor generation
        h_pc3 = processed_data['h_pc3']
        d_pc3 = processed_data['d_pc3']
        z_pc3 = processed_data['z_pc3']
        logger.info("Data preprocessed successfully (PC3 filtered). ")

        # 3. Build tensor
        tensor_builder = TensorBuilder()
        input_tensor = tensor_builder.build(h_pc3, d_pc3, z_pc3)
        
        if input_tensor.shape != (3, 128, 1440):
            logger.error(f"Unexpected tensor shape: {input_tensor.shape}. Expected (3, 128, 1440).")
            print(json.dumps({"status": "error", "message": "Unexpected tensor shape"}))
            sys.exit(1)

        logger.info(f"Tensor built successfully with shape {input_tensor.shape}.")

        # 4. Run inference
        inference_service = InferenceService(args.model_path)
        prediction_results = inference_service.predict(input_tensor)
        logger.info(f"Inference completed. Results: {prediction_results}")

        # 5. Save results to PostgreSQL (mocked for now)
        db_saver = PostgreSQLSaver()
        db_saver.save_prediction(args.station, file_date, prediction_results)

        # Output results as JSON
        output = {
            "status": "success",
            "station": args.station,
            "date": args.date,
            "probability": prediction_results['probability'],
            "alert": prediction_results['alert'],
            "magnitude": prediction_results['magnitude'],
            "azimuth": prediction_results['azimuth'],
        }
        print(json.dumps(output, indent=2))

    except Exception as e:
        logger.critical(f"An unhandled error occurred: {e}", exc_info=True)
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
