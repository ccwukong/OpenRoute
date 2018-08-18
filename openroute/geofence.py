import copy
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from .models import Coordinates, GeoArea, Location

class GeoTools(object):
    @staticmethod
    def is_point_in_area(edge_locations, locations):
        polygon = []
        for item in edge_locations:
            polygon.append((item[0], item[1]))

        return [loc for loc in locations if Polygon(polygon).contains(Point(loc[0], loc[1]))]