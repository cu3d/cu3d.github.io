# Blender python code for generating a paraboloid and approximations of it by disks and washers.
# Author: Athena Sparks
#
# To run, open a Text Editor view in Blender, open this file, then press the "Run Script" button.


import bpy
import mathutils
from math import *
import os


#### xy coordinates for point around a circle #### 
circle_xy_vertices = []
circle_num_points = 100
for i in range(circle_num_points):
    theta = i*2*3.1415926535/circle_num_points
    circle_xy_vertices.append( ( sin(theta), cos(theta) ) )

#### magnet dimensions ####
mag_depth =  float(4/15)+float(2/15) # depth is 4 mm plus 2mm for clearance
mag_width = float(10/15)+float(1.5/15) # diam)eter is 10 mm plus 1.5mm for clearance
mag_radius = mag_width/2

#### magnet shape with open bottom ####
def magnet_shape_open(name):
    vertices =[]
    faces = []
    l = len(circle_xy_vertices)
    # bottom vertices
    for v in circle_xy_vertices:
        vertices.append((mag_radius*v[0],mag_radius*v[1],-mag_depth/2))
    # top vertices
    for v in circle_xy_vertices:
        vertices.append((mag_radius*v[0],mag_radius*v[1],mag_depth/2))
    # top faces
    for i in range(l-2):
        faces.append((l,i+l+1,i+l+2))
    # side faces
    for i in range(l-1):
       faces.append((i,i+1,i+1+l,i+l))
    faces.append((l-1,0,l,2*l-1))

    me = bpy.data.meshes.new("MagnetMesh")
    ob = bpy.data.objects.new(name, me)
    ob.show_name = True
    bpy.context.scene.objects.link(ob)
    me.from_pydata(vertices, [], faces)
    me.update(calc_edges = True)


#### Disk model ####
def create_disk_model(a,b,num_slices, R, magnet=False):
    dz = float(b-a)/num_slices
    # simple disk
    bpy.ops.mesh.primitive_cylinder_add(radius= 1, depth= 1, vertices = 100)
    cyl = bpy.context.scene.objects.active
    mesh = cyl.data
    cyl.name = 'Cylinder'
    for i in range(num_slices):
        # heights
        z_mid = dz*i
        z_bot = dz*i+dz/2
        z_mag = z_mid+mag_depth/2.
        # create piece
        disk = cyl.copy() 
        disk.data = mesh.copy()
        disk.scale = (R(z_mid),R(z_mid),dz)
        disk.location = (0,0,z_bot)
        bpy.context.scene.objects.link(disk)
        disk.name = "Disk"
        disk.show_name = True
        if magnet:
            # Hole for magnet
            mag = cyl.copy()
            mag.data = mesh.copy()
            mag.scale = (mag_radius,mag_radius,mag_depth/2.)
            mag.location = (0,0,z_mag)
            bpy.context.scene.objects.link(mag)
            mag.name = 'Mag'
            bpy.context.scene.objects.active = disk
            # Create a boolean modifier named 'magnet_mod' for the sliced object.
            mod_bool = disk.modifiers.new('magnet_mod', 'BOOLEAN')
            # Set the mode of the modifier to DIFFERENCE.
            mod_bool.operation = 'DIFFERENCE'
            # Set the object to be used by the modifier.
            mod_bool.object = mag
            # Apply the modifier.
            res = bpy.ops.object.modifier_apply(modifier = 'magnet_mod')

    #Delete all magnets and simple cylinders
    bpy.ops.object.select_all(action='DESELECT')
    scene = bpy.context.scene
    for ob in scene.objects:
        if ob.name.startswith("Mag"):
            ob.select = True
        elif ob.name.startswith("Cyl"):
            ob.select = True
        else: 
            ob.select = False
    bpy.ops.object.delete()
        
