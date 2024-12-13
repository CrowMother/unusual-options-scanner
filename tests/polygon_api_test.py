import os
import sys

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))  # Path to this script
project_root = os.path.abspath(os.path.join(current_dir, ".."))  # One level up (parent directory)

# Add the project root to sys.path
sys.path.insert(0, project_root)

# Now you can safely import modules
import modules
import modules.polygon_api


import unittest.mock as mock

def test_process_message():
    msg = mock.Mock(
        event_type='T',
        exchange=320,
        id=None,
        price=1.24,
        sequence_number=1085599239,
        size=10000,
        symbol='O:ACAD250117P00003000',
        tape=None,
        timestamp=1733937449037,
        trf_id=None,
        trf_timestamp=None
    )
    modules.polygon_api.process_message(msg)




if __name__ == "__main__":
    test_process_message()