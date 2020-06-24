import pika
import yaml
from rabbitmq_admin import AdminAPI
class modbus_rabbitmq_agent:

    #rabbit mq init
    def __init__(self):
        with open('config_develop.yaml', 'r') as file:
            config_obj = yaml.load(file, Loader=yaml.FullLoader)
            self.rabbitmq_server = config_obj['mqtt']['rabbitmq']['host']
            self.rabbitmq_port = config_obj['mqtt']['rabbitmq']['port']
            self.rabbitmq_id = config_obj['mqtt']['rabbitmq']['id']
            self.rabbitmq_pwd = config_obj['mqtt']['rabbitmq']['pwd']


    def connect_mqtt(self,virtual_host, queue_name):
        try:
            api = AdminAPI(url='http://'+self.rabbitmq_server+':'+str(8080), auth=(self.rabbitmq_id, self.rabbitmq_pwd))
            vhosts_info = api.list_vhosts()
            vhost_list = [ vhost['name'] for vhost in vhosts_info]
            if virtual_host not in vhost_list:
                api.create_vhost(virtual_host)
            api.create_user_permission(name= self.rabbitmq_id, vhost = virtual_host)

            credentials = pika.PlainCredentials(self.rabbitmq_id, self.rabbitmq_pwd)
            params = pika.ConnectionParameters(self.rabbitmq_server, self.rabbitmq_port, virtual_host, credentials)
            connection = pika.BlockingConnection(params)
            self.channel = connection.channel()

        except Exception as ex:  # 에러 종류
            print('RabbitMQ Connect fail', ex)  # ex는 발생한 에러의 이름을 받아오는 변수
            return False
        try:
            self.channel.queue_declare(queue=queue_name)
            return True
        except Exception as ex:  # 에러 종류
            print('Declare Queue fail', ex)  # ex는 발생한 에러의 이름을 받아오는 변수
            return False

    def read_instrument(self):
        pass
