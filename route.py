import sys
from math import cos, asin, sqrt, pi, tanh
import heapq

def clean_data():
    """
    Cleans the data and stores it into two different dictionaries, one for the city coordinates 
    and one for the city's neighbors.

    Parameters: none

    Returns
    ------------------------------------------------------------
    city_locs : dict {str: (float, float)}
                a dict of the city's latitude and longitude values

    adj_list  : dict {str: [[str, int, int, str]...]}
                a dict of the city's neighbors and information, including name, segment distance, 
                speed limit, and highway name
    """
    
    # lists to store all the file data
    cities_data = open('city-gps.txt', 'r').readlines()
    segments_data = open('road-segments.txt','r').readlines()
    
    # dicts for easy lookup of city information
    city_locs = {} # {city: (lat, lon)}, stores the cities coordinates
    adj_list = {} # {city: [[neighbor, dist, spd, highway]...]} stores the city's neighbors and info
    
    for i in range(len(cities_data)):
        line = cities_data[i].replace('\n', '').split(' ')
        city_locs[line[0]] = (float(line[1]), float(line[2]))
        
    for i in range(len(segments_data)):
        line = segments_data[i].replace('\n', '').split(' ')
        if line[0] in adj_list:
            adj_list[line[0]] = adj_list[line[0]] + [line[1:]]
        else: adj_list[line[0]] = [line[1:]]
            
        if line[1] in adj_list:
            adj_list[line[1]] = adj_list[line[1]] + [[line[0]] + line[2:]]
        else: adj_list[line[1]] = [[line[0]] + line[2:]]
        
    return city_locs, adj_list

def distance(lat1, lon1, lat2, lon2):
    """
    Calculates the distance in miles between two coordinates. Unfortunately, because a degree in longitude or latitude changes
    depending on location, this heuristic is not consistent. But, it yields pretty good results, and more importantly, 
    fast results.
    
    Citation
    URL : https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula
    Author: Salvador Dali (username)
    """
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return 12742 * asin(sqrt(a))
    
def h_function_segment(city1, city2, city_locs):
    """
    Estimates the number of segments between city1 and city2. It calculates the miles between the cities then
    divides that number by 99. 99 is the length of the largest segment in the dataset, so this function will
    always underestimate the number of segments, making it admissible. 
    """
    if city1 not in city_locs: return 0
    
    lat1 = city_locs[city1][0]
    lon1 = city_locs[city1][1]
    lat2 = city_locs[city2][0]
    lon2 = city_locs[city2][1]
    
    h = distance(lat1, lon1, lat2, lon2)/99
    
    return h

def h_function_distance(city1, city2, city_locs):
    """
    Estimates the distance between two cities using the straight line distance (in miles) between the two
    cities. The straight line distance is always the shortest distance between the two cities, so this 
    heuristic function is admissible.
    """
    if city1 not in city_locs: return 0
    
    lat1 = city_locs[city1][0]
    lon1 = city_locs[city1][1]
    lat2 = city_locs[city2][0]
    lon2 = city_locs[city2][1]
    
    h = distance(lat1, lon1, lat2, lon2)
    
    return h

def h_function_time(city1, city2, city_locs):
    """
    Estimates the time between two cities by diving the straight line distance by the highest speed limit in the 
    dataset (65 mph). This should always underestimate the time because it's impossible to drive faster 65 using
    a shorter distance than the straight line distance.
    """
    if city1 not in city_locs: return 0
    
    lat1 = city_locs[city1][0]
    lon1 = city_locs[city1][1]
    lat2 = city_locs[city2][0]
    lon2 = city_locs[city2][1]
    
    h = distance(lat1, lon1, lat2, lon2)/65
    
    return h

def c_function_segment(city1, city2, adj_list, g):
    """
    The cost of moving one segment is always 1
    """
    return 1

def c_function_distance(city1, city2, adj_list, g):
    """
    The cost of moving a segment is the distance of the segment.
    """
    for c in adj_list[city1]:
        if c[0] == city2:
            return float(c[1])
    return 0

def c_function_time(city1, city2, adj_list, g):
    """
    The cost of moving one segment is the distance/speed limit because that's
    the time it would take to drive the segment (given you drive the speed limit)
    """
    for c in adj_list[city1]:
        if c[0] == city2:
            return float(c[1])/float(c[2])
    return 0

def c_function_delivery(city1, city2, adj_list, g):
    for c in adj_list[city1]:
        if c[0] == city2:
            spd = float(c[2])
            dist = float(c[1])
            p = 0
            if spd >= 50: p = tanh(dist/1000)
            return (dist/spd) + (p * 2 * (dist/spd + g))
    return 0

