from decimal import Decimal

from bson import json_util
from flask import request
from flask import Flask
import json
import pymongo as pymongo
import os
from flask import Blueprint
from datetime import datetime

from codes_mongodb.helper import getAutoId
from codes_mongodb.taxi import tripTaxiOn,checkIfExists
from codes_mongodb.user import checkIfUserExists
from codes_mongodb.taxi_location import editlocation, updateLocation, updateStatus

tripnamespace = Blueprint('trip', __name__)


db_uri = os.environ['DB_URI']
aggregator_db = os.environ['DB_NAME']
trip_table = os.environ['USER_TRIP']


client = pymongo.MongoClient(db_uri)
aggregator_db = client[aggregator_db]

@tripnamespace.route('/list', methods=['GET'])
def getAllTrips():
    trips = aggregator_db[trip_table]
    cursor = trips.find({});
    list_cur = list(cursor)
    for cur in list_cur:
        cur['origin_timestamp'] = cur['origin_timestamp'].isoformat()
        cur['dest_timestamp'] = cur['dest_timestamp'].isoformat()
    return (
            json_util.dumps(list_cur),
        200,
        {'Content-type': "application/json"}
    )


@tripnamespace.route('/get/<trip_id>', methods=['GET'])
def getTrip(trip_id):
    if checkTripIfExists(trip_id) == False:
        return json_response({"message": "Trip Does Not Exists"})
    trips = aggregator_db[trip_table]
    trip = trips.find_one({"trip_id":trip_id});
    trip['origin_timestamp'] = trip['origin_timestamp'].isoformat()
    trip['dest_timestamp'] = trip['dest_timestamp'].isoformat()
    return (
        json_util.dumps(trip),
        200,
        {'Content-type': "application/json"}
    )

@tripnamespace.route('/getByTaxi/<taxi_id>', methods=['GET'])
def getTripByTaxiId(taxi_id):
    if checkIfExists(taxi_id) == False:
        return json_response({"message": "Taxi Does Not Exists"})
    trips = aggregator_db[trip_table]
    trip = trips.find_one({"taxi_id":taxi_id});
    trip['origin_timestamp'] = trip['origin_timestamp'].isoformat()
    trip['dest_timestamp'] = trip['dest_timestamp'].isoformat()
    return (
        json_util.dumps(trip),
        200,
        {'Content-type': "application/json"}
    )

@tripnamespace.route('/getByUser/<user_id>', methods=['GET'])
def getTripByUser(user_id):
    if checkIfUserExists(user_id,"active") == False:
        return json_response({"message": "User Does Not Exists"})
    trips = aggregator_db[trip_table]
    trip = trips.find_one({"user_id":user_id});
    trip['origin_timestamp'] = trip['origin_timestamp'].isoformat()
    trip['dest_timestamp'] = trip['dest_timestamp'].isoformat()
    return (
        json_util.dumps(trip),
        200,
        {'Content-type': "application/json"}
    )
@tripnamespace.route('/start', methods=['POST'])
def register():
    json_loaded = json.loads(request.data)
    json_loaded.update({'trip_id': "trip_" + getAutoId(trip_table)})
    # Create a Database
    if checkIfExists(json_loaded["taxi_id"],"active") == False :
      return (
            json.dumps({'Message': 'Taxi does not exist'}),
            200,
            {'Content-type': "application/json"})
    if checkIfUserExists(json_loaded["user_id"],"active") == False :
      return (
            json.dumps({'Message': 'User does not exist'}),
            200,
            {'Content-type': "application/json"})
    trip = aggregator_db[trip_table]
    json_loaded["origin"] = {
        'type': "Point",
        'coordinates': json_loaded['origin']
    }

    json_loaded['origin_timestamp'] = datetime.utcnow();
    json_loaded['status'] = 'active';
    json_loaded['destination'] = None;
    json_loaded['dest_timestamp'] = None;
    res = trip.insert_one(json_loaded)
    tripTaxiOn(json_loaded["taxi_id"],1);
    #updateStatus(json_loaded["taxi_id"],{"status":"unavailable"})
    return (
        json.dumps({'Message': 'Trip Has been Started'}),
        200,
        {'Content-type': "application/json"}
    )
@tripnamespace.route('/end/<trip_id>', methods=['PUT'])
def editTrip(trip_id):
    if checkTripIfExists(trip_id,"active") == False:
        return json_response({"message": "Trip Does Not Exists"})
    query = {"trip_id": trip_id,'status' : 'active'}
    json_loaded = json.loads(request.data)
    tripTable = aggregator_db[trip_table]
    trip_details = tripTable.find_one(query)
    attribute_updates_dict = {"$set": {
         "destination": {
            'type': "Point",
            'coordinates': json_loaded['destination']
            },
        "dest_timestamp":datetime.utcnow(),
        "status" : "completed"
    }
    };
    tripTable.update_one(query,attribute_updates_dict)
    #updateLocation(trip_details['taxi_id'],{"location":json_loaded['destination']})
    tripTaxiOn(trip_details['taxi_id'],0)
    return (
        json.dumps({'Message': 'Trip Has been completed !!'}),
        200,
        {'Content-type': "application/json"}
    )

@tripnamespace.route('/cancel/<trip_id>', methods=['GET'])
def deleteTrip(trip_id):
        if checkTripIfExists(trip_id,None) == False:
         return json_response({"message": "Trip Does Not Exists"})
        query = {"trip_id": trip_id}
        trip = aggregator_db[trip_table]
        attribute_updates_dict = {"$set": {'status': 'inactive', 'dest_timestamp': datetime.utcnow()}};
        trip.update_one(query, attribute_updates_dict)
        return json_response({"message": "Trip has been cancelled !!"})

def checkTripIfExists(trip_id,status = None):
    if status == None:
        query = {"trip_id": trip_id}
    else:
        query = {"trip_id": trip_id,"status":status}

    taxi = aggregator_db[trip_table]
    count = taxi.count(query)
    if count == 0:
        return False
    else:
        return True


def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}
