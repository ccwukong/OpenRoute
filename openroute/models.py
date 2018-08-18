import json
import pickle


class Driver(object):
    def __init__(self, id, time_slots, capacity, speed, ref=''):
        self._id = id
        self._time_slots = time_slots
        self._capacity = capacity
        self._speed = speed
        self._ref = ref

    @property
    def id(self):
        return self._id

    @property
    def time_slots(self):
        return self._time_slots

    @property
    def capacity(self):
        return self._capacity

    @property
    def speed(self):
        return self._speed

    @property
    def ref(self):
        return self._ref

    def to_json(self):
        return {'id': self._id,
                'time_slots': self._time_slots,
                'capacity': self._capacity,
                'speed': self._speed,
                'ref': self._ref}


class Location(object):
    def __init__(self, coordinates, address, delivery_window,
                 capacity, order_time=0, ref=''):
        if not isinstance(coordinates, Coordinates):
            raise TypeError('Coordinates object expected.')

        self._coordinates = coordinates.coordinates
        self._address = address
        self._delivery_window = delivery_window
        self._capacity = capacity
        self._order_time = order_time
        self._ref = ref

    @property
    def coordinates(self):
        return self._coordinates

    @property
    def address(self):
        return self._address

    @property
    def delivery_window(self):
        return self._delivery_window

    @property
    def order_time(self):
        return self._order_time

    @property
    def capacity(self):
        return self._capacity

    @property
    def ref(self):
        return self._ref

    def to_json(self):
        m, s = divmod(self._delivery_window[0], 60)
        h, m = divmod(m, 60)
        fr = '%02d:%02d' % (h, m)

        m, s = divmod(self._delivery_window[1], 60)
        h, m = divmod(m, 60)
        to = '%02d:%02d' % (h, m)
        return {'coordinates': [self._coordinates[0], self._coordinates[1]],
                'address': self._address,
                'delivery_window': [fr, to],
                'order_time': self._order_time,
                'capacity': self._capacity,
                'ref': self._ref}


class Coordinates(object):
    def __init__(self, latitude, longitude):
        self._latitude = latitude
        self._longitude = longitude

    @property
    def coordinates(self):
        return [self._latitude, self._longitude]

    def to_json(self):
        return {'coordinates': [self._latitude, self._longitude]}


class GeoArea(object):
    _edge_locations = []
    _locations = []

    @property
    def edge_locations(self):
        return self._edge_locations

    @edge_locations.setter
    def edge_locations(self, edge_locations):
        self._edge_locations = edge_locations

    @property
    def locations(self):
        return self._locations

    @locations.setter
    def locations(self, locations):
        self._locations = locations

    def __str__(self):
        return pickle.dumps(self.__dict__)


class Wave(object):
    def __init__(self, cutoff_time):
        self._cutoff_time = cutoff_time

    @property
    def cutoff_time(self):
        return self._cutoff_time

    def __str__(self):
        return self.__dict__
