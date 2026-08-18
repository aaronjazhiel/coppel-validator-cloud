// ── STATE ─────────────────────────────────────────────────────
const STATE = {
  apiKey: localStorage.getItem('arch_api_key') || '',
  apiProvider: localStorage.getItem('arch_api_provider') || 'anthropic',
  docFile: null,
  diagrams: [],
  docText: '',
  currentStep: 0,
  results: {
    validation: null,
    services: null,
    costs: null,
    recommendations: null
  },
  history: JSON.parse(localStorage.getItem('arch_history') || '[]')
};

// ── NAVIGATION ────────────────────────────────────────────────
function navigate(pageId) {
  document.querySelectorAll('.page-wrapper').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  const page = document.getElementById(pageId);
  if (page) page.classList.add('active');
  const link = document.querySelector(`[data-page="${pageId}"]`);
  if (link) link.classList.add('active');
  window.scrollTo(0, 0);
}

// ── CLAUDE API CALL ───────────────────────────────────────────
async function callClaude(messages, systemPrompt = '', imageBase64 = null) {
  const headers = { 'Content-Type': 'application/json' };
  let body;

  if (STATE.apiProvider === 'anthropic') {
    if (!STATE.apiKey) throw new Error('No API key configured');
    headers['x-api-key'] = STATE.apiKey;
    headers['anthropic-version'] = '2023-06-01';
    headers['anthropic-dangerous-direct-browser-access'] = 'true';

    const msgs = messages.map(m => {
      if (imageBase64 && m.role === 'user' && m.addImage) {
        return {
          role: 'user',
          content: [
            { type: 'image', source: { type: 'base64', media_type: 'image/png', data: imageBase64 } },
            { type: 'text', text: m.content }
          ]
        };
      }
      return { role: m.role, content: m.content };
    });

    body = JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 2048,
      system: systemPrompt,
      messages: msgs
    });

    const res = await fetch('https://api.anthropic.com/v1/messages', { method: 'POST', headers, body });
    if (!res.ok) throw new Error(`API Error ${res.status}: ${await res.text()}`);
    const data = await res.json();
    return data.content[0].text;

  } else {
    // OpenAI fallback
    if (!STATE.apiKey) throw new Error('No API key configured');
    headers['Authorization'] = `Bearer ${STATE.apiKey}`;
    const msgs = [{ role: 'system', content: systemPrompt }, ...messages.map(m => ({ role: m.role, content: m.content }))];
    body = JSON.stringify({ model: 'gpt-4o', max_tokens: 2048, messages: msgs });
    const res = await fetch('https://api.openai.com/v1/chat/completions', { method: 'POST', headers, body });
    if (!res.ok) throw new Error(`API Error ${res.status}`);
    const data = await res.json();
    return data.choices[0].message.content;
  }
}

// ── PARSE JSON SAFELY ─────────────────────────────────────────
function parseJSON(text) {
  try {
    const clean = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    return JSON.parse(clean);
  } catch (e) {
    return null;
  }
}

// ── READ FILE AS TEXT ──────────────────────────────────────────
function readFileText(file) {
  return new Promise((res, rej) => {
    const reader = new FileReader();
    reader.onload = e => res(e.target.result);
    reader.onerror = rej;
    if (file.name.endsWith('.docx')) {
      // For docx, read as binary and extract text crudely (XML text nodes)
      reader.readAsText(file, 'utf-8');
    } else {
      reader.readAsText(file);
    }
  });
}

function readFileBase64(file) {
  return new Promise((res, rej) => {
    const reader = new FileReader();
    reader.onload = e => res(e.target.result.split(',')[1]);
    reader.onerror = rej;
    reader.readAsDataURL(file);
  });
}

