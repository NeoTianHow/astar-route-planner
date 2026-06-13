from utilities import find_node, calculate_distance
import heapq
from config import WALKING_SPEED, BUS_SPEED, BUS_ARRIVAL_WAIT_TIME, STOP_TIME


class AStar:
    def __init__(self, graph):
        self.graph = graph

    def shortest_path(self, start, end):
        start_node = find_node(self.graph.node_list, start)
        end_node = find_node(self.graph.node_list, end)

        # Initialize open_nodes as a priority queue and
        # closed_nodes as a set
        open_nodes = []
        closed_nodes = set()

        # Initialize g_score for starting node as 0
        g_scores = {}
        g_scores[start_node.name] = 0

        parent_nodes = {}
        parent_nodes[start_node.name] = None

        # Add starting node to open_nodes with f-score of 0
        heapq.heappush(open_nodes, (0, start_node))

        while open_nodes:
            # Get node with lowest f score from open_nodes
            current_node = heapq.heappop(open_nodes)[1]
            # If end node is reached, reconstruct path and return it
            if current_node == end_node:
                return self.reconstruct_path(parent_nodes, current_node)

            closed_nodes.add(current_node)

            neighbours = self.get_neighbours(current_node)
            if neighbours is not None:
                # Loop through current node's neighbours
                for i, neighbour in enumerate(neighbours):
                    neighbour_node = find_node(self.graph.node_list, neighbour[0])

                    # If neighbour is already in closed set, skip it
                    if neighbour_node in closed_nodes:
                        continue

                    # Calculate tentative g score for neighbour
                    tentative_g = g_scores[current_node.name] + neighbour[1]  # weight

                    neighbour_node.selected_bus_service = neighbour[3]
                    neighbour_node.distance = neighbour[1]

                    # If neighbour is not in open set, add it
                    if (
                        neighbour_node not in [x[1] for x in open_nodes]
                        # There's a chance that the neighbour_node miaght be the starting node,
                        # which causes an infinite loop
                        and neighbour_node.name != start_node.name
                    ):
                        parent_nodes[neighbour_node.name] = current_node
                        g_scores[neighbour_node.name] = tentative_g
                        f_score = tentative_g + calculate_distance(
                            neighbour_node.coordinates, end_node.coordinates
                        )

                        heapq.heappush(open_nodes, (f_score, neighbour_node))

                    # If neighbour is already in open set and tentative g score
                    # is better than current g score, update it
                    elif tentative_g < g_scores[neighbour_node.name]:
                        parent_nodes[neighbour_node.name] = current_node

                        g_scores[neighbour_node.name] = tentative_g
                        f_score = tentative_g + calculate_distance(
                            neighbour_node.coordinates, end_node.coordinates
                        )

                        # Update f_score of neighbour in open_nodes and maintain heap property
                        for i, (f_score, node) in enumerate(open_nodes):
                            if node == neighbour_node:
                                open_nodes[i] = (f_score, neighbour_node)
                                heapq.heapify(open_nodes)

        # If open set is empty and end_node is
        # not reached, no path exists
        return None

    def get_neighbours(self, v):
        # Get neighbours of a node from the adjacency list of the graph
        if v.name in self.graph.adj_list:
            return self.graph.adj_list[v.name]
        else:
            return None

    def reconstruct_path(self, parent_nodes, current_node):
        total_distance = 0
        total_time = 0
        bus_path = {
            "name": [],
            "coordinates": [],
            "bus_service": [],
            "total_distance": 0,
            "total_time": 0,
        }
        while current_node:
            bus_path["name"].append(current_node.name)
            bus_path["coordinates"].append(current_node.coordinates)
            bus_path["bus_service"].append(current_node.selected_bus_service)
            total_distance += current_node.distance
            total_time += self.calculate_time(
                current_node.distance, current_node.selected_bus_service
            )
            current_node = parent_nodes[current_node.name]
        bus_path["name"].reverse()
        bus_path["coordinates"].reverse()
        bus_path["bus_service"].reverse()
        bus_path["total_distance"] = total_distance
        bus_path["total_time"] = total_time
        return bus_path

    def calculate_time(self, distance, bus_service):
        # walking
        if bus_service is None:
            if distance != 0:
                time = (distance / WALKING_SPEED) * 60
                time += BUS_ARRIVAL_WAIT_TIME + STOP_TIME
                return time
        # Bus
        else:
            time = time = (distance / BUS_SPEED) * 60
            time += STOP_TIME
            return time
        return 0
