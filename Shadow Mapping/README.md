The Shadow Mapping algorithm is inspired by the approach presented in "Estimation of Position and Intensity of Dynamic Light Sources using Cast Shadows on Textured
real Surfaces" from Jiddi S., Robert P., Marchand E. [1]

The idea of this approach is to separate shadow areas and not shadow areas on a heatmap. Then, several possible light source position are declared in a specified area.
For every light source position, a heatmap is created and compared to the original heatmap through mse. The light source with the smallest mse is declared the reconstructed light source.

Here is the algorithm implemented for Blender:

1. create light.png (image showing the scene object with its shadows)
2. create ambient.png either by either removing all light sources in the scene or "over illuminating" the scene so that the shadows aren't to be seen anymore
   (image showing object without its shadows)
3. convert both images to CIELAB- color space
4. compare their pixels using a threshhold (if value < threshhold -> shadow, else not shadow)
       The threshold is usually a value that shows the boundary for the values to be compared, whether they are in the 80% of the smaller values of the brightness
       of the entire image, or in the larger 20% (one percentile of 80%).
5. declare step size for possible light source positions and the area in which they're tested (an imaginary cube wrapping the scene)
6. for every position
     set light source at this position
     create heatmap out of shadows infuenced by this set light source and the ambient.png
     compare this heatmap with the original heatmap through mse
     save the mse and the light source position
7. declare position with smallest mse the reconstructed light source position

The algorithm can be tested using the instructions on the Wiki.


[1] Jiddi S., Robert P., Marchand E.: "Estimation of Position and Intensity of Dynamic Light Sources Using Cast Shadows on Textured Real Surfaces.", 2018 25th IEEE International Conference on Image Processing (ICIP), pp. 1063-1067, 2018