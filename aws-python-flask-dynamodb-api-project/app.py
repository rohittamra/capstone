#import os
from codes_mongodb.area_registration import areanamespace
from codes_mongodb.taxi import taxinamespace
from codes_mongodb.taxi_location import taxilocationnamespace
from codes_mongodb.trip import tripnamespace
from codes_mongodb.user import usernamespace
from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

app.register_blueprint(taxinamespace, url_prefix='/taxi')
app.register_blueprint(taxilocationnamespace, url_prefix='/taxi-location')
app.register_blueprint(tripnamespace, url_prefix='/trip')
app.register_blueprint(areanamespace, url_prefix='/area')
app.register_blueprint(usernamespace, url_prefix='/user')

@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
