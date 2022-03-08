from flask import Flask, request, jsonify
from flask_cors import CORS

import sys
sys.path.insert(1, '../../pyserini')

from pyserini.search.lucene import LuceneGeoSearcher
from pyserini.search.lucene._geo_searcher import JSort, JLatLonDocValuesField, JLatLonShape, JQueryRelation

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/", methods=['POST', 'GET'])
def rivers_search():
  if request.method == 'POST':
    req = request.json
    
    print(req['searchText'])

    # get mouths of river coords from req['searchText']. list of [lat, lon]
    

    # get river segments from mouths of geo coords
    searcher = LuceneGeoSearcher('indexes/hydrorivers')
    query = JLatLonShape.newBoxQuery("geometry", JQueryRelation.INTERSECTS, 43, 44, -78, -77);
    hits = searcher.search(query)
    print(hits)
    # trace upstream to get entire rivers
    

    # return json containing matching rivers coords and metadata
    return jsonify({"hi": "bye"})
  
  elif request.method == 'GET':
    return "This is the endpoint for geo search."


def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']

if __name__ == "__main__":
  searcher = LuceneGeoSearcher('indexes/hydrorivers')
  print(props(JQueryRelation))

  query = JLatLonShape.newBoxQuery("geometry", JQueryRelation.INTERSECTS, 43, 44, -78, -77)
  sort = JSort(JLatLonDocValuesField.newDistanceSort("point", -35, 0))
  hits = searcher.search(query, 2, sort)
  print(hits[0].raw)