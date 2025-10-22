import os
import pytest
import time
from utils.flash_tools import flash_device, reset_device
import sys
sys.path.append(os.getcwd())
from utils.logger import get_logger

logger = get_logger()

def test_device_message(dut_board):
    '''
    Test that verifies that device can connect to nRF Cloud and send device messages.
    '''
    flash_device(os.path.abspath(hex_file))
    dut_cloud.uart.xfactoryreset()
    dut_cloud.uart.flush()
    reset_device()

    dut_cloud.uart.wait_for_str_ordered(
        [
            "Connected to LTE",
            "nrf_cloud_coap_transport: Authorized",
            "Sent Hello World message with ID"
        ],
        timeout=240
    )
