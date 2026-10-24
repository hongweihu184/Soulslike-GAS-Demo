"""Small editor-only graph builder for the isolated DS3 prototype assets."""
import unreal
AI='/Game/Gameplay/AI/DS3BrokenSword/'
KM='/Script/Engine.KismetMathLibrary.'
BT='/Script/AIModule.BTFunctionLibrary.'
bb=unreal.load_asset(AI+'BB_DS3BrokenSword');keys=list(bb.get_editor_property('keys'))
def selector(name):
 i=next(i for i,k in enumerate(keys) if str(k.get_editor_property('entry_name'))==name)
 s=unreal.BlackboardKeySelector();s.set_editor_property('selected_key_name',name);s.set_editor_property('selected_key_id',i);s.set_editor_property('selected_key_type',keys[i].get_editor_property('key_type').get_class());return s
def pin(n,name):
 p=[p for p in n.list_all_pins() if str(p.get_pin_name())==name]
 assert len(p)==1,(n.get_name(),name,[str(x.get_pin_name()) for x in n.list_all_pins()]);return p[0]
def link(a,an,b,bn):assert pin(a,an).try_create_connection(pin(b,bn)),(a.get_name(),an,b.get_name(),bn)
def val(n,name,v):
 p=pin(n,name);ok=p.set_pin_value(str(v));assert ok or p.get_pin_value()==str(v),(name,v,p.get_pin_value())
def seq(a,b,out='then'):link(a,out,b,'execute');return b
def castout(n):return next(str(p.get_pin_name()) for p in n.list_all_pins() if str(p.get_pin_name()).startswith('As'))
class Graph:
 def __init__(self,name,variables,events):
  variables=list(variables)+[(str(k.get_editor_property('entry_name'))+'Key','key',str(k.get_editor_property('entry_name'))) for k in keys]
  self.b=unreal.load_asset(AI+name);assert self.b
  assert self.b.get_path_name().startswith(AI)
  for n,typ,default in variables:
   try:unreal.get_default_object(self.b.generated_class()).get_editor_property(n)
   except:
    pt=unreal.BlueprintEditorLibrary.get_struct_type(unreal.BlackboardKeySelector.static_struct()) if typ=='key' else unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.AnimMontage.static_class()) if typ=='montage' else unreal.BlueprintEditorLibrary.get_basic_type_by_name(typ)
    assert unreal.BlueprintEditorLibrary.add_member_variable(self.b,n,pt),n
   unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(self.b,n,True)
  unreal.BlueprintEditorLibrary.compile_blueprint(self.b)
  unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([self.b])
  self.g=unreal.BlueprintEditorLibrary.find_event_graph(self.b);self.ed=unreal.BlueprintGraphEditor.get_graph_editor(self.g);assert self.ed
  self.ed.remove_nodes([n for n in self.ed.list_all_nodes() if not isinstance(n,unreal.K2Node_Event)])
  self.events={e:self.ed.find_event_node(e) or unreal.BlueprintEditorLibrary.add_event_override(self.b,e,unreal.IntPoint(0,i*1200)) for i,e in enumerate(events)}
  self.variables=variables;self.i=0
 def pos(self,n):
  assert n;n.set_node_pos(unreal.IntPoint(300+(self.i%8)*350,(self.i//8)*260));self.i+=1;return n
 def fn(self,path):return self.pos(self.ed.add_call_function_node(path))
 def get(self,n,cls=''):return self.pos(self.ed.add_get_member_variable_node(n,cls))
 def set(self,n,cls=''):return self.pos(self.ed.add_set_member_variable_node(n,cls))
 def branch(self,cond=None):
  n=self.pos(self.ed.add_branch_node())
  if cond:link(cond[0],cond[1],n,'Condition')
  return n
 def cast(self,n):return self.pos(self.ed.create_node_from_name(next(t for t in self.ed.list_available_nodes([]) if t.endswith('|CastTo'+n)),unreal.Vector2D(0,0),[]))
 def calc(self,name,a,ap='ReturnValue',b=None,bp='ReturnValue',constant=None):
  n=self.fn(KM+name);link(a,ap,n,'A')
  if b is not None:link(b,bp,n,'B')
  elif constant is not None:val(n,'B',constant)
  return n
 def bbget(self,typ,name):
  n=self.fn(BT+'GetBlackboardValueAs'+typ);link(self.get(name+'Key'),name+'Key',n,'Key');return n
 def bbset(self,typ,name,previous,value=None,source=None,out='then'):
  n=self.fn(BT+'SetBlackboardValueAs'+typ);link(self.get(name+'Key'),name+'Key',n,'Key');seq(previous,n,out)
  if source:link(source[0],source[1],n,'Value')
  elif value is not None:val(n,'Value',str(value).lower() if isinstance(value,bool) else value)
  return n
 def store(self,name,previous,value=None,source=None,out='then'):
  n=self.set(name);seq(previous,n,out)
  if source:link(source[0],source[1],n,name)
  elif value is not None:val(n,name,str(value).lower() if isinstance(value,bool) else value)
  return n
 def finish(self,text):
  self.ed.add_comment_node(text,unreal.Vector2D(0,-250),unreal.Vector2D(2700,160));unreal.BlueprintEditorLibrary.compile_blueprint(self.b)
  errors=self.ed.list_nodes_with_errors();assert not errors,str(errors)
  cdo=unreal.get_default_object(self.b.generated_class())
  for n,typ,default in self.variables:cdo.set_editor_property(n,selector(default) if typ=='key' else default)
  assert unreal.EditorAssetLibrary.save_loaded_asset(self.b,False)
  print('DS3_BP',self.b.get_name(),len(self.ed.list_all_nodes()))
def location(g,node,p):
 n=g.fn('/Script/Engine.Actor.K2_GetActorLocation');link(node,p,n,'self');return n
def distance(g,e):
 target=g.bbget('Actor','TargetActor');pl=location(g,e,'ControlledPawn');tl=location(g,target,'ReturnValue')
 d=g.fn(KM+'Vector_Distance2D');link(pl,'ReturnValue',d,'V1');link(tl,'ReturnValue',d,'V2');return d,pl,tl,target
def now(g):return g.fn('/Script/Engine.GameplayStatics.GetTimeSeconds')
def finish(g,previous,success=True,out='then',abort=False):
 n=g.fn('/Script/AIModule.BTTask_BlueprintBase.'+('FinishAbort' if abort else 'FinishExecute'));seq(previous,n,out)
 if not abort:val(n,'bSuccess',str(success).lower())
 return n
def compare(g,op,node,p='ReturnValue',constant=None,other=None,otherpin='ReturnValue'):
 return g.calc(op,node,p,other,otherpin,constant)
def stop(g,e,previous,out='then'):
 n=g.fn('/Script/Engine.Controller.StopMovement');link(e,'OwnerController',n,'self');seq(previous,n,out);return n
def movement(g,e,previous):
 m=g.fn('/Script/Engine.Pawn.GetMovementComponent');link(e,'ControlledPawn',m,'self');c=g.cast('CharacterMovementComponent');link(m,'ReturnValue',c,'Object');seq(previous,c);return c,castout(c)
def flag(g,prop,obj,op,previous,value):
 n=g.set(prop,'/Script/Engine.CharacterMovementComponent');link(obj,op,n,'self');val(n,prop,str(value).lower());seq(previous,n);return n
