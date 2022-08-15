from datetime import datetime

import pymongo

from bson import json_util
from flask import request
import json
from flask import Blueprint
import os


from codes_mongodb.helper import getAutoId

taxinamespace = Blueprint('taxi', __name__)

db_uri = os.environ['DB_URI']
aggregator_db = os.environ['DB_NAME']
taxi_table = os.environ['TAXI_TABLE']

client = pymongo.MongoClient(db_uri)
aggregator_db = client[aggregator_db]

@taxinamespace.route('/getalltaxis', methods=['GET'])
def getalltaxis():
    taxis = aggregator_db[taxi_table]
    cursor = taxis.find({}).sort('timestamp',pymongo.DESCENDING);
    list_cur = list(cursor)
    return (
        json_util.dumps(list_cur),
        200,
        {'Content-type': "application/json"}
    )

@taxinamespace.route('/edittaxi/<taxi_id>', methods=['PATCH'])
def edittaxitaxiid(taxi_id):
    if checkIfExists(taxi_id,"active") == False:
        return json_response({"message": "Taxi Not Exists"})
    json_loaded=json.loads(request.data)
    query = {"taxi_id": taxi_id}
    taxis = aggregator_db[taxi_table]
    attribute_updates_dict = {"$set": {
            'contact': json_loaded["contact"],
            'driver_name': json_loaded["driver_name"],
            'type': json_loaded["type"],
            'vehicle_no': json_loaded["vehicle_no"],
             'timestamp': datetime.utcnow()
            }};
    # print(attribute_updates_dict)
    taxis.update_one(query, attribute_updates_dict)
    return json_response({"message": "taxi entry updated"})

@taxinamespace.route('/addtaxi', methods=['POST'])
def addtaxi():
    json_loaded = json.loads(request.data)
    json_loaded.update({'taxi_id': "taxi_" + getAutoId(taxi_table)})
    json_loaded.update({'timestamp': datetime.utcnow()})
    taxi = aggregator_db[taxi_table]

    #users = aggregator_db[user_table]
    taxi.insert_one(json_loaded)
    return (
        json.dumps({'Message': 'taxi entry created'}),
        200,
        {'Content-type': "application/json"}
    )

@taxinamespace.route('/changeStatus/<taxi_id>', methods=['POST'])
def changeStatus(taxi_id):
    if checkIfExists(taxi_id) == False:
        return json_response({"message": "Taxi Not Exists"})
    json_loaded = json.loads(request.data)
    query = {"taxi_id": taxi_id}
    taxi = aggregator_db[taxi_table]
    attribute_updates_dict = {"$set": {'status': json_loaded['status'],'timestamp': datetime.utcnow()}};
    taxi.update_one(query, attribute_updates_dict)
    return json_response({"message": "Taxi Status Changed !"})

def tripTaxiOn(taxi_id,is_tripped):
    if checkIfExists(taxi_id,"active") == False:
        return json_response({"message": "Taxi Not Exists"})
    query = {"taxi_id": taxi_id}
    taxi = aggregator_db[taxi_table]
    attribute_updates_dict = {"$set": {'is_tripped': is_tripped,"timestamp":datetime.utcnow()}};
    taxi.update_one(query, attribute_updates_dict)
    return json_response({"message": "Taxi is tripped"})

def checkIfExists(taxi_id,status = None):
    if status == None :
        query = {"taxi_id": taxi_id}
    else :
        query = {"taxi_id": taxi_id,"status":status}

    taxi = aggregator_db[taxi_table]
    count = taxi.count(query)
    if count == 0:
        return False
    else:
        return True

@taxinamespace.route('/getspecifictaxi/<taxi_id>', methods=['GET'])
def getspecifictaxi(taxi_id):
    if checkIfExists(taxi_id,None) == False:
        return json_response({"message": "Taxi Does Not Exists"})
    taxi = aggregator_db[taxi_table]
    taxi_info = taxi.find_one({"taxi_id":taxi_id});
    return (
        json_util.dumps(taxi_info),
        200,
        {'Content-type': "application/json"}
    )


def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}


#Method to initialise the bulk taxis
@taxinamespace.route('/bulkRegister', methods=['POST'])
def bulkRegister():
    json_loaded=json.loads(request.data)
    for taxi in json_loaded :
        taxi.update({'taxi_id': "taxi_"+getAutoId(taxi_table)})
        taxi.update({'timestamp': datetime.utcnow()})

    users = aggregator_db[taxi_table]
    users.insert_many(json_loaded)
    return (
        json.dumps({'Message': 'taxis has been registered'}),
        200,
        {'Content-type': "application/json"}
    )