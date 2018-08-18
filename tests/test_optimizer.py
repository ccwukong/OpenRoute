import os
import sys
import time
import unittest
current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_path + '/../')
from decimal import Decimal
from openroute.optimize import Routing
from openroute.models import Driver, Location, Coordinates
from openroute.grouping import DriverGrouping, LocationGrouping
from data import drivers, locations, drivers_merge, locations_merge, \
    locations4, drivers4


class TestOptimizer(unittest.TestCase):
    # def test_optimization_with_predefined_data(self):
    #     schedules = DriverGrouping().group_drivers_by_time_slot(
    #         drivers=[Driver(id=item.get('id'),
    #                         time_slots=item.get('time_slots'),
    #                         capacity=item.get('capacity'),
    #                         speed=item.get('speed')) for item in drivers])

    #     data, _ = LocationGrouping().group_locations(locations,
    #                                                  schedules,
    #                                                  True)

    #     self.assertEqual(len(_), 0)

    #     inhouse = []
    #     for pickup_address, pickup_windows in data.items():
    #         for pickup_window, obj in pickup_windows.items():
    #             locs = obj.get('locations')
    #             driver_ids = obj.get('driver_ids')
    #             while locs and driver_ids:
    #                 driver = None 
    #                 for item in drivers:
    #                     if item.get('id') == driver_ids[0]:
    #                         driver = item
    #                         break

    #                 filtered_indices = []
    #                 for k, v in enumerate(locs):
    #                     if v.capacity <= driver.get('capacity'):
    #                         filtered_indices.append(k)

    #                 indices = Routing(
    #                     locations=[loc for loc in locs if
    #                                loc.capacity <= driver.get('capacity')],
    #                     num_vehicles=len(locs)).generate_routes(
    #                         vehicle_capacity=driver.get('capacity'),
    #                         speed=driver.get('speed'),
    #                         service_time_unit=1800)

    #                 if len(indices) == 0:
    #                     print(driver.get('id'))
    #                     print(indices)
    #                     break
    #                 else:
    #                     # remove driver from available driver
    #                     # list only if a route has been built
    #                     driver_id = driver_ids.pop(0)

    #                     routes = []
    #                     for item in indices[0]:
    #                         if ';' in locs[filtered_indices[item]].ref:
    #                             for sub_item in locs[filtered_indices[item]].ref.split(';'):
    #                                 itm_info = sub_item.split(',')
    #                                 routes.append(
    #                                     Location(coordinates=Coordinates(
    #                                                 locs[filtered_indices[item]].coordinates[0], 
    #                                                 locs[filtered_indices[item]].coordinates[1]),
    #                                              address=locs[filtered_indices[item]].address,
    #                                              delivery_window=locs[filtered_indices[item]].delivery_window,
    #                                              capacity=float(itm_info[1]),
    #                                              ref=itm_info[0]))
    #                         else:
    #                             routes.append(locs[filtered_indices[item]])
    #                         if filtered_indices[item] != 0:
    #                             locs[filtered_indices[item]] = None
    #                     inhouse.append({driver_id: routes})
    #                     locs = list(filter(lambda x: x is not None, locs))
    #             obj['locations'] = locs if len(locs) > 1 else []

    #     public = []
    #     for pickup_address, pickup_windows in data.items():
    #         for pickup_window, obj in pickup_windows.items():
    #             locs = obj.get('locations')
    #             if locs:
    #                 indices = Routing(
    #                             locations=locs,
    #                             num_vehicles=len(locs)).generate_routes(
    #                                 vehicle_capacity=30,
    #                                 speed=30,
    #                                 service_time_unit=1800)

    #                 if len(indices) == 0:
    #                     break
    #                 else:
    #                     for idx_list in indices:
    #                         routes = []

    #                         for item in idx_list:
    #                             if ';' in locs[item].ref:
    #                                 for sub_item in locs[item].ref.split(';'):
    #                                     itm_info = sub_item.split(',')
    #                                     routes.append(
    #                                         Location(
    #                                             coordinates=Coordinates(
    #                                                 locs[item].coordinates[0],
    #                                                 locs[item].coordinates[1]),
    #                                             address=locs[item].address,
    #                                             delivery_window=locs[item].delivery_window,
    #                                             capacity=float(itm_info[1]),
    #                                             ref=itm_info[0]))
    #                             else:
    #                                 routes.append(locs[item])

    #                             if item != 0:
    #                                 locs[item] = None
    #                         public.append(routes)
    #                     locs = list(filter(lambda x: x is not None, locs))
    #                     obj['locations'] = locs if len(locs) > 1 else []

    #     inhouse, public = Routing.merge_routes(inhouse_routes=inhouse,
    #                                            public_routes=public,
    #                                            drivers=drivers)

    #     self.assertEqual(len(inhouse), 7)
    #     self.assertEqual(len(public), 8)

    # def test_optimization_with_inhouse_merge(self):
    #     schedules = DriverGrouping().group_drivers_by_time_slot(
    #         drivers=[Driver(id=item.get('id'),
    #                         time_slots=item.get('time_slots'),
    #                         capacity=item.get('capacity'),
    #                         speed=item.get('speed')) for item in drivers])

    #     data, _ = LocationGrouping().group_locations(locations,
    #                                                  schedules,
    #                                                  True)

    #     self.assertEqual(len(_), 0)

    #     for key, val in data.items():
    #         for k, v in val.items():
    #             if len(v.get('locations')) < 2:
    #                 data[key][k]['locations'] = []

    #     inhouse = []

    #     def build_route(indices, filtered_indices, locs):
    #         routes = []
    #         for item in indices[0]:
    #             loc = locs[filtered_indices[item]]
    #             if ';' in locs[filtered_indices[item]].ref:
    #                 for sub_item in loc.ref.split(';'):
    #                     itm_info = sub_item.split(',')
    #                     routes.append(Location(
    #                         coordinates=Coordinates(
    #                             loc.coordinates[0],
    #                             loc.coordinates[1]),
    #                         address=loc.address,
    #                         delivery_window=loc.delivery_window,
    #                         capacity=float(itm_info[1]),
    #                         ref=itm_info[0]))
    #             else:
    #                 routes.append(loc)

    #             if filtered_indices[item] != 0:
    #                 locs[filtered_indices[item]] = None
    #         return routes

    #     for pickup_address, pickup_windows in data.items():
    #         for pickup_window, obj in pickup_windows.items():
    #             locs = obj.get('locations')
    #             driver_ids = obj.get('driver_ids')
    #             while locs and driver_ids:
    #                 driver = None
    #                 for item in drivers:
    #                     if item.get('id') == driver_ids[0]:
    #                         driver = item
    #                         break

    #                 filtered_indices = []
    #                 for k, v in enumerate(locs):
    #                     if v.capacity <= driver.get('capacity'):
    #                         filtered_indices.append(k)

    #                 indices = Routing(
    #                     locations=[loc for loc in locs if
    #                                loc.capacity <= driver.get('capacity')],
    #                     num_vehicles=len(locs)).generate_routes(
    #                         vehicle_capacity=driver.get('capacity'),
    #                         speed=driver.get('speed'),
    #                         service_time_unit=1800)

    #                 if len(indices) == 0:
    #                     break
    #                 else:
    #                     # remove driver from available driver
    #                     # list only if a route has been built
    #                     driver_id = driver_ids.pop(0)

    #                     routes = build_route(indices,
    #                                          filtered_indices,
    #                                          locs)
    #                     inhouse.append({driver_id: routes})
    #                     locs = list(filter(lambda x: x is not None, locs))
    #             obj['locations'] = locs if len(locs) > 1 else []

    #     public = []
    #     for pickup_address, pickup_windows in data.items():
    #         for pickup_window, obj in pickup_windows.items():
    #             locs = obj.get('locations')
    #             if locs:
    #                 indices = Routing(
    #                             locations=locs,
    #                             num_vehicles=len(locs)).generate_routes(
    #                                 vehicle_capacity=30,
    #                                 speed=30,
    #                                 service_time_unit=1800)

    #                 if len(indices) == 0:
    #                     break
    #                 else:
    #                     for idx_list in indices:
    #                         routes = []

    #                         for item in idx_list:
    #                             if ';' in locs[item].ref:
    #                                 for sub_item in locs[item].ref.split(';'):
    #                                     itm_info = sub_item.split(',')
    #                                     routes.append(
    #                                         Location(
    #                                             coordinates=Coordinates(
    #                                                 locs[item].coordinates[0],
    #                                                 locs[item].coordinates[1]),
    #                                             address=locs[item].address,
    #                                             delivery_window=locs[item].delivery_window,
    #                                             capacity=float(itm_info[1]),
    #                                             ref=itm_info[0]))
    #                             else:
    #                                 routes.append(locs[item])

    #                             if item != 0:
    #                                 locs[item] = None
    #                         public.append(routes)
    #                     locs = list(filter(lambda x: x is not None, locs))
    #                     obj['locations'] = locs if len(locs) > 1 else []

    #     inhouse, public = Routing.merge_routes(inhouse_routes=inhouse,
    #                                            public_routes=[],
    #                                            drivers=drivers,
    #                                            mode=3)
    #     counter = 0
    #     pickups = 0
    #     for item in inhouse:
    #         for driver_id, routes in item.items():
    #             counter += len(routes)
    #             for r in routes:
    #                 if r.capacity == 0:
    #                     pickups += 1
    #     print(pickups)
    #     print(counter)
    #     self.assertEqual(len(inhouse), 3)
    #     self.assertEqual(len(public), 0)

    # def test_optimization_with_larger_capacity(self):
    #     schedules = DriverGrouping().group_drivers_by_time_slot(
    #         drivers=[Driver(id=item.get('id'),
    #                         time_slots=item.get('time_slots'),
    #                         capacity=item.get('capacity'),
    #                         speed=item.get('speed')) for item in drivers_merge])

    #     data, _ = LocationGrouping().group_locations(locations_merge,
    #                                                  schedules,
    #                                                  True)

    #     self.assertEqual(len(_), 0)

    #     inhouse = []
    #     for pickup_address, pickup_windows in data.items():
    #         for pickup_window, obj in pickup_windows.items():
    #             locs = obj.get('locations')
    #             driver_ids = obj.get('driver_ids')
    #             while locs and driver_ids:
    #                 driver = None
    #                 for item in drivers_merge:
    #                     if item.get('id') == driver_ids[0]:
    #                         driver = item
    #                         break

    #                 filtered_indices = []
    #                 for k, v in enumerate(locs):
    #                     if v.capacity <= driver.get('capacity'):
    #                         filtered_indices.append(k)

    #                 indices = Routing(
    #                     locations=[loc for loc in locs if
    #                                loc.capacity <= driver.get('capacity')],
    #                     num_vehicles=len(locs)).generate_routes(
    #                         vehicle_capacity=driver.get('capacity'),
    #                         speed=driver.get('speed'),
    #                         service_time_unit=1800)

    #                 if len(indices) == 0:
    #                     break
    #                 else:
    #                     # remove driver from available driver
    #                     # list only if a route has been built
    #                     driver_id = driver_ids.pop(0)

    #                     routes = []
    #                     for item in indices[0]:
    #                         if ';' in locs[filtered_indices[item]].ref:
    #                             for sub_item in locs[filtered_indices[item]].ref.split(';'):
    #                                 itm_info = sub_item.split(',')
    #                                 routes.append(
    #                                     Location(coordinates=Coordinates(
    #                                                 locs[filtered_indices[item]].coordinates[0],
    #                                                 locs[filtered_indices[item]].coordinates[1]),
    #                                              address=locs[filtered_indices[item]].address,
    #                                              delivery_window=locs[filtered_indices[item]].delivery_window,
    #                                              capacity=float(itm_info[1]),
    #                                              ref=itm_info[0]))
    #                         else:
    #                             routes.append(locs[filtered_indices[item]])
    #                         if filtered_indices[item] != 0:
    #                             locs[filtered_indices[item]] = None
    #                     inhouse.append({driver_id: routes})
    #                     locs = list(filter(lambda x: x is not None, locs))
    #             obj['locations'] = locs if len(locs) > 1 else []

    #     public = []
    #     for pickup_address, pickup_windows in data.items():
    #         for pickup_window, obj in pickup_windows.items():
    #             locs = obj.get('locations')
    #             if locs:
    #                 indices = Routing(
    #                             locations=locs,
    #                             num_vehicles=len(locs)).generate_routes(
    #                                 vehicle_capacity=30,
    #                                 speed=30,
    #                                 service_time_unit=1800)

    #                 if len(indices) == 0:
    #                     break
    #                 else:
    #                     for idx_list in indices:
    #                         routes = []

    #                         for item in idx_list:
    #                             if ';' in locs[item].ref:
    #                                 for sub_item in locs[item].ref.split(';'):
    #                                     itm_info = sub_item.split(',')
    #                                     routes.append(
    #                                         Location(
    #                                             coordinates=Coordinates(
    #                                                 locs[item].coordinates[0],
    #                                                 locs[item].coordinates[1]),
    #                                             address=locs[item].address,
    #                                             delivery_window=locs[item].delivery_window,
    #                                             capacity=float(itm_info[1]),
    #                                             ref=itm_info[0]))
    #                             else:
    #                                 routes.append(locs[item])

    #                             if item != 0:
    #                                 locs[item] = None
    #                         public.append(routes)
    #                     locs = list(filter(lambda x: x is not None, locs))
    #                     obj['locations'] = locs if len(locs) > 1 else []

    #     inhouse, public = Routing.merge_routes(inhouse_routes=inhouse,
    #                                            public_routes=public,
    #                                            drivers=drivers_merge)

    #     self.assertEqual(len(inhouse), 7)
    #     self.assertEqual(len(public), 8)

    # def test_optimization_with_inhouse_merge_larger_capacity(self):
    #     schedules = DriverGrouping().group_drivers_by_time_slot(
    #         drivers=[Driver(id=item.get('id'),
    #                         time_slots=item.get('time_slots'),
    #                         capacity=item.get('capacity'),
    #                         speed=item.get('speed')) for item
    #                  in drivers_merge])

    #     data, _ = LocationGrouping().group_locations(locations_merge,
    #                                                  schedules,
    #                                                  True)

    #     self.assertEqual(len(_), 0)

    #     inhouse = []
    #     for pickup_address, pickup_windows in data.items():
    #         for pickup_window, obj in pickup_windows.items():
    #             locs = obj.get('locations')
    #             driver_ids = obj.get('driver_ids')
    #             while locs and driver_ids:
    #                 driver = None 
    #                 for item in drivers_merge:
    #                     if item.get('id') == driver_ids[0]:
    #                         driver = item
    #                         break

    #                 filtered_indices = []
    #                 for k, v in enumerate(locs):
    #                     if v.capacity <= driver.get('capacity'):
    #                         filtered_indices.append(k)

    #                 indices = Routing(
    #                     locations=[loc for loc in locs if
    #                                loc.capacity <= driver.get('capacity')],
    #                     num_vehicles=len(locs)).generate_routes(
    #                         vehicle_capacity=driver.get('capacity'),
    #                         speed=driver.get('speed'),
    #                         service_time_unit=1800)

    #                 if len(indices) == 0:
    #                     break
    #                 else:
    #                     # remove driver from available driver
    #                     # list only if a route has been built
    #                     driver_id = driver_ids.pop(0)

    #                     routes = []
    #                     for item in indices[0]:
    #                         if ';' in locs[filtered_indices[item]].ref:
    #                             for sub_item in locs[filtered_indices[item]].ref.split(';'):
    #                                 itm_info = sub_item.split(',')
    #                                 routes.append(
    #                                     Location(coordinates=Coordinates(
    #                                                 locs[filtered_indices[item]].coordinates[0],
    #                                                 locs[filtered_indices[item]].coordinates[1]),
    #                                              address=locs[filtered_indices[item]].address,
    #                                              delivery_window=locs[filtered_indices[item]].delivery_window,
    #                                              capacity=float(itm_info[1]),
    #                                              ref=itm_info[0]))
    #                         else:
    #                             routes.append(locs[filtered_indices[item]])
    #                         if filtered_indices[item] != 0:
    #                             locs[filtered_indices[item]] = None
    #                     inhouse.append({driver_id: routes})
    #                     locs = list(filter(lambda x: x is not None, locs))
    #             obj['locations'] = locs if len(locs) > 1 else []

    #     public = []
    #     for pickup_address, pickup_windows in data.items():
    #         for pickup_window, obj in pickup_windows.items():
    #             locs = obj.get('locations')
    #             if locs:
    #                 indices = Routing(
    #                             locations=locs,
    #                             num_vehicles=len(locs)).generate_routes(
    #                                 vehicle_capacity=30,
    #                                 speed=30,
    #                                 service_time_unit=1800)

    #                 if len(indices) == 0:
    #                     break
    #                 else:
    #                     for idx_list in indices:
    #                         routes = []

    #                         for item in idx_list:
    #                             if ';' in locs[item].ref:
    #                                 for sub_item in locs[item].ref.split(';'):
    #                                     itm_info = sub_item.split(',')
    #                                     routes.append(
    #                                         Location(
    #                                             coordinates=Coordinates(
    #                                                 locs[item].coordinates[0],
    #                                                 locs[item].coordinates[1]),
    #                                             address=locs[item].address,
    #                                             delivery_window=locs[item].delivery_window,
    #                                             capacity=float(itm_info[1]),
    #                                             ref=itm_info[0]))
    #                             else:
    #                                 routes.append(locs[item])

    #                             if item != 0:
    #                                 locs[item] = None
    #                         public.append(routes)
    #                     locs = list(filter(lambda x: x is not None, locs))
    #                     obj['locations'] = locs if len(locs) > 1 else []
    #     print('Before merging')
    #     for routes in inhouse:
    #         for driver_id, route in routes.items():
    #             print([r.to_json() for r in route])
    #     inhouse, public = Routing.merge_routes(inhouse_routes=inhouse,
    #                                            public_routes=public,
    #                                            drivers=drivers_merge,
    #                                            mode=3)
    #     print('After merging')
    #     for routes in inhouse:
    #         for driver_id, route in routes.items():
    #             print([r.to_json() for r in route])
    #     self.assertEqual(len(inhouse), 5)
    #     self.assertEqual(len(public), 0)

    def test_impossible_route(self):
        schedules = DriverGrouping().group_drivers_by_time_slot(
            drivers=[Driver(id=item.get('id'),
                            time_slots=item.get('time_slots'),
                            capacity=item.get('capacity'),
                            speed=item.get('speed')) for item
                     in drivers4])

        data, _ = LocationGrouping().group_locations(locations4,
                                                     schedules,
                                                     True)
        self.assertEqual(len(_), 0)
        print(data)
        inhouse = []
        for pickup_address, pickup_windows in data.items():
            for pickup_window, obj in pickup_windows.items():
                locs = obj.get('locations')
                driver_ids = obj.get('driver_ids')
                while locs and driver_ids:
                    driver = None 
                    for item in drivers4:
                        if item.get('id') == driver_ids[0]:
                            driver = item
                            break

                    filtered_indices = []
                    for k, v in enumerate(locs):
                        if v.capacity <= driver.get('capacity'):
                            filtered_indices.append(k)

                    indices = Routing(
                        locations=[loc for loc in locs if
                                   loc.capacity <= driver.get('capacity')],
                        num_vehicles=len(locs)).generate_routes(
                            vehicle_capacity=driver.get('capacity'),
                            speed=driver.get('speed'),
                            service_time_unit=1800)

                    if len(indices) == 0:
                        break
                    else:
                        # remove driver from available driver
                        # list only if a route has been built
                        driver_id = driver_ids.pop(0)

                        routes = []
                        for item in indices[0]:
                            if ';' in locs[filtered_indices[item]].ref:
                                for sub_item in locs[filtered_indices[item]].ref.split(';'):
                                    itm_info = sub_item.split(',')
                                    routes.append(
                                        Location(coordinates=Coordinates(
                                                    locs[filtered_indices[item]].coordinates[0],
                                                    locs[filtered_indices[item]].coordinates[1]),
                                                 address=locs[filtered_indices[item]].address,
                                                 delivery_window=locs[filtered_indices[item]].delivery_window,
                                                 capacity=float(itm_info[1]),
                                                 ref=itm_info[0]))
                            else:
                                routes.append(locs[filtered_indices[item]])
                            if filtered_indices[item] != 0:
                                locs[filtered_indices[item]] = None
                        inhouse.append({driver_id: routes})
                        locs = list(filter(lambda x: x is not None, locs))
                obj['locations'] = locs if len(locs) > 1 else []
        for item in inhouse:
            for _, routes in item.items():
                print([route.to_json() for route in routes])
        self.assertEqual(len(inhouse), 1)
