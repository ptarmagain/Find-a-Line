from rasterio.plot import show
import rasterio as rio
import numpy as np
import math as m

# Global Variables
pxl_gran = 30   # pixel granularity
desired_min_length = 90
desired_max_length = 300
valid_lines = []


def find_significant_slopes() -> list:
    # read slopes file
    with rio.open('/Users/andrewpurchase/Documents/raster_data/hoffstadt/viz/viz.be_slope.tif') as slope_dataset:
        slope_band = slope_dataset.read(1)

        # filter null data points?

        # find significant slopes
        significant_slopes = np.argwhere(slope_band > pxl_gran * 1.15 + 6)
        significant_slopes_list = significant_slopes.tolist()

        return significant_slopes_list
    
def pair_points_by_distance(all_points: list):
    """Receives a list of raster pixel points and returns 
    point pairs that are between a specified distance of each other
    ex:) Input: [[1,2],[1,3],[1,4],[10,20]], 1,3  
        Output: [[[1,2],1,3]]]
    """
    valid_lines = []
    count = 0

    # Compare every point..
    for i in range(len(all_points)):
        a = all_points[i]
        count += 1
        print(count)
        # To every other point
        for j in range(i + 1,len(all_points)):
            b = all_points[j]
            d = m.dist(a,b)
            if 60 < d and d < 100:
                # Find difference between our formula and what the actual elevation is
                elev_diffs = evaluate_line_elevation([a,b])
                # If all pixels  meet our maximum height requirements, add the line to our list
                if all(e > 0 for e in elev_diffs): 
                    valid_lines.append([a,b])
    # Print output as coordinates
    coordify(valid_lines)

def coordify(pixels: list):
    """Print the longitude and latitude of pairs of pixel values
    ex:) Input: [[[1,][2]],[[3][4]]]
        Output: [[[33.448376],[112.074036],[33.873940],[112.1748744]]]"""
    coords_list = []
    with rio.open('/Users/andrewpurchase/Documents/raster_data/hoffstadt/output_be.tif') as elevation_dataset:
        for anchors in pixels:
            coords_a1 = list(elevation_dataset.xy(*anchors[0]))
            coords_a2 = list(elevation_dataset.xy(*anchors[1]))
            coords_list.append([coords_a1, coords_a2])
    print(coords_list)

    
    
def evaluate_line_elevation(anchors: list) -> list:
    # Read elevation file
    with rio.open('/Users/andrewpurchase/Documents/raster_data/hoffstadt/output_be.tif') as elevation_dataset:
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

        for i in range(steps - 1):
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

if __name__ == "__main__":
    significant_slopes = find_significant_slopes()
    print(len(significant_slopes))
    pair_points_by_distance(significant_slopes)
