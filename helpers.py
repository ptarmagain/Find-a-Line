from rasterio.plot import show
import rasterio as rio
import numpy as np
import math as m
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import contextily as ctx
import sys

def find_significant_slopes(slope_file: str, pixel_granularity: int) -> list:
    """Finds significant slopes from a raster file
    Significant slopes are defined as slopes matching our formula.
    Outputs a list of pixel coords matching criteria."""
    with rio.open(f'{slope_file}') as slope_dataset:
        slope_band = slope_dataset.read(1)
        return np.argwhere(slope_band > pixel_granularity * 1.15 + 6).tolist()
    
def find_valid_lines(all_points: list, elevation_file: str, min_length: str, max_length: str):
    """Receives a list of raster pixel points and returns 
       point pairs that are between a specified distance of each other
       and match our elevation requirements
    ex:) Input: [[1,2],[1,3],[1,4],[10,20]], 1,3  
        Output: [[[1,2],1,3]]]
    """
    valid_lines = []
    count = 0

    # Compare every anchor..
    for i in range(len(all_points)):
        a1 = all_points[i]
        count += 1
        if i%100 == 0: print(round(100*count/len(all_points), 2),'% done')
        # To every other anchor
        for j in range(i + 1,len(all_points)):
            a2 = all_points[j]
            d = m.dist(a1,a2)
            if min_length < d and d < max_length:
                # Find difference between our formula and what the actual elevation is
                elev_diffs = evaluate_line_elevation([a1,a2], elevation_file)
                # If all pixels  meet our maximum height requirements, add the line to our list
                if all(e > 0 for e in elev_diffs): 
                    valid_lines.append([a1,a2])
                    break   # no need to continue evaluating anchor if we know it has a valid line
    if len(valid_lines) == 0: sys.exit('No lines found matching parameters.')
    return valid_lines

def evaluate_line_elevation(anchors: list, elevation_file: str) -> list:
    """Draws a line between to points.
        Determines the difference between our maximum desired elevation and the 
        actual elevation of each point in the line.
    ex:) Input: [[1,1][1,10]]
        Output: [10,8,7,5,-2,3,4,6]"""
    # Read elevation file
    with rio.open(f'{elevation_file}') as elevation_dataset:
        elevation_band = elevation_dataset.read(1)

        # Retrieve the pixel locations of our anchors
        x_a1, y_a1 = anchors[0]
        x_a2, y_a2 = anchors[1]

        # DDA algorithm - draw a line between the two points
        x_c = x_a1  # initalize current "step" coordinates to first anchor
        y_c = y_a1
        dx = x_a2 - x_a1
        dy = y_a2 - y_a1
        steps = max(abs(dx), abs(dy))
        x_increment = dx / steps
        y_increment = dy / steps
        elev_diffs = []

        for _ in range(steps - 1):
            x_c = x_c + x_increment
            y_c = y_c + y_increment
            # Distance to nearest anchor
            d = min(m.dist([x_c, y_c], [x_a1, y_a1]), m.dist([x_c, y_c], [x_a2, y_a2]))   
            # Elevation of nearest anchor
            elev_nr_a = min(elevation_band[round(x_a1), round(y_a1)], elevation_band[round(x_a2), round(y_a2)])
            # Find elevation of current pixel in our line
            elev_c = elevation_band[round(x_c), round(y_c)]
            # Get difference of max acceptable elevation and current pixel elevation
            elev_diff = elev_nr_a - (0.15 * d) - 6 - elev_c
            # Add to list of elevation differences for each pixel in line
            elev_diffs.append(elev_diff)
        return elev_diffs

def coordify(pixel_pairs: list, elevation_file: str):
    """Print the longitude and latitude of pairs of pixel values
    ex:) Input: [[[1,][2]],[[3][4]]]
        Output: [[[33.448376],[112.074036],[33.873940],[112.1748744]]]"""
    coord_pairs = []
    with rio.open(f'{elevation_file}') as elevation_dataset:
        for anchors in pixel_pairs:
            coords_a1 = list(elevation_dataset.xy(*anchors[0]))
            coords_a2 = list(elevation_dataset.xy(*anchors[1]))
            coords_a1f = [float(c) for c in coords_a1]
            coords_a2f = [float(c) for c in coords_a2]
            coord_pairs.append(coords_a1f)
            coord_pairs.append(coords_a2f)
    return coord_pairs

def mapify(coord_pairs: list):
    """Make a map with points of coordinate values"""
    gdf = gpd.GeoDataFrame(
        geometry=[Point(lon, lat) for lon, lat in coord_pairs],
        crs="EPSG:4326"  # WGS84 coordinate system
    )
    
    # Plot the points
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(ax=ax, color='blue', markersize=50)

    # Add basemap
    ctx.add_basemap(ax, crs=gdf.crs, source=ctx.providers.OpenTopoMap)

    # plt.title("Map with Points")
    plt.show()