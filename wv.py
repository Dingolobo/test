 # -*- coding: utf-8 -*-
# Module: KEYS-L3
# Created on: 11-10-2021
# Authors: -∞WKS∞-
# Version: 1.1.0

import base64, requests, sys, xmltodict
import headers_claro
from pywidevine.L3.cdm import cdm, deviceconfig
from base64 import b64encode
from pywidevine.L3.decrypt.wvdecryptcustom import WvDecrypt

pssh = input('\nPSSH: ')
lic_url = input('License URL: ')
token = input('Token: ')
device_id = input('device_id: ')

def WV_Function(pssh, lic_url, cert_b64=None):
    wvdecrypt = WvDecrypt(init_data_b64=pssh, cert_data_b64=cert_b64, device=deviceconfig.device_android_generic)
    challengeb64 = str(b64encode(wvdecrypt.get_challenge()),"utf-8")
    data = {"token":token,"device_id":device_id,"widevineBody":challengeb64}              
    widevine_license = requests.post(url=lic_url, json=data, headers=headers_claro.headers)
    print(widevine_license.request.body)
    license_b64 = b64encode(widevine_license.content)
    wvdecrypt.update_license(license_b64)
    Correct, keyswvdecrypt = wvdecrypt.start_process()
    if Correct:
        return Correct, keyswvdecrypt   
correct, keys = WV_Function(pssh, lic_url)

print()
for key in keys:
    print('--key ' + key)
