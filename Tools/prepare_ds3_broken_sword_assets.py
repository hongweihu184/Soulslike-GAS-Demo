import unreal,json
from pathlib import Path
assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
AI='/Game/Gameplay/AI/DS3BrokenSword/'
tools=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.EditorAssetLibrary
def asset(name,cls,factory):
 obj=unreal.load_asset(AI+name)
 return obj or tools.create_asset(name,AI.rstrip('/'),cls,factory)
bb=asset('BB_DS3BrokenSword',unreal.BlackboardData,unreal.BlackboardDataFactory())
fields={'TargetActor':'Object','Initialized':'Bool','ThinkParamID':'Int','TeamRole':'Int','EventRequest1':'Int','Action':'Int','ForcedAction':'Int','AfterAction':'Int','ThirdHit':'Bool','Last3003Time':'Float','RadiusCm':'Float','UnitScale':'Float','RunSpeed':'Float','ApproachRadius':'Float','ApproachLife':'Float','MoveDuration':'Float','MoveDistance':'Float','SideDirection':'Float','PostAllowed':'Bool','DecisionCount':'Int','AttackID':'Int'}
keys=list(bb.get_editor_property('keys'))
for name,typ in fields.items():
 if not any(str(k.get_editor_property('entry_name'))==name for k in keys):
  key=unreal.BlackboardEntry();key.set_editor_property('entry_name',name);key.set_editor_property('key_type',unreal.new_object(unreal.load_class(None,'/Script/AIModule.BlackboardKeyType_'+typ),outer=bb));keys.append(key)
bb.set_editor_property('keys',keys);lib.save_loaded_asset(bb,False)
bt=asset('BT_DS3BrokenSword',unreal.BehaviorTree,unreal.BehaviorTreeFactory());bt.set_editor_property('blackboard_asset',bb);lib.save_loaded_asset(bt,False)
names=['BTT_DSInit','BTT_DSDecide','BTT_DSLocomotion','BTT_DSAttack','BTT_DSRelativeMove','BTT_DSAfterAttack','BTT_DSComboChoice']
assets=[bb,bt]
for name in names:
 obj=unreal.load_asset(AI+name)
 if not obj:
  factory=unreal.BlueprintFactory();factory.set_editor_property('parent_class',unreal.BTTask_BlueprintBase);obj=tools.create_asset(name,AI.rstrip('/'),unreal.Blueprint,factory)
 assets.append(obj)
dummy=unreal.load_asset('/Game/Gameplay/Characters/BP_Dummy')
try:unreal.get_default_object(dummy.generated_class()).get_editor_property('DS3AttackMontage')
except:
 assert unreal.BlueprintEditorLibrary.add_member_variable(dummy,'DS3AttackMontage',unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.AnimMontage.static_class()))
 unreal.BlueprintEditorLibrary.compile_blueprint(dummy);lib.save_loaded_asset(dummy,False)
ga=unreal.load_asset('/Game/Gameplay/GAS/Abilities/GA_DS3BrokenSwordAttack') or lib.duplicate_asset('/Game/Gameplay/GAS/Abilities/GA_EnemyAttack','/Game/Gameplay/GAS/Abilities/GA_DS3BrokenSwordAttack')
assets += [ga,dummy]
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets(assets)
m=unreal.load_asset('/Game/Gameplay/Anims/Enemy/AM_EnemyAttack')
report={'montage':[x.export_text() for x in m.get_editor_property('slot_anim_tracks')],'methods':[x for x in dir(unreal.AnimationLibrary) if any(t in x.lower() for t in ['montage','notify','track'])],'skeleton':str(m.get_editor_property('skeleton'))}
Path('E:/UE5.8Project/ProjectUnreal/Saved/DS3-MontageProbe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('DS3_ASSETS_CREATED',len(assets))
