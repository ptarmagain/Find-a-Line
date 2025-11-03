import helpers as sh

# Global Variables
    # A higher min/max length yield better results, but takes longer to calculate
    # A wider min/max length gap also results in longer calculation
    # I suggest to run multiple times with narrow selections for desired line lengths
    # If using NASADEM data, these values are in metres
desired_min_length = 100
desired_max_length = 130
slope_file = '/Users/andrewpurchase/Documents/raster_data/hoffstadt/viz/viz.be_slope.tif'
elevation_file = '/Users/andrewpurchase/Documents/raster_data/hoffstadt/output_be.tif'
pixel_granularity = 30 # if using NASADEM data, 30 metres

if __name__ == "__main__":
    desired_min_length = desired_min_length // pixel_granularity
    desired_max_length = desired_max_length // pixel_granularity
    valid_lines = []

    # Find raster pixels with significant slope for promising anchors
    significant_slopes = sh.find_significant_slopes(slope_file, pixel_granularity)
    print(len(significant_slopes), 'potential anchors to evaluate')
    # Compare each promising anchor each other promising anchor
    valid_lines = sh.find_valid_lines(significant_slopes, elevation_file, desired_min_length, desired_max_length)
    # Turn our list of raster pixels into a list of GPS coordinates
    valid_line_coords = sh.coordify(valid_lines, elevation_file)
    print(valid_line_coords)
    # Display these coordinate points on a map
    sh.mapify(valid_line_coords)