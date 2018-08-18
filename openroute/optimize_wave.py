from ortools.constraint_solver import pywrapcp
from math import sin, cos, sqrt, atan2, asin, radians
from happybunch import delivery_window, locations, max_weights, delivery_addresses

class CreateDistanceCallback(object):
    """Create callback to calculate distances between points."""

    def __init__(self, locations):
        """Initialize distance array."""
        size = len(locations)
        self.matrix = {}

        for from_node in range(size):
            self.matrix[from_node] = {}
            for to_node in range(size):
                x1 = locations[from_node][0]
                y1 = locations[from_node][1]
                x2 = locations[to_node][0]
                y2 = locations[to_node][1]
                self.matrix[from_node][to_node] = CreateDistanceCallback.distance(x1, y1, x2, y2)

    def distance_callback(self, from_node, to_node):
        return int(self.matrix[from_node][to_node])

    @staticmethod
    def distance(lat1, long1, lat2, long2):
        lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])

        # haversine formula 
        dlon = long2 - long1 
        dlat = lat2 - lat1 

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles
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

    def __init__(self, demands, time_per_demand_unit):
        self.matrix = demands
        self.time_per_demand_unit = time_per_demand_unit

    def ServiceTime(self, from_node, to_node):
        return int(self.matrix[from_node] * self.time_per_demand_unit)

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
    def __init__(self, addresses, locations, max_weights, delivery_windows, pickup_addresses, pickup_locations, num_vehicles=1, depot=0):
        """
        depot: the time spent on departure for things like loading stuff etc...
        """
        self._addresses = addresses
        self._locations = locations
        self._pickup_addresses = pickup_addresses
        self._pickup_locations = pickup_locations
        self._num_locations = len(locations)
        self._max_weights = max_weights
        self._num_vehicles = num_vehicles
        self._depot = depot
        self._delivery_windows= delivery_windows

        # The number of nodes of the VRP is num_locations.
        # Nodes are indexed from 0 to num_locations - 1. By default the starting of
        # a route is node 0.
        self._routing = pywrapcp.RoutingModel(self._num_locations, self._num_vehicles, self._depot)
        self._search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()

    def find_nearest_pickup_location(self, pickup_locations, first_location_in_route):
        try:
            nearest = 0
            distance = CreateDistanceCallback.distance(pickup_locations[nearest][0], 
                                                       pickup_locations[nearest][1],
                                                       first_location_in_route[0],
                                                       first_location_in_route[1])
                                                       
            for index, value in enumerate(pickup_locations):
                dist = CreateDistanceCallback.distance(value[0], 
                                                       value[1],
                                                       first_location_in_route[0],
                                                       first_location_in_route[1])
                if  dist < distance:
                    nearest = index
                    distance = dist
                else:
                    continue
            return nearest
        except Exception as e:
            raise e

    def generate_routes(self, vehicle_capacity=100, speed=1, working_hours=24):
        try:
            #if there's only a single delivery location, return this directly
            if self._num_locations == 1:
                pickup_index = self.find_nearest_pickup_location(self._pickup_locations, self._locations[0])                
                return ([self._pickup_locations[pickup_index], self._locations[0]],
                        [self._pickup_addresses[pickup_index], self._addresses[0]],
                        []) 

            # Callbacks to the distance function and travel time functions here.
            dist_between_locations = CreateDistanceCallback(self._locations)
            dist_callback = dist_between_locations.distance_callback

            self._routing.SetArcCostEvaluatorOfAllVehicles(dist_callback)
            demands_at_locations = CreateDemandCallback(self._max_weights)
            demands_callback = demands_at_locations.demand_callback

            # Adding capacity dimension constraints.
            slack_max = 0;
            fix_start_cumul_to_zero = True
            capacity = "Capacity"

            self._routing.AddDimension(demands_callback,
                                       slack_max,
                                       vehicle_capacity,
                                       fix_start_cumul_to_zero,
                                       capacity)
            # Add time dimension.
            time_per_demand_unit = 900
            horizon = working_hours * 3600
            time = "Time"

            service_times = CreateServiceTimeCallback(self._max_weights,
                                                    time_per_demand_unit)
            service_time_callback = service_times.ServiceTime

            travel_times = CreateTravelTimeCallback(dist_callback, speed)
            travel_time_callback = travel_times.TravelTime

            total_times = CreateTotalTimeCallback(service_time_callback, travel_time_callback)
            total_time_callback = total_times.TotalTime

            self._routing.AddDimension(total_time_callback,  # total time function callback
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

            # Solve displays a solution if any.
            assignment = self._routing.SolveWithParameters(self._search_parameters)        
            if assignment:
                # # Solution cost.
                # print("Total distance of all routes: " + str(assignment.ObjectiveValue()) + "\n")
                # Inspect solution.
                capacity_dimension = self._routing.GetDimensionOrDie(capacity);
                time_dimension = self._routing.GetDimensionOrDie(time);

                possible_routes = []
                possible_addresses = []
                used_location = []           

                for vehicle_nbr in range(self._num_vehicles):
                    index = self._routing.Start(vehicle_nbr)
                    temp_list = []
                    temp_addr_list = []

                    while not self._routing.IsEnd(index):
                        node_index = self._routing.IndexToNode(index)
                        load_var = capacity_dimension.CumulVar(index)
                        time_var = time_dimension.CumulVar(index)
                        
                        temp_list.append(self._locations[node_index])
                        temp_addr_list.append(self._addresses[node_index])
                        
                        used_location.append(self._locations[node_index])
                        index = assignment.Value(self._routing.NextVar(index))
                        

                    node_index = self._routing.IndexToNode(index)
                    load_var = capacity_dimension.CumulVar(index)
                    time_var = time_dimension.CumulVar(index)

                    temp_list.append(self._locations[node_index])
                    temp_addr_list.append(self._addresses[node_index])
                    used_location.append(self._locations[node_index])

                    if len(temp_list) > 2:
                        # pickup_index = self.find_nearest_pickup_location(self._pickup_locations, temp_list[0])
                        # temp_list.insert(0, self._pickup_locations[pickup_index])
                        # temp_addr_list.insert(0, self._pickup_addresses[pickup_index])
                    
                        del temp_list[-1]
                        del temp_addr_list[-1]

                        possible_routes.append(temp_list)
                        possible_addresses.append(temp_addr_list)
                unused = []
                
                for item in self._locations:                
                    if item in used_location:                                   
                        unused.append(item)
                
                return (possible_routes, possible_addresses,unused)
            else:
                return ([], [], self._locations) 
        except Exception as e:
            raise e

if __name__ == '__main__':
    routes, addresses, unused = Routing(addresses=delivery_addresses, locations=locations, 
          max_weights=max_weights, delivery_windows=delivery_window, 
          pickup_addresses=[], pickup_locations=[], 
          num_vehicles=len(locations), depot=0).generate_routes(4, 50)


    
    for k, v in enumerate(routes):
        result = []
        for key, val in enumerate(v):
            result.append([addresses[k][key], routes[k][key][0], routes[k][key][1]])

        print(result)