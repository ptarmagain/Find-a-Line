from rasterio.plot import show
import rasterio as rio
import numpy as np
import math as m
import geopandas as gpd
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
import contextily as ctx
import sys
from multiprocessing import Pool, cpu_count
from functools import partial
from typing import List, Tuple, Optional
import time

def find_significant_slopes(slope_file: str, pixel_granularity: int) -> List[List[int]]:
    """Finds significant slopes from a raster file.
    
    Significant slopes are defined as slopes matching our formula.
    Outputs a list of pixel coords matching criteria.
    
    Args:
        slope_file: Path to the slope raster file
        pixel_granularity: Pixel resolution in meters (e.g., 30 for NASADEM)
    
    Returns:
        List of [row, col] pixel coordinates with significant slopes
    """
    with rio.open(slope_file) as slope_dataset:
        slope_band = slope_dataset.read(1)
        return np.argwhere(slope_band > pixel_granularity * 1.15 + 6).tolist()


def load_elevation_data(elevation_file: str) -> Tuple[np.ndarray, dict]:
    """Load elevation data and return it with metadata.
        
    Args:
        elevation_file: Path to the elevation raster file
    
    Returns:
        Tuple of (elevation_band numpy array, rasterio metadata dict)
    """
    with rio.open(elevation_file) as elevation_dataset:
        elevation_band = elevation_dataset.read(1)
        metadata = {
            'transform': elevation_dataset.transform,
            'crs': elevation_dataset.crs,
            'width': elevation_dataset.width,
            'height': elevation_dataset.height
        }
    return elevation_band, metadata


def evaluate_line_elevation(anchors: Tuple[List[int], List[int]], 
                            elevation_band: np.ndarray) -> List[float]:
    """Evaluates elevation differences along a line between two anchor points.
        
    Draws a line between two points using DDA algorithm and determines the 
    difference between our maximum desired elevation and the actual elevation 
    of each point in the line.
    
    Args:
        anchors: Tuple of two anchor points [[x1, y1], [x2, y2]]
        elevation_band: Pre-loaded elevation data as numpy array
    
    Returns:
        List of elevation differences for each pixel along the line
        Positive values indicate elevation is below maximum safe height
    """
    a1, a2 = anchors
    x_a1, y_a1 = int(a1[0]), int(a1[1])
    x_a2, y_a2 = int(a2[0]), int(a2[1])
    
    # Validate bounds
    if (x_a1 < 0 or y_a1 < 0 or x_a2 < 0 or y_a2 < 0 or
        x_a1 >= elevation_band.shape[0] or y_a1 >= elevation_band.shape[1] or
        x_a2 >= elevation_band.shape[0] or y_a2 >= elevation_band.shape[1]):
        return []

    # DDA algorithm - draw a line between the two points
    dx = x_a2 - x_a1
    dy = y_a2 - y_a1
    steps = max(abs(dx), abs(dy))
    
    if steps == 0:
        return []
    
    x_increment = dx / steps
    y_increment = dy / steps
    
    # Pre-calculate anchor elevations and use numpy for distance calculations
    elev_a1 = elevation_band[x_a1, y_a1]
    elev_a2 = elevation_band[x_a2, y_a2]
    elev_nr_a = min(elev_a1, elev_a2)
    
    # Convert anchors to numpy arrays for vectorized distance calculation
    a1_np = np.array([x_a1, y_a1])
    a2_np = np.array([x_a2, y_a2])
    
    elev_diffs = []
    x_c = float(x_a1)
    y_c = float(y_a1)

    for _ in range(steps - 1):
        x_c += x_increment
        y_c += y_increment
        
        # Round to nearest pixel for indexing
        x_c_round = int(round(x_c))
        y_c_round = int(round(y_c))
        
        # Bounds check
        if (x_c_round < 0 or y_c_round < 0 or 
            x_c_round >= elevation_band.shape[0] or y_c_round >= elevation_band.shape[1]):
            continue
        
        # Vectorized distance calculation using numpy
        current_point = np.array([x_c, y_c])
        d1 = np.linalg.norm(current_point - a1_np)
        d2 = np.linalg.norm(current_point - a2_np)
        d = min(d1, d2)
        
        # Find elevation of current pixel in our line
        elev_c = elevation_band[x_c_round, y_c_round]
        
        # Get difference of max acceptable elevation and current pixel elevation
        # Formula: max_elev = min_anchor_elev - (0.15 * distance) - 6
        elev_diff = elev_nr_a - (0.15 * d) - 6 - elev_c
        elev_diffs.append(elev_diff)
        
        # Early exit: if we find a pixel that's too high, stop checking
        if elev_diff <= 0:
            break
    
    return elev_diffs


