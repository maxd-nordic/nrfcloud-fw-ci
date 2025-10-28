import os
import re
import pytest
import types
from utils.flash_tools import recover_device
from utils.uart import Uart, UartBinary
import sys
sys.path.append(os.getcwd())
from utils.logger import get_logger
from utils.nrfcloud import NRFCloud, NRFCloudFOTA

logger = get_logger()

UART_TIMEOUT = 60 * 30

SEGGER = os.getenv('SEGGER')
UART_ID = os.getenv('UART_ID', SEGGER)
DEVICE_UUID = os.getenv('UUID')
NRFCLOUD_API_KEY = os.getenv('NRFCLOUD_API_KEY')
DUT_DEVICE_TYPE = os.getenv('DUT_DEVICE_TYPE')
ARTIFACT_PATH = os.getenv('ARTIFACT_PATH')

def get_uarts():
    base_path = "/dev/serial/by-id"
    try:
        serial_paths = [os.path.join(base_path, entry) for entry in os.listdir(base_path)]
    except (FileNotFoundError, PermissionError) as e:
        raise RuntimeError("Failed to list serial devices") from e
    if not UART_ID:
        raise RuntimeError("UART_ID not set")
    uarts = [x for x in sorted(serial_paths) if UART_ID in x]
    return uarts

def scan_log_for_assertions(log):
    assert_counts = log.count("ASSERT")
    if assert_counts > 0:
        pytest.fail(f"{assert_counts} ASSERT found in log: {log}")

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logstart(nodeid, location):
    logger.info(f"Starting test: {nodeid}")

@pytest.hookimpl(trylast=True)
def pytest_runtest_logfinish(nodeid, location):
    logger.info(f"Finished test: {nodeid}")

@pytest.fixture(scope="function")
def dut_board(request):
    all_uarts = get_uarts()
    if not all_uarts:
        pytest.fail("No UARTs found")
    log_uart_string = all_uarts[0]
    uart = Uart(log_uart_string, timeout=UART_TIMEOUT)
    modem_traces_uart = UartBinary(all_uarts[1], timeout=UART_TIMEOUT)

    yield types.SimpleNamespace(
        uart=uart,
        device_type=DUT_DEVICE_TYPE
    )

    uart_log = uart.whole_log
    uart.stop()

    scan_log_for_assertions(uart_log)

    sample_name = request.node.name
    modem_traces_uart.stop()
    modem_traces_uart.save_to_file(os.path.join("outcomes/", f"trace_{sample_name}.bin"))

@pytest.fixture(scope="function")
def dut_cloud(dut_board):
    if not NRFCLOUD_API_KEY:
        pytest.skip("NRFCLOUD_API_KEY environment variable not set")
    if not DEVICE_UUID:
        pytest.skip("UUID environment variable not set")

    cloud = NRFCloud(api_key=NRFCLOUD_API_KEY)
    device_id = DEVICE_UUID

    yield types.SimpleNamespace(
        **dut_board.__dict__,
        cloud=cloud,
        device_id=device_id,
    )

@pytest.fixture(scope="function")
def dut_fota(dut_board):
    if not NRFCLOUD_API_KEY:
        pytest.skip("NRFCLOUD_API_KEY environment variable not set")
    if not DEVICE_UUID:
        pytest.skip("UUID environment variable not set")

    fota = NRFCloudFOTA(api_key=NRFCLOUD_API_KEY)
    device_id = DEVICE_UUID
    data = {
        'job_id': '',
    }
    fota.cancel_incomplete_jobs(device_id)

    yield types.SimpleNamespace(
        **dut_board.__dict__,
        fota=fota,
        device_id=device_id,
        data=data
    )
    fota.cancel_incomplete_jobs(device_id)


@pytest.fixture(scope="module")
def dut_traces(dut_board):
    all_uarts = get_uarts()
    trace_uart_string = all_uarts[1]
    uart_trace = UartBinary(trace_uart_string)

    yield types.SimpleNamespace(
        **dut_board.__dict__,
        trace=uart_trace,
        )

    uart_trace.stop()

@pytest.fixture(scope="session")
def coap_device_message_hex_file():
    return os.path.join(ARTIFACT_PATH, "thingy91x-nrf_cloud_coap_device_message/zephyr.signed.hex")
