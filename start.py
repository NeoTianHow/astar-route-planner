from flask import Flask, render_template, request, session, flash, redirect, url_for
import psycopg2
import folium
from folium import plugins
import openrouteservice
import requests
from a_star import AStar
import pandas as pd
from graph import Graph
from utilities import calculate_distance, find_node
import config
from werkzeug.security import check_password_hash, generate_password_hash

# Database connection
conn = psycopg2.connect(
    user=config.USER,
    password=config.PASSWORD,
    host=config.HOST,
    port=config.PORT,
    database=config.DATABASE,
)

# Declare global variables at the beginning of the file
global graph, disrupted_list, all_bus_stops
disrupted_list = []
graph = Graph()
all_bus_stops = graph.build_graph(disrupted_list)

app = Flask(__name__)
# Include session secret key for a unique session
app.secret_key = config.SECRET_KEY

@app.route('/', methods=['POST'])
def handle_post_request():
    return 'Success!'

@app.route("/")
def index():
    m = folium.Map(location=[1.4655, 103.7578], zoom_start=12)
    # Check if any user is logged in
    if session.get("isLoggedIn") == 1:
        isLoggedIn = session.get("isLoggedIn")
        username = session.get("username")
        searchHistory = session.get("savedSearches")
        return render_template(
            "map.html",
            map_html=m._repr_html_(),
            saved_searches=searchHistory,
            isLoggedIn=isLoggedIn,
            username=username,
            route_text="",
            error_message="",
        )
    else:
        session["isLoggedIn"] = 0
        session["username"] = ""
        session["savedSearches"] = "Please login to view previous searches."
        return render_template(
            "map.html",
            map_html=m._repr_html_(),
            saved_searches="Please login to view previous searches.",
            isLoggedIn=0,
            route_text="",
            error_message="",
        )
    
# Create User method
@app.route("/register", methods=["POST"])
def register():
    cur = conn.cursor()
    username = request.form["username"]
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    if username == "" or name == "" or email == "" or password == "":
        return render_template(
            "register.html", error_message="Please fill in field(s)."
        )

    # Check if username exists
    if checkUsername(username) is True:
        return render_template(
            "register.html", error_message="Username exists! Please change username."
        )
    else:
        # Insert into database
        cur.execute(
            'INSERT INTO "User" ("username", "name", "email", "password") VALUES (%s, %s, %s, %s)',
            (username, name, email, generate_password_hash(password)),
        )
        conn.commit()
        return render_template("login.html", success_message="Account created!")

# Authenticate Login
def is_admin_login(username, password):
    if not config.ADMIN_USERNAME or not config.ADMIN_PASSWORD_HASH:
        return False
    return (
        username == config.ADMIN_USERNAME
        and check_password_hash(config.ADMIN_PASSWORD_HASH, password)
    )


@app.route("/login", methods=["POST"])
def login():
    m = folium.Map(
        location=[1.4655, 103.7578],
        zoom_start=12,
        position="relative",
        width="100%",
        height="100%",
    )
    cur = conn.cursor()
    username = request.form["username"]
    password = request.form["password"]
    if is_admin_login(username, password):
        return render_template("admin.html", disrupted_list = disrupted_list)
    else:
        cur.execute(
            'SELECT "password" FROM "User" WHERE username = %s',
            (username,),
        )
        user = cur.fetchone()
        # Authentication
        if user and check_password_hash(user[0], password):
            # Using sessions to save the variables
            session["isLoggedIn"] = 1
            session["username"] = username
            session["savedSearches"] = loadPreviousSearchHistory()
            # Redirect to the index page on successful login
            return index()
        else:
            # Return error message on failed login
            return render_template("login.html", message="Invalid username or password")

# logout function of user
@app.route("/logout")
def logout():
    # Clear session and set values as default
    session.clear()
    session["savedSearches"] = "Please login to view previous searches."
    session["isLoggedIn"] = 0
    session["username"] = ""
    return index()

# Additional feature to disrupt bus stop
@app.route("/disruption-bus-stop", methods=["POST"])
def add_disruption():
    global disrupted_list
    if (request.form["busstop"] == ""):
        return render_template("admin.html", error_message = "Please fill in field.")
    else:
        disrupted_list.append(request.form["busstop"])
        return render_template("admin.html", message = "Successfully disrupted bus stop!", disrupted_list = disrupted_list)

# Additional feature to remove a disruption from a bus stop
@app.route('/disruption-bus-stop/<string:param>', methods=['DELETE'])
def remove_disruption(param):
    global disrupted_list
    disrupted_list.remove(param)
    return render_template("admin.html", message = "Successfully removed disrupted bus stop!", disrupted_list = disrupted_list)

