from bson import json_util
from flask import request
import json
import pymongo as pymongo
import os
from flask import Blueprint

from codes_mongodb.helper import getAutoId
from codes_mongodb.taxi_location import getTaxiByLocation
from codes_mongodb.area_registration import checkArea


usernamespace = Blueprint('user', __name__)

db_uri = os.environ['DB_URI']
aggregator_db = os.environ['DB_NAME']
user_table = os.environ['USERS_TABLE']

client = pymongo.MongoClient(db_uri)
aggregator_db = client[aggregator_db]

@usernamespace.route('/getallusers', methods=['GET'])
def getallusers():
    users = aggregator_db[user_table]
    cursor = users.find({});
    list_cur = list(cursor)
    return (
            json_util.dumps(list_cur),
        200,
        {'Content-type': "application/json"}
    )


@usernamespace.route('/getspecificuser/<user_id>', methods=['GET'])
def getspecificuser(user_id):
    if checkIfUserExists(user_id,"active") == False:
        return json_response({"message": "User Does Not Exists"})
    users = aggregator_db[user_table]
    user = users.find_one({"user_id":user_id});
    return (
        json_util.dumps(user),
        200,
        {'Content-type': "application/json"}
    )

@usernamespace.route('/register', methods=['POST'])
def register():
    json_loaded=json.loads(request.data)
    json_loaded.update({'user_id': "user_"+getAutoId(user_table)})
    #password=json_loaded["password"]
    users = aggregator_db[user_table]
    json_converted=bytes(json.dumps(json_loaded), 'utf-8')
    users.insert_one(json.loads(json_converted))
    return (
        json.dumps({'Message': 'user entry created'}),
        200,
        {'Content-type': "application/json"}
    )

@usernamespace.route('/deleteuser/<user_id>', methods=['POST'])
def deleteuseruserid(user_id):
        if checkIfUserExists(user_id,None) == False:
            return json_response({"message": "User Not Available"})
        query = {"user_id": user_id}
        users = aggregator_db[user_table]
        attribute_updates_dict = {"$set": {'status': 'Inactive'}};
        users.update_one(query, attribute_updates_dict)
        return json_response({"message": "user marked Unavailable"})


@usernamespace.route('/book/<user_id>', methods=['POST'])
def bookTaxi(user_id):
    if checkIfUserExists(user_id,"active") == False:
        return json_response({"message": "User Not Available"})
    count = checkArea(request.data);
    if count == False:
        return json_response({"message": "Location is out of supported area !!"})
    cursor = getTaxiByLocation(request.data)
    list_cur = list(cursor)
    if len(list_cur) == 0:
        return json_response({"message": "No Taxi is available around specified Location !!"})
    return (
        json_util.dumps(list_cur),
        200,
        {'Content-type': "application/json"}
    )

def checkIfUserExists(user_id,status:None):
    if status == None :
        query = {"user_id": user_id}
    else :
        query = {"user_id": user_id,"status": "active"}
    users = aggregator_db[user_table]
    count = users.count(query)
    if count == 0:
        return False
    else:
        return True

def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}
