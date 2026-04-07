import bpy
import numpy as np
import math
from mathutils import Vector
import random
import time

def get_patch_center(object, patch): #get center of a patch
    verts = []
    for vertex in patch.vertices:
        verts.append(object.data.vertices[vertex].co)
    return object.matrix_world @ (sum(verts, Vector())/len(verts))

def monte_carlo_ray(norm): #generate random direction over the half sphere
    theta = random.uniform(0, np.pi)
    phi = random.uniform(0, 2 * np.pi)
    direction = Vector((np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)))
    if norm.angle(direction) >= math.radians(90):
        direction = direction * (-1)
        
    return direction    

def visualize_ray(start_point, direction, distance, c):
    end_point = start_point + direction.normalized() * distance
    
    edge_container = bpy.data.meshes.new(name = f"Ray_container{c}")
    edge = bpy.data.objects.new(name = f"Ray{c}", object_data=edge_container)
    bpy.context.collection.objects.link(edge)
    
    edge_container.from_pydata([start_point, end_point], [(0,1)], [])
    edge_container.update()
    
start_time = time.time()
lightmap = bpy.data.images.load(".../LightMap.png") #load lightmap from your directory

width, height = lightmap.size
lightmap_pixels = (np.array(lightmap.pixels[:])).reshape(width, height, 4)
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()

scene_object = bpy.data.objects["SceneObject"] #Scene Object
wrapper_object = bpy.data.objects["WrapperObject"] #Wrapper Object (add "2" or "3" depending on which one you want to test)
recovered_lightsource = bpy.data.objects["Recovered_Pointlight"]

uv_layer = scene_object.data.uv_layers.active.data #prepare patches from scene_object
patches = []
for polygon in scene_object.data.polygons:
    patch_uvs = [uv_layer[index].uv for index in polygon.loop_indices]
    patches.append(patch_uvs)

patch_intensities = []
selected_patches = []
hit_patches = []
final_patches_centers = []
form_factors = {}
numRaysToShoot = 10

max_intensity = float('-inf')

for patch in patches: #extract the intensity of all patches
    pixel_intensities = []
    for p in patch:
        x = int(min(p.x * width, width - 1))
        y = int(min(p.y * height, height -1))
        pixel = lightmap_pixels[y, x]
        intensity = sum(pixel[:3])
        pixel_intensities.append(intensity)
        
        if intensity > max_intensity:
            max_intensity = intensity
            max_intensity_coords = (x, y)
            
    patch_intensities.append(np.mean(pixel_intensities))

threshhold = max_intensity * 0.9 #find a suitable threshhold
 #threshold in order to choose "illuminated" patches
for patch_index, inten in enumerate(patch_intensities): #choosing illuminated patches
    if inten > threshhold:
        selected_patches.append(patch_index)
        
print(f"Selected Patches: {selected_patches}")     
        
if selected_patches: #mark chosen patches
    for patch in selected_patches:
        scene_object.data.polygons[patch].material_index = 1 
                            
w_matrix = scene_object.matrix_world
c = 0
print(f"Number of selected Patches: {len(selected_patches)}")               
for i in selected_patches: #go through every selected patch
    c = c + 1
    print(f"Selected Patch {c} with the Number {i}")   
    numRays = 0 #number of fired rays of current patch
    wrapper_hits = set() #patches of the wrapper object that were hit
    wrapper_hits_count = {} #how often the individual patches of the wrapper object were hit
    
    patch = scene_object.data.polygons[i]
    patch_center = get_patch_center(scene_object, patch)
    
    while (1): #fire rays until new hit patches of the wrapper object are below 20%
        new_hits = set()
        count = 0
        while count < numRaysToShoot:
            random_ray = monte_carlo_ray(w_matrix.to_3x3() @ patch.normal) #random direction          
            hit, location, normal, patch_index, hit_object, matrix = scene.ray_cast(depsgraph, patch_center + (w_matrix.to_3x3() @ patch.normal)*0.0001, random_ray) #Strahl verfolgen
            if hit and hit_object == wrapper_object:
                #visualize_ray(patch_center, random_ray, (location - patch_center).length, numRays + count) #needs longer to compute
                new_hits.add(patch_index)
                if patch_index not in wrapper_hits_count: #save how often the patch of the wrapper object was hit
                    wrapper_hits_count[patch_index] = 0
                wrapper_hits_count[patch_index] += 1
            count += 1
    
        unique_new_hits = new_hits - wrapper_hits #filter out unique new hits
        wrapper_hits.update(unique_new_hits)
    
        numRays += numRaysToShoot   
     
        if len(new_hits) == 0 or len(unique_new_hits)/len(new_hits) < 0.2:
            break
        
    hit_patches.append((wrapper_hits)) #save wrapper object patches hits for the patches of the scene object
    for j, numRaysGot in wrapper_hits_count.items(): #create form factor
        form_factors[i, j] = numRaysGot/numRays               
print(hit_patches)    
if hit_patches: #filter out patches of the wrapper object that were hit by every patch        
    intersected_patches = set.intersection(*hit_patches)
else:
    raise ValueError("No hit patches on Wrapper Object")
        
     
chosen_patches = intersected_patches.copy()
for wrapper_patch in intersected_patches: #sort out with the help of form factor
    count = 0        
    for scene_object_patch in selected_patches:
        if form_factors[scene_object_patch, wrapper_patch] < 1/len(hit_patches[count]):
            chosen_patches.remove(wrapper_patch)
            break
        count += 1
        
if len(chosen_patches) == 0: #if there are no patches left, go back to intersection
    print("Intersected patches had to be chosen")
    chosen_patches = intersected_patches.copy()        

print(f"Chosen Patches: {chosen_patches}")        
        
if chosen_patches:
    for patch in chosen_patches: #mark patches of Wrapper Object and declare their center as the reconstructed light source
        wrapper_object.data.polygons[patch].material_index = 0
        p = wrapper_object.data.polygons[patch]
        final_patches_centers.append(get_patch_center(wrapper_object, p))
    recovered_lightsource.location = (sum(final_patches_centers, Vector())/len(final_patches_centers))
    print(recovered_lightsource.location)       
    
end_time = time.time()
time_taken = end_time - start_time
print(f"Time needed: {time_taken}")  