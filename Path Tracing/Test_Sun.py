import bpy
from mathutils import Vector

vector = (Vector((0.0985, -0.5212, 0.8477))).normalized() #input direction of the the light source for the sun
lightsource = bpy.data.objects['Sun']

lightsource.rotation_mode = 'QUATERNION'
lightsource.rotation_quaternion = vector.to_track_quat('Z','Y')