class Node:
    def __init__(self, name, coordinates, bus_service):
        self.name = name
        self.coordinates = coordinates
        self.bus_services = [bus_service]
        # We'll only know through the A* algorithm and adjaceny list.
        self.selected_bus_service = None
        self.distance = 0

    def __eq__(self, other):
        if isinstance(other, Node):
            return (
                self.name == other.name
                and self.coordinates == other.coordinates
                and self.selected_bus_service == other.selected_bus_service
                and self.bus_services == other.bus_services
                and self.distance == other.distance
            )
        return False

    def __lt__(self, other):
        return self.selected_bus_service < other.selected_bus_service

    def __hash__(self):
        return hash(
            (
                self.name,
                tuple(self.coordinates),
                self.selected_bus_service,
                tuple(self.bus_services),
                self.distance,
            )
        )

    def __str__(self):
        return f"name: {self.name}, coordinates: {self.coordinates}, selected_bus_service: {self.selected_bus_service}, bus_services: {self.bus_services}, distance: {self.distance}"