def expand_node(curr_node, end_city, explored, city_locs, adj_list, h_function, c_function):
    """
    We expand a node and return all nodes connected to curr_node that aren't in the list of explored.
    In the case of a intersection, we recursively call expand_node so that it attaches the segment from
    curr_node to the intersection to all neighbors of the intersection. An example is given below
    
    Say we have the following situation
    
    0 --- I-29 --- 1
    |       |
    |       |
    2       3
    
    We would call expand_node on 0, which would return node 2 and I-29. Since I-29 is not in city_locs, we 
    would call expand_node on I-29, which would add the distance from 0 to I-29 to the distance from 
    I-29 and 1 and I-29 and 3. Once we expand I-29, we return nodes 1 and 3. In total, from the call on 0, 
    we would return nodes 1,2, and 3.
    
    If a value is already in explored, we return nothing because we've already expanded that node and it
    doesn't need to be in the fringe.
    """
    fringe = []
    
    # base case
    if curr_node[0] in explored:
        return []
    
    # expand node
    for neighbor in adj_list[curr_node[0]]:
            g = float(curr_node[1]) + c_function(curr_node[0], neighbor[0], adj_list, curr_node[1])
            h = h_function(neighbor[0], end_city, city_locs)
            route = curr_node[3] + [(neighbor[0], neighbor[3] + ' for ' + neighbor[1] + ' miles.')]
            segments = curr_node[4] + c_function_segment(curr_node[0], neighbor[0], adj_list, 0)
            distance = curr_node[5] + c_function_distance(curr_node[0], neighbor[0], adj_list, 0)
            time = curr_node[6] + c_function_time(curr_node[0], neighbor[0], adj_list, 0)
            delivery = curr_node[7] + c_function_delivery(curr_node[0], neighbor[0], adj_list, curr_node[7])
            next_node = [neighbor[0], g, h, route, segments, distance, time, delivery]
            
            if neighbor[0] in city_locs:
                fringe += [next_node]
            else:
                fringe += expand_node(next_node, end_city, explored + [curr_node[0]], city_locs, adj_list, h_function, c_function)
   
    return fringe

def parse_node(node):
    """
    Gets the output in the format outlined by the problem.
    """
    route = {}
    route['total-segments'] = node[4]
    route['total-miles'] = node[5]
    route['total-hours'] = node[6]
    route["total-delivery-hours"] = node[7]
    route['route-taken'] = node[3]
    
    return route
    
    
def get_route(start, end, cost):
    
    """
    Find shortest driving route between start city and end city
    based on a cost function.

    1. Your function should return a dictionary having the following keys:
        -"route-taken" : a list of pairs of the form (next-stop, segment-info), where
           next-stop is a string giving the next stop in the route, and segment-info is a free-form
           string containing information about the segment that will be displayed to the user.
           (segment-info is not inspected by the automatic testing program).
        -"total-segments": an integer indicating number of segments in the route-taken
        -"total-miles": a float indicating total number of miles in the route-taken
        -"total-hours": a float indicating total amount of time in the route-taken
        -"total-delivery-hours": a float indicating the expected (average) time 
                                   it will take a delivery driver who may need to return to get a new package
    2. Do not add any extra parameters to the get_route() function, or it will break our grading and testing code.
    3. Please do not use any global variables, as it may cause the testing code to fail.
    4. You can assume that all test cases will be solvable.
    5. The current code just returns a dummy solution.
    """
    # set h and cost function
    if cost == 'segments':
        h_function = h_function_segment
        c_function = c_function_segment
    if cost == 'distance':
        h_function = h_function_distance
        c_function = c_function_distance
    if cost == 'time':
        h_function = h_function_time
        c_function = c_function_time
    if cost == 'delivery':
        h_function = h_function_time
        c_function = c_function_delivery
        
    # calculate city dictionary and adjacency list
    city_locs, adj_list = clean_data()
    
    # get the h value of the starting node
    h = h_function(start, end, city_locs)
    
    # set the values for the starting node
    # each node is represented with a list of the form 
    # [current city name, g value, h value, total segments, total distance, total time, total delivery]
    starting_node = [start, 0, h, [], 0, 0.0, 0.0, 0.0]
    
    # lists to keep track of the fringe and explored nodes
    fringe = []
    explored = []
    
    # we are going to push our starting node to the priority queue
    # for heapq, all items have the form (f(n), node). So, when we push a value, we want to calculate f(n') = g(n, n') + h(n')
    # then, when we pop a value, it will pop the node with the smallest f value
    heapq.heappush(fringe, (starting_node[1] + starting_node[2], starting_node))
    
    # while there is something in the fringe
    while fringe:
        # pop the node with the smallest f value. We use the [1] so that we only get the node and not (f, node)
        next_node = heapq.heappop(fringe)[1]
        # check if the node is a goal state
        if next_node[0] == end:
            return parse_node(next_node)
        
        # get all the nodes connected to the current node
        expanded_nodes = expand_node(next_node, end, explored, city_locs, adj_list, h_function, c_function)
        # add all those nodes to the fringe
        for node in expanded_nodes:
            heapq.heappush(fringe, (node[1] + node[2], node))
        # add the current city to explored, so that we don't try to explore it again
        explored += [next_node[0]]
        
    return [("No route found")]

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise(Exception("Error: expected 3 arguments"))

    (_, start_city, end_city, cost_function) = sys.argv
    if cost_function not in ("segments", "distance", "time", "delivery"):
        raise(Exception("Error: invalid cost function"))

    result = get_route(start_city, end_city, cost_function)

    # Pretty print the route
    print("Start in %s" % start_city)
    for step in result["route-taken"]:
        print("   Then go to %s via %s" % step)

    print("\n          Total segments: %4d" % result["total-segments"])
    print("             Total miles: %8.3f" % result["total-miles"])
    print("             Total hours: %8.3f" % result["total-hours"])
    print("Total hours for delivery: %8.3f" % result["total-delivery-hours"])


