import logging
import yaml
import json
import pika
import sys
import redis
from influxdb import InfluxDBClient
import time
import mongo_manager

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    stream=sys.stdout, level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger("pika").propagate = False

mongo_mgr = mongo_manager.MongoMgr()


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
    except Exception as exp:
        logging.error(str(exp))
    return redis_obj


def con_influxdb(host, port, name, pwd, db):
    """
    :param host: InfluxDB access host ip
    :param port: InfluxDB access port
    :param name: InfluxDB access user name
    :param pwd: InfluxDB access user password
    :param db: Database to access
    :return: InfluxDB connector
    """
    client = None
    try:
        client = InfluxDBClient(host=host, port=port, username=name, password=pwd, database=db)
    except Exception as exp:
        logging.error(str(exp))
    return client


def get_messagequeue(address, port):
    """
    If you don't have rabbitmq, you can use docker.
    docker run -d --hostname whaleshark --name whaleshark-rabbit \
    -p 5672:5672 -p 8080:15672 -e RABBITMQ_DEFAULT_USER=whaleshark \
    -e RABBITMQ_DEFAULT_PASS=whaleshark rabbitmq:3-management

    get message queue connector (rabbit mq) with address, port
    :param address: rabbit mq server ip
    :param port: rabbitmq server port(AMQP)
    :return: rabbitmq connection channel
    """
    channel = None
    try:
        credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
        param = pika.ConnectionParameters(address, port, '/', credentials)
        connection = pika.BlockingConnection(param)
        channel = connection.channel()

    except Exception as exp:
        logging.exception(str(exp))

    return channel


influxdb_client = None


def callback_mqreceive(ch, method, properties, body):
    body = body.decode('utf-8')
    facility_msg_json = json.loads(body)
    table_name = list(facility_msg_json.keys())[0]
    fields = {}
    tags = {}
    logging.debug('mqtt body:' + str(facility_msg_json))
    me_timestamp = time.time()
    for key in facility_msg_json[table_name].keys():
        if key != 'pub_time':
            logging.debug('config key:'+key + 'value:'+str(facility_msg_json[table_name][key]))
            fields[key] = float(facility_msg_json[table_name][key])
       
    pub_time = facility_msg_json[table_name]['pub_time']
    day = pub_time.split(' ')[0]
    pub_doc = mongo_mgr.document_bykey('facility', table_name, {'DAY': day})
    if pub_doc is not None:
        mongo_mgr.document_upsert('facility', table_name, day, pub_time, status='CHECK')
    
    fields['me_time'] = me_timestamp
    influx_json = [{
        'measurement': table_name,
        'fields': fields
    }]
    try:
        if influxdb_client.write_points(influx_json) is True:
            logging.debug('influx write success:' + str(influx_json))
        else:
            logging.debug('influx write faile:' + str(influx_json))
    except Exception as exp:
        print(str(exp))


def config_facility_desc(redis_con):
    facilities_dict = redis_con.get('facilities_info')

    if facilities_dict is None:
        facilities_dict = {'TS0001': {
            '0001': 'TS_VOLT1_(RS)',
            '0002': 'TS_VOLT1_(ST)',
            '0003': 'TS_VOLT1_(RT)',
            '0004': 'TS_AMP1_(R)',
            '0005': 'TS_AMP1_(S)',
            '0006': 'TS_AMP1_(T)',
            '0007': 'INNER_PRESS',
            '0008': 'PUMP_PRESS',
            '0009': 'TEMPERATURE1(PV)',
            '0010': 'TEMPERATURE1(SV)',
            '0011': 'OVER_TEMP'}
        }
        redis_con.set('facilities_info', json.dumps(facilities_dict))


if __name__ == '__main__':
    with open('config/config_server_develop.yaml', 'r') as file:
        config_obj = yaml.load(file, Loader=yaml.FullLoader)
        rabbitmq_host = config_obj['iiot_server']['rabbit_mq']['ip_address']
        rabbitmq_port = config_obj['iiot_server']['rabbit_mq']['port']
        
        redis_host = config_obj['iiot_server']['redis_server']['ip_address']
        redis_port = config_obj['iiot_server']['redis_server']['port']
        
        influx_host = config_obj['iiot_server']['influxdb']['ip_address']
        influx_port = config_obj['iiot_server']['influxdb']['port']
        
        influx_id = config_obj['iiot_server']['influxdb']['id']
        influx_pwd = config_obj['iiot_server']['influxdb']['pwd']
        influx_db = config_obj['iiot_server']['influxdb']['db']
    
    influxdb_client = con_influxdb(host=influx_host, port=influx_port, name=influx_id, pwd=influx_pwd, db=influx_db)
    if influxdb_client is None:
        logging.error('influxdb configuration fail')
        
    mq_channel = get_messagequeue(address=rabbitmq_host, port=rabbitmq_port)
    if mq_channel is None:
        logging.error('rabbitmq configuration fail')
    
    redis_con = connect_redis(redis_host, redis_port)
    config_facility_desc(redis_con)
    facilities_dict = json.loads(redis_con.get('facilities_info'))
    for facility_id in facilities_dict.keys():
        result = mq_channel.queue_declare(queue=facility_id, exclusive=True)
        queue_name = result.method.queue
        mq_channel.queue_bind(exchange='facility', queue=queue_name)
        
        call_back_arg = {'measurement': queue_name}
        try:
            mq_channel.basic_consume(queue_name, on_message_callback=callback_mqreceive)
        except Exception as e:
            logging.error(str(e))
    
    mq_channel.start_consuming()
