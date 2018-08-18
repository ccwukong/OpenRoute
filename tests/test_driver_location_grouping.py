# import os
# import sys
# import unittest
# from decimal import Decimal
# current_path = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, current_path + '/../')
# from openroute.models import Driver, Location, Coordinates
# from openroute.grouping import DriverGrouping, LocationGrouping
# from openroute.optimize import Routing


# class TestDriverLocationGrouping(unittest.TestCase):
#     def setUp(self):
#         self._drivers = [
#             {
#                 'id': 981,
#                 'time_slots': [[53000, 61600], [30000, 42000]],
#                 'capacity': 100,
#                 'speed': 20
#             }, {
#                 'id': 1000,
#                 'time_slots': [[53000, 61600], [30000, 42000]],
#                 'capacity': 16,
#                 'speed': 5
#             }]

#         self._locations = [
#             {
#                 'coordinates': [-33.8815474, 150.9625217],
#                 'delivery_window': [64800, 72000],
#                 'capacity': 7.8,
#                 'order_time': 30660
#             }, {
#                 'coordinates': [-33.8322542, 151.0548105],
#                 'delivery_window': [32400, 39600],
#                 'capacity': 15.8,
#                 'order_time': 33600
#             }, {
#                 'coordinates': [-33.881716, 150.9136746],
#                 'delivery_window': [32400, 39600],
#                 'capacity': 3.8,
#                 'order_time': 45000
#             }, {
#                 'coordinates': [-33.9545249, 150.9406193],
#                 'delivery_window': [54000, 61200],
#                 'capacity': 35.5,
#                 'order_time': 55800
#             }]

#     def test_driver_schedule_grouping(self):
#         self.assertRaises(TypeError, lambda: DriverGrouping().group(
#             drivers=self._drivers,
#             locations=self._locations))

#         result = DriverGrouping().group(
#             drivers=[Driver(id=item.get('id'),
#                             time_slots=item.get('time_slots'),
#                             capacity=item.get('capacity'),
#                             speed=item.get('speed')) for
#                      item in self._drivers],
#             locations=[Location(
#                 coordinates=Coordinates(item.get('coordinates')[0],
#                                         item.get('coordinates')[1]),
#                 address=item.get('address'),
#                 delivery_window=item.get('delivery_window'),
#                 capacity=item.get('capacity'),
#                 order_time=item.get('order_time')) for
#                         item in self._locations])

#         self.assertEqual(len(list(result.items())), 3)

#     def test_driver_schedule_multiple_pickup_windows_grouping(self):
#         drivers = [{
#                 'id': 1,
#                 'name': 'Driver 1',
#                 'time_slots': [[0, 43140], [43140, 79200]],
#                 'capacity': 500,
#                 'speed': 50
#             }, {
#                 'id': 2,
#                 'name': 'Driver 2',
#                 'time_slots': [[0, 43140]],
#                 'capacity': 400,
#                 'speed': 50
#             }, {'id': 3,
#                 'name': 'Driver 3',
#                 'time_slots': [[0, 43140]],
#                 'capacity': 500,
#                 'speed': 50
#             }, {'id': 4,
#                 'name': 'Driver 4',
#                 'time_slots': [[28800, 43140]],
#                 'capacity': 500,
#                 'speed': 50
#             }, {'id': 5,
#                 'name': 'Driver 5',
#                 'time_slots': [[28800, 79200]],
#                 'capacity': 500,
#                 'speed': 50
#             }, {'id': 6,
#                 'name': 'Driver 6',
#                 'time_slots': [[0, 43140]],
#                 'capacity': 500,
#                 'speed': 50
#             }, {'id': 7,
#                 'name': 'Driver 7',
#                 'time_slots': [[0, 43140], [58800, 80000]],
#                 'capacity': 500,
#                 'speed': 50
#             }, {'id': 8,
#                 'name': 'Driver 8',
#                 'time_slots': [[28800, 79200]],
#                 'capacity': 500,
#                 'speed': 50
#             }, {'id': 9,
#                 'name': 'Driver 9',
#                 'time_slots': [[0, 79200]],
#                 'capacity': 500,
#                 'speed': 50
#             }, {'id': 10,
#                 'name': 'Driver 10',
#                 'time_slots': [[0, 50800], [60400, 89200]],
#                 'capacity': 800,
#                 'speed': 60
#             }]

#         locations = {
#             (1.3001, 102.0001):
#             {
#                 (12000, 20000):
#                 [
#                     {
#                         'coordinates': [-33.8815474, 150.9625217],
#                         'address': 'pick up 1',
#                         'delivery_window': [12000, 20000],
#                         'capacity': 0,
#                         'order_time': 30660
#                     }, {
#                         'coordinates': [-33.8322542, 151.0548105],
#                         'address': 'Delivery 1',
#                         'delivery_window': [16400, 39600],
#                         'capacity': 65.8,
#                         'order_time': 33600
#                     }, {
#                         'coordinates': [-33.881716, 150.9136746],
#                         'address': 'Delivery 2',
#                         'delivery_window': [22400, 39600],
#                         'capacity': 43.8,
#                         'order_time': 45000
#                     }
#                 ],
#                 (52000, 58600):
#                 [
#                     {
#                         'coordinates': [-33.8815431, 151.9234],
#                         'address': 'pickup 2',
#                         'delivery_window': [54800, 58600],
#                         'capacity': 0,
#                         'order_time': 30660
#                     }, {
#                         'coordinates': [-32.8311, 152.2341],
#                         'address': 'delivery 3',
#                         'delivery_window': [60000, 68000],
#                         'capacity': 15.8,
#                         'order_time': 33600
#                     }
#                 ]
#             },
#             (1.3002, 102.0002):
#             {
#                 (40000, 44000):
#                 [{
#                     'coordinates': [-33.9545249, 150.9406193],
#                     'address': 'pickup 3',
#                     'delivery_window': [40000, 44000],
#                     'capacity': 0,
#                     'order_time': 55800
#                 }, {
#                     'coordinates': [-33.9375904, 150.8350134],
#                     'address': 'delivery 4',
#                     'delivery_window': [44000, 61200],
#                     'capacity': 15.5,
#                     'order_time': 35800
#                 }, {
#                     'coordinates': [-33.8800401, 151.1104426],
#                     'address': 'delivery 5',
#                     'delivery_window': [44000, 61200],
#                     'capacity': 25,
#                     'order_time': 45800
#                 }]
#             },
#             (1.3003, 102.0003):
#                 {(20000, 26800):
#                 [{
#                     'coordinates': [-33.7171208, 151.0952565],
#                     'address': 'pickup 4',
#                     'delivery_window': [20000, 26800],
#                     'capacity': 0,
#                     'order_time': 55800
#                 }, {
#                     'coordinates': [-33.9545249, 150.9406193],
#                     'address': 'delivery 6',
#                     'delivery_window': [36000, 41200],
#                     'capacity': 35.5,
#                     'order_time': 55800
#                 }]
#             }
#         }

#         schedules = DriverGrouping().group_drivers_by_time_slot(
#             drivers=[Driver(id=item.get('id'),
#                             time_slots=item.get('time_slots'),
#                             capacity=item.get('capacity'),
#                             speed=item.get('speed')) for item in drivers])

#         data = LocationGrouping().group_locations(locations, schedules)

#         self.assertEqual(len(data), 2)
