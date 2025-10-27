# Find-a-Line
This is an application that finds and outputs locations with significant highline potential. It works by extracting DEM data from .tiff files and evalutating the potential of each raster pixel by applying a custom "maximum elevation formula". Considering the vast volume of data available, a genetic algorithm making use of the sigmoid function is implemented in order to focus on regions that have the most promising topographical characteristics.

## Maximum Elevation Formula
Due to deflection, the further you travel from the nearest anchor the lower elevation required. The maximum safe elevation for a hypothetical 0 meter highline is 6 meters lower than the anchors- this is to account for a leash fall. From there we require 15cm more clearance for every meter longer the line is. This slope was calculated based on a mid stretch webbing, a 155kg athlete, and 2kN tension for a median stretch webbing. Naturally there are many other variables to account for, but for simplicity sake we are using a formula that may be described as an "overestimation" for this specific application. 

The maximum safe height at any given distance from the nearest anchor can be described as below.
<img width="407" height="27" alt="Screenshot 2025-10-22 at 10 15 20 PM" src="https://github.com/user-attachments/assets/8f818536-91d3-4191-a9b0-31892a2b3ecc" />
- a<sub>1</sub> = anchor 1
- a<sub>2</sub> = anchor 2
- c = current point
- d = distance from the current point to an anchor
- e = elevation

This may be visualised as a slope below the line that is always exactly 6 meters below the line at maximum deflection.
<img width="1361" height="224" alt="visualisation" src="https://github.com/user-attachments/assets/5147f16f-768c-4a63-89b6-105c0c6ea8bd" />


*It is worth noting that this formula for a "maximum safe highline elevation at any given point" does not account for a potential mainline failure, under which circumstance a substantially lower elevation is required for safety. As always, use your best judgement; this is simply a tool to aid in surveying.*

## Algorithm Breakdown
- We first extract raster pixels of significant slope to use as a starting point for promising anchors.
- Using two random points between argument-designated distance from each other, we "draw" a line using a DDA (Digital Differential Analyzer) algorithm
- For each raster pixel that exists along this line, the maximum elevation is calculated using our formula, and the pixel's elevation is subtracted from this value to retrieve the elevation difference. *A **positive** elevation difference implies that the pixel's elevation is **lower** than our required maximum.. a **higher** difference is **better**!*
- The elevation differences of each pixel are summed and passed through a sigmoid function to determine a weight that is used for genetics.

## Learn More
- [Tension calculator](https://www.balancecommunity.com/pages/tension-calculator)
- [A good resource for finding DEM data for this project](https://portal.opentopography.org/raster?opentopoID=OTSDEM.032021.4326.2)