#### Shell Model ####
def create_shell_model(a, b, num_shells, R, r=lambda x: 0, magnet=False):
    dx = float(b-a)/num_shells
    for i in range(num_shells):
        vertices = []
        faces = []
        in_x  = (a+dx*i)+1/30.#/5mm of clearance
        if in_x==1/30.:
            in_x = 0
        mid_x = a + dx/2 + dx*i
        out_x = a + dx*(i+1)

        # top inside vertices
        for v in circle_xy_vertices:
            vertices.append( (in_x*v[0], in_x*v[1], R(mid_x) ))
        # top outside vertices
        for v in circle_xy_vertices:
            vertices.append( (out_x*v[0], out_x*v[1], R(mid_x) ))
        # bottom inside vertices
        if i==0 and magnet:
            shell_radius = out_x
            for v in circle_xy_vertices:
                vertices.append( (in_x*v[0], in_x*v[1], r(mid_x)+1.5*mag_depth ))
        else:
            for v in circle_xy_vertices:
                vertices.append( (in_x*v[0], in_x*v[1], r(mid_x) ))
        # bottom outside vertices
        if i==0 and magnet:
            for v in circle_xy_vertices:
                vertices.append( (out_x*v[0], out_x*v[1], r(mid_x)+1.5*mag_depth ))
        else:
            for v in circle_xy_vertices:
                vertices.append( (out_x*v[0], out_x*v[1], r(mid_x) ))
            
        len_circle = len(circle_xy_vertices)
        len_verts = len(vertices)
    
        # top rim face
        for i in range(len_circle-1):
            faces.append( (i,i+1,i+len_circle+1,i+len_circle))
        faces.append((len_circle-1,0,len_circle,2*len_circle-1))
        
        # bottom rim face
        for i in range(len_circle-1):
            faces.append( (i+2*len_circle,i+1+2*len_circle,i+3*len_circle+1,i+3*len_circle))
        faces.append((3*len_circle-1,2*len_circle,3*len_circle,4*len_circle-1))
        
        # inside side face
        for i in range(len_circle-1):
            faces.append((i, i+1, i+1+2*len_circle, i+2*len_circle))
        faces.append((len_circle-1, 0, 2*len_circle,3*len_circle-1))
        
        # outside side face
        for i in range(len_circle-1):
            faces.append((i+len_circle, i+1+len_circle, i+1+3*len_circle, i+3*len_circle))
        faces.append((2*len_circle-1, len_circle, 3*len_circle,4*len_circle-1))

        # create shell
        me = bpy.data.meshes.new("ShellMesh")
        ob = bpy.data.objects.new("Shell", me)
        ob.show_name = True
        bpy.context.scene.objects.link(ob)
        me.from_pydata(vertices, [], faces)
        me.update(calc_edges = True)

    # add magnet to center shell
    if magnet:
        # simple cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius= 1, depth= 1, vertices = 100)
        cyl = bpy.context.scene.objects.active
        mesh = cyl.data
        cyl.name = 'Cylinder'
        # piece of shell for magnet
        mag_shell = cyl.copy()
        mag_shell.data = mesh.copy()
        mag_shell.scale = (shell_radius,shell_radius,mag_depth/2.)
        mag_shell.location = (0,0,mag_depth)
        bpy.context.scene.objects.link(mag_shell)
        mag_shell.name = 'Mag_Shell'
        # bottom piece of shell
        mag_bottom = cyl.copy()
        mag_bottom.data = mesh.copy()
        mag_bottom.scale = (shell_radius,shell_radius,mag_depth/2.)
        mag_bottom.location = (0,0,mag_depth/2)
        bpy.context.scene.objects.link(mag_bottom)
        mag_bottom.name = 'Mag_Bottom'
        # magnet hole
        mag = cyl.copy()
        mag.data = mesh.copy()
        mag.scale = (mag_radius,mag_radius,mag_depth)
        mag.location = (0,0,mag_depth)
        bpy.context.scene.objects.link(mag)
        mag.name = 'Mag'
        bpy.context.scene.objects.active = mag_shell
        # Create a boolean modifier named 'magnet_mod' for the sliced object.
        mod_bool = mag_shell.modifiers.new('magnet_mod', 'BOOLEAN')
        # Set the mode of the modifier to DIFFERENCE.
        mod_bool.operation = 'DIFFERENCE'
        # Set the object to be used by the modifier.
        mod_bool.object = mag
        # Apply the modifier.
        res = bpy.ops.object.modifier_apply(modifier = 'magnet_mod')

        #Delete magnet and simple cylinder
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['Cylinder'].select = True
        bpy.data.objects['Mag'].select = True
        bpy.ops.object.delete()

        # Join center shell pieces
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['Shell'].select = True
        bpy.data.objects['Mag_Shell'].select = True
        bpy.data.objects['Mag_Bottom'].select = True
        bpy.ops.object.join()


   
