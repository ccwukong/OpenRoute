import copy
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from .models import Driver, Location, Wave, Coordinates, GeoArea


class DriverGrouping(object):
    def __init__(self):
        pass

    def group(self, drivers, locations,
              start_buffer_time=0, end_buffer_time=0):
        # Verifying data type
        illegal_driver_data = \
            [item for item in drivers if not isinstance(item, Driver)]
        illegal_location_data = \
            [item for item in locations if not isinstance(item, Location)]

        if illegal_driver_data:
            raise TypeError(
                'All element in the list should have the same type Driver.')

        if illegal_location_data:
            raise TypeError(
                'All element in the list should have the same type Location.')

        result = {}

        for driver in drivers:
            result[driver.id] = {}
            for time_slot in driver.time_slots:
                result[driver.id][(time_slot[0], time_slot[1])] = []
                for idx, val in enumerate(locations):
                    if not val:
                        continue
                    elif (time_slot[0] + start_buffer_time) < val.delivery_window[0] and \
                        val.delivery_window[1] < (time_slot[1] - end_buffer_time) and \
                        self.if_loc_capacity_within(val.capacity, driver.capacity):
                        result[driver.id][(time_slot[0], time_slot[1])].append(val)
                        locations[idx] = None

        result['unprocessed'] = \
            [item for item in locations if item is not None]
        return result

    def group_drivers_by_time_slot(self, drivers):
        # Verifying data type
        illegal_driver_data = \
            [item for item in drivers if not isinstance(item, Driver)]

        if illegal_driver_data:
            raise TypeError(
                'All element in the list should have the same type Driver.')

        time_slots = {}

        for driver in drivers:
            for time_slot in driver.time_slots:
                if (time_slot[0], time_slot[1]) in time_slots:
                    if time_slots[(time_slot[0], time_slot[1])]:
                        time_slots[(time_slot[0], time_slot[1])].append(driver)
                    else:
                        time_slots[(time_slot[0], time_slot[1])] = [driver]
                else:
                    time_slots[(time_slot[0], time_slot[1])] = [driver]
        return time_slots

    def if_loc_capacity_within(self, location_weight, driver_capacity):
        return driver_capacity > location_weight


