from pymongo import MongoClient, ReturnDocument
import yaml
import logging
import sys

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', stream=sys.stdout, level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')

class MongoMgr:
    
    def __init__(self):
        with open('config/config_server_develop.yaml', 'r') as file:
            config_obj = yaml.load(file, Loader=yaml.FullLoader)
            self.mongo_host = config_obj['iiot_server']['mongodb']['ip_address']
            self.mongo_port = config_obj['iiot_server']['mongodb']['port']
            self.id = config_obj['iiot_server']['mongodb']['id']
            self.pwd = config_obj['iiot_server']['mongodb']['pwd']
            self.db = config_obj['iiot_server']['mongodb']['db']
        self.mongo_client = MongoClient(self.mongo_host, username = self.id,    password = self.pwd,  authSource = self.db, authMechanism = 'SCRAM-SHA-1')
    def mongo_conn(self):
        return self.mongo_client
    
    def collections(self, database):
        return self.mongo_client[database].collection_names()
    
    def documents(self, database, collection):
        documents_list = self.mongo_client[database].get_collection(collection).find({})
        return documents_list
    
    def document_bykey(self, database, collection, doc_key):
        return self.mongo_client[database].get_collection(collection).find_one(doc_key)
    
    def document_upsert(self, database, collection, doc_key, pub_time, status={'SENT':''}):
        document = self.mongo_client[database].get_collection(collection).find_one({'DAY':doc_key})
        if document is None:
            """
            Daily append
            """
            self.mongo_client[database].get_collection(collection).insert_one({'DAY':doc_key,"LOG":{pub_time:status}})
        else:
            """
            Secondary append
            """
            if pub_time in document['LOG'].keys():#수신 확인시
                doc_id = document['_id']
                if 'SENT' in document['LOG'][pub_time]:
                    document['LOG'][pub_time]['SENT']='RECEIVED'
                    self.mongo_client[database].get_collection(collection).find_one_and_update({'_id': doc_id},
                                                                                           {'$set': document})
                else:
                    logging.error('KEY:'+ pub_time + ' NO SENT')
            else:
                doc_id = document['_id']
                document['LOG'][pub_time]={'SENT':''}
                self.mongo_client[database].get_collection(collection).find_one_and_update({'_id': doc_id},
                                                                                           {'$set': document})
            
            
            