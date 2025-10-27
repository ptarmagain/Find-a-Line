from rasterio.plot import show
import rasterio as rio
import numpy as np
import math as m

# Global Variables
pxl_gran = 30   # pixel granularity
desired_min_length = 90
desired_max_length = 300
promising_points = []
valid_lines = []


# read slopes file
with rio.open('/Users/andrewpurchase/Documents/raster_data/hoffstadt/viz/viz.be_slope.tif') as slope_dataset:
    slope_band = slope_dataset.read(1)

    # filter null data points?

    # find significant slopes
    significant_slopes = np.argwhere(slope_band > pxl_gran * 1.15 + 6)
    significant_slopes_list = significant_slopes.tolist()
    print(len(significant_slopes_list))

    # format significant slopes and store as coordinates in promising points list
    for point in significant_slopes_list:
        coords_precasted = list(slope_dataset.xy(*point))
        coords = [float(c) for c in coords_precasted]
        promising_points.append(coords)


# read elevation file
with rio.open('/Users/andrewpurchase/Documents/raster_data/hoffstadt/output_be.tif') as elevation_dataset:
    elevation_band = elevation_dataset.read(1)

    # get the coordinates of two promising points
    x_a1, y_a1 = elevation_dataset.index(*promising_points[0])
    print(x_a1, y_a1)

    x_a2, y_a2 = elevation_dataset.index(*promising_points[10])
    print(x_a2, y_a2)

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
    # Apply the sigmoid function to the sum of all our height differences
    tot_elev_diff = (sum(elev_diffs) - np.mean(elev_diffs)) / np.std(elev_diffs) # Z-Score Standardization to avoid extreme sigmoid results
    fitness = 1 / (1 + np.exp(-tot_elev_diff)) # sigmoid function
    # If every pixel in the current line is below our max acceptable elevation, add it to the "valid lines" list
    if all(e <= 0 for e in elev_diffs):
        valid_lines.append([[x_a1, y_a1],[x_a2, y_a2], fitness])
    print(tot_elev_diff)
    print(valid_lines)
        
    # Evaluate line as a whole
    # if fitness < .5 then good genetics pass
    # if fitness >=.5 then detemine how poorly performed





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