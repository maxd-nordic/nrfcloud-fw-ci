import os
import pytest
import time
import sys
sys.path.append(os.getcwd())
from utils.logger import get_logger
from utils.flash_tools import flash_device, reset_device

logger = get_logger()

CLOUD_TIMEOUT = 60 * 3

def test_device_message(dut_cloud, coap_device_message_hex_file):
    '''
    Test that verifies that device can connect to nRF Cloud and send device messages.
    '''
    flash_device(os.path.abspath(coap_device_message_hex_file))
    dut_cloud.uart.xfactoryreset()
    dut_cloud.uart.flush()

    test_start_time = time.time()
    reset_device()

    dut_cloud.uart.wait_for_str_ordered(
        [
            "Connected to LTE",
            "nrf_cloud_coap_transport: Authorized",
            "Sent Hello World message with ID"
        ],
        timeout=CLOUD_TIMEOUT
    )

    # Poll for message to be reported to cloud
    start = time.time()
    while time.time() - start < CLOUD_TIMEOUT:
        time.sleep(5)
        messages = dut_cloud.cloud.get_messages(dut_cloud.device_id, appname=None, max_records=20, start=test_start_time)
        logger.debug(f"Found messages: {messages}")

        if messages:
            message_object = messages[0][1]
            message_content = message_object.get('sample_message', '')

            if "Hello World, from the CoAP Device Message Sample!" in message_content:
                break
        else:
            logger.debug("No message with recent timestamp, retrying...")
            continue
    else:
        raise RuntimeError("No new message to cloud observed")
