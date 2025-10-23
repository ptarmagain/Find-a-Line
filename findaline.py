import rasterio as rio
import numpy as np

pixel_granularity = 30
desired_min_length = 90
desired_max_length = 300
valid_lines = []

with rio.open('/Users/andrewpurchase/Documents/my-learning-sandbox/rasterio_geopandas/opentopography/viz/viz.be_slope.tif') as dataset:
    slope_band = dataset.read(1)

    # filter null data points?

    # find significant slopes
    significant_slopes = np.argwhere(slope_band > pixel_granularity*1.14+6)
    significant_slopes_list = significant_slopes.tolist()
    print(len(significant_slopes_list))


    # read elevation band / file



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