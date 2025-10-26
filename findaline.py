from rasterio.plot import show
import rasterio as rio
import numpy as np
import math as m

# Global Variables
pxl_gran = 30           # pixel granularity
desired_min_length = 90
desired_max_length = 300
promising_points = []
valid_lines = []

def eval_pixel(c, a1, a2):
    # print(c)
    # Find distance between current location and nearest anchor   
    d = min(m.dist(c, a1), m.dist(c, a2))
    
    # Determine if this pixel meets our criteria
    elev_c = elevation_band[*c]           # modularize, cannot have a dependency like this. If cannot modularize then pass elevation band as a variable
    elev_a = min(elevation_band[*a1], elevation_band[*a2])
    print(elev_c <= elev_a - 0.15 * d - 6 * pxl_gran)

    print(elev_a, d, elev_c)


# read slopes file
with rio.open('/Users/andrewpurchase/Documents/raster_data/hoffstadt/viz/viz.be_slope.tif') as slope_dataset:
    slope_band = slope_dataset.read(1)

    # filter null data points?

    # find significant slopes
    significant_slopes = np.argwhere(slope_band > pxl_gran * 1.15 + 6) #* pxl_gran)
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
    print(elevation_band[x_a1, y_a1])  

    x_a2, y_a2 = elevation_dataset.index(*promising_points[10])
    print(x_a2, y_a2)
    print(elevation_band[x_a2, y_a2])  

    print('DDA begins here:')

    # draw a line between the two points using DDA
    x = x_a1
    y = y_a1
    dx = x_a2 - x_a1
    dy = y_a2 - y_a1
    steps = max(abs(dx), abs(dy))
    x_increment = dx / steps
    y_increment = dy / steps
    print(x_increment, y_increment  )

    for i in range(steps - 1):
        x = x + x_increment
        y = y + y_increment
        eval_pixel([round(x), round(y)], [x_a1, y_a1], [x_a2, y_a2])



    # log to console




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