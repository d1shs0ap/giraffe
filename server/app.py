from flask import Flask, request, jsonify
from flask_cors import CORS
import json

import sys
sys.path.insert(1, '../../pyserini')
sys.path.insert(1, '../../watersheds')

from pyserini.search.lucene import LuceneGeoSearcher
from pyserini.search.lucene._geo_searcher import JSort, JLatLonDocValuesField, JLatLonShape, JQueryRelation, JLongPoint
from pyserini.search.lucene import LuceneSearcher

from shapely.geometry import Point
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
from watersheds._base import Basin, River

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/", methods=['POST', 'GET'])
def rivers_search():
  if request.method == 'POST':
    req = request.json
    results = getGeometries(req['searchText'])
    return jsonify(results)
  
  elif request.method == 'GET':
    return "This is the endpoint for geo search."

def getGeometries(text):
  # get rivers and their mouths from text
  print("Searching for rivers in wiki...")
  searcher = LuceneSearcher('indexes/wikidata')
  hits = searcher.search(text, fields={'contents': 1.0}, k=5)
  
  # convert raw string results to json
  print("Converting string results to json...")
  results = []
  for i in range(len(hits)):
    raw = json.loads(hits[i].raw)
    results.append(raw)
  
  # get geometries of each river
  print("Getting geometries of rivers...")
  searcher = LuceneGeoSearcher('indexes/hydrorivers')
  
  for result in results:
    print(f"Getting geometry of {result['contents']}...")

    # query for initial segment
    query = JLatLonShape.newBoxQuery("geometry", JQueryRelation.INTERSECTS, -90, 90, -180, 180)
    sort = JSort(JLatLonDocValuesField.newDistanceSort("point", result['details']['coordinate'][0][1], result['details']['coordinate'][0][0]))
    hits = searcher.search(query, 1, sort)

    # trace segment down
    wkts = []
    cur_segment = json.loads(hits[0].raw)
    
    while cur_segment['NEXT_DOWN'] != 0:
      wkts.append(cur_segment['geometry'])
      
      nextQuery = JLongPoint.newExactQuery('HYRIV_ID', cur_segment['NEXT_DOWN'])
      hits = searcher.search(nextQuery, 1)
      cur_segment = json.loads(hits[0].raw)
    
    wkts.append(cur_segment['geometry'])

    # WKT string -> Shapely shape -> coordinates of each segment[]
    segments = gpd.GeoSeries.from_wkt(wkts)
    # reverse the coordinates to be [lat, lon]
    result['geometry'] = [[[p[1], p[0]] for p in list(line.coords)] for line in segments]

    # set zoom bounds, first point bottom left and second point top right
    result['bounds'] = [ 
      [min([min(line, key=lambda p: p[0]) for line in result['geometry']], key=lambda p: p[0])[0], min([min(line, key=lambda p: p[1]) for line in result['geometry']], key=lambda p: p[1])[1]],
      [max([max(line, key=lambda p: p[0]) for line in result['geometry']], key=lambda p: p[0])[0], max([max(line, key=lambda p: p[1]) for line in result['geometry']], key=lambda p: p[1])[1]]
    ]

  return results

if __name__ == "__main__":
  getGeometries('Ob')

  # na_basin = Basin()
  # na_river = River()

  # res = []
  
  # for result in results:
  #   # process river only if we have both mouth and source
  #   if len(result['details']['coordinate']) < 2:
  #     continue
    
  #   # put mouth and source into Point
  #   stl_river_mouth_point = Point(result['details']['coordinate'][0][0], result['details']['coordinate'][0][1])
  #   stl_river_source_point = Point(result['details']['coordinate'][1][0], result['details']['coordinate'][1][1])

  #   # get basins near mouth and source
  #   result_mouth = na_basin.find_point_belongs_to(stl_river_mouth_point)
  #   result_source = na_basin.find_point_belongs_to(stl_river_source_point)

  #   # if they don't exist (probably because not in NA, skip)
  #   if not result_mouth or not result_source:
  #     continue

  #   # Get all basins and river IDs in those basins
  #   all_btw_basins = na_basin.find_basins_btw_source_mouth(result_source[0], result_mouth[0])
  #   all_btw_rivers = na_river.get_rivers_id_in_basins(all_btw_basins)

  #   # Get all coordinates using river IDs
  #   geo_stlr_rivers = [gpd.GeoSeries(na_river.get_geo_by_id(item)) for item in all_btw_rivers]
  #   print(na_river.get_geo_by_id(all_btw_rivers[0]))
    
  #   result['geometry'] = geo_stlr_rivers
  #   res.append(result)
  
  # print(res)



