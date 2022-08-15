import json

import pymongo as pymongo
import os
from flask import Blueprint

managenamespace = Blueprint('manage', __name__)

db_uri = os.environ['DB_URI']
aggregator_db = os.environ['DB_NAME']

client = pymongo.MongoClient(db_uri)
aggregator_db = client[aggregator_db]

@managenamespace.route('/cleanup/<table_name>', methods=['GET'])
def cleanup(table_name):
    if table_name == 'all':
        client.drop_database(aggregator_db)
    else :
        table = aggregator_db[os.environ[table_name]];
        table.drop();
    return (
        json.dumps({'Message': 'Tables has been dropped'}),
        200,
        {'Content-type': "application/json"}
    )


