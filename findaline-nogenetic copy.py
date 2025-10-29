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
    x = True


    import numpy as np

    points = np.array(all_points)  # Shape: (N, 2)
    # Compute all pairwise differences
    print('w')
    diff = points[:, np.newaxis, :] - points[np.newaxis, :, :]  # Shape: (N, N, 2)
    print('x')
    # Compute all distances
    distances = np.linalg.norm(diff, axis=2)  # Shape: (N, N)
    print('y')
    # Extract only the upper triangle (no duplicates, no self-comparisons)
    upper_triangle = np.triu_indices(len(points), k=1)
    print('z')
    unique_distances = distances[upper_triangle]
    print('a')

    for idx, (i, j) in enumerate(zip(*upper_triangle)):
        count = idx + 1
        print(count)
        d = unique_distances[idx]  # Access the distance by index
        a = all_points[i]
        b = all_points[j]
        if d > 60:
            # Find difference between our formula and what the actual elevation is
            elev_diffs = evaluate_line_elevation([a,b])
            # If all pixels  meet our maximum height requirements, add the line to our list
            if all(e > 0 for e in elev_diffs): 
                valid_lines.append([a,b])
                x = False
                break
        if x == False: break
        print(i,j)
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

    # significant_slopes = [[significant_slopes[0], significant_slopes[10]]]
    # for anchors in significant_slopes:
    #     elev_diffs = evaluate_line_elevation(anchors)
    #     print(elev_diffs, anchors)
    #     setup_generation(elev_diffs, anchors)





    # Evaluate line as a whole
    # if fitness < .5 then good genetics pass
    # if fitness >=.5 then detemine how poorly performed

    # open elevation file in main function and run evaluate line and setup generation within 



    # update readme formula, no need for absolute values
    # log to console isntead of priting
    # this line:
    #    elev_diff = elev_nr_a - (0.15 * d) - 6 - elev_c
    #  the distance is being calculated based on pixels, not meters (1px=30m)




    # use slope band to determine significant points, such as 6 or higher (depends on granularity)
        # save these points
    #
    # use the elevation band to draw lines between signifiicant locations
    # for 'i' in significant locations:
    #   find each other significant location within 200? meters
    #   for j in each othernearby significant location
    #       draw a line between the current significant location and other nearby significant location
    #       determine if this line follows our formula
    #       

    # or

    # pick random X significant locations and Y other significant locations that are between 50 and 250 meters of each X,
    # for i, j in X, Y:
    #   keep i and j in a list so that we don't attempt this exact same combination again
    #   draw a line between the two and determine genetics
    #   genetics are a percentage( pixels aligning with slope algorithm divided by total pixels in line ) (multiplied by a factor of how much the pixels exceed our minimum expectations)
    #   any genetics that are 100 are stored in a list for final output
    #   drop the lower 50% of genetics
    #   for the top 50% of genetics, make one dna based on i and one on j, both to new locations, ensure not in "don't attempt" list
    #   repeat i and j again
    #   stop after a certain number of generations or if we have reached X number of satisfactory outputs


    # The further you travel from the nearest anchor the lower elevation 

        # https://portal.opentopography.org/lidarDataset?opentopoID=OTLAS.022011.2994.1&minX=-122.82526016235349&minY=45.51091832390634&maxX=-122.70166397094724&maxY=45.61571843784051
        # resolution 6 ft