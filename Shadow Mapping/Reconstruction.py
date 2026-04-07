import bpy
import numpy as np
import time

def convert_to_cielab(rgb):
    r, g, b, q = rgb
    x = r * 0.4125 + g * 0.3576 + b * 0.1804
    y = r * 0.2127 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9502
    
    l = 116 * y**(1/3) - 16 if y > 0.008856 else 903.3
    a = 500 * (x**(1/3)/x - y**(1/3)/y)
    b = 200 * (y**(1/3)/y - z**(1/3)/z)
    return l, a, b, q 

def generate_heatmap(): #see original_shadowmap
    scene.render.filepath = ".../heatmap.png" #your directory
    bpy.ops.render.render(write_still=True)
    light_image = bpy.data.images.load(".../light.png") #your directory
    ambient_image = bpy.data.images.load(".../ambient.png") #your directory

    width, height = ambient_image.size
    ambient_pixels = (np.array(ambient_image.pixels[:])).reshape(width, height, 4)
    light_pixels = (np.array(light_image.pixels[:])).reshape(width, height, 4)

    width, height, _ = ambient_pixels.shape
    ambient_cielab = np.zeros((width, height, 4))
    light_cielab = np.zeros((width, height, 4))

    for i in range(width):
        for j in range(height):
            ambient_cielab[i, j] = convert_to_cielab(ambient_pixels[i, j])
            light_cielab[i, j] = convert_to_cielab(light_pixels[i, j])       
       
    l_ambient = ambient_cielab[:, :, 0]
    l_light = light_cielab[:, :, 0]

    shadow_map = np.zeros(l_ambient.shape)
    light_threshold = np.percentile(l_ambient, 3.5)

    for i in range(width):
        for j in range(height):
            if l_light[i, j] < light_threshold:
                shadow_map[i, j] = 1

    heatmap_pixels = np.zeros((width, height, 4))            
    for i in range(width):
        for j in range(height):
            if shadow_map[i, j]: 
                heatmap_pixels[i, j] = [0.0, 0.0, 1.0, 1.0]
            else:
                heatmap_pixels[i, j] = [1.0, 1.0, 0.0, 1.0]           

    flat_pixels = heatmap_pixels.flatten()
    heatmap_image = bpy.data.images.new("HeatMap_1", width=width, height=height)
    heatmap_image.pixels = flat_pixels        
    heatmap_image.file_format = 'PNG'
    heatmap_image.save_render(filepath=".../result_heatmap_1.png") #your directory

    print("Shadow Map saved")

start_time = time.time()    
scene = bpy.context.scene
main_heatmap = bpy.data.images.load(".../result_heatmap_1.png") #load original Shadow Map
width, height = main_heatmap.size
main_heatmap_pixels = (np.array(main_heatmap.pixels[:])).reshape(width, height, 4)

border_corners = [(25, 24, -4), (25, -27, -4), (-26, -27, -4), (-26, 24, -4), (25, 24, 47), (25, -27, 47), (-26, -27, 47), (-26, 24, 47)] #Grenzen der potenziellen Positionen bestimmen
light_positions = [] #potential light sources
differences = [] #MSE's of shadow maps

x = border_corners[0][0]
x_end = border_corners[2][0] #declare step size inside area
step = 12 #change value here
if x < x_end:
    x_step = step
else:
    x_step = -step
    
y = border_corners[0][1]
y_end = border_corners[1][1]
if y < y_end:
    y_step = step
else:
    y_step = -step
    
z = border_corners[0][2]
z_end = border_corners[4][2]
if z < z_end:
    z_step = step
else:
    z_step = -step
    
for i in range(x, x_end, x_step):
    for j in range(y, y_end, y_step):
        for k in range(z, z_end, z_step):
            light_positions.append((i, j, k))
print(len(light_positions))            
count = 1            
for light_position in light_positions: #go through every possible position
    l_data = bpy.data.lights.new(name = 'Point_Light', type='POINT') #add light source
    l_data.energy = 10000
    l_source = bpy.data.objects.new(name= 'Point_Light', object_data = l_data)
    bpy.context.collection.objects.link(l_source)
    bpy.context.view_layer.objects.active = l_source
    l_source.location = light_position
    
    generate_heatmap() #generate current shadow map
    current_heatmap = bpy.data.images.load(".../result_heatmap_1.png")
    current_heatmap_pixels = (np.array(current_heatmap.pixels[:])).reshape(width, height, 4)
    
    difference = np.mean((current_heatmap_pixels - main_heatmap_pixels) ** 2) #MSE between original and current heatmap
    print(f"{count}: {difference}")
    
    bpy.data.images.remove(current_heatmap, do_unlink=True) #delete current shadow map
    bpy.data.objects.remove(l_source, do_unlink=True) #delete current light source
    
    differences.append(difference)
    count += 1
 
lightsource_difference = min(differences) #light source with smallest MSE
print(lightsource_difference)
ind = differences.index(lightsource_difference)
pos = light_positions[ind]

print(f"Lightsource Position: {pos}")
end_time = time.time()
time_taken = end_time - start_time
print(f"Time needed: {time_taken}")  