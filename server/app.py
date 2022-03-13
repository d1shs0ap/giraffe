from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from collections import deque

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

basin = Basin()

@app.route("/", methods=['POST', 'GET'])
def rivers_search():
  if request.method == 'POST':
    req = request.json
    results = get_geometries(req['searchText'])
    return jsonify(results)
  
  elif request.method == 'GET':
    return "This is the endpoint for geo search."

def get_mouth_segment(result, searcher):
  # if we have the mouth, or we have neither the mouth nor the source
  if (1 in result['details']['coordinate_state']) or (1 not in result['details']['coordinate_state'] and 0 not in result['details']['coordinate_state']):
    mouth_index = 0
    if 1 in result['details']['coordinate_state']:
      mouth_index = result['details']['coordinate_state'].index(1)

    # query for initial segment
    query = JLatLonShape.newBoxQuery("geometry", JQueryRelation.INTERSECTS, -90, 90, -180, 180)
    sort = JSort(JLatLonDocValuesField.newDistanceSort("point", result['details']['coordinate'][mouth_index][1], result['details']['coordinate'][mouth_index][0]))
    hits = searcher.search(query, 1, sort)
    mouth_segment = json.loads(hits[0].raw)

  # if we only have the source, trace down to the bottom to get mouth segment
  elif 0 in result['details']['coordinate_state']:
    # get source coordinate index
    source_index = result['details']['coordinate_state'].index(0)

    # query for source segment
    query = JLatLonShape.newBoxQuery("geometry", JQueryRelation.INTERSECTS, -90, 90, -180, 180)
    sort = JSort(JLatLonDocValuesField.newDistanceSort("point", result['details']['coordinate'][source_index][1], result['details']['coordinate'][source_index][0]))
    hits = searcher.search(query, 1, sort)
    mouth_segment = json.loads(hits[0].raw)

    # move down the river to eventually end up with the mouth segment
    while mouth_segment['NEXT_DOWN'] != 0:
      nextQuery = JLongPoint.newExactQuery('HYRIV_ID', mouth_segment['NEXT_DOWN'])
      hits = searcher.search(nextQuery, 1)
      mouth_segment = json.loads(hits[0].raw)
  
  return mouth_segment

def bfs(result, searcher, mouth_segment):
  # keep track of river geometries and basin ids
  wkts = []
  main_riv_ids = set()
  basin_ids = set()

  # bfs from mouth segment
  q = deque([mouth_segment])
  while q:
    cur_segment = q.popleft()

    wkts.append(cur_segment['geometry'])
    main_riv_ids.add(cur_segment['MAIN_RIV'])
    basin_ids.add(cur_segment['HYBAS_L12'])

    query = JLongPoint.newExactQuery('NEXT_DOWN', cur_segment['HYRIV_ID'])
    hits = searcher.search(query, 10000000)
    for hit in hits:
      q.append(json.loads(hit.raw))

  # convert river wkt to list
  segments = gpd.GeoSeries.from_wkt(wkts)
  result['geometry'] = [[[p[1], p[0]] for p in list(line.coords)] for line in segments]

  # convert main river wkt to list
  print(main_riv_ids)
  main_riv_wkts = []
  for id in main_riv_ids:
    main_riv_query = JLongPoint.newExactQuery('HYRIV_ID', id)
    main_riv_hits = searcher.search(main_riv_query, 1)
    main_riv = json.loads(main_riv_hits[0].raw)
    main_riv_wkts.append(main_riv['geometry'])

  main_riv_segments = gpd.GeoSeries.from_wkt(main_riv_wkts)
  result['main_riv_geometry'] = [[[p[1], p[0]] for p in list(line.coords)] for line in main_riv_segments]

  # convert basins ids to basin geometries
  basin_polygons = []
  for id in basin_ids:
    basin_polygons.append(basin.get_geo_by_id(id))

  result['basin_geometry'] = []
  for multipolygon in basin_polygons:
    for polygon in multipolygon.geoms:
      result['basin_geometry'].append([[[p[1], p[0]] for p in list(polygon.exterior.coords)], []])

def get_geometries(text):
  # get rivers and their mouths from text
  print("Searching for rivers in wiki...")
  searcher = LuceneSearcher('indexes/wikidata')
  hits = searcher.search(text, fields={'contents': 1.0}, k=2)
  searcher.close()
  
  # convert raw string results to json
  print("Converting string results to json...")
  results = []
  for i in range(len(hits)):
    raw = json.loads(hits[i].raw)
    results.append(raw)
  
  # get geometries of each river
  print("Getting geometries of rivers...")
  searcher = LuceneGeoSearcher('indexes/hydrorivers')
  
  for i, result in enumerate(results):
    print(f"Getting mouth segment of {result['contents']}...")
    print(result)
    mouth_segment = get_mouth_segment(result, searcher)
    print(mouth_segment)


    print(f"BFS on {result['contents']}...")
    bfs(result, searcher, mouth_segment)

    # set zoom bounds, first point bottom left and second point top right
    result['bounds'] = [ 
      [min([min(line, key=lambda p: p[0]) for line in result['geometry']], key=lambda p: p[0])[0], min([min(line, key=lambda p: p[1]) for line in result['geometry']], key=lambda p: p[1])[1]],
      [max([max(line, key=lambda p: p[0]) for line in result['geometry']], key=lambda p: p[0])[0], max([max(line, key=lambda p: p[1]) for line in result['geometry']], key=lambda p: p[1])[1]]
    ]

    # set key
    result['key'] = i

  return results
