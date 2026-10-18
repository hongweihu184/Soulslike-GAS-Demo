import unreal,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
results={}
for label,path,meshpath,bones in [
    ('source','/Game/Gameplay/Anims/Roll/Source/AS_Mixamo_StandToRoll','/Game/Gameplay/Anims/Roll/Source/SK_MixamoRollPreview',['Hips','Head','LeftHand','RightHand','LeftFoot','RightFoot']),
    ('greystone','/Game/Gameplay/Anims/Roll/AS_Greystone_StandToRoll','/Game/ParagonGreystone/Characters/Heroes/Greystone/Meshes/Greystone',['root','pelvis','head','hand_l','hand_r','foot_l','foot_r'])]:
    anim=unreal.load_asset(path)
    options=unreal.AnimPoseEvaluationOptions()
    options.optional_skeletal_mesh=unreal.load_asset(meshpath)
    frames=[]
    for i in range(9):
        time=anim.sequence_length*i/8
        pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(anim,time,options)
        frame={'time':time,'bones':{}}
        for bone in bones:
            t=unreal.AnimPoseExtensions.get_bone_pose(pose,bone,unreal.AnimPoseSpaces.WORLD)
            p=t.translation
            frame['bones'][bone]=[p.x,p.y,p.z]
            assert all(math.isfinite(v) and abs(v)<10000 for v in [p.x,p.y,p.z])
        frames.append(frame)
    results[label]={'duration':anim.sequence_length,'skeleton':anim.get_editor_property('skeleton').get_path_name(),'frames':frames,'root_motion_enabled':anim.get_editor_property('enable_root_motion')}
(root/'Saved/RollImport/poses.json').write_text(json.dumps(results,indent=2),encoding='utf8')
unreal.log('[RollVerify] Pose sampling complete')