# Methods to redirect pages
@app.route("/register-page")
def registerPage():
    return render_template("register.html")


@app.route("/redirect_login")
def loginPage():
    return render_template("login.html")

# Additional feature to send route directions as telegram message
@app.route("/send-to-telegram")
def send_to_telegram():
    m = folium.Map(location=[1.4655, 103.7578], zoom_start=12)
    route_text_telegram = "Total distance: {0} km\n".format(session.get("total_distance"))
    route_text_telegram += "Estimated time: {0}mins\n".format(session.get("total_time"))
    route_text_telegram += "Traffic: No traffic\n\n"
    route_text = session.get("route_text")
    route_text_telegram += route_text
    chatID = config.TELEGRAM_CHAT_ID
    apiURL = config.TELEGRAM_API_URL
    try:
        requests.post(apiURL, json={'chat_id': chatID, 'text': route_text_telegram})
        return render_template(
            "map.html",
            map_html=m._repr_html_(),
            route_text=route_text,
            telegram_success_message="Successfully sent!",
            saved_searches=session.get("savedSearches"),
            isLoggedIn=session.get("isLoggedIn"),
            username=session.get("username"),
            start_location=session.get("start_location"),
            end_location=session.get("end_location"),
            error_message="",
            total_distance=session.get("total_distance"),
            total_time=session.get("total_time"),
            traffic_type = "No traffic"
        )
    except Exception:
        return render_template(
            "map.html",
            map_html=m._repr_html_(),
            route_text=route_text,
            telegram_error_message="Unable to send to Telegram.",
            saved_searches=session.get("savedSearches"),
            isLoggedIn=session.get("isLoggedIn"),
            username=session.get("username"),
            start_location=session.get("start_location"),
            end_location=session.get("end_location"),
            error_message="",
            total_distance=session.get("total_distance"),
            total_time=session.get("total_time"),
            traffic_type = "No traffic"
        )

# Additional feature to get traffic flow based on a coordinate
def get_traffic(coords):
    # API Key for tomtom traffic
    api_key = config.TOMTOM_API_TOKEN
    base_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={api_key}&point={coords[1]},{coords[0]}"
    response = requests.get(base_url)

    # Parse response and return traffic flow value
    data = response.json()
    flow_data = data["flowSegmentData"]
    traffic_flow = flow_data["currentSpeed"]
    return traffic_flow

# To include marker pointers to the start and end location of each bus service
def add_Markers(bus_dict, m):
    # Color list for multiple bus services
    colors = ["blue", "green", "purple", "navy blue", "brown", "black"]

    # iterate over the services in the dictionary and assign a color to each bus service
    service_colors = {}
    i = 0
    for service in bus_dict.keys():
        service_colors[service] = colors[i % len(colors)]
        i += 1

    # iterate over bus services in the dictionary
    for service, route in bus_dict.items():
        start = route["coordinates"][0][::-1]
        end = route["coordinates"][-1][::-1]

        # set unique color for the service
        color = service_colors[service]

        # create markers for the start and end coordinates with the assigned color
        folium.Marker(
            location=start,
            tooltip=f"Start of {service}",
            icon=folium.Icon(
                icon="bus-simple", icon_color="white", prefix="fa", color=color
            ),
        ).add_to(m)

        folium.Marker(
            location=end,
            tooltip=f"End of {service}",
            icon=folium.Icon(
                icon="bus-simple", icon_color="white", prefix="fa", color=color
            ),
        ).add_to(m)


# Print out directions
def route_directions(bus_dict):
    # Find the last bus stop of the first key
    first_key = list(bus_dict.keys())[0]
    last_stop = bus_dict[first_key]["name"][-1]

    # Print out the directions
    directions = []
    for key, value in bus_dict.items():
        bus_stops = value["name"]
        num_stops = len(bus_stops)
        if key == first_key:
            directions.append(
                f"Board bus {key} at {bus_stops[0]}. Alight at {last_stop}, {num_stops} stops later.\n"
            )
            continue
        first_stop = bus_stops[0]
        # check if bus transfer bus stop is the same
        if last_stop == first_stop:  # if bus stops are the same
            directions.append(
                f"Board bus {key}. Alight at {bus_stops[-1]}, {num_stops} stops later.\n"
            )
        else:  # if bus stops not the same, need to walk
            directions.append(
                f"Walk to {first_stop} and board bus {key}. Alight at {bus_stops[-1]}, {num_stops} stops later.\n"
            )
        last_stop = bus_stops[-1]
    return "".join(directions)


# Method to get actual coordinates from user's input location
def inputLocation(input):
    api_key = config.ORS_API_TOKEN
    client = openrouteservice.Client(key=api_key)
    try:
        coordinates=client.pelias_search(text=input, country="MYS")["features"][0]['geometry']['coordinates']
    except:
        return None
    else:
        return coordinates[1], coordinates[0]