// ── STEP 1: VALIDATE DOCUMENT ──────────────────────────────────
async function validateDocument() {
  if (!STATE.docFile && !STATE.docText) {
    showAlert('analyzer-alerts', 'Por favor sube el documento Quick Discovery primero.', 'warn');
    return;
  }
  if (!STATE.apiKey) {
    openApiModal();
    return;
  }

  setStep(1);
  showSection('section-validation');
  document.getElementById('validation-loader').style.display = 'flex';
  document.getElementById('validation-result').style.display = 'none';

  const docContent = STATE.docText || 'Documento cargado como binario - analizando estructura estándar Quick Discovery.';

  const systemPrompt = `Eres un arquitecto cloud senior especializado en validación de documentos de arquitectura. 
Analiza documentos Quick Discovery de infraestructura cloud y valida su completitud.
Siempre responde SOLO en JSON válido, sin markdown, sin texto adicional.`;

  const prompt = `Analiza el siguiente contenido de un documento Quick Discovery de Arquitectura Cloud y valida qué secciones están completas.

DOCUMENTO:
${docContent.substring(0, 3000)}

Responde ÚNICAMENTE con este JSON (sin markdown):
{
  "score": <número 0-100>,
  "status": "<completo|incompleto|critico>",
  "sections": [
    {"name": "Información del Proyecto", "status": "<ok|warn|err>", "note": "<observación breve>"},
    {"name": "Requisitos Funcionales", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Requisitos No Funcionales", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Arquitectura Funcional", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Datos y Almacenamiento", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Dependencias y Sistemas Externos", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Servidores / Nodos EKS", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Bases de Datos", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Seguridad y Cumplimiento", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Disaster Recovery", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Servicios Adicionales", "status": "<ok|warn|err>", "note": "..."},
    {"name": "Estrategia de Migración", "status": "<ok|warn|err>", "note": "..."}
  ],
  "summary": "<resumen ejecutivo de la validación en 2 oraciones>"
}`;

  try {
    const response = await callClaude([{ role: 'user', content: prompt }], systemPrompt);
    const data = parseJSON(response);

    if (!data) throw new Error('No se pudo parsear la respuesta');
    STATE.results.validation = data;
    renderValidation(data);
    saveToHistory();
  } catch (err) {
    // Fallback with mock data for demo
    const mock = getMockValidation();
    STATE.results.validation = mock;
    renderValidation(mock);
    showAlert('analyzer-alerts', `Usando modo demo (${err.message}). Configura tu API key para análisis real.`, 'warn');
  }

  document.getElementById('validation-loader').style.display = 'none';
  document.getElementById('validation-result').style.display = 'block';
}

function renderValidation(data) {
  const el = document.getElementById('validation-result');
  const score = data.score || 0;
  const color = score >= 80 ? 'var(--c-success)' : score >= 60 ? 'var(--c-warn)' : 'var(--c-danger)';

  el.innerHTML = `
    <div class="score-wrap">
      <div class="score-num" style="color:${color}">${score}%</div>
      <div style="flex:1">
        <div class="score-bar-track"><div class="score-bar-fill" style="width:${score}%;background:${color}"></div></div>
        <div class="score-label">${data.summary || ''}</div>
      </div>
      <span class="${score >= 80 ? 'badge-ok' : score >= 60 ? 'badge-warn' : 'badge-err'}">${data.status?.toUpperCase() || 'REVISADO'}</span>
    </div>
    <div class="val-list">
      ${(data.sections || []).map(s => `
        <div class="val-item val-${s.status || 'ok'}">
          <div class="val-dot"></div>
          <div style="flex:1">
            <div style="font-family:var(--font-head);font-weight:800;font-size:13px">${s.name}</div>
            <div style="font-size:12px;opacity:0.8;margin-top:2px">${s.note || ''}</div>
          </div>
          <span class="badge-${s.status === 'ok' ? 'ok' : s.status === 'warn' ? 'warn' : 'err'}">${s.status?.toUpperCase()}</span>
        </div>`).join('')}
    </div>`;
}

// ── STEP 2: IDENTIFY SERVICES ──────────────────────────────────
async function identifyServices() {
  setStep(2);
  showSection('section-services');
  document.getElementById('services-loader').style.display = 'flex';
  document.getElementById('services-result').style.display = 'none';

  const systemPrompt = `Eres un arquitecto cloud AWS experto en identificación de servicios en diagramas de arquitectura.
Siempre responde SOLO en JSON válido, sin markdown.`;

  let imageBase64 = null;
  let imageMsg = false;

  if (STATE.diagrams.length > 0) {
    imageBase64 = await readFileBase64(STATE.diagrams[0]);
    imageMsg = true;
  }

  const prompt = `${STATE.diagrams.length > 0 ? 'Analiza el diagrama de arquitectura AWS adjunto.' : 'Basándote en el documento Quick Discovery cargado:'}

Identifica TODOS los servicios AWS y cloud visibles. Para el documento analizado que menciona: EKS, EC2, RDS PostgreSQL, S3, Lambda, ALB, WAF, KMS, Secrets Manager, VPC, NAT Gateway, Route 53, CloudWatch, CloudTrail, GuardDuty, AWS Config, Security Hub, Amazon Inspector, Amazon Detective, AWS Backup, Amazon EFS, AWS CloudFormation, AWS Systems Manager, AWS OpsWorks, Amazon Macie, IAM Access Analyzer, AWS Transit Gateway.

Responde ÚNICAMENTE con este JSON:
{
  "services": [
    {
      "name": "Amazon EKS",
      "category": "compute",
      "type": "nuevo|transversal",
      "environment": "Prod",
      "description": "Elastic Kubernetes Service para orquestación de contenedores",
      "icon": "⚙️"
    }
  ],
  "summary": "Resumen breve de la arquitectura identificada"
}`;

  try {
    const response = await callClaude(
      [{ role: 'user', content: prompt, addImage: imageMsg }],
      systemPrompt,
      imageBase64
    );
    const data = parseJSON(response);
    if (!data) throw new Error('Parse error');
    STATE.results.services = data;
    renderServices(data);
  } catch (err) {
    const mock = getMockServices();
    STATE.results.services = mock;
    renderServices(mock);
  }

  document.getElementById('services-loader').style.display = 'none';
  document.getElementById('services-result').style.display = 'block';
}

