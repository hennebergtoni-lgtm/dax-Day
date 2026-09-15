from pathlib import Path


def test_mobile_console_is_read_only_and_uses_dom_text_instead_of_html_payloads():
    html = Path('web/operator.html').read_text()
    js = Path('web/operator.js').read_text()
    css = Path('web/operator.css').read_text()
    assert 'viewport-fit=cover' in html
    assert '@media(max-width:650px)' in css
    assert 'min-height:44px' in css
    assert 'Versionierte Research-Evidenz' in html
    assert 'STATIC ONLY' in html
    assert 'SUPERVISOR STARTUP COMMIT' in html
    assert 'textContent' in js and 'replaceChildren' in js
    assert 'innerHTML' not in js and 'eval(' not in js
    assert "method:'GET'" in js and "credentials:'omit'" in js
    assert "fetch('/api/operator'" in js
    assert 'UNVERIFIED_THRESHOLD' in js
    assert 'no-store' in js
    assert 'clear(' in js and 'BACKGROUND_VIEW_NOT_CURRENT' in js
    assert html.count('<button') == 1
    for value in ('NEON_DATABASE_URL', 'postgresql://', 'MetaTrader5', 'order_send', 'order_execution_enabled=true'):
        assert value not in html + js + css


def test_new_web_boundary_is_implemented_local_but_never_real_host_or_public_health():
    import json
    s = json.loads(Path('web/status.json').read_text())
    assert s['runtime_truth_included'] is False
    assert s['runtime_boundary']['browser_runtime_endpoint'] == 'IMPLEMENTED_LOCAL_GET_ONLY'
    assert s['runtime_boundary']['remote_deployment'] == 'WAITING_EXTERNAL_PROTECTED_ACCESS'
    assert s['readiness']['paper'] == 'BLOCKED'
    assert s['readiness']['live'] == 'BLOCKED'
