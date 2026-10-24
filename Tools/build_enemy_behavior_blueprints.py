"""Editor-only construction of the BT's context service, retreat goal and tasks.
Runtime decisions remain in the behavior tree. No controller Tick movement.
Back up affected assets and open their Blueprint editors before running.
"""
import unreal,json
from pathlib import Path
AI='/Game/Gameplay/AI/'
KM='/Script/Engine.KismetMathLibrary.'
BT='/Script/AIModule.BTFunctionLibrary.'

def pin(n,name):
 p=[p for p in n.list_all_pins() if str(p.get_pin_name())==name]
 assert len(p)==1,(n.get_name(),name,[str(x.get_pin_name()) for x in n.list_all_pins()])
 return p[0]
def link(a,an,b,bn):assert pin(a,an).try_create_connection(pin(b,bn)),(a.get_name(),an,b.get_name(),bn)
def val(n,name,v):
 ok=pin(n,name).set_pin_value(str(v));assert ok or pin(n,name).get_pin_value()==str(v),(name,v,pin(n,name).get_pin_value())
def seq(a,b,out='then'):link(a,out,b,'execute');return b
def castout(n):return next(str(p.get_pin_name()) for p in n.list_all_pins() if str(p.get_pin_name()).startswith('As'))

bb=unreal.load_asset(AI+'BB_Enemy');keys=list(bb.get_editor_property('keys'))
for name,cls in [('ContextReady',unreal.load_class(None,'/Script/AIModule.BlackboardKeyType_Bool')),('InCombatRange',unreal.load_class(None,'/Script/AIModule.BlackboardKeyType_Bool')),('AttackReady',unreal.load_class(None,'/Script/AIModule.BlackboardKeyType_Bool')),('NextAttackTime',unreal.load_class(None,'/Script/AIModule.BlackboardKeyType_Float')),('TargetDistance',unreal.load_class(None,'/Script/AIModule.BlackboardKeyType_Float')),('ChaseSpeed',unreal.load_class(None,'/Script/AIModule.BlackboardKeyType_Float')),('RetreatGoal',unreal.load_class(None,'/Script/AIModule.BlackboardKeyType_Vector'))]:
 if not any(str(k.get_editor_property('entry_name'))==name for k in keys):
  entry=unreal.BlackboardEntry();entry.set_editor_property('entry_name',name);entry.set_editor_property('key_type',unreal.new_object(cls,outer=bb));keys.append(entry)
bb.set_editor_property('keys',keys);assert unreal.EditorAssetLibrary.save_loaded_asset(bb,False)
def selector(name):
 i=next(i for i,k in enumerate(keys) if str(k.get_editor_property('entry_name'))==name)
 s=unreal.BlackboardKeySelector();s.set_editor_property('selected_key_name',name);s.set_editor_property('selected_key_id',i);s.set_editor_property('selected_key_type',keys[i].get_editor_property('key_type').get_class());return s

