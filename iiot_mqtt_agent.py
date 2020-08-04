import logging
import yaml
import json
import pika

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

def callback_ts0001(ch, method, properties, body):
    body = body.decode('utf-8')
    msg_json = json.loads(body)
    print(msg_json)
	
def callback_ts0002(ch, method, properties, body):
    body = body.decode('utf-8')
    msg_json = json.loads(body)
    print(msg_json)

if __name__ == '__main__':
	with open('config/config_server_develop.yaml', 'r') as file:
		config_obj = yaml.load(file, Loader=yaml.FullLoader)
		rabbitmq_host = config_obj['iiot_server']['rabbit_mq']['ip_address']
		rabbitmq_port = config_obj['iiot_server']['rabbit_mq']['port']

	mq_channel = get_messagequeue(address=rabbitmq_host, port=rabbitmq_port)
	if mq_channel == None:
		logging.error('rabbitmq configuration fail')
	
	result1 = mq_channel.queue_declare(queue='TS0001', exclusive=True)
	queue_name1 = result1.method.queue
	mq_channel.basic_consume(queue_name1, on_message_callback=callback_ts0001)
	
	mq_channel.start_consuming()
		