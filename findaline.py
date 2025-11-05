"""
Find-a-Line - Highline Location Finder
========================================

This application finds locations with significant highline potential by analyzing
DEM (Digital Elevation Model) raster data.

"""

import helpers as sh

# Configuration Variables
# =======================
# If using NASADEM data, these values are in metres
desired_min_length = 200  # Minimum line length in metres
desired_max_length = 2000  # Maximum line length in metres
slope_file = '/path/to/data/viz/viz.be_slope.tif'
elevation_file = '/path/to/data/output_be.tif'
pixel_granularity = 30  # Pixel resolution in metres (30m for NASADEM data)

# Optional: Set number of parallel processes (defaults to CPU count - 1)
# num_processes = 4  # Uncomment and set to override default

if __name__ == "__main__":
    # Convert length constraints from metres to pixels
    desired_min_length_px = desired_min_length // pixel_granularity
    desired_max_length_px = desired_max_length // pixel_granularity
    
    print("="*60)
    print("Find-a-Line - Highline Location Finder")
    print("="*60)
    print(f"Length constraints: {desired_min_length}m - {desired_max_length}m")
    print(f"Pixel constraints: {desired_min_length_px}px - {desired_max_length_px}px")
    print("="*60)
    
    # Step 1: Find raster pixels with significant slope for promising anchors
    print("\nStep 1: Finding significant slopes...")
    significant_slopes = sh.find_significant_slopes(slope_file, pixel_granularity)
    print(f"Found {len(significant_slopes)} potential anchors to evaluate")
    
    # Step 2: Compare each promising anchor to every other anchor
    # This uses parallel processing for optimal performance
    print("\nStep 2: Evaluating anchor pairs...")
    valid_lines = sh.find_valid_lines(
        significant_slopes, 
        elevation_file, 
        desired_min_length_px, 
        desired_max_length_px
        # num_processes=num_processes  # Uncomment to override default
    )
    
    # Step 3: Convert pixel coordinates to GPS coordinates
    print("\nStep 3: Converting pixel coordinates to GPS coordinates...")
    valid_line_coords = sh.coordify(valid_lines, elevation_file)
    print(f"\nFound {len(valid_line_coords) // 2} valid line pairs")
    print("GPS Coordinates:")
    for i in range(0, len(valid_line_coords), 2):
        print(f"  Line {i//2 + 1}:")
        print(f"    Anchor 1: {valid_line_coords[i]}")
        print(f"    Anchor 2: {valid_line_coords[i+1]}")
    
    # Step 4: Display results on a map
    print("\nStep 4: Displaying results on map...")
    sh.mapify(valid_line_coords)
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)