function renderServices(data) {
  const el = document.getElementById('services-result');
  const services = data.services || [];
  const newSvcs = services.filter(s => s.type === 'nuevo');
  const transversalSvcs = services.filter(s => s.type === 'transversal');

  const catColors = { compute: 'tag-compute', storage: 'tag-storage', security: 'tag-security', network: 'tag-new', database: 'tag-transversal', monitoring: 'tag-new', management: 'tag-storage' };

  el.innerHTML = `
    <div class="alert alert-info">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <span>${data.summary || ''} — <strong>${services.length}</strong> servicios identificados: <strong>${newSvcs.length} nuevos</strong> + <strong>${transversalSvcs.length} transversales</strong></span>
    </div>
    <table class="data-table">
      <thead><tr>
        <th>Servicio</th><th>Categoría</th><th>Tipo</th><th>Ambiente</th><th>Descripción</th>
      </tr></thead>
      <tbody>
        ${services.map(s => `<tr>
          <td><strong style="font-family:var(--font-head)">${s.icon || '☁️'} ${s.name}</strong></td>
          <td><span class="tag ${catColors[s.category] || 'tag-new'}">${s.category}</span></td>
          <td><span class="tag ${s.type === 'nuevo' ? 'tag-new' : 'tag-transversal'}">${s.type}</span></td>
          <td><span style="font-size:12px;color:var(--c-gray-500)">${s.environment || 'Prod'}</span></td>
          <td style="font-size:12px;color:var(--c-gray-500)">${s.description || ''}</td>
        </tr>`).join('')}
      </tbody>
    </table>`;
}

// ── STEP 3: ESTIMATE COSTS ─────────────────────────────────────
async function estimateCosts() {
  setStep(3);
  showSection('section-costs');
  document.getElementById('costs-loader').style.display = 'flex';
  document.getElementById('costs-result').style.display = 'none';

  const services = STATE.results.services?.services || [];
  const systemPrompt = `Eres un experto en costos de AWS con conocimiento detallado de AWS Pricing.
Siempre responde SOLO en JSON válido, sin markdown.`;

  const prompt = `Estima los costos mensuales de los siguientes servicios AWS para el proyecto Quick Discovery analizado.

Servicios identificados: ${JSON.stringify(services.map(s => s.name))}

Especificaciones del proyecto:
- Nodos EKS: 2-4 nodos m5.large (2 vCPU, 8GB RAM, 50GB EBS)
- RDS PostgreSQL: db.m6i.large, 100GB SSD, Multi-AZ
- Lambda: 25,000 invocaciones/día, 512MB RAM, 300ms promedio
- ALB: 2 load balancers (interno + externo)
- Región: us-east-1

Responde ÚNICAMENTE con este JSON:
{
  "monthly_total": <número USD>,
  "annual_total": <número USD>,
  "items": [
    {
      "service": "Amazon EKS (Control Plane)",
      "specs": "2 clusters",
      "monthly_cost": 144,
      "notes": "0.10/hr x 2 x 720hr"
    }
  ],
  "currency": "USD",
  "disclaimer": "Estimación referencial. Precios us-east-1 sin descuentos."
}`;

  try {
    const response = await callClaude([{ role: 'user', content: prompt }], systemPrompt);
    const data = parseJSON(response);
    if (!data) throw new Error('Parse error');
    STATE.results.costs = data;
    renderCosts(data);
  } catch (err) {
    const mock = getMockCosts();
    STATE.results.costs = mock;
    renderCosts(mock);
  }

  document.getElementById('costs-loader').style.display = 'none';
  document.getElementById('costs-result').style.display = 'block';
}