# Global variable for elevation data (loaded once per worker process)
_worker_elevation_cache = {}


def _worker_init(elevation_file: str):
    """Initialize worker process - load elevation data once per worker.
    
    This is called once when each worker process starts, avoiding the overhead
    of loading the elevation file for every task.
    
    Args:
        elevation_file: Path to elevation raster file
    """
    global _worker_elevation_cache
    elevation_band, _ = load_elevation_data(elevation_file)
    _worker_elevation_cache['band'] = elevation_band


def _evaluate_line_pair(args: Tuple[List[int], List[int]]) -> Optional[List[List[int]]]:
    """Helper function for parallel processing.
    
    Evaluates a single line pair between two anchor points.
    This function is designed to be called by multiprocessing workers.
    
    Args:
        args: Tuple of (anchor1, anchor2) pixel coordinates
    
    Returns:
        Valid line pair [a1, a2] if valid, None otherwise
    """
    global _worker_elevation_cache
    a1, a2 = args
    elevation_band = _worker_elevation_cache.get('band')
    
    if elevation_band is None:
        return None
    
    # Evaluate line elevation
    elev_diffs = evaluate_line_elevation((a1, a2), elevation_band)
    
    # If all pixels meet our maximum height requirements, return valid line
    if elev_diffs and all(e > 0 for e in elev_diffs):
        return [a1, a2]
    
    return None


