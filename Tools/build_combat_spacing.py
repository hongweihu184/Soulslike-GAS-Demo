"""Run inside Unreal Editor with the controller and task Blueprint editors open.

Back up the affected assets first. The shared notify fix is a separate script.

Runtime policy stays in editable Blueprint graphs. No native graph pointers.
"""
import unreal, json
from pathlib import Path

ROOT = Path('E:/UE5.8Project/ProjectUnreal')
AI = '/Game/Gameplay/AI/'

class Graph:
    def __init__(self, bp):
        self.bp = bp
        self.g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        self.ed = unreal.BlueprintGraphEditor.get_graph_editor(self.g)
        assert self.ed
        self.i = 0
    def pos(self, n):
        n.set_node_pos(unreal.IntPoint(300 + (self.i % 6)*380, 1800 + (self.i//6)*280))
        self.i += 1
        return n
    def fn(self, name):
        n = self.ed.add_call_function_node(name)
        assert n, name
        return self.pos(n)
    def get(self, name, cls=''):
        return self.pos(self.ed.add_get_member_variable_node(name, cls))
    def set(self, name, cls=''):
        return self.pos(self.ed.add_set_member_variable_node(name, cls))
    def branch(self): return self.pos(self.ed.add_branch_node())
    def cast(self, name):
        t = next(t for t in self.ed.list_available_nodes([]) if t.endswith('|CastTo'+name))
        return self.pos(self.ed.create_node_from_name(t, unreal.Vector2D(0,0), []))
    def comment(self, text):
        self.ed.add_comment_node(text, unreal.Vector2D(0, 1600), unreal.Vector2D(2600,180))

def pin(n,name):
    ps = [p for p in n.list_all_pins() if str(p.get_pin_name()) == name]
    assert len(ps)==1, (n.get_name(),name,[str(p.get_pin_name()) for p in n.list_all_pins()])
    return ps[0]
def link(a,an,b,bn):
    assert pin(a,an).try_create_connection(pin(b,bn)), (a.get_name(),an,b.get_name(),bn)
def val(n,p,v):
    result=pin(n,p).set_pin_value(str(v))
    assert result or pin(n,p).get_pin_value()==str(v), (n.get_name(),p,v,pin(n,p).get_pin_value())
def seq(a,b,out='then'):
    link(a,out,b,'execute'); return b
def calc(g,name,a,ap,b=None,bp='ReturnValue',constant=None):
    n=g.fn('/Script/Engine.KismetMathLibrary.'+name);link(a,ap,n,'A')
    if b:link(b,bp,n,'B')
    elif constant is not None:val(n,'B',constant)
    return n
def addvars(bp,vs):
    existing=set()
    cdo=unreal.get_default_object(bp.generated_class())
    for name,typ,default in vs:
        try:cdo.get_editor_property(name);existing.add(name)
        except Exception:pass
    for name,typ,default in vs:
        if name not in existing:
            assert unreal.BlueprintEditorLibrary.add_member_variable(bp,name,unreal.BlueprintEditorLibrary.get_basic_type_by_name(typ))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo=unreal.get_default_object(bp.generated_class())
    for name,typ,default in vs:cdo.set_editor_property(name,default)
def compile_save(bp):
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    g=unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
    errors=ed.list_nodes_with_errors()
    assert not errors, str(errors)
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)

controller=unreal.load_asset(AI+'BP_EnemyAIController')
params=[('CombatMoveSpeed','real',120.0),('CombatTurnRate','real',180.0),
 ('RetreatEnterDistance','real',145.0),('RetreatStopDistance','real',180.0),
 ('ApproachEnterDistance','real',200.0),('ApproachStopDistance','real',185.0),
 ('ChaseDistance','real',450.0),('CachedChaseSpeed','real',300.0),
 ('SpacingIntent','real',0.0),('SpacingInitialized','bool',False),
 ('NextPathRequestTime','real',0.0)]
addvars(controller,params)
c=Graph(controller)
baseline={'K2Node_Event_0','K2Node_Event_1','K2Node_Event_2','K2Node_VariableGet_0','K2Node_CallArrayFunction_0','K2Node_PromotableOperator_0','K2Node_IfThenElse_0'} | {'K2Node_CallFunction_'+str(i) for i in range(7)}
c.ed.remove_nodes([n for n in c.ed.list_all_nodes() if n.get_name() not in baseline])
tick=c.ed.find_event_node('ReceiveTick')
assert tick
assert not pin(tick,'then').get_pin_value() # previously unused tick
c.comment('Combat spacing: TargetActor, finite yaw, hysteresis. Policy parameters are in Class Defaults. Attack/MoveLocked yields to the ability.')
pawn=c.fn('/Script/Engine.Controller.K2_GetPawn')
validp=c.fn('/Script/Engine.KismetSystemLibrary.IsValid');link(pawn,'ReturnValue',validp,'Object')
vp=c.branch();seq(tick,vp);link(validp,'ReturnValue',vp,'Condition')
bb=c.fn('/Script/AIModule.AIBlueprintHelperLibrary.GetBlackboard')
link(pawn,'ReturnValue',bb,'Target')
targetobj=c.fn('/Script/AIModule.BlackboardComponent.GetValueAsObject');link(bb,'ReturnValue',targetobj,'self');link(c.get('Key Name'),'Key Name',targetobj,'KeyName')
cast=c.cast('Actor');seq(vp,cast);link(targetobj,'ReturnValue',cast,'Object')
target=cast; tp=next(str(p.get_pin_name()) for p in cast.list_all_pins() if str(p.get_pin_name()).startswith('As'))
validt=c.fn('/Script/Engine.KismetSystemLibrary.IsValid');link(target,tp,validt,'Object')
vt=c.branch();seq(cast,vt);link(validt,'ReturnValue',vt,'Condition')
stopinvalid=c.fn('/Script/Engine.Controller.StopMovement');seq(cast,stopinvalid,'CastFailed');seq(vt,stopinvalid,'else')
asc=c.fn('/Script/GameplayAbilities.AbilitySystemBlueprintLibrary.GetAbilitySystemComponent');link(pawn,'ReturnValue',asc,'Actor')
locked=c.fn('/Script/GameplayAbilities.AbilitySystemComponent.GetGameplayTagCount');link(asc,'ReturnValue',locked,'self');val(locked,'GameplayTag','(TagName="State.MoveLocked")')
attacking=c.fn('/Script/GameplayAbilities.AbilitySystemComponent.GetGameplayTagCount');link(asc,'ReturnValue',attacking,'self');val(attacking,'GameplayTag','(TagName="State.Attacking")')
sumtags=calc(c,'Add_IntInt',locked,'ReturnValue',attacking)
free=calc(c,'EqualEqual_IntInt',sumtags,'ReturnValue',constant=0)
gate=c.branch();seq(vt,gate);link(free,'ReturnValue',gate,'Condition')
mc=c.fn('/Script/Engine.Pawn.GetMovementComponent');link(pawn,'ReturnValue',mc,'self')
cm=c.cast('CharacterMovementComponent');seq(gate,cm);link(mc,'ReturnValue',cm,'Object')
cmp=next(str(p.get_pin_name()) for p in cm.list_all_pins() if str(p.get_pin_name()).startswith('As'))
init=c.branch();seq(cm,init);link(c.get('SpacingInitialized'),'SpacingInitialized',init,'Condition')
cache=c.set('CachedChaseSpeed');seq(init,cache,'else')
speedget=c.get('MaxWalkSpeed','/Script/Engine.CharacterMovementComponent');link(cm,cmp,speedget,'self');link(speedget,'MaxWalkSpeed',cache,'CachedChaseSpeed')
inited=c.set('SpacingInitialized');val(inited,'SpacingInitialized','true');seq(cache,inited)
orient=c.set('bOrientRotationToMovement','/Script/Engine.CharacterMovementComponent');seq(init,orient);seq(inited,orient);link(cm,cmp,orient,'self');val(orient,'bOrientRotationToMovement','false')
desired=c.set('bUseControllerDesiredRotation','/Script/Engine.CharacterMovementComponent');seq(orient,desired);link(cm,cmp,desired,'self');val(desired,'bUseControllerDesiredRotation','false')
yawflag=c.set('bUseControllerRotationYaw','/Script/Engine.Pawn');seq(desired,yawflag);link(pawn,'ReturnValue',yawflag,'self');val(yawflag,'bUseControllerRotationYaw','false')
ploc=c.fn('/Script/Engine.Actor.K2_GetActorLocation');link(pawn,'ReturnValue',ploc,'self')
tloc=c.fn('/Script/Engine.Actor.K2_GetActorLocation');link(target,tp,tloc,'self')
look=c.fn('/Script/Engine.KismetMathLibrary.FindLookAtRotation');link(ploc,'ReturnValue',look,'Start');link(tloc,'ReturnValue',look,'Target')
br=c.fn('/Script/Engine.KismetMathLibrary.BreakRotator');link(look,'ReturnValue',br,'InRot')
flat=c.fn('/Script/Engine.KismetMathLibrary.MakeRotator');link(br,'Yaw',flat,'Yaw')
rot=c.fn('/Script/Engine.Actor.K2_GetActorRotation');link(pawn,'ReturnValue',rot,'self')
interp=c.fn('/Script/Engine.KismetMathLibrary.RInterpTo_Constant');link(rot,'ReturnValue',interp,'Current');link(flat,'ReturnValue',interp,'Target');link(tick,'DeltaSeconds',interp,'DeltaTime');link(c.get('CombatTurnRate'),'CombatTurnRate',interp,'InterpSpeed')
turn=c.fn('/Script/Engine.Actor.K2_SetActorRotation');seq(yawflag,turn);link(pawn,'ReturnValue',turn,'self');link(interp,'ReturnValue',turn,'NewRotation')
dist=c.fn('/Script/Engine.KismetMathLibrary.Vector_Distance2D');link(ploc,'ReturnValue',dist,'V1');link(tloc,'ReturnValue',dist,'V2')
isfar=calc(c,'Greater_DoubleDouble',dist,'ReturnValue',c.get('ChaseDistance'),'ChaseDistance')
far=c.branch();seq(turn,far);link(isfar,'ReturnValue',far,'Condition')
fast=c.set('MaxWalkSpeed','/Script/Engine.CharacterMovementComponent');seq(far,fast);link(cm,cmp,fast,'self');link(c.get('CachedChaseSpeed'),'CachedChaseSpeed',fast,'MaxWalkSpeed')
now=c.fn('/Script/Engine.GameplayStatics.GetTimeSeconds')
due=calc(c,'GreaterEqual_DoubleDouble',now,'ReturnValue',c.get('NextPathRequestTime'),'NextPathRequestTime')
pathgate=c.branch();seq(fast,pathgate);link(due,'ReturnValue',pathgate,'Condition')
request=c.fn('/Script/AIModule.AIController.MoveToActor');seq(pathgate,request);link(target,tp,request,'Goal');val(request,'AcceptanceRadius',200);val(request,'bStopOnOverlap','false');val(request,'bCanStrafe','true')
nexttime=calc(c,'Add_DoubleDouble',now,'ReturnValue',constant=0.4)
settime=c.set('NextPathRequestTime');seq(request,settime);link(nexttime,'ReturnValue',settime,'NextPathRequestTime')
slow=c.set('MaxWalkSpeed','/Script/Engine.CharacterMovementComponent');seq(far,slow,'else');link(cm,cmp,slow,'self');link(c.get('CombatMoveSpeed'),'CombatMoveSpeed',slow,'MaxWalkSpeed')
stop=c.fn('/Script/Engine.Controller.StopMovement');seq(slow,stop)
# Hysteresis: enter retreat below 145, stop at 180; enter approach above 200, stop at 185.
too_close=calc(c,'Less_DoubleDouble',dist,'ReturnValue',c.get('RetreatEnterDistance'),'RetreatEnterDistance')
checkclose=c.branch();seq(stop,checkclose);link(too_close,'ReturnValue',checkclose,'Condition')
back=c.set('SpacingIntent');val(back,'SpacingIntent',-1);seq(checkclose,back)
too_far=calc(c,'Greater_DoubleDouble',dist,'ReturnValue',c.get('ApproachEnterDistance'),'ApproachEnterDistance')
checkfar=c.branch();seq(checkclose,checkfar,'else');link(too_far,'ReturnValue',checkfar,'Condition')
forward=c.set('SpacingIntent');val(forward,'SpacingIntent',1);seq(checkfar,forward)
intent=c.get('SpacingIntent')
wasback=calc(c,'Less_DoubleDouble',intent,'SpacingIntent',constant=0)
backremaining=calc(c,'Less_DoubleDouble',dist,'ReturnValue',c.get('RetreatStopDistance'),'RetreatStopDistance')
continueback=calc(c,'BooleanAND',wasback,'ReturnValue',backremaining)
checkback=c.branch();seq(checkfar,checkback,'else');link(continueback,'ReturnValue',checkback,'Condition')
wasforward=calc(c,'Greater_DoubleDouble',intent,'SpacingIntent',constant=0)
forwardremaining=calc(c,'Greater_DoubleDouble',dist,'ReturnValue',c.get('ApproachStopDistance'),'ApproachStopDistance')
continueforward=calc(c,'BooleanAND',wasforward,'ReturnValue',forwardremaining)
checkforward=c.branch();seq(checkback,checkforward,'else');link(continueforward,'ReturnValue',checkforward,'Condition')
idle=c.set('SpacingIntent');val(idle,'SpacingIntent',0);seq(checkforward,idle,'else')
direction=c.fn('/Script/Engine.KismetMathLibrary.GetDirectionUnitVector');link(ploc,'ReturnValue',direction,'From');link(tloc,'ReturnValue',direction,'To')
breakdir=c.fn('/Script/Engine.KismetMathLibrary.BreakVector');link(direction,'ReturnValue',breakdir,'InVec')
flatdir=c.fn('/Script/Engine.KismetMathLibrary.MakeVector');link(breakdir,'X',flatdir,'X');link(breakdir,'Y',flatdir,'Y')
normalize=c.fn('/Script/Engine.KismetMathLibrary.Normal');link(flatdir,'ReturnValue',normalize,'A')
move=c.fn('/Script/Engine.Pawn.AddMovementInput');link(pawn,'ReturnValue',move,'self');link(normalize,'ReturnValue',move,'WorldDirection');link(c.get('SpacingIntent'),'SpacingIntent',move,'ScaleValue')
for n,output in [(back,'then'),(forward,'then'),(checkback,'then'),(checkforward,'then'),(idle,'then')]:seq(n,move,output)
compile_save(controller)

# Attack task: wait for a legal facing/range, start once, then wait for the GA.
task=unreal.load_asset(AI+'BTT_EnemyAttack')
addvars(task,[('AttackStarted','bool',False),('AttackFacingTolerance','real',15.0),('AttackStartDistance','real',200.0)])
t=Graph(task)
events=[n for n in t.ed.list_all_nodes() if isinstance(n,unreal.K2Node_Event)]
t.ed.remove_nodes([n for n in t.ed.list_all_nodes() if not isinstance(n,unreal.K2Node_Event)])
execute=t.ed.find_event_node('ReceiveExecuteAI');ttick=t.ed.find_event_node('ReceiveTickAI');abort=t.ed.find_event_node('ReceiveAbortAI')
t.comment('Wait for target distance and facing, then commit once. Spacing controller handles turning/navigation until GA starts; no snap rotation. Cooldown begins after GA exits.')
reset=t.set('AttackStarted');val(reset,'AttackStarted','false');seq(execute,reset)
started=t.get('AttackStarted');check=t.branch();seq(ttick,check);link(started,'AttackStarted',check,'Condition')
target=t.fn('/Script/AIModule.BTFunctionLibrary.GetBlackboardValueAsActor');link(t.get('TargetKey'),'TargetKey',target,'Key')
v=t.fn('/Script/Engine.KismetSystemLibrary.IsValid');link(target,'ReturnValue',v,'Object')
vc=t.branch();seq(check,vc,'else');link(v,'ReturnValue',vc,'Condition')
fail=t.fn('/Script/AIModule.BTTask_BlueprintBase.FinishExecute');val(fail,'bSuccess','false');seq(vc,fail,'else')
pl=t.fn('/Script/Engine.Actor.K2_GetActorLocation');link(ttick,'ControlledPawn',pl,'self')
tl=t.fn('/Script/Engine.Actor.K2_GetActorLocation');link(target,'ReturnValue',tl,'self')
d=t.fn('/Script/Engine.KismetMathLibrary.Vector_Distance2D');link(pl,'ReturnValue',d,'V1');link(tl,'ReturnValue',d,'V2')
near=calc(t,'LessEqual_DoubleDouble',d,'ReturnValue',t.get('AttackStartDistance'),'AttackStartDistance')
look=t.fn('/Script/Engine.KismetMathLibrary.FindLookAtRotation');link(pl,'ReturnValue',look,'Start');link(tl,'ReturnValue',look,'Target')
rotation=t.fn('/Script/Engine.Actor.K2_GetActorRotation');link(ttick,'ControlledPawn',rotation,'self')
delta=t.fn('/Script/Engine.KismetMathLibrary.NormalizedDeltaRotator');link(look,'ReturnValue',delta,'A');link(rotation,'ReturnValue',delta,'B')
br=t.fn('/Script/Engine.KismetMathLibrary.BreakRotator');link(delta,'ReturnValue',br,'InRot')
absn=t.fn('/Script/Engine.KismetMathLibrary.Abs');link(br,'Yaw',absn,'A')
aligned=calc(t,'LessEqual_DoubleDouble',absn,'ReturnValue',t.get('AttackFacingTolerance'),'AttackFacingTolerance')
legal=calc(t,'BooleanAND',near,'ReturnValue',aligned)
can=t.branch();seq(vc,can);link(legal,'ReturnValue',can,'Condition')
stop=t.fn('/Script/Engine.Controller.StopMovement');seq(can,stop);link(ttick,'OwnerController',stop,'self')
movement=t.fn('/Script/Engine.Pawn.GetMovementComponent');link(ttick,'ControlledPawn',movement,'self')
halt=t.fn('/Script/Engine.MovementComponent.StopMovementImmediately');seq(stop,halt);link(movement,'ReturnValue',halt,'self')
asc=t.fn('/Script/GameplayAbilities.AbilitySystemBlueprintLibrary.GetAbilitySystemComponent');link(ttick,'ControlledPawn',asc,'Actor')
activate=t.fn('/Script/GameplayAbilities.AbilitySystemComponent.TryActivateAbilityByClass');seq(halt,activate);link(asc,'ReturnValue',activate,'self');val(activate,'InAbilityToActivate','/Game/Gameplay/GAS/Abilities/GA_EnemyAttack.GA_EnemyAttack_C')
ok=t.branch();seq(activate,ok);link(activate,'ReturnValue',ok,'Condition');seq(ok,fail,'else')
mark=t.set('AttackStarted');val(mark,'AttackStarted','true');seq(ok,mark)
count=t.fn('/Script/GameplayAbilities.AbilitySystemComponent.GetGameplayTagCount');link(asc,'ReturnValue',count,'self');val(count,'GameplayTag','(TagName="State.Attacking")')
ended=calc(t,'EqualEqual_IntInt',count,'ReturnValue',constant=0)
done=t.branch();seq(check,done);link(ended,'ReturnValue',done,'Condition')
finish=t.fn('/Script/AIModule.BTTask_BlueprintBase.FinishExecute');val(finish,'bSuccess','true');seq(done,finish)
cast=t.cast('BaseCharacter');seq(abort,cast);link(abort,'ControlledPawn',cast,'Object')
cancel=t.fn('/Script/ProjectUnreal.BaseCharacter.CancelAttack');seq(cast,cancel);link(cast,next(str(p.get_pin_name()) for p in cast.list_all_pins() if str(p.get_pin_name()).startswith('As')),cancel,'self')
aborted=t.fn('/Script/AIModule.BTTask_BlueprintBase.FinishAbort');seq(cancel,aborted);seq(cast,aborted,'CastFailed')
compile_save(task)

# Existing MoveTo remains long-range pathfinding; close positioning is owned by the controller.
bt=unreal.load_asset(AI+'BT_EnemyMeleeCombat')
next(x for x in bt.root_node.children[0].decorators if isinstance(x,unreal.BTDecorator_IsAtLocation)).set_editor_property('acceptable_radius',200.0)
move=bt.root_node.children[1].child_composite.children[0].child_task
radius=unreal.ValueOrBBKey_Float();radius.import_text('(DefaultValue=450.0,Key=None)')
move.set_editor_property('acceptable_radius',radius)
assert unreal.EditorAssetLibrary.save_loaded_asset(bt,False)

lung=unreal.load_class(None,'/Game/Gameplay/Notify/ANS/ANS_AttackLungeWindow.ANS_AttackLungeWindow_C')
report={'controller_defaults':{k:v for k,typ,v in params},'montages':[]}
for letter,speed in [('A',100.0),('B',100.0),('C',125.0)]:
    path='/Game/Gameplay/Anims/Combo/Attack_Primary'+letter+'_Montage'
    a=unreal.load_asset(path)
    states=[n.get_editor_property('notify_state_class') for n in unreal.AnimationLibrary.get_animation_notify_events(a)]
    states=[s for s in states if s and s.get_class()==lung]
    assert len(states)==1
    states[0].set_editor_property('LungeSpeed',speed)
    assert unreal.EditorAssetLibrary.save_loaded_asset(a,False)
    report['montages'].append({'path':path,'speed':speed,'start':0.2,'duration':0.4,'nominal_distance':speed*0.4})
a=unreal.load_asset('/Game/Gameplay/Anims/Enemy/AM_EnemyAttack')
states=[n.get_editor_property('notify_state_class') for n in unreal.AnimationLibrary.get_animation_notify_events(a) if n.get_editor_property('notify_state_class') and n.get_editor_property('notify_state_class').get_class()==lung]
if not states:
    unreal.AnimationLibrary.add_animation_notify_track(a,'AttackAdvance')
    state=unreal.AnimationLibrary.add_animation_notify_state_event(a,'AttackAdvance',0.10,0.25,lung)
else:
    assert len(states)==1
    state=states[0]
state.set_editor_property('LungeSpeed',220.0)
assert unreal.EditorAssetLibrary.save_loaded_asset(a,False)
report['montages'].append({'path':a.get_path_name(),'speed':220,'start':0.1,'duration':0.25,'nominal_distance':55})
Path(ROOT/'Saved/Spacing-Implementation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('SPACING_IMPLEMENTATION_SAVED')
