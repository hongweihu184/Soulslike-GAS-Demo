"""Build a new, reviewable BT asset; bind only after reload verification.
Uses public exported UE editor graph methods on this newly created package.
No raw memory reads/writes or changes to the original behavior tree.
"""
import unreal,json,ctypes,re
from pathlib import Path
AI='/Game/Gameplay/AI/'
bt=unreal.load_asset(AI+'BT_EnemyMeleeCombat_V2');bb=unreal.load_asset(AI+'BB_Enemy');bt.set_editor_property('blackboard_asset',bb)
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
 raise RuntimeError('Stop PIE before constructing the tree.')
controller=unreal.load_asset(AI+'BP_EnemyAIController')
controller_graph=unreal.BlueprintEditorLibrary.find_event_graph(controller)
run_node=unreal.find_object(None,controller_graph.get_path_name()+'.K2Node_CallFunction_1')
if run_node and any(str(p.get_pin_name())=='BTAsset' and p.get_pin_value()==bt.get_path_name() for p in run_node.list_all_pins()):
 raise RuntimeError('This tree is already bound. Generator refuses to replace its graph; edit the visible tree instead.')
# This is our new, not-yet-bound asset. Clear its earlier generated graph nodes
# through UEdGraph's public removal API so retries never leave duplicate subtrees.
graph=unreal.find_object(None,bt.get_path_name()+':Behavior Tree')
def object_pointer(obj):
 assert obj and unreal.Object.get_path_name(obj).startswith(bt.get_path_name()+':')
 return int(re.search(r'\(0x([0-9a-fA-F]+)\)',str(obj)).group(1),16)
engine=ctypes.WinDLL('E:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Engine.dll')
remove=getattr(engine,'?RemoveNode@UEdGraph@@QEAA_NPEAVUEdGraphNode@@_N1@Z')
remove.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_bool,ctypes.c_bool];remove.restype=ctypes.c_bool
for old in [o for o in unreal.ObjectIterator() if isinstance(o,unreal.EdGraphNode) and o.get_outer()==graph and o.get_class().get_name()!='BehaviorTreeGraphNode_Root']:
 remove(object_pointer(graph),object_pointer(old),True,True)
keys=list(bb.get_editor_property('keys'))
def selector(name):
 i=next(i for i,k in enumerate(keys) if str(k.get_editor_property('entry_name'))==name)
 s=unreal.BlackboardKeySelector();s.set_editor_property('selected_key_name',name);s.set_editor_property('selected_key_id',i);s.set_editor_property('selected_key_type',keys[i].get_editor_property('key_type').get_class());return s
def make(type_name,name,label=None):
 cls=unreal.load_class(None,AI+type_name+'.'+type_name+'_C') if type_name.startswith(('BTT_','BTS_')) else unreal.load_class(None,'/Script/AIModule.'+type_name)
 n=unreal.find_object(bt,name) or unreal.new_object(cls,outer=bt,name=name)
 if label:n.set_editor_property('node_name',label)
 return n
def scalar(value):
 v=unreal.ValueOrBBKey_Float();v.import_text('(DefaultValue='+str(value)+',Key=None)');return v
def key(node,name):node.set_editor_property('blackboard_key',selector(name))
def condition(name,keyname,isset,abort):
 n=make('BTDecorator_Blackboard',name)
 key(n,keyname)
 operation=n.get_editor_property('basic_operation')
 n.set_editor_property('basic_operation',type(operation).SET if isset else type(operation).NOT_SET)
 n.set_editor_property('flow_abort_mode',abort)
 return n
def at(name,radius,invert=False):
 n=make('BTDecorator_IsAtLocation',name)
 key(n,'TargetActor');n.set_editor_property('acceptable_radius',radius)
 b=unreal.ValueOrBBKey_Bool();b.import_text('(DefaultValue=false,Key=None)');n.set_editor_property('path_finding_based_test',b)
 n.set_editor_property('geometric_distance_type',type(n.get_editor_property('geometric_distance_type')).DISTANCE2D)
 n.set_editor_property('inverse_condition',invert);n.set_editor_property('flow_abort_mode',unreal.BTFlowAbortMode.NONE)
 return n
def child(node,decorators=None):
 c=unreal.BTCompositeChild();c.set_editor_property('child_composite' if isinstance(node,unreal.BTCompositeNode) else 'child_task',node)
 if decorators:c.set_editor_property('decorators',decorators)
 return c
def move(name,keyname,radius):
 n=make('BTTask_MoveTo',name)
 key(n,keyname);n.set_editor_property('acceptable_radius',scalar(radius))
 for prop in ['reach_test_includes_agent_radius','reach_test_includes_goal_radius']:
  v=unreal.ValueOrBBKey_Bool();v.import_text('(DefaultValue=false,Key=None)');n.set_editor_property(prop,v)
 for prop in ['track_moving_goal','allow_strafe']:
  v=unreal.ValueOrBBKey_Bool();v.import_text('(DefaultValue=true,Key=None)')
  try:n.set_editor_property(prop,v)
  except:n.set_editor_property(prop,True)
 return n
