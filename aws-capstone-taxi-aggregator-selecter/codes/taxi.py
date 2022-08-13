
from flask import request
import boto3
import json
from flask import Blueprint


taxinamespace = Blueprint('taxi', __name__)

ddb = boto3.resource('dynamodb')
taxi_table= ddb.Table('taxis')
taxi_location_table= ddb.Table('taxi_location')

# @taxinamespace.route('/', methods=['GET'])
# def test():
#         return (
# 			json.dumps({'msg':'asdksadj'}),
# 			200,
# 			{'Content-type': "application/json"}
# 		)

@taxinamespace.route('/getalltaxis', methods=['GET'])
def getalltaxis():
        users = taxi_table.scan()['Items']
        return (
			json.dumps(users),
			200,
			{'Content-type': "application/json"}
		)
        
@taxinamespace.route('/getlocationtaxis', methods=['GET'])
def getlocationtaxis():
        users = taxi_location_table.scan()['Items']
        return (
			json.dumps(users),
			200,
			{'Content-type': "application/json"}
		)
  
@taxinamespace.route('/getlocationtaxis/<taxi_id>', methods=['GET'])
def getlocationtaxistaxiid(taxi_id):
    key = {'taxi_id': taxi_id}
    print(type(key))
    taxi = taxi_location_table.get_item(Key=key).get('Item')
    if taxi:
        return json_response(taxi)
    else:
        return json_response({"message": "taxi not found"}, 404)

@taxinamespace.route('/edittaxi/<taxi_id>', methods=['PATCH'])
def edittaxitaxiid(taxi_id):
    json_loaded=json.loads(request.data)
    attribute_updates_dict = ({ 
            'contact': json_loaded["contact"],
            'driver_name': json_loaded["driver_name"],
            'status': json_loaded["status"],
            'type': json_loaded["type"]
            })
    # print(attribute_updates_dict)
    attribute_updates = {key: {'Value': value, 'Action': 'PUT'}
                            for key, value in attribute_updates_dict.items()}
    taxi_table.update_item( Key={'taxi_id': taxi_id },  AttributeUpdates=attribute_updates )
    return json_response({"message": "taxi entry updated"})
    
@taxinamespace.route('/edittaxilocation/<taxi_id>', methods=['PATCH'])
def edittaxilocationtaxiid(taxi_id):
    json_loaded=json.loads(request.data)
    attribute_updates_dict = ({ 
            'lat': json_loaded["lat"],
            'long': json_loaded["long"]
            })
    attribute_updates = {key: {'Value': value, 'Action': 'PUT'}
                            for key, value in attribute_updates_dict.items()}
    taxi_location_table.update_item( Key={'taxi_id': taxi_id },  AttributeUpdates=attribute_updates )
    return json_response({"message": "taxi location entry updated"})

@taxinamespace.route('/addtaxi', methods=['POST'])
def addtaxi():
    taxi_table.put_item(Item=json.loads(request.data))
    return (
        json.dumps({'Message': 'taxi entry created'}),
        200,
        {'Content-type': "application/json"}
    )
  
@taxinamespace.route('/addtaxilocations', methods=['POST'])
def addtaxilocations():
    print(type(request.data))
    taxi_location_table.put_item(Item=json.loads(request.data))
    return (
        json.dumps({'Message': 'taxilocation entry created'}),
        200,
        {'Content-type': "application/json"}
    )
              
@taxinamespace.route('/deletetaxi/<taxi_id>', methods=['POST'])
def deletetaxitaxiid(taxi_id):
        attribute_updates_dict = ({ 
                'status': 'Unavailable'
                })
        attribute_updates = {key: {'Value': value, 'Action': 'PUT'}
                                for key, value in attribute_updates_dict.items()}
        taxi_table.update_item( Key={'taxi_id': taxi_id },  AttributeUpdates=attribute_updates )
        return json_response({"message": "taxi marked Unavailable"})

def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}