# Blender python script for generating solids with given cross-sections.
# Authors: Sebastian Bozlee, Athena Sparks
#
# To run, open a Text Editor view in Blender, open this file, then press the "Run Script" button.
#
# To generate different solids, edit the function calls at the bottom of the file.

import bpy
import mathutils
from math import *


##### Generate vertices for cross-section shapes #####
square_centered_at_middle = [ (-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
square_centered_at_bottom = [ (-1.0, 0), (1.0, 0.), (1.0, 2.0), (-1.0, 2.0) ]
eqtriangle_centered_at_bottom = [ (-1.0, 0), (1.0, 0.0), (0.0, sqrt(3)) ]
rttriangle_centered_at_bottom = [ (-1.0, 0), (1.0, 0.0), (-1.0, 2.0) ]

semicircle_centered_at_bottom = []
circle_num_points = 80
for i in range(circle_num_points):
    theta = i*3.1415926535/circle_num_points
    semicircle_centered_at_bottom.append( ( cos(theta), sin(theta) ) )
    
circle_centered_at_middle = []
circle_num_points = 60
for i in range(circle_num_points):
    theta = i*2*3.1415926535/circle_num_points
    circle_centered_at_middle.append( ( sin(theta), cos(theta) ) )

# Code for generating models of various types.
# Sample uses at the end of the file, below.
#
# Each function uses a subset of the following parameters:
# a = min x-value
# b = max x-value
# num_slices = number of slices
# fy = y-scaling as a function of x
# fz = z-scaling as a function of x
# cross_section = List of (x,y) vertices for the cross-section shape.
#                 Easiest to use one of the pre-defined lists above.
# R = outer radius as a function of x
# r = inner radius as a function of x

# Generates a model with chunky slices, as in a Riemann-sum.
def create_sliced_model(a, b, num_slices, fy, fz, cross_section):
	vertices = []
	edges = []
	faces = []
	vertices_chunk_start = 0
	
	dx = float(b-a)/num_slices
	
	for i in range(num_slices):
		x = a + dx*i
		fy_of_x = fy(x + 0.5*dx)
		fz_of_x = fz(x + 0.5*dx)
		
		# Left face of chunk
		for v in cross_section:
			vertices.append( (x, fy_of_x*v[0], fz_of_x*v[1]) )
			
		for j in range(len(cross_section) - 1):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + j + 1) )
		edges.append((vertices_chunk_start + len(cross_section) - 1, vertices_chunk_start))
		
		# if first slice, fill in left hand face.
		if i == 0:
			for j in range(len(cross_section) - 2):
				faces.append( (vertices_chunk_start, vertices_chunk_start + j + 1, vertices_chunk_start + j + 2) )
        # if not first slice, connect to previous slice
		if i != 0:
			previous_chunk_start = vertices_chunk_start - len(cross_section)
			for j in range(len(cross_section) - 1):
				faces.append( (previous_chunk_start + j, previous_chunk_start + j + 1, vertices_chunk_start + j + 1, vertices_chunk_start + j) )
			faces.append( (previous_chunk_start + len(cross_section) - 1, previous_chunk_start, vertices_chunk_start, vertices_chunk_start + len(cross_section) - 1) )
		
		vertices_chunk_start = len(vertices)
		
		# Right face of chunk
		for v in cross_section:
			vertices.append( (x + dx, fy_of_x*v[0], fz_of_x*v[1]) )
			
		for j in range(len(cross_section) - 1):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + j + 1) )
		edges.append((vertices_chunk_start + len(cross_section) - 1, vertices_chunk_start))
		
		# If last slice, fill in the right hand face. If not, this will be filled in as left side of next slice.
		if i == num_slices - 1:
			for j in range(len(cross_section) - 2):
				faces.append( (vertices_chunk_start, vertices_chunk_start + j + 1, vertices_chunk_start + j + 2) )
		
		# move back to where vertices of this chunk start...
		vertices_chunk_start = len(vertices) - 2*len(cross_section)
		
		# "dx edges"/"outside edges" of chunk
		for j in range(len(cross_section)):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + len(cross_section) + j) )

        # "dx faces"/"outside faces" of chunk
		for j in range(len(cross_section) - 1):
			faces.append( (vertices_chunk_start + j,
				vertices_chunk_start + j + 1,
				vertices_chunk_start + len(cross_section) + j + 1,
				vertices_chunk_start + len(cross_section) + j) )
		faces.append( (vertices_chunk_start + len(cross_section) - 1,
			vertices_chunk_start,
			vertices_chunk_start + len(cross_section),
			vertices_chunk_start + 2*len(cross_section) - 1) )
			
		vertices_chunk_start = len(vertices)
	
	me = bpy.data.meshes.new("SliceyMesh")
	ob = bpy.data.objects.new("Slicey", me)
	ob.location = (0,0,0)
	ob.show_name = True
	bpy.context.scene.objects.link(ob)
	me.from_pydata(vertices, edges, faces)
	me.update(calc_edges = True)