def find_valid_lines(all_points: List[List[int]], 
                     elevation_file: str, 
                     min_length: float, 
                     max_length: float,
                     num_processes: Optional[int] = None) -> List[List[List[int]]]:
    """Finds valid line pairs using parallel processing.
    
    OPTIMIZED VERSION with the following improvements:
    - Uses multiprocessing to evaluate line pairs in parallel
    - Better progress tracking and performance metrics
    
    Receives a list of raster pixel points and returns point pairs that are 
    between a specified distance of each other and match our elevation requirements.
    
    Args:
        all_points: List of anchor point coordinates [[x1, y1], [x2, y2], ...]
        elevation_file: Path to elevation raster file
        min_length: Minimum line length in pixels
        max_length: Maximum line length in pixels
        num_processes: Number of parallel processes (defaults to CPU count - 1)
    
    Returns:
        List of valid line pairs [[[x1, y1], [x2, y2]], ...]
    """
    start_time = time.time()
    
    # Convert to numpy array for faster distance calculations
    points_array = np.array(all_points)
    num_points = len(all_points)
    
    print(f"Evaluating {num_points} potential anchors...")
    print(f"Estimated total comparisons: ~{num_points * (num_points - 1) // 2}")
    
    # Pre-filter: Generate candidate pairs using vectorized distance calculations
    print("Generating candidate anchor pairs within length constraints...")
    candidate_pairs = []
    
    # Process in chunks to balance memory usage and speed
    chunk_size = 500  # Process 500 anchors at a time
    for i in range(0, num_points, chunk_size):
        end_i = min(i + chunk_size, num_points)
        
        # For each anchor in this chunk, compare with all remaining anchors
        for j in range(i, end_i):
            a1 = points_array[j]
            # Only compare with anchors after this one (avoid duplicates and self-comparisons)
            remaining_points = points_array[j+1:]
            
            if len(remaining_points) > 0:
                # Vectorized distance calculation
                distances = np.linalg.norm(remaining_points - a1, axis=1)
                # Filter by distance constraints
                valid_mask = (distances > min_length) & (distances < max_length)
                valid_indices = np.where(valid_mask)[0] + j + 1
                
                # Add candidate pairs to list
                for idx in valid_indices:
                    candidate_pairs.append((all_points[j], all_points[idx]))
        
        if i % 500 == 0 and i > 0:
            elapsed = time.time() - start_time
            print(f"  Generated {len(candidate_pairs)} candidate pairs from {end_i}/{num_points} anchors "
                  f"({elapsed:.1f}s)")
    
    print(f"\nFound {len(candidate_pairs)} candidate pairs within length constraints")
    
    if len(candidate_pairs) == 0:
        sys.exit('No anchor pairs found within specified length constraints.')
    
    # Setup parallel processing
    if num_processes is None:
        num_processes = max(1, cpu_count() - 1)  # Leave one core free for system
    
    print(f"Using {num_processes} parallel processes for elevation evaluation...")
    print(f"Each worker will load elevation data once at startup...")
    
    # Use multiprocessing to evaluate candidate pairs in parallel
    # Each worker loads elevation data once via _worker_init
    valid_lines = []
    batch_size = max(1000, len(candidate_pairs) // (num_processes * 4))  # Adaptive batch size
    
    with Pool(processes=num_processes, initializer=_worker_init, initargs=(elevation_file,)) as pool:
        # Process candidate pairs in batches to show progress
        processed = 0
        total_batches = (len(candidate_pairs) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, len(candidate_pairs))
            batch = candidate_pairs[batch_start:batch_end]
            
            # Execute batch in parallel
            results = pool.map(_evaluate_line_pair, batch)
            
            # Collect valid lines (filter out None results)
            batch_valid = [r for r in results if r is not None]
            valid_lines.extend(batch_valid)
            
            processed += len(batch)
            elapsed = time.time() - start_time
            progress = 100 * processed / len(candidate_pairs)
            rate = processed / elapsed if elapsed > 0 else 0
            
            print(f"Progress: {progress:.1f}% ({processed}/{len(candidate_pairs)} pairs) - "
                  f"Found {len(valid_lines)} valid lines - "
                  f"Rate: {rate:.0f} pairs/s - Elapsed: {elapsed:.1f}s")
    
    elapsed_total = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Completed in {elapsed_total:.2f} seconds")
    print(f"Evaluated {len(candidate_pairs)} candidate pairs")
    print(f"Found {len(valid_lines)} valid line pairs")
    print(f"Average rate: {len(candidate_pairs)/elapsed_total:.0f} pairs/second")
    print(f"{'='*60}")
    
    if len(valid_lines) == 0:
        sys.exit('No lines found matching elevation requirements.')
    
    return valid_lines

def coordify(pixel_pairs: List[List[List[int]]], elevation_file: str) -> List[List[float]]:
    """Convert pixel coordinates to GPS coordinates (longitude, latitude).
        
    Args:
        pixel_pairs: List of pixel coordinate pairs [[[x1, y1], [x2, y2]], ...]
        elevation_file: Path to elevation raster file (used for coordinate transform)
    
    Returns:
        List of GPS coordinate pairs [[lon1, lat1], [lon2, lat2], ...]
    """
    coord_pairs = []
    with rio.open(elevation_file) as elevation_dataset:
        for anchors in pixel_pairs:
            # Convert pixel coordinates to geographic coordinates
            coords_a1 = list(elevation_dataset.xy(*anchors[0]))
            coords_a2 = list(elevation_dataset.xy(*anchors[1]))
            coords_a1f = [float(c) for c in coords_a1]
            coords_a2f = [float(c) for c in coords_a2]
            coord_pairs.append(coords_a1f)
            coord_pairs.append(coords_a2f)
    return coord_pairs


def mapify(coord_pairs: List[List[float]]):
    """Visualize coordinate pairs as lines on an interactive map.
    
    Creates a map with basemap tiles showing all valid highline segments
    as thin neon pink lines connecting anchor points.
    
    Args:
        coord_pairs: List of [longitude, latitude] coordinates where
                     consecutive pairs form line segments (i.e., [0,1], [2,3], etc.)
    """
    # Create LineString geometries from consecutive coordinate pairs
    # coord_pairs contains: [anchor1_lon, anchor1_lat, anchor2_lon, anchor2_lat, ...]
    # Each line is formed by pairs: (0,1), (2,3), (4,5), etc.
    lines = []
    line_midpoints = []
    for i in range(0, len(coord_pairs), 2):
        if i + 1 < len(coord_pairs):
            # Create a line from anchor1 to anchor2
            anchor1 = coord_pairs[i]  # [lon, lat]
            anchor2 = coord_pairs[i + 1]  # [lon, lat]
            line = LineString([(anchor1[0], anchor1[1]), (anchor2[0], anchor2[1])])
            lines.append(line)
            line_midpoints.append(line.interpolate(0.5, normalized=True))  # Midpoint of line
    
    if not lines:
        print("No lines to display.")
        return
    
    # Create GeoDataFrame with LineString geometries
    gdf = gpd.GeoDataFrame(
        geometry=lines,
        crs="EPSG:4326"  # WGS84 coordinate system
    )
    
    # Plot the lines
    fig, ax = plt.subplots(figsize=(10, 10))
        
    # Plot lines
    gdf.plot(ax=ax, color='#FF10F0', linewidth=0.8, alpha=0.9)

    # Show circles at line midpoints
    gdf_midpoints = gpd.GeoDataFrame(geometry=line_midpoints, crs="EPSG:4326")
    gdf_midpoints.plot(ax=ax, color='#FF10F0', markersize=100, marker='o', alpha=0.6, zorder=3)

    # Add basemap
    ctx.add_basemap(ax, crs=gdf.crs, source=ctx.providers.OpenTopoMap)

    plt.show()