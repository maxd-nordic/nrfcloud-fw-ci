#!/usr/env bash

# needs to have API_KEY_PROD, API_KEY_DEV, and API_KEY_BETA set
# factory-reset the device before proceeding
# update MFW
# install at_client

nrfcredstore auto deleteall
create_ca_cert
device_credentials_installer -d --ca *_ca.pem --ca-key *_prv.pem --coap --verify --delete --sectag 2147483650
nrf_cloud_onboard --api-key $API_KEY_PROD && rm onboard.csv
device_credentials_installer -d --ca *_ca.pem --ca-key *_prv.pem --coap --verify --delete --stage beta --sectag 2147483651
nrf_cloud_onboard --stage beta --api-key $API_KEY_BETA && rm onboard.csv
device_credentials_installer -d --ca *_ca.pem --ca-key *_prv.pem --coap --verify --delete --stage dev --sectag 2147483652
nrf_cloud_onboard --stage dev --api-key $API_KEY_DEV && rm onboard.csv