# Generates a smooth model. Use a larger num_slices for a smoother model.
def create_smooth_model(a, b, num_slices, fy, fz, cross_section):
	vertices = []
	edges = []
	faces = []
	vertices_chunk_start = 0
	
	dx = float(b-a)/num_slices
	
	for i in range(num_slices):
		x = a + dx*i
		
		# Left face of chunk
		for v in cross_section:
			vertices.append( (x, fy(x)*v[0], fz(x)*v[1]) )
			
		for j in range(len(cross_section) - 1):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + j + 1) )
		edges.append((vertices_chunk_start + len(cross_section) - 1, vertices_chunk_start))
		
		# if first slice, fill in left hand face.
		if i == 0:
			for j in range(len(cross_section) - 2):
				faces.append( (vertices_chunk_start, vertices_chunk_start + j + 1, vertices_chunk_start + j + 2) )
		
		vertices_chunk_start = len(vertices)
		
		# Right face of chunk
		for v in cross_section:
			vertices.append( (x + dx, fy(x + dx)*v[0], fz(x + dx)*v[1]) )
			
		for j in range(len(cross_section) - 1):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + j + 1) )
		edges.append((vertices_chunk_start + len(cross_section) - 1, vertices_chunk_start))

		# If last slice, fill in the right hand face.
		if i == num_slices - 1:
			for j in range(len(cross_section) - 2):
				faces.append( (vertices_chunk_start, vertices_chunk_start + j + 1, vertices_chunk_start + j + 2) )
		
		# move back to where vertices of this chunk start...
		vertices_chunk_start = len(vertices) - 2*len(cross_section)
		
		# Edge of chunk
		for j in range(len(cross_section)):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + len(cross_section) + j) )
			
		for j in range(len(cross_section) - 1):
			faces.append( (vertices_chunk_start + j,
				vertices_chunk_start + j + 1,
				vertices_chunk_start + len(cross_section) + j + 1,
				vertices_chunk_start + len(cross_section) + j) )
		faces.append( (vertices_chunk_start + len(cross_section) - 1,
			vertices_chunk_start,
			vertices_chunk_start + len(cross_section),
			vertices_chunk_start + 2*len(cross_section) - 1) )
			
		vertices_chunk_start = len(vertices)
	
	me = bpy.data.meshes.new("SmoothMesh")
	ob = bpy.data.objects.new("Smooth", me)
	ob.location = (0,0,0)
	ob.show_name = True
	bpy.context.scene.objects.link(ob)
	me.from_pydata(vertices, edges, faces)
	me.update(calc_edges = True)

