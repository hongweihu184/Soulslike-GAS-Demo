"""Generate grounded root motion from the retargeted pelvis, then rebake."""
import unreal
from pathlib import Path

base='/Game/Gameplay/Anims/Roll'
rtg=unreal.load_asset(base+'/RTG_Mixamo_Greystone_Roll')
ctrl=unreal.IKRetargeterController.get_controller(rtg)
root_ctrl=ctrl.get_op_controller(3)
assert isinstance(root_ctrl,unreal.IKRetargetRootMotionController)
root_ctrl.set_source_root_bone('Hips')
root_ctrl.set_target_root_bone('root')
root_ctrl.set_target_pelvis_bone('pelvis')
settings=root_ctrl.get_settings()
settings.root_motion_source=unreal.RootMotionSource.GENERATE_FROM_TARGET_PELVIS
settings.root_height_source=unreal.RootMotionHeightSource.SNAP_TO_GROUND
settings.rotate_with_pelvis=False
settings.maintain_offset_from_pelvis=False
root_ctrl.set_settings(settings)
source=unreal.load_asset(base+'/Source/SK_MixamoRollPreview')
target=unreal.load_asset('/Game/ParagonGreystone/Characters/Heroes/Greystone/Meshes/Greystone')
anim=unreal.load_asset(base+'/Source/AS_Mixamo_StandToRoll')
inputs=unreal.IKRetargetBatchOperationInputs()
inputs.assets_to_retarget=[unreal.EditorAssetLibrary.find_asset_data(anim.get_path_name())]
inputs.source_mesh=source
inputs.target_mesh=target
inputs.ik_retarget_asset=rtg
inputs.target_path=base
inputs.search='AS_Mixamo_StandToRoll'
inputs.replace='AS_Greystone_StandToRoll'
inputs.overwrite_existing_files=True
assert unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
output=unreal.load_asset(base+'/AS_Greystone_StandToRoll')
output.set_editor_property('enable_root_motion',True)
unreal.EditorAssetLibrary.save_directory(base,False,True)
exec((Path(__file__).parent/'verify_roll_retarget.py').read_text(encoding='utf8'))
unreal.log('[RollVerify] Grounded root motion baked and verified')
