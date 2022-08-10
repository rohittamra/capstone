from decimal import Decimal

from bson import json_util
from flask import request

import json
import pymongo as pymongo
import os
from flask import Blueprint
from datetime import datetime

from codes_mongodb.helper import getAutoId

areanamespace = Blueprint('area', __name__)

db_uri = os.environ['DB_URI']
aggregator_db = os.environ['DB_NAME']
area_table = os.environ['AREA_TABLE']

client = pymongo.MongoClient(db_uri)
aggregator_db = client[aggregator_db]


@areanamespace.route('/list', methods=['GET'])
def getallareas():
    areas = aggregator_db[area_table]
    cursor = areas.find({});
    list_cur = list(cursor)
    for cur in list_cur:
        cur['timestamp'] = cur['timestamp'].isoformat()
    return (
            json_util.dumps(list_cur),
        200,
        {'Content-type': "application/json"}
    )


@areanamespace.route('/get/<area_id>', methods=['GET'])
def getAreas(area_id):
    if checkAreaIfExists(area_id,'active') == False:
        return json_response({"message": "Area Does Not Exists or it is InActive"})
    areas = aggregator_db[area_table]
    area = areas.find_one({"area_id":area_id});
    area['timestamp'] = area['timestamp'].isoformat()
    return (
        json_util.dumps(area),
        200,
        {'Content-type': "application/json"}
    )
@areanamespace.route('/addEdit', methods=['POST'])
def register():
    json_loaded = json.loads(request.data)
    json_loaded.update({'area_id': "area_" + getAutoId(area_table)})
    # Create a Database
    area_location = aggregator_db[area_table]
    # Populate the Collections
    json_loaded['timestamp'] = datetime.utcnow();
    res = area_location.insert_one(json_loaded)
    return (
        json.dumps({'Message': 'New Area Has been Created'}),
        200,
        {'Content-type': "application/json"}
    )
@areanamespace.route('/addEdit/<area_id>', methods=['PUT'])
def editlocation(area_id):
    if checkAreaIfExists(area_id,'active') == False:
        return json_response({"message": "Area Does Not Exists or it is InActive"})
    query = {"area_id":area_id}
    json_loaded = json.loads(request.data)
    areatable = aggregator_db[area_table]
    attribute_updates_dict = {"$set": {
        "polygons":json_loaded['polygons'],
        "timestamp":datetime.utcnow()
    }
    };
    areatable.update_one(query,attribute_updates_dict)
    return (
        json.dumps({'Message': 'Taxi Location Has been Updated'}),
        200,
        {'Content-type': "application/json"}
    )

@areanamespace.route('/changeStatus/<area_id>', methods=['PUT'])
def changeStatus(area_id):
    if checkAreaIfExists(area_id,None) == False:
        return json_response({"message": "Area Does Not Exists or it is InActive"})
    query = {"area_id": area_id}
    json_loaded = json.loads(request.data)
    area = aggregator_db[area_table]
    attribute_updates_dict = {"$set": {'status': json_loaded['status'], 'timestamp': datetime.utcnow()}};
    area.update_one(query, attribute_updates_dict)
    return json_response({"message": "Area Status changed !!"})

def checkArea(data):
    json_loaded = json.loads(data)
    area = aggregator_db[area_table]
    query = {"polygons": {"$geoIntersects":
                               {"$geometry": {"type": "Point","coordinates": json_loaded['location']}}},"status":"active"};

    cursor = area.count(query);
    return (cursor > 0)

def checkAreaIfExists(area_id,status = None):
    if status == None :
        query = {"area_id": area_id}
    else :
        query = {"area_id": area_id,"status": "active"}
    area = aggregator_db[area_table]
    count = area.count(query)
    if count == 0:
        return False
    else:
        return True


def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}