#### Smooth Model ####
def create_smooth_model(a, b, smoothness, R, r=lambda x: 0, split=False, magnet = False):

    # determine if half or full rotation
    if split:
        rotate_about_z = []
        circle_num_points = 50
        for i in range(circle_num_points):
            theta = i*3.1415926535/(circle_num_points-1)
            rotate_about_z.append( ( sin(theta), cos(theta) ) )
    else:
        rotate_about_z = []
        circle_num_points = 100
        for i in range(circle_num_points-1):
            theta = i*2*3.1415926535/circle_num_points
            rotate_about_z.append( ( sin(theta), cos(theta) ) )

    # mesh arrays
    vertices = []
    faces = []
    dx = float(b-a)/smoothness

    # top vertices
    for i in range(smoothness+1):
        for v in rotate_about_z:
            x = v[0]*(a+dx*i)
            y = v[1]*(a+dx*i)
            z = R(a+dx*i)
            vertices.append((x,y,z))
    # bottom vertices
    for i in range(smoothness+1):
        for v in rotate_about_z:
            x = v[0]*(a+dx*i)
            y = v[1]*(a+dx*i)
            z = r(a+dx*i)
            vertices.append((x,y,z))
            
    # top faces
    l = len(rotate_about_z)
    for i in range(smoothness):
        for j in range(l-1):
            faces.append((j+i*l,(j+1)+i*l,(j+1)+(i+1)*l,j+(i+1)*l))
        if not split:
            faces.append((l-1+i*l,0+i*l,l+i*l,2*l-1+i*l))
    # bottom faces
    k = (smoothness+1)*l
    for i in range(smoothness):
        for j in range(l-1):
            faces.append((j+i*l+k,(j+1)+i*l+k,(j+1)+(i+1)*l+k,j+(i+1)*l+k))
        if not split:
            faces.append((l-1+i*l+k,0+i*l+k,l+i*l+k,2*l-1+i*l+k))
    # side faces if half rotation
    if split:
        for i in range(smoothness):
            faces.append((i*l, i*l+k,(i+1)*l+k, (i+1)*l))
            faces.append(( i*l+k+l-1,i*l+l-1, (i+1)*l+l-1,(i+1)*l+k+l-1))
 
    #create mesh and object
    me = bpy.data.meshes.new("SmoothMesh")
    smooth = bpy.data.objects.new("Smooth",me)
    smooth.show_name = True
    bpy.context.scene.objects.link(smooth)
    me.from_pydata(vertices,[],faces)
    me.update(calc_edges=True)


    # hole for magnet
    if magnet:
        # simple cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius= 1, depth= 1, vertices = 100)
        cyl = bpy.context.scene.objects.active
        mesh = cyl.data
        cyl.name = 'Cylinder'
        mesh = cyl.data
        cyl.name = 'Cylinder'
        # magnet hole 
        mag = cyl.copy()
        mag.data = mesh.copy()
        mag.scale = (mag_radius,mag_radius,mag_depth)
        if split:
            mag.rotation_euler =(0, 1.5707,0)
            mag.location = (mag_depth/2-.1,0,(R(a)-R(b))/2)
        else:
            mag.location = (0,0,mag_depth/2)
        bpy.context.scene.objects.link(mag)
        mag.name = 'Hole'
        bpy.context.scene.objects.active = smooth
        smooth.select = True
        # Create a boolean modifier named 'magnet_mod' for the sliced object.
        mod_bool = smooth.modifiers.new('magnet_mod', 'BOOLEAN')
        # Set the mode of the modifier to DIFFERENCE.
        mod_bool.operation = 'DIFFERENCE'
        # Set the object to be used by the modifier.
        mod_bool.object = mag
        # Apply the modifier.
        res = bpy.ops.object.modifier_apply(modifier = 'magnet_mod')

        # put open magnet hole in place
        magnet_shape_open("Magnet")
        mag_hole = bpy.data.objects['Magnet']
        if split:
            mag_hole.location = (mag_depth/2,0,(R(a)-R(b))/2)
            mag_hole.rotation_euler =(0, 1.5707,0)
        else:
            mag_hole.location = (0,0,mag_depth/2)

        #Delete all magnets and simple cylinders
        bpy.ops.object.select_all(action='DESELECT')
        scene = bpy.context.scene
        for ob in scene.objects:
            if ob.name.startswith("Hole"):
                ob.select = True
            elif ob.name.startswith("Cyl"):
                ob.select = True
            else: 
                ob.select = False
        bpy.ops.object.delete()
        
        # join objects
        bpy.ops.object.select_all()
        bpy.ops.object.join()


