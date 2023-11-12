import bpy
import mathutils

def Prefixed(a,b):
    return a+b

def exportModelCfg(context, obj, exportBone, selectionName, animSource, prefixString, outputFile):
   
    with open(outputFile, "w") as file:
        scene = context.scene;

        # TODO: Find the lowest and highest keyframe and only export these

        startFrame = scene.frame_start
        endFrame = scene.frame_end
        numFrames = endFrame - startFrame + 1

        baseClassString = f"{prefixString}_{selectionName}_{animSource}_base"

        file.write(f"#define {prefixString}_FrameNr(f) (f/{numFrames})\n")
        file.write(f"class {baseClassString}" + " \n{\n")
        file.write("""
    type="direct";
    axisPos[] = {0,0,0};
    axisDir[] = {0,0,0};
    axisOffset = 0;
    angle = 0;
""")
        file.write(f"    source={animSource}" + ";\n")
        file.write(f"    selection={selectionName}" + ";\n")
        file.write("};\n\n")

        # Apparently it won't work if both rotation and translation are combined
        #file.write(f"#define {prefixString}_{selectionName}_{animSource}_pos(obj,frame,)

        # Get the original bone position
        scene.frame_set(-1)
        poseBone = obj.pose.bones[exportBone]
        start_location = mathutils.Vector(poseBone.location)

        for frameNr in range(startFrame, endFrame):
            scene.frame_set(frameNr)

            location = poseBone.location

            vec = mathutils.Vector( (location.x - start_location.x, location.y - start_location.y, location.z - start_location.z))
            offset = vec.length
            if offset == 0:
                vec = mathutils.Vector((0,1,0))
            vec = vec.normalized();
            axis_pos = start_location
            axis_dir = vec #[vec.x, vec.y, vec.z]
            
            #print ( f"Frame {frameNr} : axis_pos = {axis_pos}, axis_dir = {axis_dir}, offset={offset}")

            # Translation
            # TODO: Why do I have to swizzle the position but not the direction? Doesn't seem to make
            # must sense to me
            file.write("TRANSFORM_TRANSLATION(")
            file.write(f"{selectionName},{frameNr},{offset},{axis_pos.x},{axis_pos.z},{axis_pos.y},{axis_dir.x},{axis_dir.y},{axis_dir.z})" + "\n")

            start_location = mathutils.Vector(poseBone.location)


        # Rotation needs to be handled differently
        # Make sure only the export bone is selected
        for bone in obj.data.bones:
            if bone.name == exportBone:
                bone.select = True
            else:
                bone.select = False
        
        scene.frame_set(-100)
        poseBone = obj.pose.bones[exportBone]

        # Jump to first keyframe
        if 'CANCELLED' == bpy.ops.screen.keyframe_jump(next=True):
           return

        safe = 0
        while scene.frame_current <= scene.frame_end:
            safe = safe + 1 
            if safe > 50:
                return
            segment_start_frame = scene.frame_current
            # Mext Keyframe?
            if 'CANCELLED' == bpy.ops.screen.keyframe_jump(next=True):
                return
            
            segment_end_frame = scene.frame_current

            scene.frame_set(segment_start_frame)
            rotation_current = poseBone.rotation_quaternion
            axis,current_angle = rotation_current.to_axis_angle()

            print (f"output from {segment_start_frame} to {segment_end_frame}")
            for frameNr in range(segment_start_frame, segment_end_frame):
                scene.frame_set(frameNr)
                # Rotation
                rotation_current = poseBone.rotation_quaternion
                axis,angle = rotation_current.to_axis_angle()

                angle_delta = angle - current_angle
                axis_pos = poseBone.location


                print ( f"Frame {frameNr} : rotation axis/angle {axis},{angle} length {axis.length}")
                file.write("TRANSFORM_ROTATION(")
                file.write(f"{selectionName},{frameNr},{angle_delta},{axis_pos.x},{axis_pos.z},{axis_pos.y},{axis.x},{axis.y},{axis.z})" + "\n")

                current_angle = angle
            
            scene.frame_set(segment_end_frame)
    return