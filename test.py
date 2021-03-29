import nicehash
import secrets
import json
import time
from decimal import Decimal
from influxdb import InfluxDBClient
import octune


def stats():
    data =[]
    endpoint = ""
    private_api = octune.private_api('http://' + endpoint +':18000')
    devices_cuda = private_api.request('GET','/devices_cuda')
    workers_cuda = private_api.request('GET', '/workers')
    print(workers_cuda)
    for d in devices_cuda['devices']:
        for w in workers_cuda['workers']:
            if d['uuid'] == w['device_uuid']:
                print("found worker")
                continue

        print(w)
        data.append(
            "oc_devices,endpoint={endpoint},uuid={deviceid},oc_core={oc_core},oc_memory={oc_memory},oc_power_w={oc_power_w},oc_power_tdp={oc_power_tdp}"
            " kt_avg={kt_avg},kt_min={kt_min},kt_max={kt_max},vram_temperature={vram_temp},gpu_temperature={gpu_temp},temp_warning={temp_warning},hashrate={hashrate}"
            ",power={power},core={core},memory={memory}".format(
                endpoint=endpoint,
                deviceid = d['uuid'],
                oc_core=d['oc_data']['core_clock_delta'],
                oc_memory=d['oc_data']['memory_clock_delta'],
                oc_power_w=d['oc_data']['power_limit_watts'],
                oc_power_tdp=d['oc_data']['power_limit_tdp'],
                vram_temp=d['__gddr6x_temp'],
                gpu_temp=d['gpu_temp'],
                temp_warning=d['too_hot'],
                hashrate=w['algorithms'][0]['speed'],
                kt_avg=d['kernel_times']['avg'],
                kt_min=d['kernel_times']['min'],
                kt_max=d['kernel_times']['max'],
                power=d['gpu_power_usage'],
                memory=d['gpu_clock_memory'],
                core=d['gpu_clock_core']

                ))
    print(data)
    return data


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    data = stats()
    client = InfluxDBClient(host=secrets.influxhost)
    client.switch_database(secrets.influxdb)
    client.write_points(data, time_precision='ms', protocol='line')