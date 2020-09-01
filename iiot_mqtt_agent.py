import logging
import yaml
import json
import pika
import sys
import redis
import influxdb
from influxdb import InfluxDBClient

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def connect_redis(host, port):
	"""
	Get connector for redis
	If you don't have redis, you can use redis on docker with follow steps.
	Getting most recent redis image
	shell: docker pull redis

	docker pull redis
	docker run --name whaleshark-redis -d -p 6379:6379 redis
	docker run -it --link whaleshark-redis:redis --rm redis redis-cli -h redis -p 6379

	:param host: redis access host ip
	:param port: redis access port
	:return: redis connector
	"""
	redis_obj = None
	try:
		conn_params = {
			"host": host,
			"port": port,
		}
		redis_obj = redis.StrictRedis(**conn_params)
	
	except Exception as e:
		logging.error(str(e))
	
	return redis_obj


def connect_influxdb(host, port, id, pwd, db):
	"""
	:param host: InfluxDB access host ip
	:param port: InfluxDB access port
	:return: InfluxDB connector
	"""
	client = None
	try:
		client = InfluxDBClient(host=host, port=port, username=id, password=pwd, database = db)
	except Exception as e:
		logging.error(str(e))
	
	return client


def get_messagequeue(address, port):
	'''
	If you don't have rabbitmq, you can use docker.
	docker run -d --hostname whaleshark --name whaleshark-rabbit -p 5672:5672 -p 8080:15672 -e RABBITMQ_DEFAULT_USER=whaleshark -e RABBITMQ_DEFAULT_PASS=whaleshark rabbitmq:3-management

	get message queue connector (rabbit mq) with address, port
	:param address: rabbit mq server ip
	:param port: rabbitmq server port(AMQP)
	:return: rabbitmq connection channel
	'''
	channel = None
	try:
		credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
		param = pika.ConnectionParameters(address,port, '/',credentials )
		connection = pika.BlockingConnection(param)
		channel = connection.channel()

	except Exception as e:
		logging.exception(str(e))

	return channel


influxdb_client = None
def callback_mqreceive(ch, method, properties, body):
	body = body.decode('utf-8')
	facility_msg_json = json.loads(body)
	print(facility_msg_json)
	table_name = list(facility_msg_json.keys())[0]
	fields={}
	tags = {}
	print(facility_msg_json[table_name])
	for key in facility_msg_json[table_name].keys():
		if 'time' not in key:
			tags[key]=float(facility_msg_json[table_name][key])
			fields[key]=float(facility_msg_json[table_name][key])
		else:
			fields[key] = facility_msg_json[table_name][key]
		
	influx_json=[{
		'measurement':table_name,
		'fields':tags,
		'tags': tags
	}]
	try:
		if influxdb_client.write_points(influx_json) == True:
			logging.debug('influx write success' + str(influx_json))
		else:
			logging.debug('influx write faile')
			
	except Exception as e:
		print(str(e))


def config_facility_desc(redis_con):
	facilities_dict=redis_con.get('facilities_info')

	if facilities_dict==None:
		facilities_dict={'TS0001':{
			'0001':'TS_VOLT1_(RS)',
			'0002':'TS_VOLT1_(ST)',
			'0003':'TS_VOLT1_(RT)',
			'0004':'TS_AMP1_(R)',
			'0005':'TS_AMP1_(S)',
			'0006':'TS_AMP1_(T)',
			'0007':'INNER_PRESS',
			'0008':'PUMP_PRESS',
			'0009':'TEMPERATURE1',
			'0010':'OVER_TEMP'
		}
		}
		redis_con.set('facilities_info',json.dumps(facilities_dict))


if __name__ == '__main__':
	with open('config/config_server_develop.yaml', 'r') as file:
		config_obj = yaml.load(file, Loader=yaml.FullLoader)
		rabbitmq_host = config_obj['iiot_server']['rabbit_mq']['ip_address']
		rabbitmq_port = config_obj['iiot_server']['rabbit_mq']['port']
		
		redis_host = config_obj['iiot_server']['redis_server']['ip_address']
		redis_port = config_obj['iiot_server']['redis_server']['port']
		
		influxdb_host = config_obj['iiot_server']['influxdb']['ip_address']
		influxdb_port = config_obj['iiot_server']['influxdb']['port']
		
		influxdb_id = config_obj['iiot_server']['influxdb']['id']
		influxdb_pwd = config_obj['iiot_server']['influxdb']['pwd']
		influxdb_db = config_obj['iiot_server']['influxdb']['db']
	
	influxdb_client = connect_influxdb(host=influxdb_host, port=influxdb_port, id=influxdb_id, pwd=influxdb_pwd, db=influxdb_db)
	if influxdb_client == None:
		logging.error('influxdb configuration fail')
		
	mq_channel = get_messagequeue(address=rabbitmq_host, port=rabbitmq_port)
	if mq_channel == None:
		logging.error('rabbitmq configuration fail')
	
	redis_con = connect_redis(redis_host, redis_port)
	config_facility_desc(redis_con)
	facilities_dict = json.loads(redis_con.get('facilities_info'))
	for facility in facilities_dict.keys():
		result = mq_channel.queue_declare(queue=facility, exclusive=True)
		queue_name = result.method.queue
		mq_channel.queue_bind(exchange='facility', queue=queue_name)
		call_back_arg = {'measurement':queue_name}
		try:
			mq_channel.basic_consume(queue_name, on_message_callback=callback_mqreceive)
		except Exception as e:
			logging.error(str(e))
	
	mq_channel.start_consuming()