import nicehash
import secrets
import json
import time
from decimal import Decimal
from influxdb import InfluxDBClient



def stats():
    client = InfluxDBClient(host=secrets.influxhost)
    client.switch_database(secrets.influxdb)

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
                print("ID {} - Date {} - Amount {:.8f} - Fee {:.8f} - Total {:.8f}".format(paymentid,paymenttimestamp,paymentamount,paymentfee,total))
                data.append(
                    "payouts,orgid='{orgId}' paymentid=\"{paymentid}\",paymentamount={paymentamount:.8f},paymentfee={paymentfee:.8f},total={total:.8f}  {timestamp}".format(
                        orgId=orgId,
                        paymentid=paymentid,
                        paymentamount=paymentamount,
                        paymentfee=paymentfee,
                        total=total,
                        timestamp=paymenttimestamp))

        except Exception as int:
            print(int)
        print(data)
    try:
        client.write_points(data, time_precision='ms', protocol='line')
    except Exception as inst:
        print(inst)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    stats()