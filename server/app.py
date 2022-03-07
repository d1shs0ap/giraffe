from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/", methods=['POST', 'GET'])
def rivers_search():
  if request.method == 'POST':
    req = request.json
    
    print(req['searchText'])
    
    # below functionalities should be executed:
      # get mouths of river coords from req['searchText']
      # get river segments from mouths of geo coords
      # trace upstream to get entire rivers
      # return json containing matching rivers coords and metadata
    
    return jsonify({"hi": "bye"})
  
  elif request.method == 'GET':
    return "This is the endpoint for geo search."