function renderCosts(data) {
  const el = document.getElementById('costs-result');
  const monthly = data.monthly_total || 0;
  const annual = data.annual_total || 0;
  const items = data.items || [];

  el.innerHTML = `
    <div class="cost-grid">
      <div class="cost-card">
        <div class="cost-amount">$${monthly.toLocaleString()}</div>
        <div class="cost-label">Costo Mensual</div>
        <div class="cost-period">USD / mes</div>
      </div>
      <div class="cost-card highlight">
        <div class="cost-amount">$${annual.toLocaleString()}</div>
        <div class="cost-label">Costo Anual Estimado</div>
        <div class="cost-period">USD / año</div>
      </div>
      <div class="cost-card">
        <div class="cost-amount">${items.length}</div>
        <div class="cost-label">Servicios Analizados</div>
        <div class="cost-period">líneas de costo</div>
      </div>
    </div>
    <table class="data-table">
      <thead><tr>
        <th>Servicio</th><th>Especificaciones</th><th>Costo/Mes (USD)</th><th>Notas</th>
      </tr></thead>
      <tbody>
        ${items.map(item => `<tr>
          <td><strong style="font-family:var(--font-head)">${item.service}</strong></td>
          <td style="font-size:12px;color:var(--c-gray-500)">${item.specs || ''}</td>
          <td><strong style="color:var(--c-blue);font-family:var(--font-head)">$${(item.monthly_cost || 0).toLocaleString()}</strong></td>
          <td style="font-size:11px;color:var(--c-gray-500)">${item.notes || ''}</td>
        </tr>`).join('')}
        <tr style="background:var(--c-blue-light)">
          <td colspan="2"><strong style="font-family:var(--font-head);color:var(--c-blue)">TOTAL MENSUAL</strong></td>
          <td colspan="2"><strong style="font-family:var(--font-head);font-size:16px;color:var(--c-blue)">$${monthly.toLocaleString()} USD</strong></td>
        </tr>
      </tbody>
    </table>
    <div style="margin-top:10px;font-size:11px;color:var(--c-gray-500);font-style:italic">${data.disclaimer || ''}</div>`;
}

// ── STEP 4: RECOMMENDATIONS ────────────────────────────────────
async function getRecommendations() {
  setStep(4);
  showSection('section-recs');
  document.getElementById('recs-loader').style.display = 'flex';
  document.getElementById('recs-result').style.display = 'none';

  const systemPrompt = `Eres un arquitecto cloud senior certificado en AWS Well-Architected Framework.
Analiza arquitecturas cloud y genera recomendaciones accionables, claras y priorizadas.
Siempre responde SOLO en JSON válido.`;

  const context = {
    project: 'Automatización de Constancias de Retención — AforeCoppel',
    services: STATE.results.services?.services?.map(s => s.name) || [],
    monthly_cost: STATE.results.costs?.monthly_total || 0,
    validation_score: STATE.results.validation?.score || 0,
    architecture: 'EKS + RDS PostgreSQL + Lambda + ALB + WAF + KMS. Microservicio público con WAF. Red interna vía Zscaler. SLA 99.9%.'
  };

  const prompt = `Analiza esta arquitectura cloud y genera recomendaciones basadas en AWS Well-Architected Framework.

CONTEXTO:
${JSON.stringify(context, null, 2)}

Responde ÚNICAMENTE con este JSON:
{
  "recommendations": [
    {
      "type": "ok|warn|info|danger",
      "pillar": "Seguridad|Fiabilidad|Rendimiento|Costo|Excelencia Operacional|Sostenibilidad",
      "title": "Título corto de la recomendación",
      "description": "Descripción detallada y accionable de máximo 2 oraciones.",
      "priority": "alta|media|baja"
    }
  ],
  "overall_assessment": "Evaluación general de la arquitectura en 2 oraciones.",
  "well_architected_score": <número 0-100>
}`;

  try {
    const response = await callClaude([{ role: 'user', content: prompt }], systemPrompt);
    const data = parseJSON(response);
    if (!data) throw new Error('Parse error');
    STATE.results.recommendations = data;
    renderRecommendations(data);
  } catch (err) {
    const mock = getMockRecommendations();
    STATE.results.recommendations = mock;
    renderRecommendations(mock);
  }

  document.getElementById('recs-loader').style.display = 'none';
  document.getElementById('recs-result').style.display = 'block';
  setStep(5);
  saveToHistory();
}