def wait(name,seconds):
 n=make('BTTask_Wait',name);n.set_editor_property('wait_time',scalar(seconds));n.set_editor_property('random_deviation',scalar(0));return n
def mode(name,chase):
 n=make('BTT_EnemyMoveMode',name,'Chase locomotion' if chase else 'Combat locomotion + focus')
 n.set_editor_property('UseChaseSpeed',chase);return n
def service(name,typ,search=False):
 n=make(typ,name);n.set_editor_property('interval',0.2);n.set_editor_property('random_deviation',0.0);n.set_editor_property('call_tick_on_search_start',search);return n

root=make('BTComposite_Selector','RootSelector','Enemy combat: behavior tree owns decisions');bt.set_editor_property('root_node',root)
root.set_editor_property('services',[service('CombatContext','BTS_EnemyCombatContext')])
combat=make('BTComposite_Selector','CombatSelector','Chase / Attack / Guard')
chase=make('BTComposite_Sequence','ChaseSequence','Chase: enter 400, leave combat at 550')
chase.set_editor_property('children',[child(mode('ChaseMode',True)),child(move('ChaseMove','TargetActor',400)),child(wait('ChaseRecheck',0.1))])
attack=make('BTComposite_Sequence','AttackSequence','Attack ready: approach, face, commit')
face=make('BTTask_RotateToFaceBBEntry','FaceTarget','Face target within 15 degrees');key(face,'TargetActor');face.set_editor_property('precision',scalar(15.0))
attack.set_editor_property('children',[child(mode('AttackMode',False)),child(move('AttackApproach','TargetActor',180)),child(face),child(make('BTT_EnemyAttack','SingleAttack','Single GA attack; cooldown on actual end'))])
guard=make('BTComposite_Sequence','GuardSequence','Guard: focus and maintain relative distance')
choices=make('BTComposite_Selector','GuardChoice','Retreat / Approach / Hold')
retreat=make('BTComposite_Sequence','RetreatSequence','Below 140: retreat to 200')
retreat.set_editor_property('services',[service('RetreatGoalUpdate','BTS_EnemyRetreatGoal',True)])
retreat.set_editor_property('children',[child(move('RetreatMove','RetreatGoal',3)),child(wait('AfterRetreat',0.1))])
approach=make('BTComposite_Sequence','GuardApproachSequence','Above 190: approach to 150')
approach.set_editor_property('children',[child(move('GuardApproach','TargetActor',150)),child(wait('AfterApproach',0.1))])
choices.set_editor_property('children',[child(retreat,[at('TooClose',140)]),child(approach,[at('TooFar',190,True)]),child(wait('GuardHold',0.2))])
guard.set_editor_property('children',[child(mode('GuardMode',False)),child(choices)])
combat.set_editor_property('children',[child(chase,[condition('OutsideCombat','InCombatRange',False,unreal.BTFlowAbortMode.BOTH)]),child(attack,[condition('CanAttack','AttackReady',True,unreal.BTFlowAbortMode.LOWER_PRIORITY)]),child(guard)])
root.set_editor_property('children',[child(combat,[condition('HasTarget','TargetActor',True,unreal.BTFlowAbortMode.BOTH),condition('ContextReady','ContextReady',True,unreal.BTFlowAbortMode.BOTH)]),child(wait('IdleWithoutTarget',0.2))])

# Materialize the editable tree graph using public UE editor methods.
# Only accept live objects owned by this new tree's package.
prefix=bt.get_path_name()+':'
def owned():return [o for o in unreal.ObjectIterator() if isinstance(o,unreal.Object) and unreal.Object.get_path_name(o).startswith(prefix)]
def pointer(o):
 assert o and unreal.Object.get_path_name(o).startswith(prefix)
 return int(re.search(r'\(0x([0-9a-fA-F]+)\)',str(o)).group(1),16)
graph=next(o for o in owned() if unreal.Object.get_class(o).get_name()=='BehaviorTreeGraph')
graphdll=ctypes.WinDLL('E:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-BehaviorTreeEditor.dll')
nodedll=ctypes.WinDLL('E:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-AIGraph.dll')
def call(dll,symbol,obj,*args):
 f=getattr(dll,symbol);f.argtypes=[ctypes.c_void_p]+[ctypes.c_int for _ in args];f.restype=None;f(pointer(obj),*args)
call(graphdll,'?SpawnMissingNodes@UBehaviorTreeGraph@@QEAAXXZ',graph)
for n in [o for o in owned() if unreal.Object.get_class(o).get_name().startswith('BehaviorTreeGraphNode')]:
 call(nodedll,'?PostCopyNode@UAIGraphNode@@UEAAXXZ',n)
 call(nodedll,'?UpdateNodeClassData@UAIGraphNode@@UEAAXXZ',n)
call(graphdll,'?UpdateAsset@UBehaviorTreeGraph@@UEAAXH@Z',graph,0)
assert len(bt.root_node.children[0].child_composite.children)==3
assert unreal.EditorAssetLibrary.save_loaded_asset(bt,False)
print('BT_V2_TREE_SAVED',bt.get_path_name())
