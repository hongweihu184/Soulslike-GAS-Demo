"""Run a saved script through Unreal's official, localhost-only Python bridge.

The editor's Python remote execution setting must already be enabled.
This helper never changes editor settings.
"""
import argparse
import json
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('script', type=Path)
parser.add_argument('--project', default='ProjectUnreal')
args = parser.parse_args()
sys.path.insert(0, 'E:/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python')
import remote_execution

remote = remote_execution.RemoteExecution()
remote.start()
try:
    deadline = time.monotonic() + 8
    matches = []
    while time.monotonic() < deadline:
        matches = [n for n in remote.remote_nodes if n.get('project_name') == args.project]
        if matches:
            break
        time.sleep(0.25)
    if len(matches) != 1:
        raise RuntimeError(f'Expected one {args.project} editor; discovered {remote.remote_nodes}')
    remote.open_command_connection(matches[0]['node_id'])
    result = remote.run_command(args.script.resolve().as_posix(), raise_on_failure=False)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get('success'):
        sys.exit(1)
finally:
    remote.stop()
