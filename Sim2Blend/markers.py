#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import OpenSim .trc markers into Blender     ##
    ##################################################
    
    Import a .trc marker file into Blender.
    OpenSim API is not required.

    INPUTS: 
    - trc_path: path to a .trc marker file
                or to a a .c3d marker file
    - direction: 'zup' or 'yup' (default: 'zup')

    OUTPUTS:
    - Animated markers
'''


## INIT
import os
import numpy as np
import bpy
import bmesh

direction = 'zup'
RADIUS = 12/1000
COLOR =  (0, 1, 0, 0.8)


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon, Jonathan Camargo"
__copyright__ = "Copyright 2023, BlendOSim & Sim2Blend"
__credits__ = ["David Pagnon", "Jonathan Camargo"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## FUNCTIONS
def load_trc(trc_path):
    '''
    Retrieve data and marker names from trc

    INPUT: 
    - trc_path: path to the .trc file

    OUTPUT:
    - trc_data_np: 2D numpy array with marker coordinates at each time step
    - markerNames: list of marker names
    '''

    # read data
    trc_data_np = np.loadtxt(trc_path, skiprows=5)[:,1:] 
    
    # read marker names
    with open(trc_path) as f:
        for i, line in enumerate(f):
            if i == 2:
                trc_header = f.readline()[12:-3]
            elif i > 2:
                break
    markerNames = trc_header.split('\t\t\t')
    
    return trc_data_np, markerNames


def addMarker(marker_collection, position=(0,0,0), text="MARKER", color=COLOR):
    '''
    Add one marker to the scene

    INPUTS:
    - marker_collection: collection to add the marker to
    - position: marker position (default: (0,0,0))
    - text: marker name (default: "MARKER")
    - color: marker color (default: COLOR)

    OUTPUTS:
    - Created new marker
    '''

    # Color
    matg = bpy.data.materials.new("Green")
    matg.use_nodes = True
    tree = matg.node_tree
    nodes = tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    matg.diffuse_color = color
    
    #Add sphere
    mySphere=bpy.data.meshes.new('sphere')
    sphere = bpy.data.objects.new(text, mySphere)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=RADIUS)
    bm.to_mesh(mySphere)
    bm.free()
    sphere.location=position
    sphere.active_material = matg
    marker_collection.objects.link(sphere)
           
 
def import_trc(trc_path, direction='zup', target_framerate=30):
    '''
    Import a .trc marker file into Blender.
    OpenSim API is not required.

    INPUTS: 
    - trc_path: path to a .trc marker file
    - direction: 'zup' or 'yup' (default: 'zup')

    OUTPUTS:
    - Animated markers
    '''

    if trc_path.endswith('.trc'):
        # import trc    
        trc_data_np, markerNames = load_trc(trc_path)

        # set framerate
        bpy.context.scene.render.fps = target_framerate
        
        times = trc_data_np[:,0]
        fps = int((len(times)-1) / (times[-1] - times[0]))
        conv_fac_frame_rate = int(fps / target_framerate)
        # bpy.data.scenes['Scene'].render.fps = fps
            
        # create markers
        marker_collection = bpy.data.collections.new('markers')
        bpy.context.scene.collection.children.link(marker_collection)
        for markerName in markerNames:
            addMarker(marker_collection,text=markerName)
        
        # animate markers
        for i, m in enumerate(markerNames):
            coll_marker_names = [ob.name for ob in marker_collection.objects]
            m = [coll_m for coll_m in coll_marker_names if m in coll_m][0]
            for n in range(0, len(times), conv_fac_frame_rate):
                # y-up to z-up
                if direction=='zup':
                    loc_x = trc_data_np[n,3*i+1]
                    loc_z = trc_data_np[n,3*i+2]
                    loc_y = -trc_data_np[n,3*i+3]
                else:
                    loc_x = trc_data_np[n,3*i+1]
                    loc_y = trc_data_np[n,3*i+3]
                    loc_z = trc_data_np[n,3*i+2]
                obj=marker_collection.objects[m]
                obj.location=loc_x,loc_y,loc_z
                obj.keyframe_insert('location',frame=int(n/conv_fac_frame_rate)+1)
    
    elif trc_path.endswith('.c3d'):
        bpy.ops.preferences.addon_enable(module='io_anim_c3d')
        from io_anim_c3d import c3d_importer
        operator = bpy.types.Operator
        c3d_importer.load(operator, bpy.context, filepath = trc_path)
        