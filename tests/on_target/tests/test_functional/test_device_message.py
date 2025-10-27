import os
import pytest
import time
from utils.nrf91_flasher import nrf91_flasher
import sys
sys.path.append(os.getcwd())
from utils.logger import get_logger

logger = get_logger()

CLOUD_TIMEOUT = 60 * 3

def test_device_message(dut_cloud, coap_device_message_hex_file):
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

    # Wait for message to be reported to cloud
    start = time.time()
    while time.time() - start < CLOUD_TIMEOUT:
        time.sleep(5)
        messages = dut_cloud.cloud.get_messages(dut_cloud.device_id, appname=None, max_records=20, max_age_hrs=0.25)
        logger.debug(f"Found messages: {messages}")

        latest_message = messages[0] if messages else None
        logger.info(f"Latest message: {latest_message}")
        if latest_message:
            check_message_age = dut_cloud.cloud.check_message_age(message=latest_message, seconds=30)
            if check_message_age:
                break
        else:
            logger.debug("No message with recent timestamp, retrying...")
            continue
    else:
        raise RuntimeError("No new message to cloud observed")