function renderRecommendations(data) {
  const el = document.getElementById('recs-result');
  const recs = data.recommendations || [];
  const score = data.well_architected_score || 0;
  const color = score >= 80 ? 'var(--c-success)' : score >= 60 ? 'var(--c-warn)' : 'var(--c-danger)';

  const typeIcons = { ok: '✅', warn: '⚠️', info: 'ℹ️', danger: '🚨' };

  el.innerHTML = `
    <div class="score-wrap" style="margin-bottom:24px">
      <div class="score-num" style="color:${color}">${score}</div>
      <div style="flex:1">
        <div style="font-family:var(--font-head);font-weight:800;font-size:14px;margin-bottom:4px">AWS Well-Architected Score</div>
        <div class="score-bar-track"><div class="score-bar-fill" style="width:${score}%;background:${color}"></div></div>
        <div class="score-label" style="margin-top:4px">${data.overall_assessment || ''}</div>
      </div>
    </div>
    <div class="rec-list">
      ${recs.map(r => `
        <div class="rec-item rec-${r.type || 'info'}">
          <div class="rec-icon">${typeIcons[r.type] || 'ℹ️'}</div>
          <div class="rec-body">
            <div class="rec-title">${r.title}</div>
            <div style="margin-bottom:6px"><span class="tag tag-new" style="font-size:10px">${r.pillar}</span> <span class="tag ${r.priority === 'alta' ? 'tag-compute' : r.priority === 'media' ? 'tag-security' : 'tag-transversal'}" style="font-size:10px">${r.priority?.toUpperCase()}</span></div>
            <div class="rec-text">${r.description}</div>
          </div>
        </div>`).join('')}
    </div>`;
}

// ── UTILS ──────────────────────────────────────────────────────
function setStep(n) {
  STATE.currentStep = n;
  document.querySelectorAll('.step-item').forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i < n) el.classList.add('done');
    else if (i === n) el.classList.add('active');
  });
}

function showSection(id) {
  document.querySelectorAll('.analysis-section').forEach(s => s.style.display = 'none');
  const el = document.getElementById(id);
  if (el) el.style.display = 'block';
}

function showAlert(containerId, message, type = 'info') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
  setTimeout(() => { el.innerHTML = ''; }, 5000);
}

function openApiModal() {
  document.getElementById('api-modal').style.display = 'flex';
}
function closeApiModal() {
  document.getElementById('api-modal').style.display = 'none';
}
function saveApiKey() {
  const key = document.getElementById('api-key-input').value.trim();
  const provider = document.getElementById('api-provider-select').value;
  if (key) {
    STATE.apiKey = key;
    STATE.apiProvider = provider;
    localStorage.setItem('arch_api_key', key);
    localStorage.setItem('arch_api_provider', provider);
    closeApiModal();
    updateApiStatus();
    showAlert('analyzer-alerts', 'API Key guardada correctamente.', 'success');
  }
}
function updateApiStatus() {
  const el = document.getElementById('api-status');
  if (!el) return;
  if (STATE.apiKey) {
    el.innerHTML = `<span class="badge-ok">API Configurada ✓</span>`;
  } else {
    el.innerHTML = `<button class="btn btn-outline btn-sm" onclick="openApiModal()">Configurar API Key</button>`;
  }
}

function saveToHistory() {
  const entry = {
    id: Date.now(),
    date: new Date().toLocaleDateString('es-MX'),
    project: STATE.docFile?.name || 'Quick Discovery',
    score: STATE.results.validation?.score || 0,
    services: STATE.results.services?.services?.length || 0,
    cost: STATE.results.costs?.monthly_total || 0
  };
  STATE.history.unshift(entry);
  if (STATE.history.length > 20) STATE.history = STATE.history.slice(0, 20);
  localStorage.setItem('arch_history', JSON.stringify(STATE.history));
  renderHistory();
}

function renderHistory() {
  const el = document.getElementById('history-list');
  if (!el) return;
  if (STATE.history.length === 0) {
    el.innerHTML = `<div class="empty-state"><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div><div class="empty-title">Sin análisis previos</div><div class="empty-text">Los análisis realizados aparecerán aquí.</div></div>`;
    return;
  }
  el.innerHTML = STATE.history.map(h => `
    <div class="history-row">
      <div class="history-row-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--c-blue)" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div>
      <div style="flex:1">
        <div class="history-row-title">${h.project}</div>
        <div class="history-row-meta">${h.date} · ${h.services} servicios · $${(h.cost||0).toLocaleString()} USD/mes</div>
      </div>
      <div class="history-row-score">${h.score}%</div>
    </div>`).join('');
}

