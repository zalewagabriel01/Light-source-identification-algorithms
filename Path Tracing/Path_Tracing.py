import bpy
import time
import math
import mathutils
from mathutils import Vector
import random
import numpy as np

def get_rgb(obj, hit_point): #extract color from environment texture

    local_point = obj.matrix_world.inverted() @ hit_point
    radius = local_point.length
    
    u = 0.5 + math.atan2(local_point.y, local_point.x) / (2 * math.pi) #adjusting coordinates to sphere
    v = 0.5 - math.asin(local_point.z / radius) / math.pi
    
    material = obj.active_material
    if material and material.use_nodes:
        texture_node = next((n for n in material.node_tree.nodes if n.type == 'TEX_IMAGE'), None)
        if texture_node and texture_node.image:
            texture = texture_node.image
            width, height = texture.size
            x = int(u * width) % width
            y = int((1 - v) * height) % height
            rgb = texture.pixels[(y * width + x) * 4:(y * width + x) * 4 + 3]
            return tuple(rgb)
        else:
            raise ValueError("No Texture")
    else:
        raise ValueError("No Material")


def lambertian_brdf(norm): #random relect direction over the half sphere
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
    

def trace_ray (deps, scene, origin, dir, count):
    hit, location, normal, index, object, matrix = scene.ray_cast(deps, origin, dir) #Strahl verschießen
    
    #draw ray (needs much more time to execute when uncommented)
    #if hit:
    #    visualize_ray(origin, location-origin, (location-origin).length, count)
    #else:
    #    visualize_ray(origin, dir, 10000, count)
        
    return hit, location, normal, object        

start_time = time.time()    
depsgraph = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene

width = scene.render.resolution_x
height = scene.render.resolution_y

light_candidates = [] #possible light sources will be stored here

skybox = bpy.data.objects.get("Skybox")
if not skybox:
    print("No Skybox found.")
    time.sleep(5)
    exit()
    
camera = bpy.context.scene.camera
if not camera:
    print("No Camera found.")
    time.sleep(5)
    exit()
    
camera_normal = camera.matrix_world.to_3x3().col[2].normalized()  

rays_shot = 100 #change the number of rays shot here
print(f"{rays_shot} rays will be shot from the camera")
valid = 0
count = 0

while valid < rays_shot: #ray_shot rays will be taken into consideration
    #print(valid)
    x = random.uniform(0, width) #random start direction of the ray from the camera
    y = random.uniform(0, height)
    x_normalized = 2 * (x/width) - 1
    y_normalized = 2 * (y/height) - 1
    
    direction = ((camera.matrix_world @ mathutils.Vector((x_normalized, y_normalized, -1.0))) - camera.location).normalized()
    angle = camera_normal.angle(direction)
    
    if angle >= math.radians(155): #ray has to be shot inside the field of view
        hit, location, normal, object = trace_ray(depsgraph, scene, camera.location, direction, count) #ray is traced
        valid += 1
        count += 1
        
        while hit and object != skybox: #ray is supposed to be lambertian reflected on the objects surface and traced further
            hit, location, normal, object = trace_ray(depsgraph, scene, location + normal * 0.0001, lambertian_brdf(normal), count)
            count += 1
            
        if object == skybox: #Beim Erreichen der Umgebungskarte: Farbe, Position, Richtung speichern #When Skybox is reached, save color, position, direction
            rgb = get_rgb(skybox, location)
            candidate_direction = (location-skybox.location).normalized()
            light_candidates.append((rgb, location, candidate_direction))
                    
lightsource = max(light_candidates, key=lambda candidate: sum(candidate[0]), default=None) #declare the brightest spot

if lightsource:
    col, loc, dir = lightsource
    print(f"Color of light: {col}, Position on Skybox: {loc}, Direction of light source: {dir}")
end_time = time.time()
time_taken = end_time - start_time
print(f"Time needed: {time_taken:.2f} seconds needed.") 