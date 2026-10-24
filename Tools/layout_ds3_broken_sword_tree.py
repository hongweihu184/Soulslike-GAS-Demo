"""Position only the new tree's editor nodes via the public reflected int setter.
Read node identities from the standard object export; never access engine memory.
"""
import unreal,re,json
from pathlib import Path
assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
tree=unreal.load_asset('/Game/Gameplay/AI/DS3BrokenSword/BT_DS3BrokenSword')
out=Path(unreal.Paths.project_saved_dir())/'DS3-TreeLayoutExport.t3d'
task=unreal.AssetExportTask();task.object=tree;task.filename=str(out);task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.ObjectExporterT3D();assert unreal.Exporter.run_asset_export_task(task)
stack=[];mapping={};rootgraph=None
for line in out.read_text(encoding='utf-8-sig').splitlines():
 if line.strip().startswith('Begin Object'):
  m=re.search(r'Name="([^"]+)"',line);stack.append(m.group(1) if m else '')
  if 'BehaviorTreeGraphNode_Root' in line and m:rootgraph=m.group(1)
 elif line.strip()=='End Object':stack.pop()
 elif 'NodeInstance=' in line and stack and stack[-1].startswith('BehaviorTreeGraphNode'):
  m=re.search(r"NodeInstance=.*?:([^']+)'",line)
  if m:mapping[m.group(1)]=stack[-1]
setter=unreal.get_default_object(unreal.SystemLibrary);leaf=0;positions=[]
def position(name,x,y):
 graphnode=unreal.find_object(None,tree.get_path_name()+':Behavior Tree.'+name);assert graphnode
 graphnode.modify()
 setter.call_method('SetIntPropertyByName',(graphnode,unreal.Name('NodePosX'),int(x)))
 setter.call_method('SetIntPropertyByName',(graphnode,unreal.Name('NodePosY'),int(y)))
 positions.append({'node':name,'x':int(x),'y':int(y)})
def layout(node,depth):
 global leaf
 if isinstance(node,unreal.BTCompositeNode):
  xs=[layout(c.child_composite or c.child_task,depth+1) for c in node.children];x=(min(xs)+max(xs))/2
 else:
  x=leaf*420;leaf+=1
  if isinstance(node,unreal.BTTask_BlueprintBase):node.set_editor_property('bShowPropertyDetails',False)
 name=mapping.get(node.get_name());assert name,node.get_path_name()
 position(name,x,depth*260);return x
x=layout(tree.root_node,1)
assert rootgraph;position(rootgraph,x,0)
assert unreal.EditorAssetLibrary.save_loaded_asset(tree,False)
Path(unreal.Paths.project_saved_dir(),'DS3-TreePositions.json').write_text(json.dumps(positions,indent=2),encoding='utf-8')
print('DS3_SAFE_LAYOUT_SAVED',len(positions))
