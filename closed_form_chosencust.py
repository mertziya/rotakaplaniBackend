#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  3 10:35:19 2024

@author: hazalbulutcu
"""


from math import radians, cos, sin, asin, sqrt

from gurobipy import *
import math
import pandas as pnd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import json
import createDistanceMatrix as distance
from io import BytesIO

def optimizationAlgo():
    open_maps_api_key = "5b3ce3597851110001cf62487d56fbc4f7bb4a7c9375b1453dd0e1fa"
    google_api = "AIzaSyB1QGeo5CWNY_5Q84Mxen8XIQuZM_5_YvE"

    m = Model('ENS492')
    #Reading the excel file and retrieving values

    df = pnd.read_excel("chosen_customers.xlsx",index_col=0)
    df2 = pnd.read_excel("chosen_customers.xlsx")

    N= list(range(45))

    cust_ids = list(df2.iloc[0:len(N),0])

    xcoor=list(df.iloc[0:len(N),0])
    ycoor=list(df.iloc[0:len(N),1])

    listlength=len(N)

    earliest=list(df.iloc[0:len(N),2])
    latest=list(df.iloc[0:len(N),3])
    servicetime=list(df.iloc[0:len(N),4])
    ser_day=list(df.iloc[0:len(N),5])
    vehiclecap=3       #df.iloc[4,10]


    # def calculate_distance_matrix(file_path):
    #     # Reading data into a DataFrame
    #     df = pnd.read_excel(file_path)
        
    #     # Function to convert coordinates to proper float format
    #     def convert_coords(coord):
    #         # Splitting the number into integer and fractional parts
    #         integer_part = int(coord[:2])
    #         fractional_part = float("0." + coord[2:])
            
    #         return integer_part + fractional_part
        
    #     # Applying the conversion function to latitude and longitude columns
    #     df["Latitude"] = df["Latitude"].apply(lambda x: convert_coords(str(x)))
    #     df["Longitude"] = df["Longitude"].apply(lambda x: convert_coords(str(x)))
        
    #     # Preparing a distance matrix
    #     customers = df["CustomerID"].unique()
    #     num_customers = len(customers)
    #     dist_matrix = np.zeros((num_customers, num_customers))
        
    #     # Populating the distance matrix
    #     for i in range(num_customers):
    #         for j in range(num_customers):
    #             if i != j:
    #                 coords_i = (df[df["CustomerID"] == customers[i]]["Latitude"].values[0],
    #                             df[df["CustomerID"] == customers[i]]["Longitude"].values[0])
    #                 coords_j = (df[df["CustomerID"] == customers[j]]["Latitude"].values[0],
    #                             df[df["CustomerID"] == customers[j]]["Longitude"].values[0])
        
    #                 # Calculating the distance
    #                 dist_matrix[i, j] = geodesic(coords_i, coords_j).kilometers
        
    #     # Converting the distance matrix into a DataFrame for better visualization and handling
    #     dist_df = pd.DataFrame(dist_matrix, index=customers, columns=customers)
        
    #     return dist_df
            
    df = distance.calculate_distance_matrix("./chosen_customers.xlsx")
    eucdistance = df.to_numpy()
    #eucdistance = calculate_distance_matrix("distance_matrix-2.xlsx")

    # Saving the distance matrix to an Excel file
    output_file_path = "distance_matrix.xlsx"
    df.to_excel(output_file_path)

    

    df.to_clipboard(excel=True)
            # For printing the matrix
            # for i in range(len(xcoor)):
            #     for j in range(len(xcoor)):
            #         print(matrix[i][j], end=" ")
        


    num_customers = 44
    K = 8 # #no vehicles (used as upper bound)
    M = 1000000 # big number
    T = 200000 # vehicle capacity     saat olarak kapasitem


    #d = demand
    s = servicetime
    e = earliest
    l = latest
    #c = eucdistance
    t = eucdistance

    day=3

    # Create decision variables
    # x[i,j, d] Binary variable, 1 if and only if vehicle moves over the arc i,j
    x = m.addVars(num_customers, num_customers, day, vtype=GRB.BINARY, name='x')

    # b[i,d] continuous decision variable shows the service starting time at each vertex i
    b = m.addVars(num_customers, day, lb=0, vtype=GRB.INTEGER, name='b')

    # helper var?
    u = m.addVars(num_customers, lb=0, vtype=GRB.INTEGER, name='u')


    # ensure there is only 1 vehicle entering and leaving each node
    m.addConstrs(quicksum(x[i,j,d] for d in range(day) for j in range(num_customers)) == 1 for i in range(1,num_customers))
    m.addConstrs(quicksum(x[i,j,d] for d in range(day) for i in range(num_customers)) == 1 for j in range(1, num_customers))


    # for d in range(day):
    #     m.addConstrs(quicksum(x[i,j,d] for j in range(num_customers)) == 1 for i in range(1,num_customers))
    #     m.addConstrs(quicksum(x[i,j,d] for i in range(num_customers)) == 1 for j in range(1, num_customers))
    # ensure same # of vehicles leaves and returns to node 0
    # for d in range(day):
    m.addConstr(quicksum(x[0,j,d] for d in range(day) for j in range(1, num_customers)) == K)
    m.addConstr(quicksum(x[i,0,d] for d in range(day) for i in range(1, num_customers)) == K)    
        

    # m.addConstr(quicksum((x[0,j,0] + x[0,j,1])for j in range(1, num_customers)) <= K)
    # m.addConstr(quicksum((x[i,0,0] + x[i,0,1]) for i in range(1, num_customers)) <= K)

    # ensure service at each node is within the time window
    m.addConstrs(e[j] <= b[j,d] for d in range(day) for j in range(num_customers))
    m.addConstrs(b[j,d] <= l[j] for d in range(day) for j in range(num_customers))

    for d in range(day):
        m.addConstrs(quicksum(x[i,j,d] for j in range(num_customers)) == quicksum(x[j,i,d] for j in range(num_customers)) for i in range(1,num_customers))

    # links arrival time at a node to the departure time from the preceding node

    for d in range(day):
        for i in range(num_customers):
            for j in range(1,num_customers):
                m.addConstr(b[i,d] + s[i] + t[i,j] 
                            - M * (1 - (x[i,j,0] + x[i,j,1] + x[i,j,2])) <= b[j,d])
    
    # for d in range(day):
    #     for i in range(num_customers):
    #         for j in range(1,num_customers):
    #             m.addConstr(x[i,j,d]+x[i,j,1] == 1)

    # m.addConstrs(quicksum(x[0,j,d]  for j in range(1,num_customers)) ==  100 for d in range(day))
    
    for d in range(day):       
        for i in range(num_customers):
            for j in range(num_customers):
                #m.addConstr(b[i,d] + s[i] + t[i,0] <= T)
                m.addConstr(b[i,d] + s[i] + t[i,0] 
                            - M * (1 - (x[i,0,0] + x[i,0,1] + x[i,0,2])) <= T)
        
        

    m.setObjective(quicksum((x[i,j,d]*t[i,j]) for d in range(day) for i in range(num_customers) for j in range(num_customers) ), GRB.MINIMIZE)
    #m.setObjective(quicksum(x[i,j,d]*t[i,j] for i in range(num_customers) for j in range(num_customers) for d in range(day)), GRB.MINIMIZE)

    m.setParam('OutputFlag', 0)
    # solve the model
    m.optimize()

    status = m.status
    object_Value = m.objVal
    print()
    print("model status is: ", status)
    print()
    print("Objective value for optimal solution is: ", object_Value)

    out = []

    def insert_decimal(value, int_digits):
        value_str = str(value)
        return float(value_str[:int_digits] + '.' + value_str[int_digits:])

    if status != 3 and status != 4:
        for v in m.getVars():
            if m.objVal < 1e+99 and v.x != 0:
                if v.Varname[0] in ["u"]:
                    continue
                if v.Varname[0] in ["x"]:
                    x_values = v.Varname.split('[')[1].split(']')[0].split(',')
                    start_x = insert_decimal(xcoor[int(x_values[0])], 2)
                    start_y = insert_decimal(ycoor[int(x_values[0])], 2)
                    end_x = insert_decimal(xcoor[int(x_values[1])], 2)
                    end_y = insert_decimal(ycoor[int(x_values[1])], 2)
                    out.append({
                        "start_index": cust_ids[int(x_values[0])],
                        "start_x": start_x,
                        "start_y": start_y,
                        "end_index": cust_ids[int(x_values[1])],
                        "end_x": end_x,
                        "end_y": end_y,
                        "day": x_values[2]
                    })

                    

    print(out)
    with open('calculated.json', 'w') as out_file: 
        out_file.write(json.dumps(out))            
                
    return out