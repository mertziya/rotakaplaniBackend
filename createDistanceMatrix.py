import pandas as pd
from geopy.distance import geodesic
import numpy as np

def calculate_distance_matrix(file_path):
    # Reading data into a DataFrame
    df = pd.read_excel(file_path)
    
    # Function to convert coordinates to proper float format
    def convert_coords(coord):
        # Splitting the number into integer and fractional parts
        integer_part = int(coord[:2])
        fractional_part = float("0." + coord[2:])
        
        return integer_part + fractional_part
    
    # Applying the conversion function to latitude and longitude columns
    df["Latitude"] = df["Latitude"].apply(lambda x: convert_coords(str(x)))
    df["Longitude"] = df["Longitude"].apply(lambda x: convert_coords(str(x)))
    
    # Preparing a distance matrix
    customers = df["CustomerID"].unique()
    num_customers = len(customers)
    dist_matrix = np.zeros((num_customers, num_customers))
    
    # Populating the distance matrix
    for i in range(num_customers):
        for j in range(num_customers):
            if i != j:
                coords_i = (df[df["CustomerID"] == customers[i]]["Latitude"].values[0],
                            df[df["CustomerID"] == customers[i]]["Longitude"].values[0])
                coords_j = (df[df["CustomerID"] == customers[j]]["Latitude"].values[0],
                            df[df["CustomerID"] == customers[j]]["Longitude"].values[0])
    
                # Calculating the distance
                dist_matrix[i, j] = geodesic(coords_i, coords_j).kilometers
    
    # Converting the distance matrix into a DataFrame for better visualization and handling
    dist_df = pd.DataFrame(dist_matrix, index=customers, columns=customers)
    
    return dist_df

# Example usage:
# file_path = "chosen_customers.xlsx"
# distance_matrix_df = calculate_distance_matrix(file_path)
# print(distance_matrix_df)