#### Base with poles for smooth/disk/shell method ####
def create_pole_base(l, w, h, num_poles, pole_height=2, pole_radius = .1):
    # vertices
    vertices = [(.5*l, .5*w, 0),
         (.5*l, -.5*w, 0),
        (-.5*l, -.5*w, 0),
        (-.5*l, .5*w, 0),
         (.5*l, .5*w, h),
         (.5*l, -.5*w, h),
        (-.5*l, -.5*w, h),
        (-.5*l, .5*w, h)]
         
    # faces
    faces = [(0, 1, 2, 3),
         (4, 7, 6, 5),
         (0, 4, 5, 1),
         (1, 5, 6, 2),
         (2, 6, 7, 3),
         (4, 0, 3, 7)]

    # create base
    me = bpy.data.meshes.new("BaseMesh")
    ob = bpy.data.objects.new("Base", me)
    ob.location = (0,0,0)
    ob.show_name = True
    bpy.context.scene.objects.link(ob)
    me.from_pydata(vertices, [], faces)
    me.update(calc_edges = True)

    # Create poles.
    dist = l/num_poles
    loc = (-.5*l+dist/2,0, .5*pole_height)
    bpy.ops.mesh.primitive_cylinder_add(location=loc, radius= pole_radius, depth= pole_height, vertices = 100)
    pole = bpy.context.scene.objects.active
    mesh = pole.data
    for i in range(num_poles-1):
        loc = (loc[0]+dist, loc[1],loc[2])
        pole = pole.copy() # copy pole
        pole.data = mesh.copy()
        pole.location = loc
        bpy.context.scene.objects.link(pole) # link it to the scene

