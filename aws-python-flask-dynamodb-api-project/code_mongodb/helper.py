import pymongo

db_uri = 'mongodb://localhost:27017'
client = pymongo.MongoClient(db_uri)
user_table = 'USER_REGISTRATION'
aggregator_db = client['taxi_aggregator_selector']

def getAutoId(collection_name):
    seq = aggregator_db["seqs"]
    return str(seq.seqs.find_and_modify(
        query={'collection': collection_name},
        update={'$inc': {'id': 1}},
        fields={'id': 1, '_id': 0},
        new=True,
        upsert= True
    ).get('id'))
