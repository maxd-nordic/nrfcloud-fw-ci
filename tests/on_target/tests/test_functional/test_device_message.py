import os
import pytest
import time
from utils.nrf91_flasher import nrf91_flasher
import sys
sys.path.append(os.getcwd())
from utils.logger import get_logger

logger = get_logger()

def test_device_message(dut_board, coap_device_message_hex_file):
    '''
    Test that verifies that device can connect to nRF Cloud and send device messages.
    '''
    nrf91_flasher(erase=False, program=os.path.abspath(coap_device_message_hex_file))
    dut_cloud.uart.xfactoryreset()
    dut_cloud.uart.flush()
    nrf91_flasher()

    dut_cloud.uart.wait_for_str_ordered(
        [
            "Connected to LTE",
            "nrf_cloud_coap_transport: Authorized",
            "Sent Hello World message with ID"
        ],
        timeout=240
    )
