"""Create the new unbound, editable tree and proxy montages. Never rebuild a bound tree."""
import unreal,sys,ctypes,re,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from ds3_blueprint_graph import selector,pin,link,val,castout,AI
assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
lib=unreal.EditorAssetLibrary
bt=unreal.load_asset(AI+'BT_DS3BrokenSword');bb=unreal.load_asset(AI+'BB_DS3BrokenSword')
controller=unreal.load_asset('/Game/Gameplay/AI/BP_EnemyAIController');cg=unreal.BlueprintEditorLibrary.find_event_graph(controller)
run=unreal.find_object(None,cg.get_path_name()+'.K2Node_CallFunction_1')
assert pin(run,'BTAsset').get_pin_value()!=bt.get_path_name(),'Tree is already bound; do not regenerate live graph.'

# Existing licensed same-skeleton animations stand in for source attack IDs.
mapping={3000:'Attack_A_Dusk',3001:'Attack_B_Dusk',3002:'Attack_C_Dusk',3003:'Attack_D_Dusk',3007:'Attack_F_Dusk',20005:'Attack_E_Dusk',20006:'Attack_G_Dusk'}
montages={};report=[]
for aid,animation in mapping.items():
 path='/Game/Gameplay/Anims/Enemy/DS3BrokenSword/AM_DSBrokenSword_'+str(aid)
 a=unreal.load_asset('/Game/ParagonMinions/Characters/Minions/Down_Minions/Animations/Super/'+animation);duration=a.get_play_length()
 m=unreal.load_asset(path)
 if not m:
  factory=unreal.AnimMontageFactory();factory.set_editor_property('source_animation',a);factory.set_editor_property('target_skeleton',a.get_editor_property('skeleton'))
  m=unreal.AssetToolsHelpers.get_asset_tools().create_asset(path.split('/')[-1],path.rsplit('/',1)[0],unreal.AnimMontage,factory)
  unreal.AnimationLibrary.add_animation_notify_track(m,'Combat')
  damage=unreal.load_class(None,'/Game/Gameplay/Notify/ANS/ANS_ConfiguredDamageWindow.ANS_ConfiguredDamageWindow_C')
  hit=unreal.AnimationLibrary.add_animation_notify_state_event(m,'Combat',duration*.3/1.1,duration*.35/1.1,damage);hit.set_editor_property('DamageID','30001')
  lung=unreal.load_class(None,'/Game/Gameplay/Notify/ANS/ANS_AttackLungeWindow.ANS_AttackLungeWindow_C')
  advance=unreal.AnimationLibrary.add_animation_notify_state_event(m,'Combat',.1,min(.25,duration-.11),lung);advance.set_editor_property('LungeSpeed',2100.0 if aid==3007 else 220.0)
 assert abs(m.get_play_length()-duration)<.001
 lib.save_loaded_asset(m,False);montages[aid]=m;report.append({'id':aid,'proxy':a.get_path_name(),'length':duration,'lunge_speed':2100 if aid==3007 else 220})
