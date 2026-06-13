import math
import pandas as pd
import os


def find_node(node_list, n):
    for node in node_list:
        if node.name == n:
            return node


def calculate_distance(point1, point2):
    # convert degrees to radians
    lon1 = math.radians(point1[0])
    lat1 = math.radians(point1[1])
    lon2 = math.radians(point2[0])
    lat2 = math.radians(point2[1])

    # calculate the differences between latitudes and longitudes
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # apply the haversine formula
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # radius of earth in kilometers
    return c * r


def read_bus_stops():
    # Get the directory path of the current file
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Join the directory path with the filename and read excel
    excel_data = pd.read_excel(os.path.join(dir_path, "bus.xlsx"))

    data = pd.DataFrame(
        excel_data, columns=["Stop_ID", "Bus_Stop", "GPS_Location", "Bus_Service"]
    ).dropna()
    return data
