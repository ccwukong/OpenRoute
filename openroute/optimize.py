from ortools.constraint_solver import pywrapcp
from math import sin, cos, sqrt, atan2, asin, radians
import math
import copy


class CreateDistanceCallback(object):
    """Create callback to calculate distances between points."""

    def __init__(self, locations):
        """Initialize distance array."""
        size = len(locations)
        depot = 0
        self.matrix = {}

        for from_node in range(size):
            self.matrix[from_node] = {}
            for to_node in range(size):
                if from_node == to_node:
                    # Define the distance from the depot to any node to be 0.
                    self.matrix[from_node][to_node] = 0
                else:
                    x1 = locations[from_node][0]
                    y1 = locations[from_node][1]
                    x2 = locations[to_node][0]
                    y2 = locations[to_node][1]
                    self.matrix[from_node][to_node] = \
                        CreateDistanceCallback.distance(x1, y1, x2, y2)

    def distance_callback(self, from_node, to_node):
        return self.matrix[from_node][to_node]

    @staticmethod
    def distance(lat1, long1, lat2, long2):
        lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])

        # haversine formula
        dlon = long2 - long1
        dlat = lat2 - lat1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles
        return c * r


# Demand callback
class CreateDemandCallback(object):
    """Create callback to get demands at each location."""

    def __init__(self, demands):
        self.matrix = demands

    def demand_callback(self, from_node, to_node):
        return self.matrix[from_node]


# Service time (proportional to demand) callback.
class CreateServiceTimeCallback(object):
    """Create callback to get time windows at each location."""

    def __init__(self, demands, time_per_demand_unit, fixed_time=True):
        self.matrix = demands
        self.time_per_demand_unit = time_per_demand_unit
        self.fixed_time = fixed_time

    def ServiceTime(self, from_node, to_node):
        try:
            if self.fixed_time:
                return self.time_per_demand_unit
            else:
                return int(self.matrix[from_node] * self.time_per_demand_unit)
        except Exception as e:
            raise e


# Create the travel time callback (equals distance divided by speed).
class CreateTravelTimeCallback(object):
    """Create callback to get travel times between locations."""
    def __init__(self, dist_callback, speed):
        self.dist_callback = dist_callback
        self.speed = speed

    def TravelTime(self, from_node, to_node):
        travel_time = self.dist_callback(from_node, to_node) / self.speed
        return int(travel_time)


# Create total_time callback (equals service time plus travel time).
class CreateTotalTimeCallback(object):
    """Create callback to get total times between locations."""

    def __init__(self, service_time_callback, travel_time_callback):
        self.service_time_callback = service_time_callback
        self.travel_time_callback = travel_time_callback

    def TotalTime(self, from_node, to_node):
        service_time = self.service_time_callback(from_node, to_node)
        travel_time = self.travel_time_callback(from_node, to_node)
        return service_time + travel_time


