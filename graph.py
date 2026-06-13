from utilities import find_node, calculate_distance, read_bus_stops
from node import Node


class Graph:
    def __init__(self):
        self.adj_list = {}
        self.node_list = []

    def build_graph(self, disrupted_bus_stops):
        data = read_bus_stops()

        for i, (curr_row, next_row) in enumerate(
            zip(data[:-1].itertuples(), data[1:].itertuples()), start=1
        ):
            curr_bus_stop, curr_location, curr_bus_service = self.extract_info(
                curr_row
            )[:3]
            next_bus_stop, next_location, next_bus_service, stop_id = self.extract_info(
                next_row
            )[:4]

            self.add_node(curr_bus_stop, curr_location, curr_bus_service)

            if curr_bus_stop in self.adj_list:
                # check if the next bus stop is not already in the list of neighbors
                # and if the next bus stop is not the first stop in a new route
                if (
                    not any(
                        next_bus_stop == tup[0] and curr_bus_service == tup[3]
                        for tup in self.adj_list[curr_bus_stop]
                    )
                    and stop_id != 1
                ):
                    # add the next bus stop as a neighbor of the curr bus stop
                    self.adj_list[curr_bus_stop].append(
                        (
                            next_bus_stop,
                            calculate_distance(curr_location, next_location),
                            next_location,
                            # [curr_bus_service, next_bus_service],
                            curr_bus_service,
                        )
                    )

            else:
                self.adj_list[curr_bus_stop] = [
                    (
                        next_bus_stop,
                        calculate_distance(curr_location, next_location),
                        next_location,
                        # [curr_bus_service, next_bus_service],
                        curr_bus_service,
                    )
                ]
        for i, (curr_row, next_row) in enumerate(
            zip(data[:-1].itertuples(), data[1:].itertuples()), start=1
        ):
            curr_bus_stop, curr_location, curr_bus_service = self.extract_info(
                curr_row
            )[:3]

            # Find nearby bus_stops within 400m - walking
            for key in self.adj_list.keys():
                node = find_node(self.node_list, key)
                if (
                    calculate_distance(curr_location, node.coordinates) < 0.4
                    and curr_bus_stop != key
                    and curr_bus_service not in node.bus_services
                    # cannot be in the current bus service, cos it wouldn't make sense
                    # to alight and walk, when you can continue to take the bus
                    and not any(
                        curr_bus_stop == tup[0] for tup in self.adj_list[node.name]
                    )
                ):
                    self.adj_list[node.name].append(
                        (
                            curr_bus_stop,
                            calculate_distance(curr_location, node.coordinates),
                            curr_location,
                            None,  # Since they are walking, don't have bus service
                        )
                    )

        for disrupted_bus_stop in disrupted_bus_stops:
            data = data[~data['Bus_Stop'].str.contains(disrupted_bus_stop)] # remove from data data

            del self.adj_list[disrupted_bus_stop]                           # remove from adj_list
            
            for node in self.node_list:                                     # remove from node_list
                if node.name == disrupted_bus_stop:
                    del node
        return data

    def add_node(self, bus_stop, location, bus_service):
        isExist = False
        for node in self.node_list:
            if node.name == bus_stop:
                isExist = True
                if bus_service not in node.bus_services:
                    node.bus_services.append(bus_service)
                    break

        if isExist == False:
            self.node_list.append(Node(bus_stop, location, bus_service))

    def extract_info(self, row):
        bus_stop = row.Bus_Stop
        location = self.parse_location(row.GPS_Location)
        bus_service = row.Bus_Service
        stop_id = row.Stop_ID
        return bus_stop, location, bus_service, stop_id

    def parse_location(self, location):
        lat, lon = map(float, location.split(",")[::-1])
        return lat, lon
