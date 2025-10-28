import os
import pytest
import time
from utils.nrf91_flasher import nrf91_flasher
import sys
sys.path.append(os.getcwd())
from utils.logger import get_logger

logger = get_logger()

CLOUD_TIMEOUT = 60 * 3

def test_cell_location(dut_cloud, coap_cell_location_hex_file):
    '''
    Test that verifies that device can connect to nRF Cloud and request cell location.
    '''
    nrf91_flasher(erase=False, program=os.path.abspath(coap_cell_location_hex_file))
    dut_cloud.uart.xfactoryreset()
    dut_cloud.uart.flush()
    nrf91_flasher()

    dut_cloud.uart.wait_for_str_ordered(
        [
            "Connected to network",
            "nrf_cloud_coap_transport: Authorized",
            "Current cell info: Cell ID: ",
            "nrf_cloud_coap_cell_location_sample: Lat:"
        ],
        timeout=CLOUD_TIMEOUT
    )
