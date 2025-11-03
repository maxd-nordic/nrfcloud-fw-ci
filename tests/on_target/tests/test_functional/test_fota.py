import os
import pytest
import time
import sys
import functools
sys.path.append(os.getcwd())
from utils.logger import get_logger
from utils.flash_tools import flash_device, reset_device

logger = get_logger()

CLOUD_TIMEOUT = 60 * 3

DELTA_MFW_BUNDLEID_20X_TO_FOTA_TEST = "b8f85a5a-fe11-46fe-9bf9-81d4a9129338"
DELTA_MFW_BUNDLEID_FOTA_TEST_TO_20X = "2b78985e-9519-42a8-9814-2eec9730a4e2"
FULL_MFW_BUNDLEID = "61cedb8d-0b6f-4684-9150-5aa782c6c8d5"
MFW_DELTA_VERSION_20X_FOTA_TEST = "mfw_nrf91x1_2.0.3-FOTA-TEST"
MFW_202_VERSION = "mfw_nrf91x1_2.0.3"

APP_BUNDLEID = os.getenv("APP_BUNDLEID", None)

def await_nrfcloud(func, expected, field, timeout):
    start = time.time()
    logger.info(f"Awaiting {field} == {expected} in nrfcloud shadow...")
    while True:
        time.sleep(5)
        if time.time() - start > timeout:
            raise RuntimeError(f"Timeout awaiting {field} update")
        try:
            data = func()
        except Exception as e:
            logger.warning(f"Exception {e} during waiting for {field}")
            continue
        logger.debug(f"Reported {field}: {data}")
        if expected in data:
            break

def test_mfw_delta_fota(dut_fota, coap_fota_hex_file):
    '''
    Test that verifies that device can connect to nRF Cloud and perform FOTA update.
    '''

    flash_device(os.path.abspath(coap_fota_hex_file))
    dut_fota.uart.xfactoryreset()
    dut_fota.uart.flush()

    test_start_time = time.time()
    reset_device()

    dut_fota.uart.wait_for_str_ordered(
        [
            "Connected to LTE",
            "nrf_cloud_info: Modem FW:",
            "nrf_cloud_coap_transport: Authorized",
        ],
        timeout=CLOUD_TIMEOUT
    )

    for line in dut_fota.uart.whole_log.splitlines():
        if "Modem FW:" in line:
            current_version = line.split("Modem FW:")[-1].strip()
            logger.info(f"Current Modem FW version: {current_version}")
            break

    if MFW_DELTA_VERSION_20X_FOTA_TEST in current_version:
        bundle_id = DELTA_MFW_BUNDLEID_FOTA_TEST_TO_20X
    elif MFW_202_VERSION in current_version:
        bundle_id = DELTA_MFW_BUNDLEID_20X_TO_FOTA_TEST
    else:
        raise RuntimeError(f"Unexpected starting modem FW version: {current_version}")

    try:
        dut_fota.data['job_id'] = dut_fota.fota.create_fota_job(dut_fota.device_id, bundle_id)
        dut_fota.data['bundle_id'] = bundle_id
    except NRFCloudFOTAError as e:
        pytest.skip(f"FOTA create_job REST API error: {e}")
    logger.info(f"Created FOTA Job (ID: {dut_fota.data['job_id']})")

    await_nrfcloud(
        functools.partial(dut_fota.fota.get_fota_status, dut_fota.data['job_id']),
        "IN_PROGRESS",
        "FOTA status",
        CLOUD_TIMEOUT
    )
    reset_device()
    await_nrfcloud(
        functools.partial(dut_fota.fota.get_fota_status, dut_fota.data['job_id']),
        "COMPLETED",
        "FOTA status",
        CLOUD_TIMEOUT
    )
    await_nrfcloud(
        functools.partial(get_appversion, dut_fota),
        new_version,
        "appVersion",
        CLOUD_TIMEOUT
    )
