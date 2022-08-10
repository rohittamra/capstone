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

#Method to initialise the bulk users
@usernamespace.route('/bulkRegister', methods=['POST'])
def bulkRegister():
    json_loaded=json.loads(request.data)
    for user in json_loaded :
        user.update({'user_id': "user_"+getAutoId(user_table)})
    users = aggregator_db[user_table]
    users.insert_many(json_loaded)
    return (
        json.dumps({'Message': 'user entries are created'}),
        200,
        {'Content-type': "application/json"}
    )

#Method to initialise the bulk taxis
@taxinamespace.route('/bulkRegister', methods=['POST'])
def bulkRegister():
    json_loaded=json.loads(request.data)
    for taxi in json_loaded :
        taxi.update({'taxi_id': "taxi_"+getAutoId(taxi_table)})
    users = aggregator_db[taxi_table]
    users.insert_many(json_loaded)
    return (
        json.dumps({'Message': 'taxis has been registered'}),
        200,
        {'Content-type': "application/json"}
    )