#### Base with magnets for smooth/disk/shell method ####
def create_magnet_base(l, w, h, num_mags):
    # vertices
    vertices = [(.5*l, .5*w, 0),
         (.5*l, -.5*w, 0),
        (-.5*l, -.5*w, 0),
        (-.5*l, .5*w, 0),
         (.5*l, .5*w, h),
         (.5*l, -.5*w, h),
        (-.5*l, -.5*w, h),
        (-.5*l, .5*w, h)]
         
    # faces
    faces = [(0, 1, 2, 3),
         (4, 7, 6, 5),
         (0, 4, 5, 1),
         (1, 5, 6, 2),
         (2, 6, 7, 3),
         (4, 0, 3, 7)]

    # create base
    me = bpy.data.meshes.new("BaseMesh")
    base = bpy.data.objects.new("Base", me)
    base.location = (0,0,0)
    base.show_name = True
    bpy.context.scene.objects.link(base)
    me.from_pydata(vertices, [], faces)
    me.update(calc_edges = True)


    # simple disk
    bpy.ops.mesh.primitive_cylinder_add(radius= 1, depth= 1, vertices = 100)
    cyl = bpy.context.scene.objects.active
    mesh = cyl.data
    cyl.name = 'Cylinder'

    # magnet holes
    dist = l/num_mags
    loc = (-.5*l+dist/2, 0, h/2.)
    for i in range(num_mags):
        mag = cyl.copy()
        mag.data = mesh.copy()
        mag.scale = (mag_radius,mag_radius,mag_depth/2) ### changed to half mag_depth
        mag.location = (loc[0]+dist*i, loc[1],loc[2])
        bpy.context.scene.objects.link(mag)
        mag.name = 'Mag'
        bpy.context.scene.objects.active = base
        # Create a boolean modifier named 'magnet_mod' for the sliced object.
        mod_bool = base.modifiers.new('magnet_mod', 'BOOLEAN')
        # Set the mode of the modifier to DIFFERENCE.
        mod_bool.operation = 'DIFFERENCE'
        # Set the object to be used by the modifier.
        mod_bool.object = mag
        # Apply the modifier.
        res = bpy.ops.object.modifier_apply(modifier = 'magnet_mod')
    #Delete all magnets and simple cylinders
    bpy.ops.object.select_all(action='DESELECT')
    scene = bpy.context.scene
    for ob in scene.objects:
        if ob.name.startswith("Mag"):
            ob.select = True
        elif ob.name.startswith("Cyl"):
            ob.select = True
        else: 
            ob.select = False
    bpy.ops.object.delete()

#### Base with depression for smooth/disk/shell method ####
def create_depression_base(x_2, z_2, f_z, num_shells, num_disks):

    # radii for depressions order: smooth, shell, disk
    disk_radius = f_z(z_2/float(num_disks*2))
    shell_radius = x_2 - x_2/float(num_disks*2)
    # add 1.5mm clearance
    radius = x_2 + 1/15.
    radii = [radius, shell_radius + 2/15., disk_radius + 2/15.]
    
    #dimensions for base
    l =(radius*2+20./15)*3 #10 mm clearance
    w = radius*2+20./15
    h = 6./15  # 6mm height
    
    # vertices
    vertices = [(.5*l, .5*w, 0),
         (.5*l, -.5*w, 0),
        (-.5*l, -.5*w, 0),
        (-.5*l, .5*w, 0),
         (.5*l, .5*w, h),
         (.5*l, -.5*w, h),
        (-.5*l, -.5*w, h),
        (-.5*l, .5*w, h)]
         
    # faces
    faces = [(0, 1, 2, 3),
         (4, 7, 6, 5),
         (0, 4, 5, 1),
         (1, 5, 6, 2),
         (2, 6, 7, 3),
         (4, 0, 3, 7)]

    # create base
    me = bpy.data.meshes.new("BaseMesh")
    base = bpy.data.objects.new("Base", me)
    base.location = (0,0,0)
    base.show_name = True
    bpy.context.scene.objects.link(base)
    me.from_pydata(vertices, [], faces)
    me.update(calc_edges = True)

    # create cylinder for depression
    bpy.ops.mesh.primitive_cylinder_add(radius= 1, depth= 1, vertices = 100)
    cyl = bpy.context.scene.objects.active
    mesh = cyl.data
    cyl.name = 'Cylinder'

    # locations for depressions order: smooth, shell,disk
    locs = [(0,0,h-1/15.),((l/3)*(-1),0, h-1/15.),((l/3),0, h-1/15.)]

    # create depressions
    for i in range(3):
        dep = cyl.copy()
        dep.data = mesh.copy()
        dep.scale = (radii[i], radii[i], 2./15)
        dep.location = locs[i]
        bpy.context.scene.objects.link(dep)
        dep.name = 'Dep'
        bpy.context.scene.objects.active = base
        # Create a boolean modifier named 'magnet_mod' for the sliced object.
        mod_bool = base.modifiers.new('magnet_mod', 'BOOLEAN')
        # Set the mode of the modifier to DIFFERENCE.
        mod_bool.operation = 'DIFFERENCE'
        # Set the object to be used by the modifier.
        mod_bool.object = dep
        # Apply the modifier.
        res = bpy.ops.object.modifier_apply(modifier = 'magnet_mod')
    #Delete all magnets and simple cylinders
    bpy.ops.object.select_all(action='DESELECT')
    scene = bpy.context.scene
    for ob in scene.objects:
        if ob.name.startswith("Dep"):
            ob.select = True
        elif ob.name.startswith("Cyl"):
            ob.select = True
        else: 
            ob.select = False
    bpy.ops.object.delete()

    