# Method to get closest bus stop for input location
def closestBusStop(all_bus_stops, LatLon):
    bus_stops_and_gps = all_bus_stops[["Bus_Stop", "GPS_Location"]]
    closest_bus_stop = []
    min_distance = float("inf")
    for index, row in bus_stops_and_gps.iterrows():
        bus_stop = row["Bus_Stop"]
        gps_coord = row["GPS_Location"]
        latitude, longitude = gps_coord.split(",")
        bus_stop_coor = [float(latitude), float(longitude)]
        distance = calculate_distance(LatLon, bus_stop_coor)
        if distance < min_distance:
            min_distance = distance
            closest_bus_stop = [bus_stop, gps_coord]
    return closest_bus_stop



# Method to search route
@app.route("/search-route", methods=["POST"])
def searchRoute():
    global all_bus_stops, disrupted_list
    
    # Create the graph for the astar algorithm
    all_bus_stops = graph.build_graph(disrupted_list)

    m = folium.Map(location=[1.4655, 103.7578], zoom_start=12)

    # Set the API key and client for OpenRouteService
    api_key = config.ORS_API_TOKEN
    client = openrouteservice.Client(key=api_key)

    # Get the start and end locations from the form data
    start_location = request.form["start-location"]
    end_location = request.form["end-location"]

    # validate inputs
    if start_location == "" or end_location == "":
        error_message = "Please fill in field(s)."
        return render_template(
            "map.html",
            map_html=m._repr_html_(),
            route_text="",
            error_message=error_message,
            saved_searches=session.get("savedSearches"),
            isLoggedIn=session.get("isLoggedIn"),
            username=session.get("username"),
            start_location=start_location,
            end_location=end_location,
        )

    # Returns lat long of user's input location
    startLatLon = inputLocation(start_location)
    endLatLon = inputLocation(end_location)

    # Get closest bus stop from user's input location
    closest_StartBusStop = closestBusStop(all_bus_stops, startLatLon)
    closest_EndBusStop = closestBusStop(all_bus_stops, endLatLon)

    route_text = ""

    if start_location != closest_StartBusStop[0]:
        route_text = "Walk to the closest bus stop: " + closest_StartBusStop[0] + "\n"

    # Call the Astar function with the start and end locations
    path_finder = AStar(graph)

    # validate if start and end is the same
    if closest_StartBusStop[0] == closest_EndBusStop[0]:
        return render_template(
            "map.html",
            map_html=m._repr_html_(),
            route_text="",
            error_message="Locations cannot be the same.",
            saved_searches=session.get("savedSearches"),
            isLoggedIn=session.get("isLoggedIn"),
            username=session.get("username"),
            start_location=start_location,
            end_location=end_location,
        )

    # Store search history if user is logged in
    if session.get("isLoggedIn") == 1:
        storeSearchHistory(start_location, end_location)
        loadPreviousSearchHistory()

    bus_path = path_finder.shortest_path(closest_StartBusStop[0], closest_EndBusStop[0])
    updateBusService(bus_path, graph)

    # Call the OpenRouteService API to get the route
    bus_dict, walk_dict = {}, {}
    bus_polyline_coords, walk_polyline_coords = [], []

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

    # Print the final directions
    route_text += route_directions(bus_dict)

    # put into session
    session["total_distance"] = round(bus_path["total_distance"], 2)
    session["total_time"] = round(bus_path["total_time"])
    session["traffic_type"] = "No traffic"
    session["start_location"] = start_location
    session["end_location"] = end_location
    session["route_text"] = route_text

    # Add markers here
    add_Markers(bus_dict, m)

    # Draw bus routes onto map
    # Create a list of colors
    colors = ["blue", "green", "purple", "navy blue", "brown", "black"]

    # Iterate over the routes in the dictionary and assign a color to each bus route
    route_colors = {}
    i = 0
    for key, value in bus_dict.items():
        if len(value) > 1:
            route_colors[key] = colors[i % len(colors)]
            i += 1
    for key in bus_dict.keys():
        if (len(bus_dict[key])) > 1:
            route = client.directions(
                coordinates=bus_dict[key]["coordinates"],
                continue_straight=True,
                instructions=False,
                options={
                    "avoid_features": ["highways", "tollways", "ferries"],
                    "profile_params": {"restrictions": {"length": 12.0, "height": 4.5}},
                    "vehicle_type": "bus",
                },
                preference="fastest",
                profile="driving-hgv",
                roundabout_exits=True,
                format="geojson",
                validate=False,
            )
            polyline_coords = [
                list(reversed(coord))
                for coord in route["features"][0]["geometry"]["coordinates"]
            ]
            # Use the assigned color for the route
            color = route_colors[key]
            folium.PolyLine(
                locations=polyline_coords, color=color, weight=5, opacity=0.5
            ).add_to(m)
            bus_polyline_coords.append(polyline_coords)

    # Draw walking routes onto map
    for key in walk_dict.keys():
        if (len(walk_dict[key])) > 1:
            route = client.directions(
                coordinates=walk_dict[key],
                profile="foot-walking",
                format="geojson",
                validate=False,
            )
            polyline_coords = [
                list(reversed(coord))
                for coord in route["features"][0]["geometry"]["coordinates"]
            ]
            folium.PolyLine(
                locations=polyline_coords, color="red", dash_array="10"
            ).add_to(m)
            walk_polyline_coords.append(polyline_coords)

    # Zoom the view to polyline
    m.fit_bounds(bus_polyline_coords + walk_polyline_coords)

    return render_template(
        "map.html",
        map_html=m._repr_html_(),
        route_text=route_text,
        saved_searches=session.get("savedSearches"),
        isLoggedIn=session.get("isLoggedIn"),
        username=session.get("username"),
        start_location=start_location,
        end_location=end_location,
        error_message="",
        total_distance = round(bus_path["total_distance"], 2),
        total_time = round(bus_path["total_time"]),
        traffic_type = "No traffic"
    )

