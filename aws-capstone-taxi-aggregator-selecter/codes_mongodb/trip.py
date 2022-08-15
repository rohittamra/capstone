from decimal import Decimal

from bson import json_util
from flask import request
from flask import Flask
import json
import pymongo as pymongo
import os
from flask import Blueprint
from datetime import datetime

#from latlon import LatLon, Longitude, Latitude

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


@tripnamespace.route('/getalltrips', methods=['GET'])
def getAllTrips():
    trips = aggregator_db[trip_table]
    cursor = trips.find({}).sort([('dest_timestamp',pymongo.DESCENDING)
                                     ,('origin_timestamp',pymongo.DESCENDING)]);
    list_cur = list(cursor)
    for cur in list_cur:
        cur['origin_timestamp'] = cur['origin_timestamp'].isoformat()
        if cur['dest_timestamp'] is not None :
            cur['dest_timestamp'] = cur['dest_timestamp'].isoformat()
    return (
        json_util.dumps(list_cur),
        200,
        {'Content-type': "application/json"}
    )


@tripnamespace.route('/getTripsByTripTd/<trip_id>', methods=['GET'])
def getTrip(trip_id):
    if checkTripIfExists(trip_id) == False:
        return json_response({"message": "Trip Does Not Exists"})
    trips = aggregator_db[trip_table]
    trip = trips.find_one({"trip_id": trip_id});
    trip['origin_timestamp'] = trip['origin_timestamp'].isoformat()
    if trip['dest_timestamp'] is not None:
        trip['dest_timestamp'] = trip['dest_timestamp'].isoformat()
    return (
        json_util.dumps(trip),
        200,
        {'Content-type': "application/json"}
    )


@tripnamespace.route('/getTripsByTaxiId/<taxi_id>', methods=['GET'])
def getTripsByTaxiId(taxi_id):
    if checkIfExists(taxi_id) == False:
        return json_response({"message": "Taxi Does Not Exists"})
    trips = aggregator_db[trip_table]
    trip = trips.find({"taxi_id": taxi_id});
    list_cur = list(trip);
    #trip['origin_timestamp'] = trip['origin_timestamp'].isoformat()
    #trip['dest_timestamp'] = trip['dest_timestamp'].isoformat()
    return (
        json_util.dumps(list_cur),
        200,
        {'Content-type': "application/json"}
    )


@tripnamespace.route('/getTripsByUserId/<user_id>', methods=['GET'])
def getTripByUser(user_id):
    if checkIfUserExists(user_id, "active") == False:
        return json_response({"message": "User Does Not Exists"})
    trips = aggregator_db[trip_table]
    trip = trips.find({"user_id": user_id});
    list_cur = list(trip);
    #trip['origin_timestamp'] = trip['origin_timestamp'].isoformat()
    #trip['dest_timestamp'] = trip['dest_timestamp'].isoformat()
    return (
        json_util.dumps(list_cur),
        200,
        {'Content-type': "application/json"}
    )


@tripnamespace.route('/starttrip', methods=['POST'])
def register():
    json_loaded = json.loads(request.data)
    json_loaded.update({'trip_id': "trip_" + getAutoId(trip_table)})
    # Create a Database
    if checkIfExists(json_loaded["taxi_id"], "active") == False:
        return (
            json.dumps({'Message': 'Taxi does not exist'}),
            200,
            {'Content-type': "application/json"})
    if checkIfUserExists(json_loaded["user_id"], "active") == False:
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
    try:
        trip.create_index([('origin', "2dsphere")])
    except:
        print("An exception occurred")

    #trip.create_index([('origin', pymongo.GEOSPHERE)])
    #trip.createIndex({"origin": "2dsphere"})
    res = trip.insert_one(json_loaded)
    tripTaxiOn(json_loaded["taxi_id"], 1);
    # updateStatus(json_loaded["taxi_id"],{"status":"unavailable"})
    return (
        json.dumps({'Message': 'Trip Has been Started'}),
        200,
        {'Content-type': "application/json"}
    )


@tripnamespace.route('/endtrip/<trip_id>', methods=['PUT'])
def editTrip(trip_id):
    if checkTripIfExists(trip_id,"active") == False:
        return json_response({"message": "Trip Does Not Exists"})
    distance_travelled = 0;
    taxi_id = '';
    json_loaded = json.loads(request.data)
    end_lat = json_loaded["end_latitude"]
    end_long = json_loaded["end_longitude"]
    query = [
        {
    "$geoNear": {
        "near": {"type": "Point", "coordinates": [end_lat, end_long]},
        "distanceField": "distancetravelled",
        "query": {"trip_id": trip_id,'status' : 'active'},
        "spherical": "true",
        "key":"origin"
    }
    }]
    tripTable = aggregator_db[trip_table]
    trip = tripTable.aggregate(query)
    for t in trip :
       distance_travelled  =  t['distancetravelled'];
       taxi_id = t["taxi_id"];
    attribute_updates_dict = {"$set": {
         "destination": {
            'type': "Point",
            'coordinates': [end_lat,end_long]
            },
         "distance": distance_travelled,
        "dest_timestamp":datetime.utcnow(),
        "status" : "completed"
    }
    };
    try:
        tripTable.create_index([('destination', "2dsphere")])
    except:
        print("An exception occurred")
    query = {"trip_id": trip_id,'status' : 'active'};
    tripTable.update_one(query,attribute_updates_dict)
    tripTaxiOn(taxi_id,0)
    query = {"trip_id": trip_id}
    trip = tripTable.find_one(query)
    trip.update({'message': 'Trip Has been completed !!'})
    return (
        json_util.dumps(trip),
        200,
        {'Content-type': "application/json"}
    )

@tripnamespace.route('/canceltrip/<trip_id>', methods=['GET'])
def deleteTrip(trip_id):
    if checkTripIfExists(trip_id) == False:
        return json_response({"message": "Trip Does Not Exists"})
    query = {"trip_id": trip_id}
    trip = aggregator_db[trip_table]
    attribute_updates_dict = {"$set": {'status': 'inactive', 'dest_timestamp': datetime.utcnow()}};
    trip.update_one(query, attribute_updates_dict)
    return json_response({"message": "Trip has been cancelled !!"})


def checkTripIfExists(trip_id, status=None):
    if status == None:
        query = {"trip_id": trip_id}
    else:
        query = {"trip_id": trip_id, "status": status}

    taxi = aggregator_db[trip_table]
    count = taxi.count(query)
    if count == 0:
        return False
    else:
        return True


def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}
