from pymongo import MongoClient, ReturnDocument
import yaml

class MongoMgr:
    
    def __init__(self):
        with open('config/config_server_develop.yaml', 'r') as file:
            config_obj = yaml.load(file, Loader=yaml.FullLoader)
            self.mongo_host = config_obj['iiot_server']['mongodb']['ip_address']
            self.mongo_port = config_obj['iiot_server']['mongodb']['port']
            self.id = config_obj['iiot_server']['mongodb']['id']
            self.pwd = config_obj['iiot_server']['mongodb']['pwd']
            self.db = config_obj['iiot_server']['mongodb']['db']
        self.mongo_client = MongoClient(self.mongo_host, username = self.id,    password = self.pwd,  authSource = self.db, authMechanism = 'SCRAM-SHA-256')
    def mongo_conn(self):
        return self.mongo_client
    
    def collections(self, database):
        return self.mongo_client[database].collection_names()
    
    def documents(self, database, collection):
        documents_list = self.mongo_client[database].get_collection(collection).find({})
        return documents_list
    
    def document_bykey(self, database, collection, doc_key):
        return self.mongo_client[database].get_collection(collection).find_one(doc_key)
    
    def document_upsert(self, database, collection, doc_key, pub_time, status='SENT'):
        document = self.mongo_client[database].get_collection(collection).find_one({'DAY':doc_key})
        if document is None:
            self.mongo_client[database].get_collection(collection).insert_one({'DAY':doc_key,"LOG":{pub_time:'SENT'}})
        else:
            document['LOG'][pub_time] = status
            doc_id = document['_id']
            self.mongo_client[database].get_collection(collection).find_one_and_update({'_id': doc_id},
                                                                                              {'$set':document})
            
    # def document_upsert(self, database, collection, doc_key, pub_time, status='SENT'):
    #     document = self.mongo_client[database].get_collection(collection).find_one({'DAY':doc_key})
    #     if document is None:
    #         self.mongo_client[database].get_collection(collection).insert_one({'DAY':{doc_key :{pub_time:'SENT'}}})
    #     else:
    #         document['TIME'][pub_time] = status
    #         doc_id = document['_id']
    #         self.mongo_client[database].get_collection(collection).find_one_and_update({'_id': doc_id},
    #                                                                                           {'$set':document})
        