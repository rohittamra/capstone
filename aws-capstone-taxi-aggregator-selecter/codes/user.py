from flask import request
import boto3
from flask import Flask
import json
#import secrets
#from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode as b64d
#from cryptography.fernet import Fernet
#from cryptography.hazmat.backends import default_backend
#from cryptography.hazmat.primitives import hashes
#from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from boto3.dynamodb.conditions import Key
from flask import Blueprint

#backend = default_backend()
iterations = 100_000
secret_key='capstone'

usernamespace = Blueprint('user', __name__)
ddb = boto3.resource('dynamodb')
user_table= ddb.Table('users')
user_location_table= ddb.Table('user_location')
taxi_table= ddb.Table('taxis')

@usernamespace.route('/getallusers', methods=['GET'])
def getallusers():
        users = user_table.scan(
                FilterExpression=Key('status').eq('Active')
            )['Items']
        return (
			json.dumps(users),
			200,
			{'Content-type': "application/json"}
		)

@usernamespace.route('/deleteuser/<user_id>', methods=['POST'])
def deleteuseruserid(user_id):
        attribute_updates_dict = ({ 
                'status': 'Unavailable'
                })
        attribute_updates = {key: {'Value': value, 'Action': 'PUT'}
                                for key, value in attribute_updates_dict.items()}
        user_table.update_item( Key={'user_id': user_id },  AttributeUpdates=attribute_updates )
        return json_response({"message": "user marked Unavailable"})
          
@usernamespace.route('/edituser/<user_id>/<email>', methods=['PATCH'])
def edituseruserid(user_id,email):
    json_loaded=json.loads(request.data)
    attribute_updates_dict = ({ 
            'contact': json_loaded["contact"],
            'fname': json_loaded["fname"],
            'secondname': json_loaded["secondname"]
            })
    attribute_updates = {key: {'Value': value, 'Action': 'PUT'}
                            for key, value in attribute_updates_dict.items()}
    user_table.update_item( Key={'user_id': user_id, 'email': email },  AttributeUpdates=attribute_updates )
    return json_response({"message": "user entry updated"})
    
@usernamespace.route('/edituserlocation/<user_id>', methods=['PATCH'])
def edituserlocationuserid(user_id):
    json_loaded=json.loads(request.data)
    attribute_updates_dict = ({ 
            'lat': json_loaded["lat"],
            'long': json_loaded["long"]
            })
    attribute_updates = {key: {'Value': value, 'Action': 'PUT'}
                            for key, value in attribute_updates_dict.items()}
    user_location_table.update_item( Key={'user_id': user_id },  AttributeUpdates=attribute_updates )
    return json_response({"message": "user location entry updated"})


@usernamespace.route('/getspecificuser/<user_id>', methods=['GET'])
def getspecificuser(user_id):
    user = user_table.scan(
                FilterExpression=Key('user_id').eq(user_id) & Key('status').eq('Active') 
            )['Items']
    if not user:
        return json_response({"message": "user not found or deactivate"}, 404)
    users=user[0]
    user_location = user_location_table.scan(
            FilterExpression=Key('user_id').eq(user_id) 
        )['Items']
    if not user_location:
        return json_response({"message": "user location not found"}, 404)
    print(user_location)
    for key,value in user_location[0].items():
        users[key]=value
    return (
			json.dumps(users),
			200,
			{'Content-type': "application/json"}
		)

# @usernamespace.route('/login', methods=['POST'])
# def login():
#     json_loaded=json.loads(request.data)
#     email_entered=json_loaded["email"]
#     password_entered=json_loaded["password"]
#     #users = user_table.scan()['Items']
#     users = user_table.scan(
#                 FilterExpression=Key('email').eq(email_entered),
#                 ProjectionExpression='password'
#             )['Items']
#     if not users:
#         return json_response({'Message': 'email id not found'},404)
#     else:
#         password=users[0]['password']
#   #      password_decrypted=password_decrypt(password, secret_key).decode()
#         if password_decrypted== password_entered:
#             return json_response({'Message': 'Login Successful'})
#         else:
#             return json_response({'Message': 'Email or password wrong'},400)

@usernamespace.route('/register', methods=['POST'])
def register():
    json_loaded=json.loads(request.data)
    user_id=json_loaded["user_id"]
    password=json_loaded["password"]
#    encryted_pass=password_encrypt(password.encode(), secret_key)
 #   json_loaded['password']=str(encryted_pass.decode("utf-8"))
    json_converted=bytes(json.dumps(json_loaded), 'utf-8')
    user_location_table.put_item(Item=json.loads(bytes(json.dumps({'user_id': user_id,'lat': '99.99' ,'long': '99.99'}),'utf-8')))
    user_table.put_item(Item=json.loads(json_converted))
    return (
        json.dumps({'Message': 'user entry created'}),
        200,
        {'Content-type': "application/json"}
    )

@usernamespace.route('/booktaxi/<taxi_id>', methods=['POST'])
def bookuser():
        #code yet to write
        return (
			json.dumps({'Message': 'Yet to code'}),
			200,
			{'Content-type': "application/json"}
		)
        
def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}
#
# def _derive_key(password: bytes, salt: bytes, iterations: int = iterations) -> bytes:
#     """Derive a secret key from a given password and salt"""
#     kdf = PBKDF2HMAC(
#         algorithm=hashes.SHA256(), length=32, salt=salt,
#         iterations=iterations, backend=backend)
#     return b64e(kdf.derive(password))
#
# def password_encrypt(message: bytes, password: str, iterations: int = iterations) -> bytes:
#     salt = secrets.token_bytes(16)
#     key = _derive_key(password.encode(), salt, iterations)
#     return b64e(
#         b'%b%b%b' % (
#             salt,
#             iterations.to_bytes(4, 'big'),
#             b64d(Fernet(key).encrypt(message)),
#         )
#     )
#
# def password_decrypt(token: bytes, password: str) -> bytes:
#     decoded = b64d(token)
#     salt, iter, token = decoded[:16], decoded[16:20], b64e(decoded[20:])
#     iterations = int.from_bytes(iter, 'big')
#     key = _derive_key(password.encode(), salt, iterations)
#     return Fernet(key).decrypt(token)