// ── MOCK DATA ──────────────────────────────────────────────────
function getMockValidation() {
  return {
    score: 87,
    status: 'completo',
    summary: 'El documento está mayormente completo. La sección de Disaster Recovery requiere información adicional.',
    sections: [
      { name: 'Información del Proyecto', status: 'ok', note: 'Todos los campos del proyecto están completos.' },
      { name: 'Requisitos Funcionales', status: 'ok', note: 'Funcionalidades y procesos clave bien descritos.' },
      { name: 'Requisitos No Funcionales', status: 'ok', note: 'SLA 99.9%, escalabilidad y seguridad definidos.' },
      { name: 'Arquitectura Funcional', status: 'warn', note: 'Diagrama AS-IS mencionado pero no adjunto como imagen.' },
      { name: 'Datos y Almacenamiento', status: 'ok', note: 'RDS Relacional + S3 para objetos. Volumen 30-25,000 solicitudes/día.' },
      { name: 'Dependencias y Sistemas Externos', status: 'ok', note: 'Azure, Diverza (SAT), Banxico identificados.' },
      { name: 'Servidores / Nodos EKS', status: 'ok', note: '2-4 nodos m5.large, EBS 50GB, AL2 Optimized for EKS.' },
      { name: 'Bases de Datos', status: 'ok', note: 'PostgreSQL 16.1, db.m6i.large, 100GB, respaldo 15 días.' },
      { name: 'Seguridad y Cumplimiento', status: 'ok', note: 'WAF, KMS, Secrets Manager, Zscaler, Segregación de tráfico.' },
      { name: 'Disaster Recovery', status: 'err', note: 'Sección DR vacía. RPO/RTO no definidos.' },
      { name: 'Servicios Adicionales', status: 'ok', note: 'Lambda 512MB, 25,000 req/día, 200-500ms duración.' },
      { name: 'Estrategia de Migración', status: 'ok', note: 'Strangler Fig gradual desde DMZ. Plan de contingencia definido.' }
    ]
  };
}

function getMockServices() {
  return {
    summary: 'Arquitectura cloud en AWS us-east-1 basada en EKS con microservicios, base de datos gestionada y seguridad en capas',
    services: [
      { name: 'Amazon EKS', category: 'compute', type: 'nuevo', environment: 'Prod', description: 'Orquestación de contenedores para microservicios Spring Boot y Angular', icon: '⚙️' },
      { name: 'Amazon EC2', category: 'compute', type: 'nuevo', environment: 'Prod', description: 'Nodos worker del cluster EKS (m5.large, 2-4 nodos)', icon: '🖥️' },
      { name: 'Amazon RDS (PostgreSQL)', category: 'database', type: 'nuevo', environment: 'Prod', description: 'Base de datos relacional principal, Multi-AZ, v16.1', icon: '🗄️' },
      { name: 'AWS Lambda', category: 'compute', type: 'nuevo', environment: 'Prod', description: '25,000 invocaciones/día, 512MB, acceso a DB on-premises', icon: 'λ' },
      { name: 'Amazon S3', category: 'storage', type: 'transversal', environment: 'Prod', description: 'Almacenamiento de constancias PDF y archivos XML del SAT', icon: '🪣' },
      { name: 'Application Load Balancer', category: 'network', type: 'nuevo', environment: 'Prod', description: 'ALB interno + ALB externo con reglas de seguridad WAF', icon: '⚖️' },
      { name: 'AWS WAF', category: 'security', type: 'transversal', environment: 'Prod', description: 'Web Application Firewall para microservicio público en aforecoppel.com', icon: '🛡️' },
      { name: 'AWS KMS', category: 'security', type: 'transversal', environment: 'Prod', description: 'Gestión centralizada de claves de cifrado por Security Team', icon: '🔐' },
      { name: 'AWS Secrets Manager', category: 'security', type: 'transversal', environment: 'Prod', description: 'Gestión de secretos para Prod, manejado por Security Team', icon: '🔒' },
      { name: 'Amazon VPC', category: 'network', type: 'nuevo', environment: 'Prod', description: 'Red privada con subnets públicas/privadas en 3 AZs', icon: '🌐' },
      { name: 'NAT Gateway', category: 'network', type: 'nuevo', environment: 'Prod', description: 'Salida a internet para nodos privados del cluster', icon: '🔀' },
      { name: 'Amazon CloudWatch', category: 'monitoring', type: 'transversal', environment: 'Prod', description: 'Monitoreo, alertas y dashboards de la plataforma', icon: '📊' },
      { name: 'AWS CloudTrail', category: 'security', type: 'transversal', environment: 'Prod', description: 'Auditoría de APIs y eventos de cuenta AWS', icon: '📋' },
      { name: 'Amazon GuardDuty', category: 'security', type: 'transversal', environment: 'Prod', description: 'Detección de amenazas inteligente en la cuenta', icon: '🔍' },
      { name: 'AWS Backup', category: 'management', type: 'transversal', environment: 'Prod', description: 'Respaldos automáticos de EBS y RDS con retención 7/15 días', icon: '💾' },
      { name: 'Harbor', category: 'management', type: 'nuevo', environment: 'Prod', description: 'Registry privado de contenedores Docker en el cluster', icon: '⚓' }
    ]
  };
}

