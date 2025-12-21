import pandas as pd
import os
import sys

# Relative import used to access the config reader utility
from ..utils.common import read_config


class DataTransformation:
    def __init__(self, config_path="config/config.yaml"):
        """
        Initializes the DataTransformation component by loading configuration
        and setting up file paths.
        """
        # Read the configuration file
        self.config = read_config(config_path)

        # Determine the project root directory safely
        # We go up 3 levels from: src/components/data_transformation.py
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Define directory paths from config
        self.raw_data_dir = os.path.join(self.base_dir, self.config['paths']['raw_data'])
        self.processed_data_dir = os.path.join(self.base_dir, self.config['paths']['processed_data'])

        # Load preprocessing parameters from config
        self.chunk_size = self.config['preprocessing']['chunk_size']
        self.start_date = self.config['preprocessing']['start_date']

    def initiate_data_transformation(self):
        """
        Reads large datasets in chunks, filters based on date, and saves the optimized file.
        Returns:
            str: Path to the processed output file.
        """
        try:
            # Define input and output file paths
            input_file = os.path.join(self.raw_data_dir, self.config['files']['transactions'])
            output_file = os.path.join(self.processed_data_dir, 'transactions_optimized.csv')

            # Check and create the processed data directory if it doesn't exist
            if not os.path.exists(self.processed_data_dir):
                os.makedirs(self.processed_data_dir)
                print(f"Directory created: {self.processed_data_dir}")

            # Remove existing output file to avoid appending to old data
            if os.path.exists(output_file):
                os.remove(output_file)

            print(f"The process begins...")
            print(f"Source: {input_file}")
            print(f"Target: {output_file}")
            print(f"Filter: Data after {self.start_date}")

            first_chunk = True
            total_rows = 0

            # Process data in chunks to handle memory efficiently
            for chunk in pd.read_csv(input_file, chunksize=self.chunk_size):

                # Convert date column to datetime object
                chunk['t_dat'] = pd.to_datetime(chunk['t_dat'])

                # Filter data based on the start date
                filtered_chunk = chunk[chunk['t_dat'] >= self.start_date]

                if not filtered_chunk.empty:
                    # Determine write mode: 'w' for the first chunk, 'a' (append) for the rest
                    mode = 'w' if first_chunk else 'a'
                    header = first_chunk

                    # Save the chunk
                    filtered_chunk.to_csv(output_file, mode=mode, header=header, index=False)

                    total_rows += len(filtered_chunk)
                    first_chunk = False
                    print(f". {len(filtered_chunk)} rows processed and added.")

            print("-" * 30)
            print(f"DONE! Total {total_rows} rows filtered and saved.")
            return output_file

        except Exception as e:
            print(f"ERROR: An error occurred during data transformation: {e}")
            raise e


if __name__ == "__main__":
    # Test execution
    try:
        transformer = DataTransformation()
        transformer.initiate_data_transformation()
    except Exception as e:
        print(e)