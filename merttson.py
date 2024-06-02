
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 17 14:18:20 2024

@author: utkucorakli
"""

import pandas as pd
import numpy as np
import json

def calculate_routes_and_convert_to_json(chosen_customers_file, distance_matrix_file):
    # Read the excel file and retrieve values
    df = pd.read_excel(chosen_customers_file, index_col=0)
    N = list(range(len(df)))

    xcoor = list(df.iloc[0:len(N), 0])
    ycoor = list(df.iloc[0:len(N), 1])

    listlength = len(N)

    earliest = list(df.iloc[0:len(N), 2])
    latest = list(df.iloc[0:len(N), 3])
    servicetime = list(df.iloc[0:len(N), 4])
    days = list(df.iloc[0:len(N), 5])
    vehiclecap = 3  
    T = 540  # Total working time for a day is 540 minutes

    # Read the distance matrix from the Excel file
    distance_df = pd.read_excel(distance_matrix_file, index_col=0)
    eucdistance = distance_df.values

    alpha = 0.9 
    n = 1
    lam = 1

    def b(route):
        b = 0
        h = 1
        while h < len(route):
            if route[h] < len(earliest):
                if route[h - 1] < eucdistance.shape[0] and route[h] < eucdistance.shape[1]:
                    pluss = servicetime[route[h - 1]] + eucdistance[route[h - 1]][route[h]]
                    bplus = b + pluss
                    earliest_value = earliest[route[h]]
                    b = max(bplus, earliest_value)
            h += 1
        return b       

    def f1(initialroute, u, bu, j):
        if initialroute[j] < eucdistance.shape[0] and u < eucdistance.shape[1] and initialroute[j + 1] < eucdistance.shape[0]:
            bini = b(initialroute[:j+2])
            f1 = alpha * (eucdistance[initialroute[j]][u] + eucdistance[u][initialroute[j+1]] 
                          - n * eucdistance[initialroute[j]][initialroute[j+1]]) + (1 - alpha) * (bu - bini)
            return f1
        else:
            return float('inf')

    def timewindow(my_list):
        length = len(my_list)
        for k in range(length):
            if not (earliest[my_list[k]] <= b(my_list[:k+1]) <= latest[my_list[k]]):
                return False
        return True

    def get_next_unvisited_node(latest, visited_nodes, day_nodes):
        min_value = float('inf')
        min_index = None

        for index in day_nodes:
            if index not in visited_nodes:
                value = latest[index]
                if value < min_value:
                    min_value = value
                    min_index = index

        if min_index is not None:
            visited_nodes.append(min_index)  # Append the index to visited_nodes
            return min_index
        else:
            return None

    routes_by_day = {0: [], 1: [], 2: []}

    for day in range(3):
        visitednodes = [0]
        daily_routes = []
        d = 0
        day_nodes = [i for i in N if days[i] == day]
        
        while len(visitednodes) - 1 < len(day_nodes):  # -1 to exclude the depot from the count
            initialnode = get_next_unvisited_node(latest, visitednodes, day_nodes)
            if initialnode is None:
                break  # Stop if there are no more nodes to visit
            initialroute = [0, initialnode, 0]
            if initialnode not in visitednodes:
                visitednodes.append(initialnode)
            sameroute = True

            while sameroute:
                fonelist = np.full((listlength, 2), None)
                ftwolist = [None] * listlength

                for u in day_nodes:
                    if u not in initialroute and u not in daily_routes and u not in visitednodes:
                        ulist = []
                        for j in range(len(initialroute) - 1):
                            newroute = initialroute.copy()
                            newroute.insert(j + 1, u)
                            partnewroute = newroute[:j + 3]
                            if all(index < len(earliest) for index in partnewroute) and all(index < listlength for index in partnewroute):
                                if partnewroute[-2] < eucdistance.shape[0] and partnewroute[-1] < eucdistance.shape[1]:
                                    bu = b(partnewroute)
                                    f = f1(initialroute, u, bu, j)
                                    if timewindow(newroute):
                                        ulist.append(f)
                                    else:
                                        ulist.append(None)

                        min_value = None
                        min_index = None
                        if ulist and any(x is not None for x in ulist):
                            min_value = min(filter(lambda x: x is not None, ulist))
                            min_index = ulist.index(min_value)

                        if min_index is not None:
                            fonelist[u][0] = min_value
                            fonelist[u][1] = min_index
                            ftwo = lam * eucdistance[0][u] - fonelist[u][0]
                            ftwolist[u] = ftwo

                max2_value = None
                max2_index = None
                for k, value2 in enumerate(ftwolist):
                    if value2 is not None:
                        if max2_value is None or value2 > max2_value:
                            max2_value = value2
                            max2_index = k

                if max2_index is not None:
                    tobeinserted = max2_value
                    inserted = max2_index
                    whichvacancy = fonelist[inserted][1]

                    if whichvacancy is not None and inserted < len(earliest):
                        total_time = sum(eucdistance[initialroute[i]][initialroute[i + 1]] for i in range(len(initialroute) - 1) if initialroute[i] < eucdistance.shape[0] and initialroute[i + 1] < eucdistance.shape[1]) + \
                                     sum(servicetime[i] for i in initialroute) + \
                                     sum(earliest[i] for i in initialroute)
                        if initialroute[-1] < eucdistance.shape[0] and inserted < eucdistance.shape[1]:
                            total_time += eucdistance[initialroute[-1]][inserted] + servicetime[inserted]

                        if total_time <= T and inserted not in initialroute:
                            initialroute.insert(whichvacancy + 1, inserted)
                            visitednodes.append(inserted)
                            sameroute = True
                        else:
                            daily_routes.append(initialroute)
                            d += 1
                            sameroute = False
                    else:
                        daily_routes.append(initialroute)
                        d += 1
                        sameroute = False
                else:
                    daily_routes.append(initialroute)
                    d += 1
                    sameroute = False

        routes_by_day[day] = daily_routes

    # Combine all daily routes into one list and calculate the objective function value
    allroutes = []
    for day, routes in routes_by_day.items():
        allroutes.extend(routes)

    objective = 0
    for route in allroutes:
        objective += sum(eucdistance[route[i]][route[i + 1]] for i in range(len(route) - 1) if route[i] < eucdistance.shape[0] and route[i + 1] < eucdistance.shape[1])

    print("Routes by day: ", routes_by_day)
    print("The objective function value is: ", objective)

    # Convert the routes to the desired format
    def convert_routes_to_json_format(routes, day):
        json_routes = []
        for route in routes:
            for i in range(len(route) - 1):
                start_index = route[i]
                end_index = route[i + 1]
                json_routes.append({
                    "start_index": start_index,
                    "start_x": xcoor[start_index],
                    "start_y": ycoor[start_index],
                    "end_index": end_index,
                    "end_x": xcoor[end_index],
                    "end_y": ycoor[end_index],
                    "day": str(day)  # Adjust day to match 1-based index
                })
        return json_routes

    # Create the JSON structure
    json_output = []
    for day, routes in routes_by_day.items():
        json_output.extend(convert_routes_to_json_format(routes, day))

    # Convert to JSON string
    results_json = json.dumps(json_output, indent=4)

    return results_json

# Example usage
chosen_customers_file = "chosen_customers.xlsx"
distance_matrix_file = "distance_matrix.xlsx"
results_json = calculate_routes_and_convert_to_json(chosen_customers_file, distance_matrix_file)
print(results_json)