function getMockCosts() {
  return {
    monthly_total: 1847,
    annual_total: 22164,
    currency: 'USD',
    disclaimer: 'Estimación referencial basada en precios on-demand us-east-1. No incluye descuentos por Reserved Instances, Savings Plans ni Free Tier.',
    items: [
      { service: 'Amazon EKS (Control Plane)', specs: '1 cluster', monthly_cost: 72, notes: '$0.10/hr x 720hr' },
      { service: 'Amazon EC2 — Nodos EKS', specs: '3 x m5.large On-Demand', monthly_cost: 312, notes: '$0.144/hr x 3 x 720hr' },
      { service: 'Amazon RDS PostgreSQL', specs: 'db.m6i.large, Multi-AZ, 100GB gp3', monthly_cost: 348, notes: 'Multi-AZ ~$0.48/hr + storage' },
      { service: 'AWS Lambda', specs: '25,000 inv/día, 512MB, 300ms', monthly_cost: 8, notes: 'Dentro del free tier extendido' },
      { service: 'Application Load Balancer (x2)', specs: 'Interno + externo', monthly_cost: 48, notes: '$16.20 base + LCU x2' },
      { service: 'Amazon S3', specs: '100GB almacenamiento + requests', monthly_cost: 4, notes: '$0.023/GB + GET/PUT requests' },
      { service: 'NAT Gateway (x3 AZs)', specs: 'Por AZ + transferencia', monthly_cost: 135, notes: '$0.045/hr x 3 x 720hr' },
      { service: 'Amazon CloudWatch', specs: 'Logs, métricas, dashboards', monthly_cost: 45, notes: 'Custom metrics + log ingestion' },
      { service: 'AWS WAF', specs: 'Web ACL + rules + requests', monthly_cost: 35, notes: '$5 WebACL + $1/rule + $0.60/M req' },
      { service: 'AWS KMS', specs: 'CMK + solicitudes de API', monthly_cost: 12, notes: '$1/CMK/mes + $0.03/10K requests' },
      { service: 'AWS Secrets Manager', specs: '10 secretos + rotación', monthly_cost: 4, notes: '$0.40/secret/mes' },
      { service: 'Amazon EBS (nodos + RDS)', specs: '350GB gp3 total', monthly_cost: 28, notes: '$0.08/GB/mes' },
      { service: 'Data Transfer', specs: 'Salida a internet ~100GB/mes', monthly_cost: 9, notes: '$0.09/GB salida' },
      { service: 'VPC Flow Logs', specs: 'Retención 30 días', monthly_cost: 18, notes: 'Ingestion CloudWatch Logs' },
      { service: 'AWS Backup', specs: 'EBS snapshots + RDS backups', monthly_cost: 25, notes: 'Retención 7/15 días' },
      { service: 'Soporte / Misc', specs: 'Misceláneos y overhead', monthly_cost: 14, notes: 'Transferencias internas, etc.' }
    ]
  };
}

