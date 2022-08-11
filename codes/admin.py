from flask import request
import boto3
from flask import Flask
import json
from flask import Blueprint

adminnamespace = Blueprint('admin', __name__)

ddb = boto3.resource('dynamodb')
user_table= ddb.user_table('users')
taxi_table= ddb.user_table('taxis')

     
@adminnamespace.route('/getallusers', methods=['GET'])
def getlocationtaxis():
        users = user_table.scan()['Items']
        return (
			json.dumps(users),
			200,
			{'Content-type': "application/json"}
		)
  
@adminnamespace.route('/getalltaxisadmin/<taxi_id>', methods=['GET'])
def getlocationtaxistaxiid(taxi_id):
    key = {'taxi_id': taxi_id}
    student = taxi_table.get_item(Key=key).get('Item')
    if student:
        return json_response(student)
    else:
        return json_response({"message": "taxi not found"}, 404)

  
@adminnamespace.route('/addtaxitype', methods=['POST'])
def getlocationtaxistaxiid(taxi_id):
        taxi_table.put_item(Item=json.loads(request.data))
        return (
            json.dumps({'Message': 'trip entry created'}),
            200,
            {'Content-type': "application/json"}
        )

def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}