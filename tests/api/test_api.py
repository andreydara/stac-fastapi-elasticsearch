# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '15 Nov 2021'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

import pytest


STAC_CORE_ROUTES = [
    "GET /",
    "GET /collections",
    "GET /collections/{collection_id}",
    "GET /collections/{collection_id}/items",
    "GET /collections/{collection_id}/items/{item_id}",
    "GET /conformance",
    "GET /search",
    "POST /search",
]

FILTER_EXTENSION_ROUTES = [
    "GET /queryables",
    "GET /collections/{collection_id}/queryables"
]


def test_core_router(api_client):
    """Test API serves all the core routes."""
    core_routes = set(STAC_CORE_ROUTES)
    api_routes = set(
        [f"{list(route.methods)[0]} {route.path}" for route in api_client.app.routes]
    )
    print(api_routes)

    assert not core_routes - api_routes


def test_filter_extension_router(api_client):
    """Test API serves all the routes for the filter extension."""
    filter_routes = set(FILTER_EXTENSION_ROUTES)
    api_routes = set(
        [f"{list(route.methods)[0]} {route.path}" for route in api_client.app.routes]
    )

    assert not filter_routes - api_routes


def test_app_search_response(app_client):
    """Check application returns a FeatureCollection"""

    resp = app_client.get("/search")
    assert resp.status_code == 200
    resp_json = resp.json()

    assert resp_json.get("type") == "FeatureCollection"


def test_app_context_extension(app_client):
    """Check context extension returns the correct number of results"""

    resp = app_client.get("/search")
    assert resp.status_code == 200
    resp_json = resp.json()

    assert "context" in resp_json
    assert resp_json["context"]["returned"] ==  resp_json["context"]["matched"] == 2


def test_search_for_collection(app_client):
    """Check searching for a collection"""
    
    # search for collection in items
    params = {
        "collections": ["Fj3reHsBhuk7QqVbt7P-"]
    }

    resp = app_client.post("/search", json=params)
    resp_json = resp.json()
    assert resp_json["context"]["returned"] == resp_json["context"]["matched"] == 2

    # search for collection that doesn't exist
    params = {
        "collections": ["Fj3reHsriut7QqVb34f*"]
    }

    resp = app_client.post("/search", json=params)
    resp_json = resp.json()
    assert resp_json["context"]["returned"] == resp_json["context"]["matched"] == 0

    # search for more than one collection
    params = {
        "collections": ["Fj3reHsriut7QqVb34f*", "Fj3reHsBhuk7QqVbt7P-"]
    }

    resp = app_client.post("/search", json=params)
    resp_json = resp.json()
    assert resp_json["context"]["returned"] == resp_json["context"]["matched"] == 2

def test_search_date_interval(app_client):
    """Check searching with a date interval"""
    
    params = {
        "datetime": "2013-12-01T00:00:00Z/2014-05-01T00:00:00Z"
    }

    resp = app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["context"]["returned"] == resp_json["context"]["matched"] == 1
    print(resp_json)
    assert resp_json["features"][0]["properties"]["datetime"] == "2014-04-09T00:00:00Z"


def test_search_invalid_date(app_client):
    """Given an invalid date, we should get a 400"""
    
    params = {
        "datetime": "2020-XX-01/2020-10-30",
    }
    resp = app_client.post("/search", json=params)
    assert resp.status_code == 400


def test_datetime_non_interval(app_client):
    """Checking search with a single date."""
    alternate_formats = [
        "2008-01-31T00:00:00+00:00",
        "2008-01-31T00:00:00.00Z",
        "2008-01-31T00:00:00Z",
        "2008-01-31T00:00:00.00+00:00",
    ]
    for date in alternate_formats:
        params = {
            "datetime": date,
        }
        resp = app_client.post("/search", json=params)
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["context"]["returned"] == resp_json["context"]["matched"] == 1
        assert resp_json["features"][0]["properties"]["datetime"][0:19] == date[0:19]


def test_search_point_intersects(app_client):
    """Check that items intersect with the given point.
    """

    point = [150.04, -33.14]
    intersects = {"type": "Point", "coordinates": point}

    params = {
        "intersects": intersects,
    }
    resp = app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


def test_search_line_string_intersects(app_client):
    """Test linestring intersect."""
    line = [[150.04, -33.14], [150.22, -33.89]]
    intersects = {"type": "LineString", "coordinates": line}

    params = {
        "intersects": intersects,
    }
    resp = app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


@pytest.mark.skip(reason="3d bbox query not supported by elasticsearch.")
def test_bbox_3d(app_client):
    """Test 3d bbox"""
    australia_bbox = [106.343365, -47.199523, 0.1, 168.218365, -19.437288, 0.1]
    params = {
        "bbox": australia_bbox,
    }
    
    resp = app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


def test_bbox(app_client):
    """Test bbox"""
    bbox = [106.343365, -47.199523, 168.218365, -19.437288]
    params = {
        "bbox": bbox,
    }
    
    resp = app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


@pytest.mark.skip(reason="Skipping for now. Need to change the mapping on the indices to "
                         "make collection_id and item_id keyword fields then update the "
                         "filter to reflect this change. There is a mismatch between the "
                         "test data and the production data, but the test data is how we want "
                         "it to be.")
def test_hierarchy(app_client):
    """Check the hierarchy flow.

        GET /
        GET /collections
        GET /collections/<collection_id>
        GET /collections/<collection_id>/items
        GET /collections/<collection_id>/items/<item_id>

    """

    resp = app_client.get("/")
    assert resp.status_code == 200

    resp = app_client.get("/collections")
    assert resp.status_code == 200

    collection_id = resp.json()['collections'][0]['id']
    resp = app_client.get(f"/collections/{collection_id}")
    assert resp.status_code == 200

    resp = app_client.get(f"/collections/{collection_id}/items")
    print(resp.json())
    assert resp.status_code == 200

    item_id = resp.json()['features'][0]['id']
    resp = app_client.get(f"/collections/{collection_id}/items/{item_id}")
    assert resp.status_code == 200