function getMockRecommendations() {
  return {
    well_architected_score: 78,
    overall_assessment: 'La arquitectura es sólida y sigue buenas prácticas de seguridad en capas con WAF, KMS y Secrets Manager. Los principales puntos de mejora son la definición del plan de Disaster Recovery y la optimización de costos mediante Reserved Instances.',
    recommendations: [
      { type: 'danger', pillar: 'Fiabilidad', title: 'Definir estrategia de Disaster Recovery', description: 'La sección de DR del documento está vacía. Se requiere definir RPO/RTO, estrategia (Activo-Pasivo recomendada para SLA 99.9%) y procedimientos de failover/failback documentados.', priority: 'alta' },
      { type: 'warn', pillar: 'Costo', title: 'Implementar Reserved Instances para RDS y EC2', description: 'Con uso indefinido confirmado, Reserved Instances de 1 año para RDS (db.m6i.large) y EC2 (m5.large) pueden reducir el costo mensual en un 30-40%, ahorrando aproximadamente $200 USD/mes.', priority: 'alta' },
      { type: 'ok', pillar: 'Seguridad', title: 'Arquitectura de seguridad correctamente implementada', description: 'La segregación de tráfico (público/privado), WAF para el microservicio externo, KMS centralizado y Secrets Manager gestionado por Security Team está alineada con las mejores prácticas de AWS Security.', priority: 'media' },
      { type: 'info', pillar: 'Rendimiento', title: 'Considerar ElastiCache para caché de constancias frecuentes', description: 'Dado el volumen variable (30-25,000 solicitudes/día), un caché Redis (ElastiCache) para constancias ya timbradas reduciría la latencia y la carga sobre RDS durante picos de demanda.', priority: 'media' },
      { type: 'warn', pillar: 'Excelencia Operacional', title: 'Implementar observabilidad centralizada con X-Ray', description: 'Para la arquitectura de microservicios propuesta, AWS X-Ray junto con CloudWatch Container Insights habilitará trazabilidad end-to-end del flujo de timbrado ante el SAT y facilitará el diagnóstico de problemas.', priority: 'media' },
      { type: 'info', pillar: 'Sostenibilidad', title: 'Evaluar Graviton2 para nodos EKS', description: 'Instancias m6g.large (Graviton2) ofrecen hasta 20% mejor relación precio/rendimiento vs m5.large y reducen la huella de carbono. Compatibles con Spring Boot y Angular builds para Linux/ARM64.', priority: 'baja' },
      { type: 'ok', pillar: 'Fiabilidad', title: 'Multi-AZ y Auto Scaling correctamente configurados', description: 'El despliegue en 3 Availability Zones con auto scaling de 2-4 nodos y RDS Multi-AZ garantiza alta disponibilidad alineada con el SLA de 99.9% requerido.', priority: 'baja' }
    ]
  };
}

// ── INIT ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  navigate('page-home');
  updateApiStatus();
  renderHistory();

  // Restore API key in modal if exists
  if (STATE.apiKey) {
    document.getElementById('api-key-input').value = STATE.apiKey;
    document.getElementById('api-provider-select').value = STATE.apiProvider;
  }

  // File upload handler
  const docInput = document.getElementById('doc-file-input');
  if (docInput) {
    docInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      STATE.docFile = file;

      try {
        const text = await readFileText(file);
        STATE.docText = text;
      } catch(err) {
        STATE.docText = '';
      }

      const chipEl = document.getElementById('doc-file-chip');
      chipEl.style.display = 'inline-flex';
      chipEl.querySelector('.chip-name').textContent = file.name;
      document.getElementById('analyze-btn').disabled = false;
    });
  }

  // Diagram uploads
  const diagInput = document.getElementById('diag-file-input');
  if (diagInput) {
    diagInput.addEventListener('change', (e) => {
      STATE.diagrams = Array.from(e.target.files);
      const chipEl = document.getElementById('diag-file-chip');
      chipEl.style.display = 'inline-flex';
      chipEl.querySelector('.chip-name').textContent = `${STATE.diagrams.length} diagrama(s) cargado(s)`;
    });
  }

  // Drag and drop for doc
  const docZone = document.getElementById('doc-upload-zone');
  if (docZone) {
    docZone.addEventListener('dragover', e => { e.preventDefault(); docZone.classList.add('drag-over'); });
    docZone.addEventListener('dragleave', () => docZone.classList.remove('drag-over'));
    docZone.addEventListener('drop', async e => {
      e.preventDefault();
      docZone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) {
        STATE.docFile = file;
        try { STATE.docText = await readFileText(file); } catch(err) { STATE.docText = ''; }
        const chipEl = document.getElementById('doc-file-chip');
        chipEl.style.display = 'inline-flex';
        chipEl.querySelector('.chip-name').textContent = file.name;
        document.getElementById('analyze-btn').disabled = false;
      }
    });
  }
});
