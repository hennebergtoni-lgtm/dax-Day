"""Execute actual JS DOM branches in Node; this does not verify browser layout."""
import json
from pathlib import Path
import shutil
import subprocess
import pytest
from test_operator_console_projection import console_sources, project


def test_actual_js_renders_inventory_stale_unknown_and_clears_unreachable_endpoint():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node missing; executable DOM verification unavailable')
    raw,snap,hb,now,_ = console_sources()
    v = project(raw,snap,hb,now)
    v['source_available'] = True
    v['system']['FEED']['state'] = 'STALE'
    v['system']['INVENTORY']['state'] = 'BLOCKED'
    v['broker_inventory'] = {'state':'BLOCKED','rows':[{'kind':'POSITION','symbol':'EXTERNAL','ticket':'123'}]}
    v['blockers'].append('LONG_BLOCKER_'+'x'*4000)
    source = Path('web/operator.js').read_text().split("  el('refresh').addEventListener")[0]
    source += '\n globalThis.consoleTest={render,clear,refresh};})();'
    setup = r'''
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.textContent='';}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
}
const elements={};globalThis.document={getElementById:id=>elements[id]??(elements[id]=new Element(id)),createElement:tag=>new Element(tag)};
const text=e=>e.textContent+e.children.map(text).join(' ');
const check=(value,message)=>{if(!value)throw new Error(message);};
'''
    checks = r'''
consoleTest.render(v);
check(elements.system.children.length===14,'14 system states');
check(text(elements.system).includes('STALE'),'stale visible');
check(text(elements.system).includes('NONE / disabled'),'execution disabled');
check(text(elements.inventory).includes('EXTERNAL'),'external inventory retained');
check(text(elements.blockers).includes('LONG_BLOCKER_'),'long blocker retained');
check(text(elements.monday).includes('USER_AUTH'),'authorization boundary');
globalThis.fetch=async()=>{throw new Error('unreachable');};
(async()=>{await consoleTest.refresh();
 check(!text(elements.inventory).includes('EXTERNAL'),'old inventory cleared');
 check(!text(elements.system).includes('GREEN'),'old green cleared');
 check(text(elements.blockers).includes('RUNTIME_SOURCE_UNAVAILABLE_OR_INVALID'),'failure blocker');
 check(text(elements.system).includes('EXECUTION DISABLED'),'disabled while disconnected');
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
    subprocess.run([node,'-e',setup+source+'\nconst v='+json.dumps(v)+';'+checks],check=True,capture_output=True,text=True)


def test_mobile_layout_contract_wraps_long_evidence_and_preserves_focus_controls():
    html = Path('web/operator.html').read_text()
    css = Path('web/operator.css').read_text()
    for id_ in ('system','inventory','monday','health','freshness','timeline','blockers'):
        assert f'id="{id_}"' in html
    assert 'overflow-wrap:anywhere' in css
    assert 'min-height:44px' in css
    assert '@media(max-width:650px)' in css
    assert html.count('<button') == 1
