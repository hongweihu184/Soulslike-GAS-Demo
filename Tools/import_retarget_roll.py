"""Import an isolated Mixamo source and bake a Greystone roll with UE 5.8."""
import unreal
from pathlib import Path
import traceback

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/RollImport/result.txt'
lines=[]
def log(value):
    lines.append(str(value)); OUT.write_text('\n'.join(lines),encoding='utf8'); unreal.log('[RollImport] '+str(value))

try:
    unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    ui=unreal.FbxImportUI()
    ui.set_editor_property('automated_import_should_detect_type',False)
    ui.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property('import_as_skeletal',True)
    ui.set_editor_property('import_mesh',True)
    ui.set_editor_property('import_animations',True)
    ui.set_editor_property('import_materials',False)
    ui.set_editor_property('import_textures',False)
    ui.set_editor_property('create_physics_asset',False)
    task=unreal.AssetImportTask()
    task.filename=str(ROOT/'Saved/RollImport/StandToRoll_SourcePreview.fbx')
    task.destination_path='/Game/Gameplay/Anims/Roll/Source'
    task.destination_name='SK_MixamoRollPreview'
    task.automated=True
    task.replace_existing=True
    task.save=True
    task.options=ui
    task.factory=unreal.FbxFactory()
    tools.import_asset_tasks([task])
    log('Imported: '+str(task.imported_object_paths))
    unreal.EditorAssetLibrary.save_directory('/Game/Gameplay/Anims/Roll',False,True)
    source=unreal.load_asset('/Game/Gameplay/Anims/Roll/Source/SK_MixamoRollPreview')
    target=unreal.load_asset('/Game/ParagonGreystone/Characters/Heroes/Greystone/Meshes/Greystone')
    assert source and target
    aui=unreal.FbxImportUI()
    aui.automated_import_should_detect_type=False
    aui.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION
    aui.import_mesh=False
    aui.import_animations=True
    aui.skeleton=source.skeleton
    atask=unreal.AssetImportTask()
    atask.filename=r'C:\Users\10645\Downloads\Stand To Roll.fbx'
    atask.destination_path='/Game/Gameplay/Anims/Roll/Source'
    atask.destination_name='AS_Mixamo_StandToRoll'
    atask.automated=True
    atask.save=True
    atask.replace_existing=True
    atask.options=aui
    atask.factory=unreal.FbxFactory()
    tools.import_asset_tasks([atask])
    log('Animation imported: '+str(atask.imported_object_paths))
    anim=unreal.load_asset('/Game/Gameplay/Anims/Roll/Source/AS_Mixamo_StandToRoll')
    assert source and target and anim
    def create(name,cls,factory):
        path='/Game/Gameplay/Anims/Roll/'+name
        return unreal.load_asset(path) or tools.create_asset(name,'/Game/Gameplay/Anims/Roll',cls,factory)
    rigs=[]
    for name,mesh in [('IK_MixamoRoll',source),('IK_GreystoneRoll',target)]:
        rig=create(name,unreal.IKRigDefinition,unreal.IKRigDefinitionFactory())
        ctrl=unreal.IKRigController.get_controller(rig)
        assert ctrl.set_skeletal_mesh(mesh)
        log(name+' auto definition: '+str(ctrl.apply_auto_generated_retarget_definition()))
        log(name+' pelvis: '+str(ctrl.get_retarget_root()))
        log(name+' chains: '+str(ctrl.get_retarget_chains()))
        rigs.append(rig)
    rtg=create('RTG_Mixamo_Greystone_Roll',unreal.IKRetargeter,unreal.IKRetargetFactory())
    ctrl=unreal.IKRetargeterController.get_controller(rtg)
    ctrl.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE,rigs[0])
    ctrl.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET,rigs[1])
    ctrl.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE,source)
    ctrl.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET,target)
    ctrl.remove_all_ops()
    ctrl.add_default_ops()
    ctrl.auto_map_chains(unreal.AutoMapChainType.FUZZY,True)
    ctrl.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
    log('Retarget operations: '+str(ctrl.get_num_retarget_ops()))
    inputs=unreal.IKRetargetBatchOperationInputs()
    inputs.assets_to_retarget=[unreal.EditorAssetLibrary.find_asset_data(anim.get_path_name())]
    inputs.source_mesh=source
    inputs.target_mesh=target
    inputs.ik_retarget_asset=rtg
    inputs.target_path='/Game/Gameplay/Anims/Roll'
    inputs.search='AS_Mixamo_StandToRoll'
    inputs.replace='AS_Greystone_StandToRoll'
    inputs.overwrite_existing_files=True
    result=unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
    log('Retarget result: '+str(result))
    unreal.EditorAssetLibrary.save_directory('/Game/Gameplay/Anims/Roll',False,True)
    output=unreal.load_asset('/Game/Gameplay/Anims/Roll/AS_Greystone_StandToRoll')
    assert output
    log('Output duration: '+str(output.sequence_length))
    log('RETARGET_COMPLETE')
except Exception:
    log(traceback.format_exc())