Path('E:/UE5.8Project/ProjectUnreal/Saved/DS3-AttackMapping.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

ga=unreal.load_asset('/Game/Gameplay/GAS/Abilities/GA_DS3BrokenSwordAttack');gg=unreal.BlueprintEditorLibrary.find_event_graph(ga);ed=unreal.BlueprintGraphEditor.get_graph_editor(gg)
play=unreal.find_object(None,gg.get_path_name()+'.K2Node_LatentAbilityCall_0');cast=unreal.find_object(None,gg.get_path_name()+'.K2Node_DynamicCast_0')
for old in [n for n in ed.list_all_nodes() if n.get_name().startswith('K2Node_VariableGet')]:
 # Only this new copied GA is edited; retry removes our former montage getter.
 if any(str(p.get_pin_name())=='DS3AttackMontage' for p in old.list_all_pins()):ed.remove_nodes([old])
getter=ed.add_get_member_variable_node('DS3AttackMontage','/Game/Gameplay/Characters/BP_Dummy.BP_Dummy_C');link(cast,castout(cast),getter,'self');link(getter,'DS3AttackMontage',play,'MontageToPlay')
unreal.BlueprintEditorLibrary.compile_blueprint(ga);assert not ed.list_nodes_with_errors();lib.save_loaded_asset(ga,False)

def scalar(value,key=None):
 v=unreal.ValueOrBBKey_Float();v.import_text('(DefaultValue='+str(value)+',Key='+str(key or 'None')+')');return v
def make(typ,name,label=None,**props):
 cls=unreal.load_class(None,AI+typ+'.'+typ+'_C') if typ.startswith('BTT_') else unreal.load_class(None,'/Script/AIModule.'+typ)
 n=unreal.find_object(bt,name) or unreal.new_object(cls,outer=bt,name=name)
 if label:n.set_editor_property('node_name',label)
 if isinstance(n,unreal.BTTask_BlueprintBase):n.set_editor_property('bShowPropertyDetails',False)
 for k,v in props.items():n.set_editor_property(k,v)
 return n
def child(n,decs=None):
 c=unreal.BTCompositeChild();c.set_editor_property('child_composite' if isinstance(n,unreal.BTCompositeNode) else 'child_task',n)
 if decs:c.set_editor_property('decorators',decs)
 return c
def sequence(name,nodes):
 s=make('BTComposite_Sequence',name,name);s.set_editor_property('children',nodes);return s
def integer(name,key,value):
 d=make('BTDecorator_Blackboard',name,key+' = '+str(value));d.set_editor_property('blackboard_key',selector(key));d.set_editor_property('arithmetic_operation',type(d.get_editor_property('arithmetic_operation')).EQUAL);d.set_editor_property('int_value',value);return d
def boolean(name,key,isset=True,abort=unreal.BTFlowAbortMode.NONE):
 d=make('BTDecorator_Blackboard',name);d.set_editor_property('blackboard_key',selector(key));d.set_editor_property('basic_operation',type(d.get_editor_property('basic_operation')).SET if isset else type(d.get_editor_property('basic_operation')).NOT_SET);d.set_editor_property('flow_abort_mode',abort);return d
def wait(name,value=0):return make('BTTask_Wait',name,wait_time=scalar(value),random_deviation=scalar(0))
def move(name,radius=0,key=None):
 n=make('BTTask_MoveTo',name,'Native approach to action distance',blackboard_key=selector('TargetActor'),acceptable_radius=scalar(radius,key))
 for p in ['reach_test_includes_agent_radius','reach_test_includes_goal_radius']:
  v=unreal.ValueOrBBKey_Bool();v.import_text('(DefaultValue=false,Key=None)');n.set_editor_property(p,v)
 return n
def mode(name,base=2.5,offset=.7,walk=False):return make('BTT_DSLocomotion',name,'Configure approach / native focus',BaseRange=base,RunOffset=offset,AlwaysWalk=walk,RunChance=50 if name in ['Mode20','Mode21'] else 100,ForceRunOffset=10.0 if name in ['Mode20','Mode21'] else 2.5)
def strike(aid,name):return make('BTT_DSAttack',name,'Strike '+str(aid)+' (proxy animation)',Montage=montages[aid],SourceAttackID=aid)
def relative(name,mode,duration=2,distance=10,after=False):return make('BTT_DSRelativeMove',name,'Sideway' if mode==1 else 'Retreat' if mode==2 else 'Approach after attack' if mode==3 else 'Turn',Mode=mode,Duration=duration,TargetDistance=distance,UseAfterSettings=after)
root=make('BTComposite_Selector','Root','DS3 110050 Broken Sword: action cycles');bt.set_editor_property('root_node',root)
branches=[]
for aid,base,offset,hits in [(1,2.5,.7,[3000,3001,3002]),(2,2.2,.7,[3001,3002,3000]),(4,2.5,.7,[3002,3001]),(5,2,.7,[3003]),(6,7.2,.7,[3007]),(20,20,1,[20005]),(21,15,1,[20006])]:
 approach=move('Approach'+str(aid),key='ApproachRadius')
 limit=make('BTDecorator_TimeLimit','ApproachBudget'+str(aid),'Source approach lifetime',time_limit=scalar(8,'ApproachLife'))
 tasks=[child(mode('Mode'+str(aid),base,offset)),child(approach,[limit])]
 if len(hits)==3:tasks.append(child(make('BTT_DSComboChoice','ComboLength'+str(aid),'Choose 2 / 3 strikes once')))
 for j,attackid in enumerate(hits):
  if len(hits)==3 and j==2:
   optional=make('BTComposite_Selector','ThirdChoice'+str(aid),'Optional third strike');optional.set_editor_property('children',[child(strike(attackid,'Strike'+str(aid)+'_'+str(j)),[boolean('ThirdHit'+str(aid),'ThirdHit')]),child(wait('NoThird'+str(aid))) ]);tasks.append(child(optional))
  else:tasks.append(child(strike(attackid,'Strike'+str(aid)+'_'+str(j))))
 action=sequence('Act'+str(aid),tasks);branches.append(child(action,[integer('Select'+str(aid),'Action',aid)]))
act11=sequence('Act11',[child(mode('Mode11',walk=True)),child(move('Approach11',1000)),child(relative('Retreat11',2,4,10))]);branches.append(child(act11,[integer('Select11','Action',11)]))
for aid,md,duration in [(12,1,2),(13,4,3)]:
 action=sequence('Act'+str(aid),[child(mode('Mode'+str(aid),walk=True)),child(relative('Relative'+str(aid),md,duration))]);branches.append(child(action,[integer('Select'+str(aid),'Action',aid)]))
act54=sequence('Act54',[child(mode('Mode54',1,0)),child(move('Approach54',100))]);branches.append(child(act54,[integer('Select54','Action',54)]))
dispatch=make('BTComposite_Selector','Dispatch','Execute selected action; no per-frame reselection');dispatch.set_editor_property('children',branches)
after=make('BTComposite_Selector','AfterDispatch','Optional after-attack motion')
after.set_editor_property('children',[child(relative('AfterSide',1,after=True),[integer('After1','AfterAction',1)]),child(relative('AfterBack',2,after=True),[integer('After2','AfterAction',2)]),child(relative('AfterApproach',3,after=True),[integer('After3','AfterAction',3)]),child(wait('NoAfterMove'))])
cycle=sequence('ActionCycle',[child(make('BTT_DSInit','Init')),child(make('BTT_DSDecide','Decide','Source priorities + weighted choice + per-action cooldown')),child(dispatch),child(mode('AfterMode',walk=True)),child(make('BTT_DSAfterAttack','AfterChoice','Optional source after-attack adjustment')),child(after)])
root.set_editor_property('children',[child(cycle,[boolean('ValidTarget','TargetActor',True,unreal.BTFlowAbortMode.BOTH)]),child(wait('NoTarget',.2))])

# Public editor graph materialization, only in this new unbound package. No auto-arrange.
prefix=bt.get_path_name()+':'
def owned():return [o for o in unreal.ObjectIterator() if unreal.Object.get_path_name(o).startswith(prefix)]
graph=next(o for o in owned() if o.get_class().get_name()=='BehaviorTreeGraph')
def pointer(o):
 assert o.get_path_name().startswith(prefix);return int(re.search(r'\(0x([0-9a-fA-F]+)\)',str(o)).group(1),16)
gd=ctypes.WinDLL('E:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-BehaviorTreeEditor.dll');nd=ctypes.WinDLL('E:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-AIGraph.dll')
def call(dll,symbol,obj,*args):
 f=getattr(dll,symbol);f.argtypes=[ctypes.c_void_p]+[ctypes.c_int for _ in args];f.restype=None;f(pointer(obj),*args)
call(gd,'?SpawnMissingNodes@UBehaviorTreeGraph@@QEAAXXZ',graph)
for node in [o for o in owned() if o.get_class().get_name().startswith('BehaviorTreeGraphNode')]:
 if node.get_class().get_name()=='BehaviorTreeGraphNode_Root':node.set_editor_property('BlackboardAsset',bb)
 call(nd,'?PostCopyNode@UAIGraphNode@@UEAAXXZ',node);call(nd,'?UpdateNodeClassData@UAIGraphNode@@UEAAXXZ',node)
call(gd,'?UpdateAsset@UBehaviorTreeGraph@@UEAAXH@Z',graph,0)
assert lib.save_loaded_asset(bt,False)
print('DS3_TREE_SAVED',len(branches),'action branches')
