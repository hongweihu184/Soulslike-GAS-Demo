import unreal,json,time
from pathlib import Path
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();assert w
d=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_class(None,'/Game/Gameplay/Characters/BP_Dummy.BP_Dummy_C'))[0];p=unreal.GameplayStatics.get_player_character(w,0)
c=d.get_controller();brain=c.get_component_by_class(unreal.BrainComponent);bb=c.get_component_by_class(unreal.BlackboardComponent);dm=d.get_component_by_class(unreal.CharacterMovementComponent)
main=unreal.load_asset('/Game/Gameplay/AI/DS3BrokenSword/BT_DS3BrokenSword');prob=unreal.load_asset('/Game/Gameplay/AI/DS3BrokenSword/Validation/BT_DS3PostProbability')
base=d.get_actor_location();start=unreal.GameplayStatics.get_time_seconds(w);wall=time.monotonic();phase=-1;previous=0;counts={};health=p.get_health_percent();health_samples=[health]
report={'tests':[],'complete':False};out=Path('E:/UE5.8Project/ProjectUnreal/Saved/DS3-ProbabilityVerification.json')
cases=[('far',800,0,{0:.5,1:.125,3:.375}),('mid',300,0,{0:.875,1:.075,2:.05}),('near',100,0,{0:.9,1:.025,2:.075}),('spectator',300,1,{0:.5,2:.5})]
brain.stop_logic('Prepare damage check');d.cancel_attack();c.stop_movement();dm.stop_movement_immediately();d.set_actor_location(base,False,True);d.set_actor_rotation(unreal.Rotator(0,0,0),True);p.set_actor_location(base+unreal.Vector(160,0,0),False,True)
bb.set_value_as_object('TargetActor',p);bb.set_value_as_int('ForcedAction',1);bb.set_value_as_int('TeamRole',0);bb.set_value_as_int('ThinkParamID',110050);brain.restart_logic()
def now():return unreal.GameplayStatics.get_time_seconds(w)
def begin(i):
 global phase,start,previous,counts
 phase=i;start=now();previous=0;counts={};brain.stop_logic('Prepare probability case');d.cancel_attack();c.stop_movement();dm.stop_movement_immediately()
 p.set_actor_enable_collision(False);d.set_actor_location(base,False,True);p.set_actor_location(base+unreal.Vector(cases[i][1],0,0),False,True)
 bb.set_value_as_object('TargetActor',p);bb.set_value_as_int('Action',1);bb.set_value_as_int('TeamRole',cases[i][2]);bb.set_value_as_int('PostCycles',0)
 assert c.run_behavior_tree(prob)
def finish(reason,error=None):
 unreal.unregister_slate_post_tick_callback(handle);brain.stop_logic('Probability checks finished');report['complete']=True;report['reason']=reason;report['exception']=error;report['passed']=reason=='finished' and all(t['passed'] for t in report['tests']);out.write_text(json.dumps(report,indent=2),encoding='utf-8');print('DS3_PROBABILITY',reason,report['passed'])
def tick(dt):
 global phase,previous
 try:
  elapsed=now()-start
  if phase==-1:
   current=p.get_health_percent()
   if abs(current-health_samples[-1])>.0001:health_samples.append(current)
   if elapsed>4:
    drops=[health_samples[i]-health_samples[i+1] for i in range(len(health_samples)-1)]
    report['tests'].append({'name':'proxy_combo_applies_existing_damage_once_per_strike','passed':bool(drops) and all(abs(x-.125)<.002 for x in drops),'health_percent_samples':health_samples,'drops':drops});begin(0)
   return
  counter=bb.get_value_as_int('PostCycles')
  if counter!=previous:
   previous=counter;value=bb.get_value_as_int('AfterAction');counts[value]=counts.get(value,0)+1
  total=sum(counts.values())
  if total>=250:
   expected=cases[phase][3];observed={k:counts.get(k,0)/total for k in set(expected)|set(counts)};passed=all(abs(observed.get(k,0)-v)<.08 for k,v in expected.items()) and all(k in expected for k in counts)
   report['tests'].append({'name':'after_attack_probability_'+cases[phase][0],'passed':passed,'samples':total,'counts':counts,'expected':expected,'observed':observed})
   if phase==len(cases)-1:finish('finished')
   else:begin(phase+1)
  elif elapsed>25:finish('sampling_timeout',{'counter':counter,'counts':counts})
  if time.monotonic()-wall>85:finish('wall_timeout')
 except Exception as ex:finish('exception',repr(ex))
handle=unreal.register_slate_post_tick_callback(tick);print('DS3_DAMAGE_PROBABILITY_STARTED')
