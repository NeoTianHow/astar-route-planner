import telebot
import config
from a_star import AStar
from graph import Graph
from start import inputLocation, closestBusStop,updateBusService,route_directions

bot = telebot.TeleBot(config.TELEGRAM_API_TOKEN)

def find_route(start_location, end_location):
    # Returns lat long of user's input location
    try:
        startLatLon = inputLocation(start_location)
        endLatLon = inputLocation(end_location)

        # Get closest bus stop from user's input location
        graph = Graph()
        bus_stops = graph.build_graph([])
        closest_StartBusStop = closestBusStop(bus_stops, startLatLon)
        closest_EndBusStop = closestBusStop(bus_stops, endLatLon)
    except:
        return "Invalid locations"

    # Call the Astar function with the start and end locations
    path_finder = AStar(graph)

    # validate if start and end is the same
    if closest_StartBusStop[0] == closest_EndBusStop[0]:
        return "Start and end location is the same."

    bus_path = path_finder.shortest_path(closest_StartBusStop[0], closest_EndBusStop[0])
    updateBusService(bus_path, graph)

    # Call the OpenRouteService API to get the route
    bus_dict, walk_dict = {}, {}

    # Separate coordinates into bus_service keys
    for i in range(len(bus_path["bus_service"])):
        name = bus_path["name"][i]
        coordinates = bus_path["coordinates"][i]
        bus_service = bus_path["bus_service"][i]
        if bus_service not in bus_dict:
            bus_dict[bus_service] = {"name": [], "coordinates": []}
        bus_dict[bus_service]["name"].append(name)
        bus_dict[bus_service]["coordinates"].append(coordinates)

    # For single bus_service
    for current_key in list(bus_dict.keys()):
        if len(bus_dict[current_key]["coordinates"]) == 1:
            if current_key == list(bus_dict)[-1]:
                keys = list(bus_dict.keys())
                current_index = keys.index(current_key)
                previous_key = keys[current_index - 1]
                bus_dict[previous_key]["coordinates"].insert(
                    0, bus_dict[current_key]["coordinates"][-1]
                )
                del bus_dict[current_key]
            else:
                keys = list(bus_dict.keys())
                current_index = keys.index(current_key)
                next_key = keys[current_index + 1]
                bus_dict[next_key]["coordinates"].insert(
                    0, bus_dict[current_key]["coordinates"][0]
                )
                del bus_dict[current_key]

    # Add walk if starting_location != bus_service[0][0]
    if bus_dict[list(bus_dict)[0]] != start_location:
        walk_dict["walk-" + start_location.replace(' ', '-') + "-to-" + list(bus_dict)[0]] = []
        walk_dict["walk-" + start_location.replace(' ', '-') + "-to-" + list(bus_dict)[0]].append([startLatLon[1], startLatLon[0]])
        walk_dict["walk-" + start_location.replace(' ', '-') + "-to-" + list(bus_dict)[0]].append(bus_dict[list(bus_dict)[0]]["coordinates"][0])

    # Add walk if swapped bus_service to walk_dict
    for current_key in list(bus_dict.keys())[:-1]:
        keys = list(bus_dict.keys())
        current_index = keys.index(current_key)
        next_key = keys[current_index + 1]
        if next_key is not None:
            if not (
                bus_dict[current_key]["coordinates"][-1]
                == bus_dict[next_key]["coordinates"][0]
            ):
                walk_dict["walk-" + current_key + "-to-" + next_key] = []
                walk_dict["walk-" + current_key + "-to-" + next_key].append(
                    bus_dict[current_key]["coordinates"][-1]
                )
                walk_dict["walk-" + current_key + "-to-" + next_key].append(
                    bus_dict[next_key]["coordinates"][0]
                )

    total_distance = round(bus_path["total_distance"], 2)
    total_time = round(bus_path["total_time"])

    # Print the final directions
    return f"Total distance: {total_distance}km\nEstimated time: {total_time}mins\n\n{route_directions(bus_dict)}"

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hi! Where would you like to go?")
    bot.register_next_step_handler(message, destination_input)

# Define a callback function to handle the user's destination
def destination_input(message):
    destination = message.text
    bot.send_message(message.chat.id, "Where are you starting from?")
    bot.register_next_step_handler(message, beginning_input, destination)

# Define a callback function to handle the user's destination
def beginning_input(message, destination):
    beginning = message.text
    bot.send_message(message.chat.id, f"Here are the directions to go from {beginning} to {destination}:\n\n{find_route(beginning, destination)}")

# Start the bot
bot.polling()