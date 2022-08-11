import pymongo
import os

db_uri = os.environ['DB_URI']
aggregator_db = os.environ['DB_NAME']
AUTO_SEQUENCE = os.environ['AUTO_SEQUENCE']

client = pymongo.MongoClient(db_uri)
aggregator_db = client[aggregator_db]

def getAutoId(collection_name):
    seq = aggregator_db[AUTO_SEQUENCE]
    return str(seq.find_and_modify(
        query={'collection': collection_name},
        update={'$inc': {'id': 1}},
        fields={'id': 1, '_id': 0},
        new=True,
        upsert= True
    ).get('id'))