def updateBusService(bus_path, graph):
    # Replaces the None values with the values of the next element. This only happens
    # when is the starting node or when it requires walking
    for i in range(len(bus_path["bus_service"])):
        if bus_path["bus_service"][i] is None and i < len(bus_path["bus_service"]) - 1:
            # If the next bus_service is None as well, just select a bus_service from the bus stop
            if bus_path["bus_service"][i + 1] is None:
                node = find_node(graph.node_list, bus_path["name"][i])
                bus_path["bus_service"][i] = node.bus_services[0]
            else:
                bus_path["bus_service"][i] = bus_path["bus_service"][i + 1]

    i = 1
    while i < len(bus_path["bus_service"]):
        prev_bus_service = bus_path["bus_service"][i - 1]
        prev_bus_name = bus_path["name"][i - 1]
        prev_bus_coords = bus_path["coordinates"][i - 1]
        curr_bus_service = bus_path["bus_service"][i]
        curr_bus_name = bus_path["name"][i]
        if i == len(bus_path["bus_service"]) - 1:
            break
        # change of bus service detected
        if prev_bus_service != curr_bus_service:
            isChange = False
            # change of bus_service at the same location
            for key in graph.adj_list.keys():
                # Check the previous's adjaceny list, see if next bus name
                # is there and got the same bus service as prev or not. If got,
                # change the next bus service
                if key == prev_bus_name:
                    for tup in graph.adj_list[key]:
                        if tup[0] == curr_bus_name and tup[3] == prev_bus_service:
                            bus_path["bus_service"][i] = tup[3]
                            isChange = True
                    break
            if isChange == False:
                needToChange = False
                for tup in graph.adj_list[key]:
                    if tup[0] == curr_bus_name and tup[3] != None:
                        needToChange = True
                        break
                if needToChange:
                    bus_path["name"].insert(i, prev_bus_name)
                    bus_path["coordinates"].insert(i, prev_bus_coords)
                    bus_path["bus_service"].insert(i, curr_bus_service)

        i += 1

# Check if username exists in database
def checkUsername(username):
    cur = conn.cursor()
    cur.execute('SELECT * FROM "User" WHERE "username" = (%s)', (username,))
    user = cur.fetchone()
    if user:
        return True
    else:
        return False

# load 5 recent search history of user
def loadPreviousSearchHistory():
    cur = conn.cursor()
    cur.execute(
        'SELECT "startLocation", "endLocation", "id" FROM "Users_Searches" WHERE username = %s order by "id" desc limit 5',
        (session["username"],),
    )
    searchHistory = cur.fetchall()
    session["savedSearches"] = searchHistory
    return searchHistory

# store previous search history of user if logged in
def storeSearchHistory(startLocation, endLocation):
    cur = conn.cursor()

    # check if result exists in database
    previousSearchHistory = loadPreviousSearchHistory()
    for location in previousSearchHistory:
        if startLocation == location[0] and endLocation == location[1]:
            break
    else:  # if does not exist, insert into database
        cur.execute(
            'INSERT INTO "Users_Searches" ("username", "startLocation", "endLocation") VALUES (%s, %s, %s)',
            (session["username"], startLocation, endLocation),
        )
        conn.commit()

if __name__ == "__main__":
    app.run(debug=config.FLASK_DEBUG)
