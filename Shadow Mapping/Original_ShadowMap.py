import bpy
import numpy as np

def convert_to_cielab(rgb): #convert RGB to CIELAB
    r, g, b, q = rgb
    x = r * 0.4125 + g * 0.3576 + b * 0.1804
    y = r * 0.2127 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9502
    
    l = 116 * y**(1/3) - 16 if y > 0.008856 else 903.3
    a = 500 * (x**(1/3)/x - y**(1/3)/y)
    b = 200 * (y**(1/3)/y - z**(1/3)/z)
    return l, a, b, q  

ambient_image = bpy.data.images.load(".../ambient.png") #load ambient png from your directory
light_image = bpy.data.images.load(".../light.png") #load light.png from your directory

width, height = ambient_image.size
ambient_pixels = (np.array(ambient_image.pixels[:])).reshape(width, height, 4)
light_pixels = (np.array(light_image.pixels[:])).reshape(width, height, 4)

width, height, _ = ambient_pixels.shape
ambient_cielab = np.zeros((width, height, 4))
light_cielab = np.zeros((width, height, 4))

for i in range(width):
    for j in range(height): #convert images
        ambient_cielab[i, j] = convert_to_cielab(ambient_pixels[i, j])
        light_cielab[i, j] = convert_to_cielab(light_pixels[i, j])                    
       
l_ambient = ambient_cielab[:, :, 0]
l_light = light_cielab[:, :, 0] 

shadow_map = np.zeros(l_ambient.shape)
light_threshold = np.percentile(l_ambient, 3.5) #declare threshold (percentile) here

for i in range(width):
    for j in range(height):
        if l_light[i, j] < light_threshold: #declare pixels as shadows that are below the threshold
            shadow_map[i, j] = 1
            
heatmap_pixels = np.zeros((width, height, 4))            
for i in range(width):
    for j in range(height): #mark shadow and not shadow differently
        if shadow_map[i, j]: 
            heatmap_pixels[i, j] = [0.0, 0.0, 1.0, 1.0]
        else:
            heatmap_pixels[i, j] = [1.0, 1.0, 0.0, 1.0]          

flat_pixels = heatmap_pixels.flatten() #create Shadow Map
heatmap_image = bpy.data.images.new("HeatMap", width=width, height=height)
heatmap_image.pixels = flat_pixels        
heatmap_image.file_format = 'PNG'
heatmap_image.save_render(filepath=".../result_heatmap.png") #save the heatmap to your directory

print("Shadow Map saved")  