class Graph:
 def __init__(self,name,variables,events):
  self.b=unreal.load_asset(AI+name)
  for n,typ,default in variables:
   try:unreal.get_default_object(self.b.generated_class()).get_editor_property(n)
   except:
    pt=unreal.BlueprintEditorLibrary.get_struct_type(unreal.BlackboardKeySelector.static_struct()) if typ=='key' else unreal.BlueprintEditorLibrary.get_basic_type_by_name(typ)
    assert unreal.BlueprintEditorLibrary.add_member_variable(self.b,n,pt)
  for n,typ,default in variables:
   if n not in ['Initialized','AttackStarted']:
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(self.b,n,True)
  unreal.BlueprintEditorLibrary.compile_blueprint(self.b)
  self.g=unreal.BlueprintEditorLibrary.find_event_graph(self.b);self.ed=unreal.BlueprintGraphEditor.get_graph_editor(self.g);assert self.ed
  self.ed.remove_nodes([n for n in self.ed.list_all_nodes() if not isinstance(n,unreal.K2Node_Event)])
  self.events={e:self.ed.find_event_node(e) or unreal.BlueprintEditorLibrary.add_event_override(self.b,e,unreal.IntPoint(0,i*1000)) for i,e in enumerate(events)}
  self.variables=variables;self.i=0
 def pos(self,n):
  assert n
  n.set_node_pos(unreal.IntPoint(300+(self.i%6)*400,(self.i//6)*300));self.i+=1;return n
 def fn(self,path):return self.pos(self.ed.add_call_function_node(path))
 def get(self,n,cls=''):return self.pos(self.ed.add_get_member_variable_node(n,cls))
 def set(self,n,cls=''):return self.pos(self.ed.add_set_member_variable_node(n,cls))
 def branch(self):return self.pos(self.ed.add_branch_node())
 def cast(self,n):return self.pos(self.ed.create_node_from_name(next(t for t in self.ed.list_available_nodes([]) if t.endswith('|CastTo'+n)),unreal.Vector2D(0,0),[]))
 def calc(self,name,a,ap,b=None,bp='ReturnValue',constant=None):
  n=self.fn(KM+name);link(a,ap,n,'A')
  if b is not None:link(b,bp,n,'B')
  elif constant is not None:val(n,'B',constant)
  return n
 def bbget(self,typ,key):
  n=self.fn(BT+'GetBlackboardValueAs'+typ);link(self.get(key),key,n,'Key');return n
 def bbset(self,typ,key):
  n=self.fn(BT+'SetBlackboardValueAs'+typ);link(self.get(key),key,n,'Key');return n
 def finish(self,description):
  self.ed.add_comment_node(description,unreal.Vector2D(0,-250),unreal.Vector2D(2600,160))
  unreal.BlueprintEditorLibrary.compile_blueprint(self.b)
  assert not self.ed.list_nodes_with_errors(),str(self.ed.list_nodes_with_errors())
  cdo=unreal.get_default_object(self.b.generated_class())
  for n,typ,default in self.variables:cdo.set_editor_property(n,selector(default) if typ=='key' else default)
  assert unreal.EditorAssetLibrary.save_loaded_asset(self.b,False)
  print('saved',self.b.get_name(),len(self.ed.list_all_nodes()))

def valid(g,obj,op,previous,out='then'):
 v=g.fn('/Script/Engine.KismetSystemLibrary.IsValid');link(obj,op,v,'Object');b=g.branch();seq(previous,b,out);link(v,'ReturnValue',b,'Condition');return b
def movement(g,event,previous):
 m=g.fn('/Script/Engine.Pawn.GetMovementComponent');link(event,'ControlledPawn',m,'self');c=g.cast('CharacterMovementComponent');link(m,'ReturnValue',c,'Object');seq(previous,c);return c,castout(c)
def flag(g,prop,obj,op,previous,value):
 n=g.set(prop,'/Script/Engine.CharacterMovementComponent');link(obj,op,n,'self');val(n,prop,str(value).lower());seq(previous,n);return n
def location(g,obj,op):
 n=g.fn('/Script/Engine.Actor.K2_GetActorLocation');link(obj,op,n,'self');return n
def attacking(g,event):
 asc=g.fn('/Script/GameplayAbilities.AbilitySystemBlueprintLibrary.GetAbilitySystemComponent');link(event,'ControlledPawn',asc,'Actor')
 n=g.fn('/Script/GameplayAbilities.AbilitySystemComponent.GetGameplayTagCount');link(asc,'ReturnValue',n,'self');val(n,'GameplayTag','(TagName="State.Attacking")');return asc,n

# Context is sampled every .2 seconds. It never issues movement requests.
vars=[(n,'key',n[:-3]) for n in ['TargetActorKey','ContextReadyKey','InCombatRangeKey','AttackReadyKey','NextAttackTimeKey','TargetDistanceKey','ChaseSpeedKey']]+[('Initialized','bool',False),('CombatEnterDistance','real',400.0),('CombatExitDistance','real',550.0)]
g=Graph('BTS_EnemyCombatContext',vars,['ReceiveTickAI']);e=g.events['ReceiveTickAI'];target=g.bbget('Actor','TargetActorKey');v=valid(g,target,'ReturnValue',e)
invalid=g.bbset('Bool','ContextReadyKey');val(invalid,'Value','false');seq(v,invalid,'else')
notready=g.bbset('Bool','AttackReadyKey');val(notready,'Value','false');seq(invalid,notready)
init=g.branch();seq(v,init);link(g.get('Initialized'),'Initialized',init,'Condition')
mc,mcp=movement(g,e,init) # true route skips cache below; route rewired to false for init
pin(init,'then').break_single_pin_link(pin(mc,'execute'));seq(init,mc,'else')
speed=g.get('MaxWalkSpeed','/Script/Engine.CharacterMovementComponent');link(mc,mcp,speed,'self')
cache=g.bbset('Float','ChaseSpeedKey');link(speed,'MaxWalkSpeed',cache,'Value');seq(mc,cache)
mark=g.set('Initialized');val(mark,'Initialized','true');seq(cache,mark)
ready=g.bbset('Bool','ContextReadyKey');val(ready,'Value','true');seq(init,ready);seq(mark,ready)
# A tree restart must not recache the temporary combat speed as chase speed.
cached=g.bbget('Float','ChaseSpeedKey');hascached=g.calc('Greater_DoubleDouble',cached,'ReturnValue',constant=0)
reuse=g.branch();seq(init,reuse,'else');link(hascached,'ReturnValue',reuse,'Condition');seq(reuse,mark);seq(reuse,mc,'else')
pl=location(g,e,'ControlledPawn');tl=location(g,target,'ReturnValue');d=g.fn(KM+'Vector_Distance2D');link(pl,'ReturnValue',d,'V1');link(tl,'ReturnValue',d,'V2')
setd=g.bbset('Float','TargetDistanceKey');link(d,'ReturnValue',setd,'Value');seq(ready,setd)
asc,tags=attacking(g,e);zero=g.calc('EqualEqual_IntInt',tags,'ReturnValue',constant=0);free=g.branch();seq(setd,free);link(zero,'ReturnValue',free,'Condition')
busy=g.bbset('Bool','AttackReadyKey');val(busy,'Value','false');seq(free,busy,'else')
near=g.calc('LessEqual_DoubleDouble',d,'ReturnValue',g.get('CombatEnterDistance'),'CombatEnterDistance');nc=g.branch();seq(free,nc);link(near,'ReturnValue',nc,'Condition')
inside=g.bbset('Bool','InCombatRangeKey');val(inside,'Value','true');seq(nc,inside)
far=g.calc('GreaterEqual_DoubleDouble',d,'ReturnValue',g.get('CombatExitDistance'),'CombatExitDistance');fc=g.branch();seq(nc,fc,'else');link(far,'ReturnValue',fc,'Condition')
outside=g.bbset('Bool','InCombatRangeKey');val(outside,'Value','false');seq(fc,outside)
now=g.fn('/Script/Engine.GameplayStatics.GetTimeSeconds');nexttime=g.bbget('Float','NextAttackTimeKey');can=g.calc('GreaterEqual_DoubleDouble',now,'ReturnValue',nexttime)
setcan=g.bbset('Bool','AttackReadyKey');link(can,'ReturnValue',setcan,'Value');seq(inside,setcan);seq(outside,setcan);seq(fc,setcan,'else')
g.finish('Context only: sample distance/cooldown at 0.2s. Freeze engagement switching during committed attack. Cache original speed once. No navigation commands.')

# Retreat destination follows the target while this subtree is active; native MoveTo owns pathing.
g=Graph('BTS_EnemyRetreatGoal',[('TargetActorKey','key','TargetActor'),('RetreatGoalKey','key','RetreatGoal'),('RetreatDistance','real',200.0)],['ReceiveTickAI']);e=g.events['ReceiveTickAI'];target=g.bbget('Actor','TargetActorKey');v=valid(g,target,'ReturnValue',e)
pl=location(g,e,'ControlledPawn');tl=location(g,target,'ReturnValue')
direction=g.fn(KM+'GetDirectionUnitVector');link(tl,'ReturnValue',direction,'From');link(pl,'ReturnValue',direction,'To')
br=g.fn(KM+'BreakVector');link(direction,'ReturnValue',br,'InVec');flat=g.fn(KM+'MakeVector');link(br,'X',flat,'X');link(br,'Y',flat,'Y')
norm=g.fn(KM+'Normal');link(flat,'ReturnValue',norm,'A')
scale=g.calc('Multiply_VectorFloat',norm,'ReturnValue',g.get('RetreatDistance'),'RetreatDistance')
goal=g.calc('Add_VectorVector',tl,'ReturnValue',scale)
project=g.fn('/Script/NavigationSystem.NavigationSystemV1.K2_ProjectPointToNavigation');link(goal,'ReturnValue',project,'Point');val(project,'QueryExtent','(X=100,Y=100,Z=300)')
ok=g.branch();seq(v,ok);link(project,'ReturnValue',ok,'Condition')
setgoal=g.bbset('Vector','RetreatGoalKey');link(project,'ProjectedLocation',setgoal,'Value');seq(ok,setgoal)
clear=g.fn(BT+'ClearBlackboardValue');link(g.get('RetreatGoalKey'),'RetreatGoalKey',clear,'Key');seq(ok,clear,'else');seq(v,clear,'else')
g.finish('Active only in Retreat subtree: project a point 200cm from target onto navigation. Update at .2s, never selects a new behavior or directly moves the pawn.')

# One-shot locomotion setup at branch entry, not Tick.
g=Graph('BTT_EnemyMoveMode',[('TargetActorKey','key','TargetActor'),('ChaseSpeedKey','key','ChaseSpeed'),('UseChaseSpeed','bool',False),('CombatSpeed','real',120.0),('TurnRate','real',180.0)],['ReceiveExecuteAI']);e=g.events['ReceiveExecuteAI'];mc,mcp=movement(g,e,e)
orient=g.set('bOrientRotationToMovement','/Script/Engine.CharacterMovementComponent');seq(mc,orient);link(mc,mcp,orient,'self');link(g.get('UseChaseSpeed'),'UseChaseSpeed',orient,'bOrientRotationToMovement')
inverse=g.fn(KM+'Not_PreBool');link(g.get('UseChaseSpeed'),'UseChaseSpeed',inverse,'A')
desired=g.set('bUseControllerDesiredRotation','/Script/Engine.CharacterMovementComponent');seq(orient,desired);link(mc,mcp,desired,'self');link(inverse,'ReturnValue',desired,'bUseControllerDesiredRotation')
yaw=g.set('bUseControllerRotationYaw','/Script/Engine.Pawn');seq(desired,yaw);link(e,'ControlledPawn',yaw,'self');val(yaw,'bUseControllerRotationYaw','false')
rotation=g.fn(KM+'MakeRotator');link(g.get('TurnRate'),'TurnRate',rotation,'Yaw');setrotation=g.set('RotationRate','/Script/Engine.CharacterMovementComponent');link(mc,mcp,setrotation,'self');link(rotation,'ReturnValue',setrotation,'RotationRate');seq(yaw,setrotation)
choose=g.branch();seq(setrotation,choose);link(g.get('UseChaseSpeed'),'UseChaseSpeed',choose,'Condition')
fast=g.set('MaxWalkSpeed','/Script/Engine.CharacterMovementComponent');seq(choose,fast);link(mc,mcp,fast,'self');link(g.bbget('Float','ChaseSpeedKey'),'ReturnValue',fast,'MaxWalkSpeed')
slow=g.set('MaxWalkSpeed','/Script/Engine.CharacterMovementComponent');seq(choose,slow,'else');link(mc,mcp,slow,'self');link(g.get('CombatSpeed'),'CombatSpeed',slow,'MaxWalkSpeed')
focus=g.fn('/Script/AIModule.AIController.K2_SetFocus');link(e,'OwnerController',focus,'self');link(g.bbget('Actor','TargetActorKey'),'ReturnValue',focus,'NewFocus');seq(fast,focus);seq(slow,focus)
finish=g.fn('/Script/AIModule.BTTask_BlueprintBase.FinishExecute');val(finish,'bSuccess','true');seq(focus,finish)
g.finish('Branch-entry setup only. Chase uses original cached speed and path direction; combat uses 120cm/s and native desired rotation at 180deg/s. Focus target once; no Tick, no MoveTo.')

# Attack only starts after the native MoveTo and RotateToFace tasks succeeded.
vars=[('TargetKey','key','TargetActor'),('NextAttackTimeKey','key','NextAttackTime'),('AttackReadyKey','key','AttackReady'),('AttackStarted','bool',False),('AttackStartDistance','real',200.0),('AttackFacingTolerance','real',15.0),('AttackCooldown','real',5.0)]
g=Graph('BTT_EnemyAttack',vars,['ReceiveExecuteAI','ReceiveTickAI','ReceiveAbortAI']);e=g.events['ReceiveExecuteAI'];tick=g.events['ReceiveTickAI'];abort=g.events['ReceiveAbortAI']
reset=g.set('AttackStarted');val(reset,'AttackStarted','false');seq(e,reset)
target=g.bbget('Actor','TargetKey');v=valid(g,target,'ReturnValue',reset)
fail=g.fn('/Script/AIModule.BTTask_BlueprintBase.FinishExecute');val(fail,'bSuccess','false');seq(v,fail,'else')
pl=location(g,e,'ControlledPawn');tl=location(g,target,'ReturnValue');d=g.fn(KM+'Vector_Distance2D');link(pl,'ReturnValue',d,'V1');link(tl,'ReturnValue',d,'V2')
near=g.calc('LessEqual_DoubleDouble',d,'ReturnValue',g.get('AttackStartDistance'),'AttackStartDistance')
look=g.fn(KM+'FindLookAtRotation');link(pl,'ReturnValue',look,'Start');link(tl,'ReturnValue',look,'Target')
rot=g.fn('/Script/Engine.Actor.K2_GetActorRotation');link(e,'ControlledPawn',rot,'self');delta=g.calc('NormalizedDeltaRotator',look,'ReturnValue',rot)
br=g.fn(KM+'BreakRotator');link(delta,'ReturnValue',br,'InRot');absolute=g.fn(KM+'Abs');link(br,'Yaw',absolute,'A')
aligned=g.calc('LessEqual_DoubleDouble',absolute,'ReturnValue',g.get('AttackFacingTolerance'),'AttackFacingTolerance');legal=g.calc('BooleanAND',near,'ReturnValue',aligned);gate=g.branch();seq(v,gate);link(legal,'ReturnValue',gate,'Condition');seq(gate,fail,'else')
stop=g.fn('/Script/Engine.Controller.StopMovement');link(e,'OwnerController',stop,'self');seq(gate,stop)
mc,mcp=movement(g,e,stop);halt=g.fn('/Script/Engine.MovementComponent.StopMovementImmediately');link(mc,mcp,halt,'self');seq(mc,halt)
disable=flag(g,'bUseControllerDesiredRotation',mc,mcp,halt,False)
clear=g.fn('/Script/AIModule.AIController.K2_ClearFocus');link(e,'OwnerController',clear,'self');seq(disable,clear)
asc,count=attacking(g,e);activate=g.fn('/Script/GameplayAbilities.AbilitySystemComponent.TryActivateAbilityByClass');link(asc,'ReturnValue',activate,'self');val(activate,'InAbilityToActivate','/Game/Gameplay/GAS/Abilities/GA_EnemyAttack.GA_EnemyAttack_C');seq(clear,activate)
ok=g.branch();seq(activate,ok);link(activate,'ReturnValue',ok,'Condition');mark=g.set('AttackStarted');val(mark,'AttackStarted','true');seq(ok,mark)
restorefail=g.set('bUseControllerDesiredRotation','/Script/Engine.CharacterMovementComponent');link(mc,mcp,restorefail,'self');val(restorefail,'bUseControllerDesiredRotation','true');seq(ok,restorefail,'else');seq(restorefail,fail)
started=g.branch();link(g.get('AttackStarted'),'AttackStarted',started,'Condition');seq(tick,started)
_,tickcount=attacking(g,tick);zero=g.calc('EqualEqual_IntInt',tickcount,'ReturnValue',constant=0);done=g.branch();seq(started,done);link(zero,'ReturnValue',done,'Condition')
def cooldown(previous,event,finish_type):
 now=g.fn('/Script/Engine.GameplayStatics.GetTimeSeconds');endtime=g.calc('Add_DoubleDouble',now,'ReturnValue',g.get('AttackCooldown'),'AttackCooldown')
 settime=g.bbset('Float','NextAttackTimeKey');link(endtime,'ReturnValue',settime,'Value');seq(previous,settime)
 ready=g.bbset('Bool','AttackReadyKey');val(ready,'Value','false');seq(settime,ready)
 mc,mcp=movement(g,event,ready);restore=flag(g,'bUseControllerDesiredRotation',mc,mcp,mc,True)
 finish=g.fn('/Script/AIModule.BTTask_BlueprintBase.'+finish_type)
 if finish_type=='FinishExecute':val(finish,'bSuccess','true')
 seq(restore,finish)
cooldown(done,tick,'FinishExecute')
cast=g.cast('BaseCharacter');link(abort,'ControlledPawn',cast,'Object');seq(abort,cast)
cancel=g.fn('/Script/ProjectUnreal.BaseCharacter.CancelAttack');link(cast,castout(cast),cancel,'self');seq(cast,cancel)
wasstarted=g.branch();link(g.get('AttackStarted'),'AttackStarted',wasstarted,'Condition');seq(cancel,wasstarted)
cooldown(wasstarted,abort,'FinishAbort')
aborted=g.fn('/Script/AIModule.BTTask_BlueprintBase.FinishAbort');seq(wasstarted,aborted,'else');seq(cast,aborted,'CastFailed')
g.finish('Single committed attack. Recheck range/facing, stop once, disable native tracking while GA runs. Actual completion/cancel starts 5s cooldown in Blackboard. Failed approach never consumes cooldown.')
print('BT_V2_BLUEPRINTS_SAVED')
