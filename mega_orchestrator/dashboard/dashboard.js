const navItems = [
  { id: 'overview', label: 'Overview', i18n: { EN: 'Overview', CZ: 'Přehled' } },
  { id: 'services', label: 'Services', i18n: { EN: 'Services', CZ: 'Služby' } },
  { id: 'vault', label: 'Vault', i18n: { EN: 'Vault', CZ: 'Vault' } },
  { id: 'monitoring', label: 'Monitoring', i18n: { EN: 'Monitoring', CZ: 'Monitoring' } },
  { id: 'logs', label: 'Logs', i18n: { EN: 'Logs', CZ: 'Logy' } },
  { id: 'providers', label: 'Providers', i18n: { EN: 'Providers', CZ: 'Poskytovatelé' } }
];
let theme = 'cockpit-dark';
let lang = 'EN';
function setActiveSection(id) {
  document.querySelectorAll('.dashboard-section').forEach(sec => {
    sec.classList.toggle('active', sec.id === `section-${id}`);
  });
  document.querySelectorAll('.dashboard-nav button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.target === id);
  });
}
function translatePage() {
  document.getElementById('title-platform').textContent = lang === 'EN' ? 'LLMS Control Dashboard' : 'Řídicí panel';
  navItems.forEach(item => {
    const btn = document.querySelector(`.dashboard-nav button[data-target='${item.id}']`);
    if (btn) btn.textContent = item.i18n[lang];
  });
}
function setTheme(id) {
  theme = id;
  document.body.dataset.theme = id;
  document.querySelectorAll('.theme-picker button').forEach(btn => btn.classList.toggle('active', btn.dataset.theme === id));
}
async function fetchOverview() {
  const res = await fetch('/dashboard/api/overview');
  const data = await res.json();
  document.getElementById('overview-health').textContent = `${data.status.toUpperCase()} (uptime ${Math.floor(data.uptime || 0)}s)`;
}
async function fetchServices() {
  const res = await fetch('/dashboard/api/services');
  const payload = await res.json();
  const list = document.getElementById('services-list');
  list.innerHTML = '';
  payload.services.forEach(service => {
    const row = document.createElement('div');
    row.className = 'card';
    row.innerHTML = `<header>${service.name}</header><h3>${service.status}</h3><p>${service.tools.join(', ')}</p>`;
    list.appendChild(row);
  });
}
async function loadVault() {
  const res = await fetch('/dashboard/api/vault/ui');
  const html = await res.text();
  const container = document.getElementById('vault-frame');
  container.innerHTML = html;
}
async function fetchProviders() {
  const res = await fetch('/dashboard/api/providers');
  const data = await res.json();
  document.getElementById('providers-list').textContent = JSON.stringify(data, null, 2);
}
function init() {
  const nav = document.querySelector('.dashboard-nav');
  navItems.forEach(item => {
    const btn = document.createElement('button');
    btn.textContent = item.i18n[lang];
    btn.dataset.target = item.id;
    btn.addEventListener('click', () => setActiveSection(item.id));
    nav.appendChild(btn);
  });
  document.querySelector('.theme-picker button[data-theme="cockpit-dark"]').classList.add('active');
  document.querySelectorAll('.theme-picker button').forEach(btn => btn.addEventListener('click', () => setTheme(btn.dataset.theme)));
  document.getElementById('lang-toggle').addEventListener('click', () => {
    lang = lang === 'EN' ? 'CZ' : 'EN';
    translatePage();
  });
  setActiveSection('overview');
  translatePage();
  setTheme('cockpit-dark');
  fetchOverview();
  fetchServices();
  fetchProviders();
  loadVault();
}
window.addEventListener('DOMContentLoaded', init);
