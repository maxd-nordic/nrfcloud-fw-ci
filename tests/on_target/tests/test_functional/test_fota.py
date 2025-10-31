import os
import pytest
import time
import sys
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

def test_app_fota(dut_fota, coap_fota_hex_file):
    '''
    Test that verifies that device can connect to nRF Cloud and perform FOTA update.
    '''

    if not APP_BUNDLEID:
        pytest.skip("APP_BUNDLEID not set, skipping FOTA test")

    flash_device(os.path.abspath(coap_fota_hex_file))
    dut_cloud.uart.xfactoryreset()
    dut_cloud.uart.flush()

    test_start_time = time.time()
    reset_device()

    dut_cloud.uart.wait_for_str_ordered(
        [
            "Connected to LTE",
            "nrf_cloud_coap_transport: Authorized",
            "nrf_cloud_coap_fota_sample: Updated shadow delta sent"
        ],
        timeout=CLOUD_TIMEOUT
    )

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
        fotatimeout
    )
    await_nrfcloud(
        functools.partial(dut_fota.fota.get_fota_status, dut_fota.data['job_id']),
        "COMPLETED",
        "FOTA status",
        fotatimeout
    )
    await_nrfcloud(
        functools.partial(get_appversion, dut_fota),
        new_version,
        "appVersion",
        DEVICE_MSG_TIMEOUT
    )