class LocationGrouping(object):
    def __init__(self):
        pass

    def _group_locations_by_time_slot(self, locations,
                                      time_slot, threshhold=0):
        """
        Return locations that not included in the given time slot
        """
        result = [[], []]
        for loc in locations:
            if threshhold == 0:
                if time_slot[0] < loc.delivery_window[0] and \
                   loc.delivery_window[1] < time_slot[1]:
                    result[0].append(loc)
                else:
                    result[1].append(loc)
            else:
                # TODO: make use of threshhold argument
                if (time_slot[0] < loc.delivery_window[0] < time_slot[1] and
                    loc.delivery_window[0] == (time_slot[0]+time_slot[1])/2) or \
                   (time_slot[0] < loc.delivery_window[1] < time_slot[1] and
                   loc.delivery_window[0] == (time_slot[0]+time_slot[1])/2):
                    result[0].append(loc)
                else:
                    result[1].append(loc)
        return result

    def group_locations(self, locations, schedules, merge_identical=False):
        """
        This method requires the locations to be grouped by pickup locations

        Sample processed:
        {'pickup1': {(12000, 18000) : {
        (43140, 79200): [<openroute.models.Location object at 0x110b62be0>],
        (0, 43140): [<openroute.models.Location object at 0x1127d66d8>,
                        <openroute.models.Location object at 0x112a15748>]}},
        'pickup2': {(12000, 18000) : {
        (28800, 79200): [<openroute.models.Location object at 0x110778320>,
                         <openroute.models.Location object at 0x112f0ecf8>,
                         <openroute.models.Location object at 0x112f0ee48>]}},
        'pickup3': {(12000, 18000) : {
        (28800, 79200): [<openroute.models.Location object at 0x112a15dd8>]}}}

        Sample unprocessed:
        {'pickup1': [],
         'pickup2': [],
         'pickup3': [<openroute.models.Location object at 0x110778390>]}
        """
        result = {}
        not_found = set()
        copied_schedules = copy.deepcopy(schedules)

        unused_driver_count = 0
        if merge_identical:
            for pickup, pickup_windows in locations.items():
                for pickup_window, dropoff_list in pickup_windows.items():
                    if len(dropoff_list) > 2:
                        for k, v in enumerate(dropoff_list):
                            if k == 0 or not v:
                                continue
                            elif v.get('coordinates') == [0, 0]:
                                not_found.add(v.get('address'))
                                dropoff_list[k] = None
                                continue

                            for idx in range(k+1, len(dropoff_list)):
                                if dropoff_list[idx] and \
                                   dropoff_list[idx]['coordinates'] == [0, 0]:
                                        not_found.add(
                                            dropoff_list[idx]['address'])
                                        dropoff_list[idx] = None
                                elif dropoff_list[idx] and v['coordinates'] == \
                                    dropoff_list[idx]['coordinates'] and \
                                    v['delivery_window'] == dropoff_list[idx]['delivery_window']:
                                        if ',' not in v['ref']:
                                            v['ref'] = ','.join([v['ref'],
                                                                 str(v['capacity'])]) + \
                                                       ';' + ','.join([dropoff_list[idx]['ref'],
                                                                       str(dropoff_list[idx]['capacity'])])
                                        else:
                                            v['ref'] = v['ref'] + ';' + \
                                                       ','.join([dropoff_list[idx]['ref'],
                                                                 str(dropoff_list[idx]['capacity'])])

                                        v['capacity'] += dropoff_list[idx]['capacity']
                                        dropoff_list[idx] = None

                    elif dropoff_list[1].get('coordinates') == [0, 0]:
                        not_found.add(dropoff_list[1]['address'])
                        dropoff_list[1] = None

                    pickup_windows[pickup_window] = \
                        [loc for loc in dropoff_list if loc]

        for pickup, pickup_windows in locations.items():
            result[pickup] = {}
            for pickup_window, dropoff_list in pickup_windows.items():
                result[pickup][pickup_window] = {'locations': [Location(
                    coordinates=Coordinates(item.get('coordinates')[0],
                                            item.get('coordinates')[1]),
                    address=item.get('address'),
                    delivery_window=item.get('delivery_window'),
                    capacity=item.get('capacity', 1),
                    ref=item.get('ref', '')) for item in dropoff_list],
                                                 'driver_ids': []}

                total_capacity = 0
                min_pickup_time = 99999
                max_pickup_time = 0

                for item in result[pickup][pickup_window]['locations']:
                    total_capacity += item.capacity
                    if item.delivery_window[0] < min_pickup_time:
                        min_pickup_time = item.delivery_window[0]

                    if item.delivery_window[1] > max_pickup_time:
                        max_pickup_time = item.delivery_window[1]

                id_containers = result[pickup][pickup_window]['driver_ids']
                for time_slot, driver_list in copied_schedules.items():
                    if driver_list and time_slot[0] <= min_pickup_time and \
                       time_slot[1] >= max_pickup_time and total_capacity > 0:

                        if total_capacity >= driver_list[0].capacity:
                            while total_capacity > 0 and driver_list:
                                driver = driver_list.pop()
                                id_containers.append(driver.id)
                                total_capacity -= driver.capacity
                        else:
                            driver = driver_list.pop()
                            id_containers.append(driver.id)
                            total_capacity = 0

                        copied_schedules[time_slot] = driver_list
                        unused_driver_count += len(driver_list)
                    if total_capacity <= 0:
                        break

        while unused_driver_count:
            prev_count = unused_driver_count
            for pickup, pickup_windows in locations.items():
                for pickup_window, dropoff_list in pickup_windows.items():
                    for time_slot, driver_list in copied_schedules.items():
                        min_pickup_time = 99999
                        max_pickup_time = 0

                        for item in result[pickup][pickup_window]['locations']:
                            if item.delivery_window[0] < min_pickup_time:
                                min_pickup_time = item.delivery_window[0]

                            if item.delivery_window[1] > max_pickup_time:
                                max_pickup_time = item.delivery_window[1]

                        if driver_list and time_slot[0] <= min_pickup_time \
                           and time_slot[1] >= max_pickup_time:
                            driver = driver_list.pop()
                            result[pickup][pickup_window]['driver_ids'].append(
                                driver.id)
                            copied_schedules[time_slot] = driver_list
                            unused_driver_count -= 1

            if prev_count == unused_driver_count:
                break

        return result, not_found


class WaveGrouping(object):
    def __init__(self):
        pass

    def group(self, waves, locations, buffer_time=0):
        illegal_wave_data = \
            [item for item in waves if not isinstance(item, Wave)]
        illegal_location_data = \
            [item for item in locations if not isinstance(item, Location)]

        if illegal_wave_data:
            raise TypeError(
                'All element in the list should have the same type Wave.')

        if illegal_location_data:
            raise TypeError(
                'All element in the list should have the same type Location.')

        result = {}
        for wave in waves:
            result[wave.cutoff_time] = [locations.pop(idx) for idx, val in
                                        enumerate(locations) if
                                        val.order_time + buffer_time <
                                        wave.cutoff_time]

        if len(locations) > 0:
            result['unprocessed'] = locations

        return result