class Routing(object):
    def __init__(self, locations, num_vehicles=1, depot=0):
        """
        depot: the time spent on departure for things like loading stuff etc...
        """
        self._locations = [item.coordinates for item in locations]
        self._num_locations = len(locations)
        self._max_weights = [item.capacity for item in locations]
        self._num_vehicles = num_vehicles
        self._depot = depot
        self._delivery_windows = [item.delivery_window for item in locations]

        # The number of nodes of the VRP is num_locations.
        # Nodes are indexed from 0 to num_locations -
        # 1. By default the starting of
        # a route is node 0.
        self._routing = pywrapcp.RoutingModel(self._num_locations,
                                              self._num_vehicles,
                                              self._depot)
        self._search_parameters = \
            pywrapcp.RoutingModel.DefaultSearchParameters()
        self._search_parameters.time_limit_ms = 5000
        self._search_parameters.solution_limit = 100

    def find_nearest_pickup_location(self, pickup_locations,
                                     first_location_in_route):
        try:
            nearest = 0
            distance = CreateDistanceCallback.distance(
                pickup_locations[nearest][0], 
                pickup_locations[nearest][1],
                first_location_in_route[0],
                first_location_in_route[1])

            for index, value in enumerate(pickup_locations):
                dist = CreateDistanceCallback.distance(
                    value[0],
                    value[1],
                    first_location_in_route[0],
                    first_location_in_route[1])
                if dist < distance:
                    nearest = index
                    distance = dist
                else:
                    continue
            return nearest
        except Exception as e:
            raise e

    def generate_routes(self, vehicle_capacity, speed, service_time_unit=1,
                        working_hours=24):
        try:
            # Callbacks to the distance function and
            # travel time functions here.
            dist_between_locations = CreateDistanceCallback(self._locations)
            dist_callback = dist_between_locations.distance_callback

            self._routing.SetArcCostEvaluatorOfAllVehicles(dist_callback)

            demands_at_locations = CreateDemandCallback(self._max_weights)
            demands_callback = demands_at_locations.demand_callback

            # Adding capacity dimension constraints.
            slack_max = 0
            fix_start_cumul_to_zero = True

            self._routing.AddDimension(demands_callback,
                                       slack_max,
                                       vehicle_capacity,
                                       fix_start_cumul_to_zero,
                                       "Capacity")
            # Add time dimension.
            time_per_demand_unit = service_time_unit
            horizon = working_hours * 3600
            time = "Time"

            service_times = CreateServiceTimeCallback(self._max_weights,
                                                      time_per_demand_unit)

            service_time_callback = service_times.ServiceTime

            travel_times = CreateTravelTimeCallback(dist_callback, speed)
            travel_time_callback = travel_times.TravelTime

            total_times = CreateTotalTimeCallback(service_time_callback,
                                                  travel_time_callback)
            total_time_callback = total_times.TotalTime

            # total time function callback
            self._routing.AddDimension(total_time_callback,
                                       horizon,
                                       horizon,
                                       fix_start_cumul_to_zero,
                                       time)

            # Add time window constraints.
            time_dimension = self._routing.GetDimensionOrDie(time)

            for location in range(1, self._num_locations):
                start = self._delivery_windows[location][0]
                end = self._delivery_windows[location][1]
                time_dimension.CumulVar(location).SetRange(start, end)
            # time_dimension.SetGlobalSpanCostCoefficient(100)

            distance = "Distance"
            maximum_distance = 300
            self._routing.AddDimension(
                dist_callback,
                0,  # null slack
                maximum_distance,  # maximum distance per vehicle
                True,  # start cumul to zero
                distance)
            distance_dimension = self._routing.GetDimensionOrDie(distance)
            #distance_dimension.SetGlobalSpanCostCoefficient(10000000)

            # Solve displays a solution if any.
            assignment = self._routing.SolveWithParameters(
                self._search_parameters)

            if assignment:
                print("Total distance: " + str(assignment.ObjectiveValue()) + "\n")
                
                time_dimension = self._routing.GetDimensionOrDie(time)

                possible_indices = []
                used_location = []

                for vehicle_nbr in range(self._num_vehicles):
                    index = self._routing.Start(vehicle_nbr)

                    # temp_list = []
                    # temp_addr_list = []
                    index_list = []
                    # route_dist = 0
                    while not self._routing.IsEnd(index):
                        node_index = self._routing.IndexToNode(index)
                        # next_node_index = self._routing.IndexToNode(
                        #     assignment.Value(self._routing.NextVar(index)))

                        index_list.append(node_index)

                        # route_dist += CreateDistanceCallback.distance(
                        #     self._locations[node_index][0],
                        #     self._locations[node_index][1],
                        #     self._locations[next_node_index][0],
                        #     self._locations[next_node_index][1])
                        # load_var = capacity_dimension.CumulVar(index)
                        # route_load = assignment.Value(load_var)

                        # time_var = time_dimension.CumulVar(index)
                        # time_min = assignment.Min(time_var)
                        # time_max = assignment.Max(time_var)

                        index = assignment.Value(self._routing.NextVar(index))

                    # temp_list.append(self._locations[node_index])
                    # temp_addr_list.append(self._addresses[node_index])
                    # index_list.append(node_index)

                    # used_location.append(self._locations[node_index])

                    if len(index_list) > 1:
                        # del temp_list[-1]
                        # del temp_addr_list[-1]

                        # possible_routes.append(temp_list)
                        # possible_addresses.append(temp_addr_list)
                        possible_indices.append(index_list)
                # unused = []

                # for item in self._locations:
                #     if not item in used_location:
                #         unused.append(item)
                return possible_indices
            else:
                return []
        except Exception as e:
            raise e

    @staticmethod
    def merge_routes(inhouse_routes, public_routes, drivers, mode=1):
        """
        1. Sort public routes by Capacity in descending order
        2. Calculate the distance between the last location of an inhouse route
           to the first location of a public route
           2.1 Make sure driver timeslot can cover the public route
           2.2 Make sure there's enough time for the driver to go to the pickup
               location again:
               (PR0 - IRn)/speed in sec >= PR0(start_time) - IRn(end_time)
        3. Merge inhouse and public route and reduce the problem sets

        Mode:
        1: only try to merge once for each in-house route
        2: aggressive merge until a driver's schedule is full
        3: merge inhouse routes first then merge public routes
           to inhouse routes once per route
        """

        # if mode 3 then merge inhouse
        try:
            if mode == 3:
                for idx, item in enumerate(inhouse_routes):
                    for driver_id, inhouse_route in item.items():
                        if not inhouse_route:
                            break

                        driver = [item for item in drivers if
                                  item.get('id') == driver_id][0]
                        route_end = inhouse_route[-1]

                        for _, time_slot in enumerate(driver['time_slots']):
                            for itr_idx, itr_item in enumerate(inhouse_routes):
                                for driver_id_tmp, inhouse_route_tmp in itr_item.items():
                                    itr_driver_id = driver_id_tmp
                                    itr_route_list = inhouse_route_tmp
                                    break

                                if not itr_route_list or driver_id == \
                                   itr_driver_id:
                                    continue

                                merging_route_start = itr_route_list[0]
                                merging_route_end = itr_route_list[-1]

                                # check if the driver has enough time to
                                # cover the merging route
                                distance = CreateDistanceCallback.distance(
                                    route_end.coordinates[0],
                                    route_end.coordinates[1],
                                    merging_route_start.coordinates[0],
                                    merging_route_start.coordinates[1])

                                if time_slot[1] < \
                                   merging_route_end.delivery_window[1] or \
                                   merging_route_start.delivery_window[0] <= \
                                   route_end.delivery_window[1] or \
                                   (merging_route_start.delivery_window[0] -
                                    route_end.delivery_window[1]) < \
                                   math.ceil(distance/driver['speed']*3600):
                                    continue

                                # check if the vehicle can handle the capacity
                                if sum([item.capacity for item in
                                   itr_route_list]) > driver['capacity']:
                                    continue

                                inhouse_route.extend(itr_route_list)
                                inhouse_routes[itr_idx][driver_id] = \
                                    inhouse_route
                                inhouse_routes[itr_idx][itr_driver_id] = []
                                break
                        break

            if public_routes:
                # Sort public routes by capacity in descending order
                public_routes.sort(key=lambda x: sum([item.capacity for item in x]),
                                   reverse=True)
                for item in inhouse_routes:
                    for driver_id, inhouse_route in item.items():
                        driver = [item for item in drivers if
                                  item.get('id') == driver_id][0]

                        if inhouse_route:
                            route_end = inhouse_route[-1]

                            for _, time_slot in enumerate(driver['time_slots']):
                                for idx, val in enumerate(public_routes):
                                    # make sure driver's available time slot
                                    # can cover the merging route's
                                    # delivery window
                                    merging_route_start = val[0]
                                    merging_route_end = val[-1]

                                    # check if the driver has enough time to
                                    # cover the merging route
                                    distance = CreateDistanceCallback.distance(
                                        route_end.coordinates[0],
                                        route_end.coordinates[1],
                                        public_routes[idx][0].coordinates[0],
                                        public_routes[idx][0].coordinates[1])

                                    if time_slot[1] < \
                                       merging_route_end.delivery_window[1] or \
                                       merging_route_start.delivery_window[0] <= \
                                       route_end.delivery_window[1] or \
                                       (merging_route_start.delivery_window[0] -
                                        route_end.delivery_window[1]) < \
                                       math.ceil(distance/driver['speed']*3600):
                                        continue

                                    # check if the vehicle can handle the capacity
                                    if sum([item.capacity for item in
                                       public_routes[idx]]) > driver['capacity']:
                                        continue

                                    inhouse_route.extend(public_routes.pop(idx))

                                    if mode == 1:
                                        break
                        else:
                            for _, time_slot in enumerate(driver['time_slots']):
                                for idx, val in enumerate(public_routes):
                                    # make sure driver's available time slot
                                    # can cover the merging route's
                                    # delivery window

                                    merging_route_start = val[0]
                                    merging_route_end = val[-1]

                                    if merging_route_start.delivery_window[1] < \
                                       time_slot[0] or \
                                       merging_route_end.delivery_window[0] > \
                                       time_slot[1]:
                                        continue

                                    # check if the vehicle can
                                    # handle the capacity
                                    if sum([item.capacity for item in
                                       public_routes[idx]]) > driver['capacity']:
                                        continue

                                    inhouse_route.extend(public_routes.pop(idx))

                                    if mode == 1:
                                        break

            inhouse_routes = list(filter(lambda x: list(x.values())[0],
                                         inhouse_routes))
            return inhouse_routes, public_routes,
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
