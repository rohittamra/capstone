from decimal import Decimal

import pymongo

from bson import json_util
from flask import request

import json
from flask import Blueprint
from datetime import datetime
import os

from codes_mongodb.taxi import checkIfExists

taxilocationnamespace = Blueprint('taxi-location', __name__)

db_uri = os.environ['DB_URI']
aggregator_db = os.environ['DB_NAME']
taxi_location = os.environ['TAXI_LOCATION']


client = pymongo.MongoClient(db_uri)
aggregator_db = client[aggregator_db]



@taxilocationnamespace.route('/addEdit', methods=['POST'])
def addlocation():
    json_loaded = json.loads(request.data)
    if checkIfExists(json_loaded["taxi_id"],"active") == False:
        return json_response({"message": "Taxi Not Exists"})
    query = {"taxi_id": json_loaded["taxi_id"]}
    taxiLocation = aggregator_db[taxi_location]
    json_loaded["location"] = {
        'type': "Point",
        'coordinates': json_loaded['location']
    }
    json_loaded['timestamp'] = datetime.utcnow();
    if taxiLocation.count(query) > 0 :
        return (
            json.dumps({'Message': 'Location for taxi already exists !!'}),
            200,
            {'Content-type': "application/json"}
        )
    taxiLocation.insert_one(json_loaded)
    return (
        json.dumps({'Message': 'Taxi Location Has been Created'}),
        200,
        {'Content-type': "application/json"}
    )

@taxilocationnamespace.route('/addEdit/<taxi_id>', methods=['PUT'])
def editlocation(taxi_id):
    if checkIfExists(taxi_id,"active") == False:
        return json_response({"message": "Taxi Not Exists"})

    if updateLocation(taxi_id,request.data):
        return (
        json.dumps({'Message': 'Taxi Location Has been Updated'}),
        200,
        {'Content-type': "application/json"}
    )
    else :
        return (
        json.dumps({'Error': 'Error in update'}), {'Content-type': "application/json"} )


def updateLocation(taxi_id,data) :
    query = {"taxi_id": taxi_id}
    json_loaded = json.loads(data)
    taxiLocation = aggregator_db[taxi_location]
    attribute_updates_dict = {"$set": {
        "location": {'type': "Point", 'coordinates': json_loaded['location']},
        "timestamp": datetime.utcnow(),
        "status" : "active"
    }
    };
    taxiLocation.update_one(query, attribute_updates_dict)
    return True;

@taxilocationnamespace.route('/changeStatus/<taxi_id>', methods=['PUT'])
def changeStatus(taxi_id):
    if checkIfExists(taxi_id,None) == False:
        return json_response({"message": "Taxi Not Exists"})
    updateStatus(taxi_id,request.data)
    return (
        json.dumps({'Message': 'Status has been changed'}),
        200,
        {'Content-type': "application/json"}
    )

def updateStatus(taxi_id,data):
    query = {"taxi_id":taxi_id}
    json_loaded = json.loads(data)
    taxiLocation = aggregator_db[taxi_location]
    attribute_updates_dict = {"$set": {'status': json_loaded['status'],'timestamp':datetime.utcnow()}};
    taxiLocation.update_one(query,attribute_updates_dict)

@taxilocationnamespace.route('/get/<taxi_id>', methods=['GET'])
def getlocationtaxistaxiid(taxi_id):
    if checkIfExists(taxi_id,"active") == False:
        return json_response({"message": "Taxi Not Exists"})
    query = {"taxi_id": taxi_id}
    taxiLocation = aggregator_db[taxi_location]
    location = taxiLocation.find_one(query);
    location['timestamp'] = location['timestamp'].isoformat()
    if location:
        return json_util.dumps(location)
    else:
        return json_response({"message": "Taxi Location not found"}, 404)

def getTaxiByLocation(data):
    json_loaded = json.loads(data)
    taxiLocation = aggregator_db[taxi_location]
    distance = json_loaded['distance']
    query = {"location": {"$near": {"$geometry": {"type": "Point", "coordinates": json_loaded['location']},
                                    "$maxDistance": distance}},"status":"active"};
    cursor = taxiLocation.find(query);
    return cursor;

def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}