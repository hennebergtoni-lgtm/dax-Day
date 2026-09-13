'use strict';
(() => {
  const LABELS = ['BOT MODE','HOST','MT5','FEED','CLOCK','ACCOUNT MODE','SYMBOL','PROTECTION','RECONCILIATION','SNAPSHOT AGE','EXECUTION'];
  const STATES = new Set(['GREEN','WARN','BLOCKED','STALE','UNKNOWN','WAITING_EXTERNAL','QUERY_REQUIRED']);
  const el = id => document.getElementById(id);
  const show = value => value === null || value === undefined ? 'UNKNOWN' : typeof value === 'object' ? JSON.stringify(value) : String(value);
  const node = (tag, text, className) => { const n=document.createElement(tag); n.textContent=show(text); if(className)n.className=className; return n; };
  const rows = (id, values) => { const target=el(id); target.replaceChildren(); for(const [key,value] of values){target.append(node('dt',key),node('dd',value));} };
  const list = (id, values) => { el(id).replaceChildren(...(Array.isArray(values)&&values.length ? values : ['UNKNOWN']).map(v=>node('li',v))); };
  const metrics = (id, values) => { el(id).replaceChildren(...values.map(([label,value])=>{const n=node('div','','metric');n.append(node('div',label,'metric-label'),node('div',value,'metric-value'));return n;})); };
  const clear = reason => {
    el('system').replaceChildren(...LABELS.map(label=>{
      const n=node('div','','system-tile '+(label==='EXECUTION'?'BLOCKED':'UNKNOWN'));
      n.append(node('div',label,'system-label'),node('div',label==='EXECUTION'?'BLOCKED':'UNKNOWN','system-state'),node('div','Quelle nicht bestätigt','system-value'));return n;
    }));
    el('commit').textContent='UNKNOWN';el('build-note').textContent='Laufender Bot-Commit nicht bestätigt.';
    el('decision').textContent='UNKNOWN';el('strategy').replaceChildren();el('trade-plan').replaceChildren();
    for(const id of ['decision-evidence','risk','session','reservation','reconciliation','virtual','recovery','context','times','provenance']) rows(id,[['Quelle','UNKNOWN']]);
    list('blockers',[reason,'EXECUTION_SAFETY_UNCONFIRMED']);list('events',[]);
    el('connection').textContent='UNKNOWN · Laufzeitdaten fehlen oder sind ungültig';
  };
  const validate = v => {
    if(!v||v.schema_version!=='DAXLAB_READONLY_OPERATOR_CONSOLE_V1'||v.execution_capability!=='NONE'||v.order_execution_enabled!==false||v.demo_paper_execution_authorized!==false||v.live_authorized!==false||v.shadow_authorized!==true)throw new Error('invalid safety contract');
    if(!v.system||!LABELS.every(k=>v.system[k]&&STATES.has(v.system[k].state)))throw new Error('invalid system states');
    if(!Array.isArray(v.blockers)||!v.blockers.every(x=>typeof x==='string'))throw new Error('invalid blockers');
    return v;
  };
  const render = v => {
    validate(v);
    el('system').replaceChildren(...LABELS.map(label=>{
      const t=v.system[label];const n=node('div','','system-tile '+t.state);
      const value=label==='SNAPSHOT AGE'&&Number.isFinite(v.timestamps?.snapshot_age_seconds)?`${v.timestamps.snapshot_age_seconds.toFixed(1)} s · UNVERIFIED_THRESHOLD`:t.value;
      n.append(node('div',label,'system-label'),node('div',t.state,'system-state'),node('div',value,'system-value'));return n;
    }));
    const c=v.candidate, ts=v.timestamps||{}, b=v.build_identity||{}, r=v.reserved_attempt, p=c?.trade_plan||{}, sx=c?.strategy||{}, rc=v.reconciliation||{}, ctx=v.account_context||{}, risk=v.risk_loss_exposure||{}, rec=v.recovery||{}, lc=v.broker_lifecycle||{};
    el('commit').textContent=show(b.runtime_commit);
    el('build-note').textContent=`${show(b.state)} · Startup: ${show(b.observation?.observed_at)} · kein Webserver-Commit`;
    el('decision').textContent=c?`${show(c.decision?.action)} / ${show(c.admission?.status)}`:'UNKNOWN';
    metrics('strategy',[['Regime',sx.regime],['Structure',sx.structure],['Setup / Entry',sx.setup]]);
    rows('decision-evidence',[['Signal',c?.signal?.direction],['Reason',c?.signal?.reason],['Risk result',c?.decision?.risk_result],['Decision ID',c?.decision?.decision_id],['Snapshot',c?.generated_at]]);
    metrics('trade-plan',[['Entry',p.entry],['Stop',p.stop],['Target',p.target],['RR',p.reward_risk]]);
    list('blockers',v.blockers);
    rows('risk',[['State',risk.state],['Risk policy',risk.risk_policy_fingerprint],['Sizing evidence',risk.sizing_evidence_fingerprint],['Loss admission',risk.loss_admission_evidence_fingerprint],['Loss observation',risk.loss_observation_checkpoint_fingerprint],['Konkrete Werte',risk.values]]);
    const sg=v.session_guard||{};
    rows('session',[['State',sg.state],['Scope',sg.scope],['Session key/date',sg.session_key??sg.session_date],['Consumed/admitted',sg.trades_admitted],['Limit',sg.max_trades_per_session],['Guard fingerprint',sg.checkpoint_fingerprint],['Observation',sg.observed_at]]);
    rows('reservation',[['State',r?.status],['Intent/client ID',r?.intent_id],['Reservation',r?.reservation_fingerprint],['Submission ordinal',r?.submission_ordinal],['Required action',r?.required_next_action],['Resubmit allowed',r?.resubmit_allowed],['Slot release allowed',r?.session_slot_release_allowed]]);
    rows('reconciliation',[['State',rc.state],['Local lifecycle',lc.local_order_state??lc.state],['Venue state',lc.venue_state],['Account inventory complete',rc.account_inventory_complete],['History completeness',rc.history_completeness],['Next action',rc.required_next_action],['Scope',rc.scope]]);
    const vp=c?.virtual_position||{};
    rows('virtual',[['Status',vp.status],['Side',vp.side],['Lifecycle ID',vp.lifecycle_id],['Origin decision',vp.origin_decision_id],['Filled at / price',`${show(vp.filled_at)} / ${show(vp.filled_price)}`],['Closed at / price',`${show(vp.closed_at)} / ${show(vp.exit_price)}`],['Exit reason',vp.exit_reason]]);
    rows('recovery',[['State',rec.state],['Candidate observed state',rec.candidate_observed_state],['Candidate reconciliation',rec.candidate_observed_reconciliation],['Scope',rec.candidate_reconciliation_scope],['Checkpoint',rec.checkpoint_fingerprint]]);
    const econ=v.economics?.observed_symbol_metadata||{};
    rows('context',[['Account mode',ctx.account_mode],['Server',ctx.server],['Account fingerprint',ctx.account_fingerprint],['Symbol',ctx.symbol],['Broker timezone (declared)',v.clock?.broker_timezone],['Timestamp interpretation',v.clock?.timestamp_interpretation],['Session review',v.clock?.session_review_state],['Broker tick time',v.clock?.broker_tick_time],['Clock OK (observed)',v.host_observation?.clock_ok],['Point / digits',`${show(econ.point)} / ${show(econ.digits)}`],['Economics review',v.economics?.verification]]);
    rows('times',[['Backend queried at',v.queried_at_utc],['Snapshot generated at',ts.snapshot_generated_at],['Last CLOSED-M5 close',ts.last_closed_m5_close_time],['Feed observed at',ts.feed_observed_at],['Current feed age (s)',ts.current_feed_age_seconds],['Source feed limit (s)',ts.source_max_feed_age_seconds],['Original bar age (s)',ts.snapshot_measured_bar_age_seconds],['Host observed at',ts.host_observed_at],['Host age (s)',ts.host_age_seconds],['Host threshold',ts.host_age_threshold],['Heartbeat observed at',ts.heartbeat_observed_at]]);
    list('events',c?.runtime?.events);
    rows('provenance',[['Candidate / core',`${show(c?.candidate_id)} / ${show(c?.core_version)}`],['Config fingerprint',c?.config_fingerprint],['Snapshot fingerprint',v.provenance?.snapshot_fingerprint],['Bundle fingerprint',v.provenance?.bundle_fingerprint],['Candidate cycle binding',v.provenance?.candidate_cycle_binding],['Evidence scope',v.provenance?.evidence_kind],['Console fingerprint',v.console_fingerprint]]);
    el('connection').textContent=`${v.source_available===false?'UNKNOWN · Quelle fehlt':'READ-ONLY · Quelle gelesen'} · Backend: ${show(v.queried_at_utc)} · keine Execution-Freigabe`;
  };
  let sequence=0;
  const refresh=async()=>{
    const attempt=++sequence;
    // Discard previous green evidence while querying; failure never keeps it.
    clear('RUNTIME_READ_PENDING');
    try{
      const response=await fetch('/api/operator',{method:'GET',cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(10000)});
      const value=await response.json();
      if(attempt!==sequence)return;
      if(!response.ok||value.source_available!==true)throw new Error('source unavailable');
      render(value);
      el('fetch-time').textContent=`Browser-Abruf: ${new Date().toISOString()} · erneuert keine Runtime-Evidenz`;
    }catch{
      if(attempt===sequence){clear('RUNTIME_SOURCE_UNAVAILABLE_OR_INVALID');el('fetch-time').textContent=`Browser-Abruf fehlgeschlagen: ${new Date().toISOString()}`;}
    }
  };
  el('refresh').addEventListener('click',refresh);
  document.addEventListener('visibilitychange',()=>{if(document.hidden){sequence++;clear('BACKGROUND_VIEW_NOT_CURRENT');}else refresh();});
  // Polling cadence is UX only; NOT a freshness/risk policy or GREEN threshold.
  setInterval(()=>{if(!document.hidden)refresh();},15000);
  refresh();
})();
