from flask import request
import boto3
from flask import Flask
import json
from flask import Blueprint

tripnamespace = Blueprint('trip', __name__)
ddb = boto3.resource('dynamodb')
trip_table= ddb.Table('trips')


@tripnamespace.route('/getalltrips', methods=['GET'])
def getalltrips():
        trips = trip_table.scan()['Items']
        return (
			json.dumps(trips),
			200,
			{'Content-type': "application/json"}
		)
        
@tripnamespace.route('/addtrip', methods=['POST'])
def addtrip():
        trip_table.put_item(Item=json.loads(request.data))
        return (
            json.dumps({'Message': 'trip entry created'}),
            200,
            {'Content-type': "application/json"}
        )
  
@tripnamespace.route('/getparticulartrip/<trip_id>', methods=['GET'])
def getlocationtaxistaxiid(trip_id):
    key = {'trip_id': trip_id}
    trip = trip_table.get_item(Key=key).get('Item')
    if trip:
        return json_response(trip)
    else:
        return json_response({"message": "taxi not found"}, 404)

def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}