import math
import random
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



@taxilocationnamespace.route('/addEditTaxiLocation', methods=['POST'])
def editlocation():
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

@taxilocationnamespace.route('/updateTaxi/<taxi_id>', methods=['PUT'])
def addEditTAXI_ID(taxi_id):
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
    if checkIfExists(taxi_id) == False:
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

@taxilocationnamespace.route('/getLocationByTaxiId/<taxi_id>', methods=['GET'])
def getlocationtaxistaxiid(taxi_id):
    if checkIfExists(taxi_id,None) == False:
        return json_response({"message": "Taxi Not Exists"})
    query = {"taxi_id": taxi_id}
    taxiLocation = aggregator_db[taxi_location]
    location = taxiLocation.find(query).sort('timestamp',pymongo.DESCENDING);
    list_cur = list(location)
    #location['timestamp'] = location['timestamp'].isoformat()
    if location:
        return json_util.dumps(list_cur)
    else:
        return json_response({"message": "Taxi Location not found"}, 404)

def getTaxiByLocation(data):
    json_loaded = json.loads(data)
    taxiLocation = aggregator_db[taxi_location]
    #taxiLocation.create_index([('location', pymongo.GEOSPHERE)])
    try:
        taxiLocation.create_index([('location', "2dsphere")])
    except:
        print("An exception occurred")
    #taxiLocation.createIndex({"location": "2dsphere"})
    distance = json_loaded['distance']
    #query = {"location": {"$near": {"$geometry": {"type": "Point", "coordinates": json_loaded['location']},
     #                               "$maxDistance": distance}},"status":"active"};
    query = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": json_loaded['location']},
                "distanceField": "distance",
                "query": {'status': 'active'},
                "spherical": "true",
                "key": "location",
                "maxDistance":distance
            }
        }]
    cursor = taxiLocation.aggregate(query);
    return cursor;

def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}


##Methods to initialise the bulk taxi locations
@taxilocationnamespace.route('/bulkLocation', methods=['POST'])
def bulkLocation():

    json_loaded = json.loads(request.data)
    taxLocationList = [];
    taxiLocationq = aggregator_db[taxi_location]
    for taxilocationobj in json_loaded:
        if checkIfExists(taxilocationobj["taxi_id"],"active") == True:
            query = {"taxi_id": taxilocationobj["taxi_id"]}
            if taxiLocationq.count(query) <= 0:
                taxilocationobj["location"] = {
                'type': "Point",
                'coordinates': taxilocationobj['location']
                }
                taxilocationobj['timestamp'] = datetime.utcnow();
                taxLocationList.append(taxilocationobj);
    if len(taxLocationList) > 0:
        taxiLocationq.insert_many(taxLocationList)
    else :
        return (
            json.dumps({'Message': 'Taxi with already initialised locations cannot be inserted'}),
            200,
            {'Content-type': "application/json"}
        )
    return (
        json.dumps({'Message': 'Locations has been initialised for following Taxis : ['
                               +",".join([item['taxi_id'] for item in taxLocationList])+']'}),
        200,
        {'Content-type': "application/json"}
    )

##Methods to initialise the random taxi locations
@taxilocationnamespace.route('/randomLocation', methods=['GET'])
def randomLocation():
    taxiLocationq = aggregator_db[taxi_location]
    query = {"status":"active"}
    taxisLocations = taxiLocationq.find(query);
    listOfTaxis = [];
    for taxilocation in taxisLocations :
        listOfTaxis.append(taxilocation['taxi_id'])
    taxi_id  = random.choice(listOfTaxis)
    query = {"taxi_id": taxi_id}
    randomTaxi = taxiLocationq.find_one(query);
    latLonArr = randomTaxi['location']['coordinates']
    newLon = initiateLon(latLonArr[0], random.randrange(100, 200))
    newLat = initiateLat(latLonArr[1], random.randrange(100, 200))
    newvalues = {"$set": {"location": {'type': "Point", 'coordinates': [newLon,newLat]}, "date": datetime.utcnow()}}
    taxiLocationq.update_one(query,newvalues)
    return (
            json.dumps({'Message': 'Taxi Location has been Re-initialised for : '+taxi_id}),
            200,
            {'Content-type': "application/json"}
        )

def initiateLat(lat,dis):
    earth = 6378.137
    pi = math.pi
    m = (1 / ((2 * pi / 360) * earth)) / 1000
    new_latitude = lat + (dis * m);
    return new_latitude

def initiateLon(lon,dis):
    earth = 6378.13
    pi = math.pi
    cos = math.cos
    m = (1 / ((2 * pi / 360) * earth)) / 1000;
    new_longitude = lon + (dis * m) / cos(28.59606  * (pi / 180));
    return new_longitude