##### save objects separately ####
def save_pieces(path, name, scale = 15):
    path = bpy.path.abspath(path)
    i = 1
    for ob in bpy.data.objects:
        print(ob.name)

    for ob in bpy.data.objects:
        # deselect all meshes
        bpy.ops.object.select_all(action='DESELECT')
        # select the object
        ob.select = True
        #scale for cura
        bpy.ops.transform.resize(value=(scale,scale,scale))
        # export object with its name as file name
        bpy.ops.export_mesh.stl(filepath=str((path + name + '_%s.stl' %ob.name)),
                                 use_selection=True)
        i += 1
        

#### smooth/disk/shell method sets ####
def create_smooth_disk_shell_set(f_x, x_1, x_2, f_z, z_1, z_2, num_disks = 7, num_shells = 7, smoothness = 50, save=None):
    # smooth model
    create_smooth_model(x_1, x_2, smoothness, f_x, split=False, magnet=False)

    # disk model
    create_disk_model(z_1, z_2, num_disks, f_z, magnet=True)
    
    # shell model
    create_shell_model(x_1, x_2, num_shells, f_x, magnet=False)
    
    # base
    create_depression_base(x_2, z_2, f_z, num_disks, num_shells)
    
    # locations
    radius = x_2 + 1.5/15.
    l =(radius*2+20./15)*3 #10 mm clearance
    
    # translate
    bpy.ops.object.select_all(action='DESELECT')
    scene = bpy.context.scene
    for ob in scene.objects:
        if ob.name.startswith("Shell"):
            loc = ob.location 
            ob.location = (loc[0]+l/3., 0, 0.5)
        elif ob.name.startswith("Disk"):
            loc = ob.location 
            ob.location = (loc[0]-l/3., loc[1], loc[2]+0.5)
        elif ob.name.startswith("Smooth"):
            loc = ob.location 
            ob.location = (0,0, 0.5)
    # save
    if save:
        save_pieces(save[0],save[1])

#create_smooth_disk_shell_set(lambda x: -x*x+3.4, 0, sqrt(3.4), lambda z: sqrt(3.4-z), 0, 3.4, save=('/Users/acsparks/Desktop/SmoothDiskShell_Parabola/', 'Paraboloid_set'))
create_smooth_disk_shell_set(lambda x: -x*x+3.4, 0, sqrt(3.4), lambda z: sqrt(3.4-z), 0, 3.4,)

#create_disk_model(0,3.4,7,  lambda z: sqrt(3.4-z), magnet=True)
#create_pole_base(6, 2, .3, 3)
#create_magnet_base(20/15,20/15, 8/15,1)
#save_pieces('/Users/acsparks/Desktop/', 'magnet_base')

#create_shell_model(0, sqrt(2), 5, lambda x: -x*x+2, magnet=True)
#save_pieces('/Users/acsparks/Desktop/', 'paraboloid_shells')

#create_disk_model(0,3.4,7, lambda z: sqrt(3.4-z,magnet=True)
#save_pieces('/Users/acsparks/Desktop/', 'paraboloid_disks')

## split with magnet not working
#create_smooth_model(0, sqrt(2), 10, lambda x: -x*x+2, split=True, magnet=True)
