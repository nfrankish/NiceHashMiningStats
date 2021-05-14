import nicehash
import secrets
import json
import time
from decimal import Decimal
from influxdb import InfluxDBClient
import octune
#Seconds for each iteration
SLEEP_TIME=60
#Number of interations to go through to get payments
PAYMENTS=30

def getPaymentData(accounts):
    data = []
    for account in secrets.accounts:
        orgId = account[0]
        try:
            private_api = nicehash.private_api('https://api2.nicehash.com', account[0], account[1], account[2])
            response = private_api.request('GET', '/main/api/v2/mining/rigs/payouts', 'page=&size=100000', '')
            payments = response['list']
            for p in payments:
                paymentid = p["id"]
                paymenttimestamp = p["created"]
                paymentamount = float(p["amount"])
                paymentfee = float(p["feeAmount"])
                total = paymentamount - paymentfee
           #     print("ID {} - Date {} - Amount {:.8f} - Fee {:.8f} - Total {:.8f}".format(paymentid, paymenttimestamp,
            #                                                                               paymentamount, paymentfee,
             #                                                                              total))
                data.append(
                    "payouts,orgid={orgId} paymentid=\"{paymentid}\",paymentamount={paymentamount:.8f},paymentfee={paymentfee:.8f},total={total:.8f}  {timestamp}".format(
                        orgId=orgId,
                        paymentid=paymentid,
                        paymentamount=paymentamount,
                        paymentfee=paymentfee,
                        total=total,
                        timestamp=paymenttimestamp))

        except Exception as int:
            print(int)
    return data


def getOctuneData(octuneAddresses):
    data = []
    for address in octuneAddresses:
        endpointName = address[0]
        endpoint = address[1]
        try:
          private_api = octune.private_api('http://' + endpoint + ':18000')
          devices_cuda = private_api.request('GET', '/devices_cuda')
          workers_cuda = private_api.request('GET', '/workers')
        except Exception as inst:
            print(inst)
            continue

        for d in devices_cuda['devices']:
            workerfound=False
            for w in workers_cuda['workers']:
                if d['uuid'] == w['device_uuid']:
                    workerfound = True
                    continue
            if workerfound:
                data.append(
                    "oc_devices,endpoint={endpoint},uuid={deviceid},oc_core={oc_core},oc_memory={oc_memory},oc_power_w={oc_power_w},oc_power_tdp={oc_power_tdp}"
                    " kt_avg={kt_avg},kt_min={kt_min},kt_max={kt_max},vram_temperature={vram_temp},gpu_temperature={gpu_temp},temp_warning={temp_warning},hashrate={hashrate}"
                    ",power={power},core={core},memory={memory}".format(
                        endpoint=endpoint,
                        deviceid=d['uuid'],
                        oc_core=d['oc_data']['core_clock_delta'],
                        oc_memory=d['oc_data']['memory_clock_delta'],
                        oc_power_w=d['oc_data']['power_limit_watts'],
                        oc_power_tdp=d['oc_data']['power_limit_tdp'],
                        vram_temp=d['__vram_temp'],
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

        return data


def getRigData(accounts):
    data = []
    for account in accounts:
        orgId = account[0]
        try:
            private_api = nicehash.private_api('https://api2.nicehash.com', account[0], account[1], account[2])
            response = private_api.request('GET', '/main/api/v2/mining/rigs2', '', '')
        except Exception as inst:
            print(inst)
            continue
        # j_rigs = json.loads(response.content)
        rigs = response['miningRigs']

        for r in rigs:
            rigId = r['rigId']
            rigName = r['name']
            rigProfit = round(Decimal(r['profitability']), 8)
            rigLocalProfit = round(Decimal(r['localProfitability']), 8)
            print('Rig {} ({}) - Profit : {} - LocalProfit : {} '.format(rigId, rigName, rigProfit, rigLocalProfit))
            rigTotalSpeed = float(0.0);
            for d in r['devices']:
                name = d['name']
                deviceId = d['id']
                vram = d['temperature'] / 65536
                gpu = d['temperature'] % 65536
                deviceType = d['deviceType']['enumName']
                speed = 0.0
                speeds = d['speeds']
                if len(speeds) == 1:
                    speed = Decimal(speeds[0]['speed'])
                    if speeds[0]['displaySuffix'] == 'MH':
                        speed = speed * 1000000
                    elif speeds[0]['displaySuffix'] == 'KH':
                        speed = speed * 1000
                rigTotalSpeed += float(speed)
                print('\tCard {} : VRAM {} : GPU {} : Speed: {} '.format(name, vram, gpu, speed))

                data.append(
                    "devices,name='{name}',rigid={rigId},deviceid={deviceId},orgid={orgId},devicetype={deviceType} gpu_temperature={gpu},vram_temperature={vram},speed={speed}".format(
                        name=name.replace(' ', '\ '),
                        rigId=rigId,
                        deviceId=deviceId,
                        orgId=orgId,
                        gpu=gpu,
                        vram=vram,
                        speed=float(speed),
                        deviceType=deviceType
                    ))

            data.append(
                "rigs,id={rigId},name={rigName},orgid={orgId} profit={rigProfit},localprofit={rigLocalProfit},totalspeed={rigTotalSpeed}".format(
                    orgId=orgId,
                    rigId=rigId,
                    rigName=rigName,
                    rigProfit=rigProfit,
                    rigTotalSpeed=rigTotalSpeed,
                    rigLocalProfit=rigLocalProfit
                ))

    return data


def stats():
    client = InfluxDBClient(host=secrets.influxhost)
    client.switch_database(secrets.influxdb)
    loop = PAYMENTS
    while True:
        data = []
        tmpData = getRigData(accounts=secrets.accounts)
        if tmpData is not None:
            data = data + tmpData

        if loop == PAYMENTS:
            tmpData = getPaymentData(accounts=secrets.accounts)
            if tmpData is not None:
               data = data + tmpData
            loop = 0

        loop = loop + 1

        tmpData = getOctuneData(octuneAddresses=secrets.octuneAddresses)
        if tmpData is not None:
            data = data + tmpData

        print(data)
        try:
            client.write_points(data, time_precision='ms',  protocol='line')
        except Exception as inst:
            print(inst)
        finally:
            client.close()
        time.sleep(SLEEP_TIME)




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    stats()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
