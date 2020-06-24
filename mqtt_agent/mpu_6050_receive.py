import pika
import json
from influxdb import InfluxDBClient
import yaml
import datetime
from datetime import timedelta

config_f = open("config.yaml", 'r')
config_obj = yaml.load(config_f)

tsdb_host = config_obj['tsdb']['influx']['host']
tsdb_port = config_obj['tsdb']['influx']['port']
tsdb_user = config_obj['tsdb']['influx']['user']
tsdb_password = config_obj['tsdb']['influx']['pasword']
tsdb_dbname = config_obj['tsdb']['influx']['dbname']
tsdv_protocol = config_obj['tsdb']['influx']['protocol']
tsdb_client = InfluxDBClient(tsdb_host, tsdb_port, tsdb_user, tsdb_password, tsdb_dbname)

rabbitmq_server = config_obj['mqtt']['rabbitmq']['host']
rabbitmq_port = config_obj['mqtt']['rabbitmq']['port']
rabbitmq_id = config_obj['mqtt']['rabbitmq']['id']
rabbitmq_pwd = config_obj['mqtt']['rabbitmq']['pwd']

credentials = pika.PlainCredentials(rabbitmq_id, rabbitmq_pwd)
connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_server,rabbitmq_port, 'th11',  credentials))
channel = connection.channel()
channel.queue_declare(queue='dht11')

def callback(ch, method, properties, body):
    json_data = body
    json_data=str(json_data, 'utf-8')
    json_data ='{' + json_data  +'}'
    try:
        parsed_json = json.loads(json_data)
        date_time_obj = datetime.datetime.strptime(parsed_json['mtime'], '%Y-%m-%dT%H:%M:%SZ')
        date_time_obj = date_time_obj + timedelta(hours=9)
        dict_record = [
                {
                    "measurement": "whaleshark_iiot_dht11",
                    #"time": date_time_obj,
                    "fields": json.loads(json_data)
                }
            ]
        tsdb_client.write_points(dict_record)
        print(date_time_obj, parsed_json['acc_x'],parsed_json['acc_y'],parsed_json['acc_z'])
    except Exception as e:
        print(str(e))

channel.basic_consume('dht11',callback,auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