# Generates a chunky object built out of "washers" as in a Riemann-sum.
def create_washer_sliced_model(a, b, num_slices, R, r, cross_section):
	vertices = []
	edges = []
	faces = []
	vertices_chunk_start = 0
	
	dx = float(b-a)/num_slices
	
	for i in range(num_slices):
		x = a + dx*i
		
		# Left face of chunk, outer edge
		for v in cross_section:
			vertices.append( (x, R(x + 0.5*dx)*v[0], R(x + 0.5*dx)*v[1]) )
			
		for j in range(len(cross_section) - 1):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + j + 1) )
		edges.append((vertices_chunk_start + len(cross_section) - 1, vertices_chunk_start))
		
		# Left face of chunk, inner edge
		for v in cross_section:
			vertices.append( (x, r(x + 0.5*dx)*v[0], r(x + 0.5*dx)*v[1]) )
			
		for j in range(len(cross_section) - 1):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + j + 1) )
		edges.append((vertices_chunk_start + len(cross_section) - 1, vertices_chunk_start))
		
		for j in range(len(cross_section) - 1):
			faces.append( (vertices_chunk_start + j,
				vertices_chunk_start + j + 1,
				vertices_chunk_start + len(cross_section) + j + 1,
				vertices_chunk_start + len(cross_section) + j) )
		faces.append( (vertices_chunk_start + len(cross_section) - 1,
			vertices_chunk_start,
			vertices_chunk_start + len(cross_section),
			vertices_chunk_start + 2*len(cross_section) - 1) )
		
		vertices_chunk_start = len(vertices)
		
		# Right face of chunk
		for v in cross_section:
			vertices.append( (x + dx, R(x + 0.5*dx)*v[0], R(x + 0.5*dx)*v[1]) )
			
		for j in range(len(cross_section) - 1):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + j + 1) )
		edges.append((vertices_chunk_start + len(cross_section) - 1, vertices_chunk_start))
		
		# Right face of chunk, inner edge
		for v in cross_section:
			vertices.append( (x + dx, r(x + 0.5*dx)*v[0], r(x + 0.5*dx)*v[1]) )
			
		for j in range(len(cross_section) - 1):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + j + 1) )
		edges.append((vertices_chunk_start + len(cross_section) - 1, vertices_chunk_start))
		
		for j in range(len(cross_section) - 1):
			faces.append( (vertices_chunk_start + j,
				vertices_chunk_start + j + 1,
				vertices_chunk_start + len(cross_section) + j + 1,
				vertices_chunk_start + len(cross_section) + j) )
		faces.append( (vertices_chunk_start + len(cross_section) - 1,
			vertices_chunk_start,
			vertices_chunk_start + len(cross_section),
			vertices_chunk_start + 2*len(cross_section) - 1) )
		
		# move back to where vertices of this chunk start...
		vertices_chunk_start = len(vertices) - 4*len(cross_section)
		
		# Edge of chunk
		for j in range(len(cross_section)):
			edges.append( (vertices_chunk_start + j, vertices_chunk_start + 2*len(cross_section) + j) )
			
		for j in range(len(cross_section) - 1):
			faces.append( (vertices_chunk_start + j,
				vertices_chunk_start + j + 1,
				vertices_chunk_start + 2*len(cross_section) + j + 1,
				vertices_chunk_start + 2*len(cross_section) + j) )
			faces.append( (vertices_chunk_start + len(cross_section) + j,
				vertices_chunk_start + len(cross_section) + j + 1,
				vertices_chunk_start + 3*len(cross_section) + j + 1,
				vertices_chunk_start + 3*len(cross_section) + j) )
		faces.append( (vertices_chunk_start + len(cross_section) - 1,
			vertices_chunk_start,
			vertices_chunk_start + 2*len(cross_section),
			vertices_chunk_start + 3*len(cross_section) - 1) )
		faces.append( (vertices_chunk_start + 2*len(cross_section) - 1,
			vertices_chunk_start + len(cross_section),
			vertices_chunk_start + 3*len(cross_section),
			vertices_chunk_start + 4*len(cross_section) - 1) )
			
		vertices_chunk_start = len(vertices)
		
	
	me = bpy.data.meshes.new("SliceyMesh")
	ob = bpy.data.objects.new("Slicey", me)
	ob.location = (0,0,0)
	ob.show_name = True
	bpy.context.scene.objects.link(ob)
	me.from_pydata(vertices, edges, faces)
	me.update(calc_edges = True)

# Generates sliced model as above, but cut into separate Blender objects at the array of x-values "split".
def split_sliced_model(a, b, num_slices, f, cross_section, split):
    split = [a]+split
    split.append(b)
    for i in range(len(split)-1):
        a_new = split[i]
        b_new = split[i+1]
        create_sliced_model(a_new, b_new, num_slices,f, cross_section)

# --------------------------------------------------------------------------------------------		
		
# Some example uses of the functions from above. This is probably the only part you want to edit.
	
##### base: circle; cross sections: square #####
create_sliced_model(-1, 1, 13, lambda x: sqrt(1-x*x),lambda x: sqrt(1-x*x), square_centered_at_bottom)
#split_sliced_model(-1, 1, 13, lambda x: sqrt(1-x*x), lambda x: sqrt(1-x*x),square_centered_at_bottom,[0])
#create_smooth_model(-1, 1, 100, lambda x: sqrt(1-x*x), lambda x: sqrt(1-x*x), square_centered_at_bottom)

##### base: circle; cross sections: equilateral triangle #####
#create_sliced_model(-1, 1, 13, lambda x: sqrt(1-x*x),lambda x: sqrt(1-x*x), eqtriangle_centered_at_bottom)
#create_smooth_model(-1, 1, 100, lambda x: sqrt(1-x*x),lambda x: sqrt(1-x*x), eqtriangle_centered_at_bottom)

##### base: parabola; cross sections: square #####
##### rescale by .7
#create_sliced_model(0, 2, 13, lambda x: sqrt(x),lambda x: sqrt(x), square_centered_at_bottom)
#create_smooth_model(0, 2, 100, lambda x: sqrt(x),lambda x: sqrt(x), square_centered_at_bottom)


##### base: parabola; cross sections: right triangle #####
##### rescale by .7
#create_sliced_model(0, 2, 13, lambda x: sqrt(x),lambda x: sqrt(x), rttriangle_centered_at_bottom)
#create_smooth_model(0, 2, 100, lambda x: sqrt(x),lambda x: sqrt(x), rttriangle_centered_at_bottom)


##### base: square; cross sections: rectangles height -x^2+1 #####
#create_sliced_model(-1,1, 13, lambda x: 1, lambda x: -x*x+1, square_centered_at_bottom)
#create_smooth_model(-1,1, 100, lambda x: 1, lambda x: -x*x+1, square_centered_at_bottom)
