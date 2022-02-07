## Problem Statement
I employed <b>Satisficing A* Search</b> to solve this problem. The algorithm starts from a state describing the starting city and continuously expands states until it finds a route to the ending city. I describe a <b>state</b> in a state space to have the following attributes:

1. Current City
2. g(n) - the current cost to reach this state
3. h(n, n') - the estimated cost to reach the goal state from the current state
4. route - the route leading up to the current state
5. total segments - the total number of segments traversed to reach this state
6. total distance - the total number of miles traversed to reach this state
7. total time - the total number of hours traveled it took to reach this state
8. total delivery - the expected amount of hours it takes to make a delivery to this state

A state is represented as a list of these 8 values.

<b>Successor Function:</b> With each iteration of the search, I pop the state with the minimum g(n) + h(n, n') value and expand it, adding all expanded states to the fringe. A state is expanded if there is a highway connecting the two cities in the states.

<b>Goal State:</b> A state with a route from the starting city to the ending city. The algorithm returns the first route it finds.

<b>Edge Weights:</b> The number of miles from one city to another 

## Heuristic Functions
Depending on the input, h(n, n') is calculated by one of these methods

1. Distance heuristic - straight line distance from n to n' in miles - The straight line distance between two points is always the shortest distance
2. Segments heuristic - straight line distance / 99. The longest segment is 99 miles, so dividing the straight line distance by 99 will always underestimate the number of segments.
3. Time heuristic - straight line distance / 65. The fastest speed limit of any segment is 65 mph, so this will always underestimate the number of hours it takes to reach a destination
4. Delivery heuristic - same as time heuristic. Of course, since delivery time is always greater than or equal to regular time, this heuristic always underestimates the cost.

Note that the distance formula between two longitude and latitudes is inconsistent and does not yield the best result. One degree of latitude does not equal the same number of miles everywhere across the globe. For example, near the north pole, one degree of latitude is 69.407 degree and near the equator it is 68.703 miles. Thus, this heuristic is inconsistent. But, when I compared the results from running an admissible with an this one, the answer was within the accepted range and ran about 30 times faster.

## Further Reading
### expand_node Function
The bulk of the work went into designing this function. I can't get an h(n, n') from an intersection because I lack the intersection's coordinates, and I can't estimate the intersections coordinates because I don't always know the direction of the highway. So my only option was to connect intersections with other intersections until I reached a city. 

I did this by recursively calling expand_node on nodes that didn't belong to the list of cities and hadn't been explored yet. This effectively connects two cities that are divided by only intersections. For example, consider the following sitution:

<pre>
 0 --- I-29 --- 1
 |      |
 |      |
 2      3
 </pre>
    
We would call expand_node on 0, which would return node 2 and I-29. Since I-29 is not in the list of cities, we 
would call expand_node on I-29, which would add the distance from 0 to I-29 to the distance from 
I-29 and 1 and I-29 and 3. Once we expand I-29, we return nodes 1 and 3. In total, from the call on 0, 
we would return nodes 1,2, and 3.

## Using a consistent and admissible heuristic function
I also tried just using the longitude and latitude values as coordinates for calculating distance. This is admissible because one degree of longitude and latitude is always more than one mile. But, when running this program from two cities very far apart, like LA and New York, the program took way to long to run. It was about 30 seconds for distance and time and indefitely for delivery and segments (I'm sure it would have terminated but I didn't want to wait that long. I'm sure the autograder wouldn't have either.)
