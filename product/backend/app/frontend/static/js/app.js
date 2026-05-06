function app() {
    return {
        // State
        isAuthenticated: false,
        token: localStorage.getItem('dw_token') || null,
        user: null,
        currentPage: 'dashboard',
        loading: false,
        apiStatus: 'checking',
        alertsCount: 0,
        loginLoading: false,
        loginError: '',
        loginForm: { username: '', password: '' },
        pageContent: '',
        pageTitle: 'Dashboard',
        pageSubtitle: 'Vue d\'ensemble de la plateforme SOC',

        // Real-time state
        sseConnected: false,
        dashboardData: { total_events: 0, total_alerts: 0, total_assets: 0, total_agents: 0, critical_alerts: 0, high_alerts: 0 },
        recentAlerts: [],
        recentEvents: [],
        eventSource: null,

        // Helpers
        get headers() {
            return { 'Authorization': `Bearer ${this.token}` };
        },

        // Init
        init() {
            this.checkHealth();
            if (this.token) {
                this.fetchUser();
            }
            setInterval(() => this.checkHealth(), 30000);
            this.connectSSE();
        },

        // Real-time SSE connection
        connectSSE() {
            if (this.eventSource) {
                this.eventSource.close();
            }

            const self = this;
            this.eventSource = new EventSource('/events/stream');

            this.eventSource.onopen = () => {
                self.sseConnected = true;
            };

            this.eventSource.onmessage = (e) => {
                try {
                    const msg = JSON.parse(e.data);
                    if (msg.type === 'dashboard' && msg.data) {
                        const d = msg.data;
                        self.dashboardData = {
                            total_events: d.total_events,
                            total_alerts: d.total_alerts,
                            total_assets: d.total_assets,
                            total_agents: d.total_agents,
                            critical_alerts: d.critical_alerts,
                            high_alerts: d.high_alerts,
                        };
                        self.alertsCount = d.total_alerts;
                        self.recentAlerts = d.alerts || [];
                        self.recentEvents = d.events || [];

                        // If on dashboard page, re-render with new data
                        if (self.currentPage === 'dashboard') {
                            self.renderDashboardWithData(d);
                        }
                    }
                } catch (err) {
                    console.warn('[SSE] parse error:', err);
                }
            };

            this.eventSource.onerror = () => {
                self.sseConnected = false;
                // Reconnect after 5 seconds
                setTimeout(() => self.connectSSE(), 5000);
            };
        },

        // Health check
        async checkHealth() {
            try {
                const r = await fetch('/health');
                const d = await r.json();
                this.apiStatus = d.database === 'ok' ? 'ok' : 'error';
            } catch (e) {
                this.apiStatus = 'error';
            }
        },

        // Auth
        async login() {
            this.loginLoading = true;
            this.loginError = '';
            try {
                const r = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.loginForm)
                });
                if (!r.ok) {
                    const err = await r.json();
                    this.loginError = err.detail || 'Identifiants invalides';
                    return;
                }
                const data = await r.json();
                this.token = data.access_token;
                localStorage.setItem('dw_token', this.token);
                await this.fetchUser();
                this.navigateTo(this.currentPage);
            } catch (e) {
                this.loginError = 'Erreur de connexion au serveur';
            } finally {
                this.loginLoading = false;
            }
        },

        async fetchUser() {
            try {
                const r = await fetch('/auth/me', { headers: this.headers });
                if (r.ok) {
                    this.user = await r.json();
                    this.isAuthenticated = true;
                    this.navigateTo(this.currentPage);
                } else {
                    this.logout();
                }
            } catch (e) {
                this.logout();
            }
        },

        logout() {
            this.token = null;
            this.user = null;
            this.isAuthenticated = false;
            localStorage.removeItem('dw_token');
        },

        // Navigation
        navigate(page) {
            this.currentPage = page;
            this.navigateTo(page);
            window.history.pushState({}, '', '/' + page);
        },

        async navigateTo(page) {
            if (!this.isAuthenticated) return;
            this.loading = true;
            const routes = {
                'dashboard': { title: 'Dashboard', subtitle: 'Vue d\'ensemble de la plateforme SOC', render: this.renderDashboard },
                'alerts': { title: 'Alertes', subtitle: 'Gestion et qualification des alertes SOC', render: this.renderAlerts },
                'events': { title: 'Evenements', subtitle: 'Journal des evenements telemetrique', render: this.renderEvents },
                'assets': { title: 'Actifs', subtitle: 'Inventaire des actifs supervises', render: this.renderAssets },
                'correlations': { title: 'Correlations', subtitle: 'Groupement d\'evenements lies', render: this.renderCorrelations },
                'audit': { title: 'Audit Logs', subtitle: 'Journal de toutes les actions effectuees', render: this.renderAuditLogs },
                'reports': { title: 'Rapports', subtitle: 'Exports et preuves de validation', render: this.renderReports },
            };
            const route = routes[page] || routes['dashboard'];
            this.pageTitle = route.title;
            this.pageSubtitle = route.subtitle;
            this.currentPage = page;
            try {
                await route.render.call(this);
            } catch (e) {
                this.pageContent = `<div class="bg-soc-danger/10 border border-soc-danger rounded-lg p-6"><p class="text-soc-danger">Erreur de chargement: ${e.message}</p></div>`;
            }
            this.loading = false;
        },

        async refreshData() {
            this.navigateTo(this.currentPage);
        },

        async fetchDashboardData() {
            if (!this.isAuthenticated || !this.token) return;
            try {
                const r = await fetch('/reports/dashboard', { headers: this.headers });
                if (r.ok) {
                    const d = await r.json();
                    this.alertsCount = d.active_alerts || 0;
                }
            } catch (e) {}
        },

        // ===================== RENDERERS =====================

        async renderDashboard() {
            const self = this;
            const hdrs = this.headers;
            const [dash, alerts, events, assets] = await Promise.all([
                fetch('/reports/dashboard', { headers: hdrs }).then(r => r.json()),
                fetch('/alerts', { headers: hdrs }).then(r => r.json()),
                fetch('/telemetry/events', { headers: hdrs }).then(r => r.ok ? r.json() : []),
                fetch('/assets', { headers: hdrs }).then(r => r.ok ? r.json() : [])
            ]);

            this.dashboardData = {
                total_events: dash.total_events || 0,
                total_alerts: dash.active_alerts || 0,
                total_assets: dash.total_assets || 0,
                total_agents: dash.total_agents || 0,
                critical_alerts: dash.critical_alerts || 0,
                high_alerts: dash.high_alerts || 0,
            };
            this.alertsCount = dash.active_alerts || 0;

            const recentAlerts = (alerts || []).slice(0, 10);
            const recentEvents = (events || []).slice(0, 10);
            this.recentAlerts = recentAlerts;
            this.recentEvents = recentEvents;

            this.pageContent = this.buildDashboardHTML(this.dashboardData, recentAlerts, recentEvents, dash);
        },

        renderDashboardWithData(data) {
            const self = this;
            const dash = {
                total_events: data.total_events,
                total_alerts: data.total_alerts,
                total_assets: data.total_assets,
                total_agents: data.total_agents,
                critical_alerts: data.critical_alerts,
                high_alerts: data.high_alerts,
                active_alerts: data.total_alerts,
                last_heartbeat: null,
                total_correlations: 0,
            };
            const recentAlerts = (data.alerts || []).slice(0, 10);
            const recentEvents = (data.events || []).slice(0, 10);
            this.recentAlerts = recentAlerts;
            this.recentEvents = recentEvents;

            this.pageContent = this.buildDashboardHTML(this.dashboardData, recentAlerts, recentEvents, dash);
        },

        buildDashboardHTML(dd, recentAlerts, recentEvents, dash) {
            const self = this;
            const pulseClass = this.sseConnected ? 'text-soc-success' : 'text-soc-muted';
            const pulseDot = this.sseConnected ? '<span class="inline-block w-2 h-2 bg-soc-success rounded-full animate-pulse mr-1"></span>' : '';

            let alertRows = recentAlerts.length > 0 ? recentAlerts.map(a => {
                const sevColor = { critical: 'bg-red-500/10 text-red-400 border-red-500/20', high: 'bg-orange-500/10 text-orange-400 border-orange-500/20', medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', low: 'bg-blue-500/10 text-blue-400 border-blue-500/20' }[a.severity] || 'bg-gray-500/10 text-gray-400';
                const statusColor = { new: 'text-red-400', acknowledged: 'text-yellow-400', investigating: 'text-blue-400', resolved: 'text-green-400', closed: 'text-gray-400' }[a.status] || 'text-gray-400';
                return `<tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors">
                    <td class="px-4 py-3"><span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${sevColor}">${a.severity.toUpperCase()}</span></td>
                    <td class="px-4 py-3 text-sm">${a.title}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${a.source_ip || '-'}</td>
                    <td class="px-4 py-3"><span class="text-sm ${statusColor} capitalize">${a.status}</span></td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${self.formatDate(a.created_at || a.ts)}</td>
                </tr>`;
            }).join('') : `<tr><td colspan="5" class="px-4 py-8 text-center text-soc-muted">Aucune alerte</td></tr>`;

            let eventItems = recentEvents.length > 0 ? recentEvents.map(e => `
                <div class="flex items-start gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border">
                    <div class="w-2 h-2 rounded-full mt-1.5 ${e.severity === 'critical' ? 'bg-soc-danger animate-pulse' : e.severity === 'high' ? 'bg-soc-warning' : 'bg-soc-accent'}"></div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm text-white truncate">${e.message || e.event_type}</p>
                        <p class="text-xs text-soc-muted">${e.source_ip || '?'} → ${e.target_ip || '?'} | ${e.event_type}</p>
                    </div>
                    <span class="text-xs text-soc-muted whitespace-nowrap">${self.formatDate(e.observed_at || e.ts)}</span>
                </div>
            `).join('') : '<p class="text-soc-muted text-center py-8">Aucun evenement</p>';

            return `
                <!-- Live indicator -->
                <div class="mb-4 flex items-center gap-2 text-xs ${pulseClass}">
                    ${pulseDot}
                    <span>Temps reel</span>
                    <span class="text-soc-muted">|</span>
                    <span class="text-soc-muted">${new Date().toLocaleTimeString('fr-FR')}</span>
                </div>

                <!-- Metric Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-soc-muted text-sm">Evenements</span>
                            <svg class="w-5 h-5 text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                        </div>
                        <p class="text-3xl font-bold text-white" id="metric-events">${dd.total_events}</p>
                        <p class="text-xs text-soc-muted mt-1">Dernier: ${dash.last_heartbeat ? this.formatDate(dash.last_heartbeat) : 'N/A'}</p>
                    </div>
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-soc-muted text-sm">Alertes actives</span>
                            <svg class="w-5 h-5 text-soc-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                        </div>
                        <p class="text-3xl font-bold text-soc-danger" id="metric-alerts">${dd.total_alerts}</p>
                        <p class="text-xs text-soc-muted mt-1">Critical: ${dd.critical_alerts} | High: ${dd.high_alerts}</p>
                    </div>
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-soc-muted text-sm">Actifs</span>
                            <svg class="w-5 h-5 text-soc-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                        </div>
                        <p class="text-3xl font-bold text-white" id="metric-assets">${dd.total_assets}</p>
                        <p class="text-xs text-soc-muted mt-1">Agents actifs: ${dd.total_agents}</p>
                    </div>
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-soc-muted text-sm">Correlations</span>
                            <svg class="w-5 h-5 text-soc-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                        </div>
                        <p class="text-3xl font-bold text-white" id="metric-correlations">${dash.total_correlations || 0}</p>
                        <p class="text-xs text-soc-muted mt-1">Alertes totales: ${dash.total_alerts || dd.total_alerts}</p>
                    </div>
                </div>

                <!-- Two Column -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Recent Alerts -->
                    <div class="bg-soc-card border border-soc-border rounded-xl">
                        <div class="px-5 py-4 border-b border-soc-border flex items-center justify-between">
                            <h3 class="font-semibold text-white">Alertes recentes</h3>
                            <button onclick="document.querySelector('[x-data]').__x.\$data.navigate('alerts')" class="text-xs text-soc-accent hover:underline">Voir tout</button>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left">
                                <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border">
                                    <th class="px-4 py-3">Severite</th><th class="px-4 py-3">Titre</th><th class="px-4 py-3">Source</th><th class="px-4 py-3">Statut</th><th class="px-4 py-3">Date</th>
                                </tr></thead>
                                <tbody>${alertRows}</tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Recent Events -->
                    <div class="bg-soc-card border border-soc-border rounded-xl">
                        <div class="px-5 py-4 border-b border-soc-border flex items-center justify-between">
                            <h3 class="font-semibold text-white">Evenements recents</h3>
                            <button onclick="document.querySelector('[x-data]').__x.\$data.navigate('events')" class="text-xs text-soc-accent hover:underline">Voir tout</button>
                        </div>
                        <div class="p-5 space-y-3" id="recent-events-list">
                            ${eventItems}
                        </div>
                    </div>
                </div>
            `;
        },

        async renderAlerts() {
            const r = await fetch('/alerts', { headers: this.headers });
            const alerts = r.ok ? await r.json() : [];

            let rows = alerts.length > 0 ? alerts.map(a => {
                const sevColor = { critical: 'bg-red-500/10 text-red-400 border-red-500/20', high: 'bg-orange-500/10 text-orange-400 border-orange-500/20', medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', low: 'bg-blue-500/10 text-blue-400 border-blue-500/20' }[a.severity] || 'bg-gray-500/10 text-gray-400';
                const isResolved = a.status === 'resolved' || a.status === 'closed';
                const statusButtons = isResolved ? '' : `
                    <div class="flex gap-1">
                        ${a.status !== 'acknowledged' ? `<button @click="changeAlertStatus(${a.id}, 'acknowledged')" class="text-xs px-2 py-1 rounded bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 hover:bg-yellow-500/20 transition-colors" title="Acknowledge">Ack</button>` : ''}
                        ${a.status !== 'investigating' ? `<button @click="changeAlertStatus(${a.id}, 'investigating')" class="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-colors" title="Investigate">Inv</button>` : ''}
                        ${a.status !== 'resolved' ? `<button @click="changeAlertStatus(${a.id}, 'resolved')" class="text-xs px-2 py-1 rounded bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20 transition-colors" title="Resolve">Res</button>` : ''}
                    </div>
                `;
                return `<tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors cursor-pointer" onclick="event.target.closest('button') || document.querySelector('[x-data]').__x.\$data.openAlertDetail(${a.id})">
                    <td class="px-4 py-3"><span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${sevColor}">${a.severity.toUpperCase()}</span></td>
                    <td class="px-4 py-3 text-sm text-white">${a.title}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${a.source_ip || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${a.target_ip || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${a.rule_name || '-'}</td>
                    <td class="px-4 py-3"><span class="text-sm capitalize ${a.status === 'new' ? 'text-red-400' : a.status === 'acknowledged' ? 'text-yellow-400' : a.status === 'investigating' ? 'text-blue-400' : a.status === 'resolved' ? 'text-green-400' : 'text-gray-400'}">${a.status}</span></td>
                    <td class="px-4 py-3">${statusButtons}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${this.formatDate(a.created_at)}</td>
                </tr>`;
            }).join('') : `<tr><td colspan="8" class="px-4 py-12 text-center text-soc-muted">
                <svg class="w-12 h-12 mx-auto mb-3 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                Aucune alerte generee pour le moment
            </td></tr>`;

            this.pageContent = `
                <div class="bg-soc-card border border-soc-border rounded-xl">
                    <div class="px-5 py-4 border-b border-soc-border flex items-center justify-between">
                        <h3 class="font-semibold text-white">Toutes les alertes (${alerts.length})</h3>
                        <span class="text-xs text-soc-muted">Cliquez sur Ack/Inv/Res pour changer le statut</span>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left">
                            <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border">
                                <th class="px-4 py-3">Severite</th><th class="px-4 py-3">Titre</th><th class="px-4 py-3">Source</th><th class="px-4 py-3">Cible</th><th class="px-4 py-3">Regle</th><th class="px-4 py-3">Statut</th><th class="px-4 py-3">Actions</th><th class="px-4 py-3">Date</th>
                            </tr></thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </div>
            `;
        },

        async changeAlertStatus(alertId, newStatus) {
            try {
                const r = await fetch(`/alerts/${alertId}/status`, {
                    method: 'PATCH',
                    headers: { ...this.headers, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (r.ok) {
                    await this.renderAlerts();
                    await this.fetchDashboardData();
                } else {
                    console.error('Failed to update alert status:', await r.text());
                }
            } catch (e) {
                console.error('Error updating alert status:', e);
            }
        },

        async renderAuditLogs() {
            const r = await fetch('/alerts/audit', { headers: this.headers });
            const logs = r.ok ? await r.json() : [];

            let rows = logs.length > 0 ? logs.map(log => {
                const actionColor = {
                    'alert_created': 'text-soc-danger',
                    'alert_status_changed': 'text-soc-warning',
                    'alert_resolved': 'text-soc-success',
                    'login_success': 'text-soc-success',
                    'login_failed': 'text-soc-danger',
                }[log.action] || 'text-soc-accent';
                return `<tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors">
                    <td class="px-4 py-3 text-sm font-medium ${actionColor}">${log.action}</td>
                    <td class="px-4 py-3 text-sm text-white">${log.actor || 'system'}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${log.target_type || '-'}${log.target_id ? '#' + log.target_id : ''}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted truncate max-w-xs" title="${log.details || ''}">${log.details || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted whitespace-nowrap">${this.formatDate(log.created_at)}</td>
                </tr>`;
            }).join('') : `<tr><td colspan="5" class="px-4 py-12 text-center text-soc-muted">
                <svg class="w-12 h-12 mx-auto mb-3 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                Aucun journal d'audit
            </td></tr>`;

            this.pageContent = `
                <div class="bg-soc-card border border-soc-border rounded-xl">
                    <div class="px-5 py-4 border-b border-soc-border flex items-center justify-between">
                        <h3 class="font-semibold text-white">Journal d'audit (${logs.length} entrees)</h3>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left">
                            <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border">
                                <th class="px-4 py-3">Action</th><th class="px-4 py-3">Acteur</th><th class="px-4 py-3">Cible</th><th class="px-4 py-3">Details</th><th class="px-4 py-3">Date</th>
                            </tr></thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </div>
            `;
        },

        async renderEvents() {
            const r = await fetch('/telemetry/events', { headers: this.headers });
            const events = r.ok ? await r.json() : [];

            let items = events.length > 0 ? events.slice(0, 50).map(e => {
                const dotColor = { critical: 'bg-soc-danger', high: 'bg-soc-warning', medium: 'bg-soc-accent', low: 'bg-soc-success' }[e.severity] || 'bg-soc-muted';
                return `<div class="flex items-start gap-4 p-4 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors cursor-pointer" onclick="document.querySelector('[x-data]').__x.\$data.openEventDetail(${e.id})">
                    <div class="w-3 h-3 rounded-full mt-1 ${dotColor} flex-shrink-0"></div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-sm font-medium text-white">${e.event_type}</span>
                            <span class="text-xs px-2 py-0.5 rounded bg-soc-card text-soc-muted border border-soc-border">${e.severity}</span>
                        </div>
                        <p class="text-sm text-soc-muted">${e.message || ''}</p>
                        <div class="flex items-center gap-4 mt-2 text-xs text-soc-muted">
                            <span>Source: ${e.source_ip || '-'}</span>
                            <span>Cible: ${e.target_ip || '-'}</span>
                            <span>Agent: ${e.agent_id || '-'}</span>
                        </div>
                    </div>
                    <span class="text-xs text-soc-muted whitespace-nowrap">${this.formatDate(e.observed_at)}</span>
                </div>`;
            }).join('') : `<div class="text-center py-12 text-soc-muted">
                <svg class="w-12 h-12 mx-auto mb-3 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                Aucun evenement enregistre
            </div>`;

            this.pageContent = `
                <div class="space-y-3">
                    <div class="bg-soc-card border border-soc-border rounded-xl px-5 py-3 flex items-center justify-between">
                        <span class="text-sm text-soc-muted">${events.length} evenements</span>
                        <div class="flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-soc-danger"></span><span class="text-xs text-soc-muted">Critical</span>
                            <span class="w-2 h-2 rounded-full bg-soc-warning ml-2"></span><span class="text-xs text-soc-muted">High</span>
                            <span class="w-2 h-2 rounded-full bg-soc-accent ml-2"></span><span class="text-xs text-soc-muted">Medium</span>
                            <span class="w-2 h-2 rounded-full bg-soc-success ml-2"></span><span class="text-xs text-soc-muted">Low</span>
                        </div>
                    </div>
                    ${items}
                </div>
            `;
        },

        async renderAssets() {
            const r = await fetch('/assets', { headers: this.headers });
            const assets = r.ok ? await r.json() : [];
            console.log('[renderAssets] status:', r.status, 'count:', assets.length);

            let rows = assets.length > 0 ? assets.map(a => {
                const typeIcon = { server: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z', workstation: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' }[a.asset_type] || 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01';
                return `<tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors">
                    <td class="px-4 py-3">
                        <svg class="w-5 h-5 text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${typeIcon}"/></svg>
                    </td>
                    <td class="px-4 py-3 text-sm font-mono text-white">${a.ip_address}</td>
                    <td class="px-4 py-3 text-sm text-white">${a.hostname || '-'}</td>
                    <td class="px-4 py-3"><span class="text-xs px-2 py-0.5 rounded bg-soc-card text-soc-muted border border-soc-border">${a.asset_type}</span></td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${a.os_guess || '-'}</td>
                    <td class="px-4 py-3"><span class="w-2 h-2 rounded-full ${a.is_active ? 'bg-soc-success' : 'bg-soc-muted'} inline-block mr-1"></span><span class="text-sm ${a.is_active ? 'text-soc-success' : 'text-soc-muted'}">${a.is_active ? 'Actif' : 'Inactif'}</span></td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${this.formatDate(a.last_seen)}</td>
                </tr>`;
            }).join('') : `<tr><td colspan="7" class="px-4 py-12 text-center text-soc-muted">
                <svg class="w-12 h-12 mx-auto mb-3 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                Aucun actif decouvert
            </td></tr>`;

            this.pageContent = `
                <div class="bg-soc-card border border-soc-border rounded-xl">
                    <div class="px-5 py-4 border-b border-soc-border flex items-center justify-between">
                        <h3 class="font-semibold text-white">Inventaire des actifs (${assets.length})</h3>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left">
                            <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border">
                                <th class="px-4 py-3"></th><th class="px-4 py-3">IP</th><th class="px-4 py-3">Hostname</th><th class="px-4 py-3">Type</th><th class="px-4 py-3">OS</th><th class="px-4 py-3">Statut</th><th class="px-4 py-3">Dernier vu</th>
                            </tr></thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </div>
            `;
        },

        // Detail modals state
        showCorrelationDetail: false,
        correlationDetail: null,
        correlationEvents: [],
        showEventDetail: false,
        eventDetail: null,
        showAlertDetail: false,
        alertDetail: null,

        async openCorrelationDetail(groupId) {
            try {
                const [groupR, eventsR] = await Promise.all([
                    fetch(`/correlation/${groupId}`, { headers: this.headers }),
                    fetch(`/correlation/${groupId}/events`, { headers: this.headers })
                ]);
                if (groupR.ok && eventsR.ok) {
                    this.correlationDetail = await groupR.json();
                    this.correlationEvents = await eventsR.json();
                    this.showCorrelationDetail = true;
                }
            } catch (e) {
                console.error('Correlation detail error:', e);
            }
        },

        closeCorrelationDetail() {
            this.showCorrelationDetail = false;
            this.correlationDetail = null;
            this.correlationEvents = [];
        },

        async resolveCorrelationGroup(groupId) {
            try {
                const r = await fetch(`/correlation/${groupId}/resolve`, {
                    method: 'PATCH',
                    headers: this.headers
                });
                if (r.ok) {
                    await this.closeCorrelationDetail();
                    await this.renderCorrelations();
                }
            } catch (e) {
                console.error('Resolve correlation error:', e);
            }
        },

        exportCorrelationDetail() {
            const g = this.correlationDetail;
            const events = this.correlationEvents;
            if (!g) return;

            const data = {
                correlation_group: g,
                events: events,
                exported_at: new Date().toISOString(),
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `correlation-${g.id}-${new Date().toISOString().slice(0, 10)}.json`;
            a.click();
            URL.revokeObjectURL(url);
        },

        renderCorrelationDetailHTML() {
            const g = this.correlationDetail;
            const events = this.correlationEvents;
            if (!g) return '';

            const sevColor = { critical: 'text-soc-danger', high: 'text-soc-warning', medium: 'text-soc-accent', low: 'text-soc-success' }[g.severity] || 'text-soc-muted';

            const eventRows = events.length > 0 ? events.map(e => `
                <tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors">
                    <td class="px-4 py-3 text-sm text-white">${e.event_type}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${e.source_ip || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${e.target_ip || '-'}</td>
                    <td class="px-4 py-3"><span class="text-xs px-2 py-0.5 rounded ${e.severity === 'critical' ? 'bg-red-500/10 text-red-400' : e.severity === 'high' ? 'bg-orange-500/10 text-orange-400' : e.severity === 'medium' ? 'bg-yellow-500/10 text-yellow-400' : 'bg-blue-500/10 text-blue-400'}">${e.severity}</span></td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${this.formatDate(e.observed_at)}</td>
                </tr>
            `).join('') : `<tr><td colspan="5" class="px-4 py-8 text-center text-soc-muted">Aucun evenement dans ce groupe</td></tr>`;

            const mlScore = g.ml_anomaly_score !== undefined ? `
                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                    <h4 class="text-sm font-medium text-white mb-2 flex items-center gap-2">
                        <svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                        Score ML Anomalie
                    </h4>
                    <div class="flex items-center gap-4">
                        <div class="flex-1 bg-soc-card rounded-full h-3">
                            <div class="h-3 rounded-full ${g.ml_anomaly_score > 0.6 ? 'bg-soc-danger' : g.ml_anomaly_score > 0.4 ? 'bg-soc-warning' : 'bg-soc-success'}" style="width: ${g.ml_anomaly_score * 100}%"></div>
                        </div>
                        <span class="text-lg font-bold ${g.ml_anomaly_score > 0.6 ? 'text-soc-danger' : g.ml_anomaly_score > 0.4 ? 'text-soc-warning' : 'text-soc-success'}">${(g.ml_anomaly_score * 100).toFixed(0)}%</span>
                    </div>
                </div>
            ` : '';

            return `
                <div class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4" @click.self="closeCorrelationDetail()">
                    <div class="bg-soc-card border border-soc-border rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                        <!-- Header -->
                        <div class="px-6 py-4 border-b border-soc-border flex items-center justify-between sticky top-0 bg-soc-card z-10">
                            <div class="flex items-center gap-3">
                                <svg class="w-6 h-6 text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                                <h3 class="text-lg font-bold text-white">Groupe de correlation #${g.id}</h3>
                            </div>
                            <button @click="closeCorrelationDetail()" class="text-soc-muted hover:text-white transition-colors">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                            </button>
                        </div>

                        <!-- Content -->
                        <div class="p-6 space-y-6">
                            <!-- Summary -->
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Type</p>
                                    <p class="text-sm font-medium text-white mt-1">${g.group_type}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Source IP</p>
                                    <p class="text-sm font-mono text-white mt-1">${g.source_ip || '-'}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Evenements</p>
                                    <p class="text-sm font-medium text-white mt-1">${g.event_count || 0}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Severite</p>
                                    <p class="text-sm font-medium ${sevColor} mt-1">${g.severity || '-'}</p>
                                </div>
                            </div>

                            <!-- Status & Actions -->
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <span class="text-sm text-soc-muted">Statut:</span>
                                    <span class="text-sm px-3 py-1 rounded ${g.is_resolved ? 'bg-soc-success/10 text-soc-success border border-soc-success/20' : 'bg-soc-danger/10 text-soc-danger border border-soc-danger/20'}">${g.is_resolved ? 'Resolu' : 'Actif'}</span>
                                </div>
                                <div class="flex gap-2">
                                    ${!g.is_resolved ? `<button @click="resolveCorrelationGroup(${g.id})" class="px-3 py-1.5 bg-soc-success/10 text-soc-success border border-soc-success/20 rounded-lg text-sm hover:bg-soc-success/20 transition-colors">Resoudre</button>` : ''}
                                    <button @click="exportCorrelationDetail()" class="px-3 py-1.5 bg-soc-accent/10 text-soc-accent border border-soc-accent/20 rounded-lg text-sm hover:bg-soc-accent/20 transition-colors">Export JSON</button>
                                    <button @click="closeCorrelationDetail()" class="px-3 py-1.5 bg-soc-bg text-soc-muted border border-soc-border rounded-lg text-sm hover:text-white transition-colors">Fermer</button>
                                </div>
                            </div>

                            <!-- ML Score -->
                            ${mlScore}

                            <!-- Events Table -->
                            <div>
                                <h4 class="text-sm font-medium text-white mb-3">Evenements correles (${events.length})</h4>
                                <div class="bg-soc-bg rounded-lg border border-soc-border overflow-hidden">
                                    <table class="w-full text-left">
                                        <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border bg-soc-card">
                                            <th class="px-4 py-3">Type</th><th class="px-4 py-3">Source</th><th class="px-4 py-3">Cible</th><th class="px-4 py-3">Severite</th><th class="px-4 py-3">Date</th>
                                        </tr></thead>
                                        <tbody>${eventRows}</tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        },

        async openEventDetail(eventId) {
            try {
                const r = await fetch(`/telemetry/events/${eventId}`, { headers: this.headers });
                if (r.ok) {
                    this.eventDetail = await r.json();
                    this.showEventDetail = true;
                }
            } catch (e) {
                console.error('Event detail error:', e);
            }
        },

        closeEventDetail() {
            this.showEventDetail = false;
            this.eventDetail = null;
        },

        exportEventDetail() {
            const e = this.eventDetail;
            if (!e) return;

            const blob = new Blob([JSON.stringify(e, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `event-${e.id}-${new Date().toISOString().slice(0, 10)}.json`;
            a.click();
            URL.revokeObjectURL(url);
        },

        renderEventDetailHTML() {
            const e = this.eventDetail;
            if (!e) return '';

            const dotColor = { critical: 'bg-soc-danger', high: 'bg-soc-warning', medium: 'bg-soc-accent', low: 'bg-soc-success' }[e.severity] || 'bg-soc-muted';
            const sevColor = { critical: 'text-soc-danger', high: 'text-soc-warning', medium: 'text-soc-accent', low: 'text-soc-success' }[e.severity] || 'text-soc-muted';

            let rawPayload = '-';
            if (e.raw_payload) {
                try {
                    rawPayload = `<pre class="text-xs text-soc-muted bg-soc-card p-3 rounded-lg border border-soc-border overflow-x-auto">${JSON.stringify(typeof e.raw_payload === 'string' ? JSON.parse(e.raw_payload) : e.raw_payload, null, 2)}</pre>`;
                } catch {
                    rawPayload = `<pre class="text-xs text-soc-muted bg-soc-card p-3 rounded-lg border border-soc-border overflow-x-auto">${e.raw_payload}</pre>`;
                }
            }

            return `
                <div class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4" @click.self="closeEventDetail()">
                    <div class="bg-soc-card border border-soc-border rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
                        <!-- Header -->
                        <div class="px-6 py-4 border-b border-soc-border flex items-center justify-between sticky top-0 bg-soc-card z-10">
                            <div class="flex items-center gap-3">
                                <div class="w-3 h-3 rounded-full ${dotColor}"></div>
                                <h3 class="text-lg font-bold text-white">Evenement #${e.id}</h3>
                            </div>
                            <div class="flex items-center gap-2">
                                <button @click="exportEventDetail()" class="text-xs px-2 py-1 rounded bg-soc-accent/10 text-soc-accent border border-soc-accent/20 hover:bg-soc-accent/20 transition-colors">Export</button>
                                <button @click="closeEventDetail()" class="text-soc-muted hover:text-white transition-colors">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                                </button>
                            </div>
                        </div>

                        <!-- Content -->
                        <div class="p-6 space-y-6">
                            <!-- Summary -->
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Type</p>
                                    <p class="text-sm font-medium text-white mt-1">${e.event_type}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Severite</p>
                                    <p class="text-sm font-medium ${sevColor} mt-1">${e.severity}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Source</p>
                                    <p class="text-sm font-mono text-white mt-1">${e.source_ip || '-'}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Cible</p>
                                    <p class="text-sm font-mono text-white mt-1">${e.target_ip || '-'}</p>
                                </div>
                            </div>

                            <!-- Message -->
                            <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                <h4 class="text-sm font-medium text-white mb-2">Message</h4>
                                <p class="text-sm text-soc-muted">${e.message || 'Aucun message'}</p>
                            </div>

                            <!-- Metadata -->
                            <div class="grid grid-cols-2 gap-4">
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Agent ID</p>
                                    <p class="text-sm font-mono text-white mt-1">${e.agent_id || '-'}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Observé le</p>
                                    <p class="text-sm text-white mt-1">${this.formatDate(e.observed_at)}</p>
                                </div>
                            </div>

                            <!-- Raw Payload -->
                            <div>
                                <h4 class="text-sm font-medium text-white mb-2">Raw Payload</h4>
                                ${rawPayload}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        },

        async openAlertDetail(alertId) {
            try {
                const r = await fetch(`/alerts/${alertId}`, { headers: this.headers });
                if (r.ok) {
                    this.alertDetail = await r.json();
                    this.showAlertDetail = true;
                }
            } catch (e) {
                console.error('Alert detail error:', e);
            }
        },

        closeAlertDetail() {
            this.showAlertDetail = false;
            this.alertDetail = null;
        },

        exportAlertDetail() {
            const a = this.alertDetail;
            if (!a) return;

            const blob = new Blob([JSON.stringify(a, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const exp = document.createElement('a');
            exp.href = url;
            exp.download = `alert-${a.id}-${new Date().toISOString().slice(0, 10)}.json`;
            exp.click();
            URL.revokeObjectURL(url);
        },

        async changeAlertStatusFromDetail(alertId, newStatus) {
            try {
                const r = await fetch(`/alerts/${alertId}/status`, {
                    method: 'PATCH',
                    headers: { ...this.headers, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (r.ok) {
                    await this.openAlertDetail(alertId);
                    await this.renderAlerts();
                    await this.fetchDashboardData();
                }
            } catch (e) {
                console.error('Error updating alert status:', e);
            }
        },

        renderAlertDetailHTML() {
            const a = this.alertDetail;
            if (!a) return '';

            const sevColor = { critical: 'text-soc-danger', high: 'text-soc-warning', medium: 'text-soc-accent', low: 'text-soc-success' }[a.severity] || 'text-soc-muted';
            const statusColor = { new: 'text-red-400', acknowledged: 'text-yellow-400', investigating: 'text-blue-400', resolved: 'text-green-400', closed: 'text-gray-400' }[a.status] || 'text-gray-400';

            const relatedEvents = (a.related_events || []).slice(0, 20);
            const eventRows = relatedEvents.length > 0 ? relatedEvents.map(e => `
                <tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors cursor-pointer" onclick="document.querySelector('[x-data]').__x.\$data.closeAlertDetail(); setTimeout(() => document.querySelector('[x-data]').__x.\$data.openEventDetail(${e.id}), 200)">
                    <td class="px-4 py-3 text-sm text-white">${e.event_type}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${e.source_ip || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${e.target_ip || '-'}</td>
                    <td class="px-4 py-3"><span class="text-xs px-2 py-0.5 rounded ${e.severity === 'critical' ? 'bg-red-500/10 text-red-400' : e.severity === 'high' ? 'bg-orange-500/10 text-orange-400' : e.severity === 'medium' ? 'bg-yellow-500/10 text-yellow-400' : 'bg-blue-500/10 text-blue-400'}">${e.severity}</span></td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${this.formatDate(e.observed_at)}</td>
                </tr>
            `).join('') : `<tr><td colspan="5" class="px-4 py-8 text-center text-soc-muted">Aucun evenement lie</td></tr>`;

            const correlations = a.related_correlations || [];
            const corrCards = correlations.length > 0 ? correlations.map(g => `
                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border cursor-pointer hover:border-soc-accent/50 transition-colors" onclick="document.querySelector('[x-data]').__x.\$data.closeAlertDetail(); setTimeout(() => document.querySelector('[x-data]').__x.\$data.openCorrelationDetail(${g.id}), 200)">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium text-white">Groupe #${g.id} - ${g.group_type}</span>
                        <span class="text-xs px-2 py-0.5 rounded ${g.is_resolved ? 'bg-soc-success/10 text-soc-success' : 'bg-soc-danger/10 text-soc-danger'}">${g.is_resolved ? 'resolu' : 'actif'}</span>
                    </div>
                    <div class="flex items-center gap-4 text-xs text-soc-muted">
                        <span>Events: ${g.event_count}</span>
                        <span>Severite: ${g.severity}</span>
                        ${g.ml_anomaly_score !== undefined ? `<span>ML: ${(g.ml_anomaly_score * 100).toFixed(0)}%</span>` : ''}
                    </div>
                </div>
            `).join('') : '<p class="text-sm text-soc-muted">Aucune correlation liee</p>';

            return `
                <div class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4" @click.self="closeAlertDetail()">
                    <div class="bg-soc-card border border-soc-border rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                        <!-- Header -->
                        <div class="px-6 py-4 border-b border-soc-border flex items-center justify-between sticky top-0 bg-soc-card z-10">
                            <div class="flex items-center gap-3">
                                <svg class="w-6 h-6 text-soc-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                                <h3 class="text-lg font-bold text-white">Alerte #${a.id}</h3>
                            </div>
                            <div class="flex items-center gap-2">
                                <button @click="exportAlertDetail()" class="text-xs px-2 py-1 rounded bg-soc-accent/10 text-soc-accent border border-soc-accent/20 hover:bg-soc-accent/20 transition-colors">Export</button>
                                <button @click="closeAlertDetail()" class="text-soc-muted hover:text-white transition-colors">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                                </button>
                            </div>
                        </div>

                        <!-- Content -->
                        <div class="p-6 space-y-6">
                            <!-- Summary -->
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Severite</p>
                                    <p class="text-sm font-medium ${sevColor} mt-1">${a.severity}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Statut</p>
                                    <p class="text-sm font-medium ${statusColor} capitalize mt-1">${a.status}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Source</p>
                                    <p class="text-sm font-mono text-white mt-1">${a.source_ip || '-'}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Cible</p>
                                    <p class="text-sm font-mono text-white mt-1">${a.target_ip || '-'}</p>
                                </div>
                            </div>

                            <!-- Title & Rule -->
                            <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                <h4 class="text-sm font-medium text-white mb-1">${a.title}</h4>
                                ${a.rule_name ? `<p class="text-xs text-soc-muted">Regle: ${a.rule_name}</p>` : ''}
                                ${a.description ? `<p class="text-sm text-soc-muted mt-2">${a.description}</p>` : ''}
                            </div>

                            <!-- Timeline -->
                            <div class="grid grid-cols-2 gap-4">
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Creee le</p>
                                    <p class="text-sm text-white mt-1">${this.formatDate(a.created_at)}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Mis a jour le</p>
                                    <p class="text-sm text-white mt-1">${this.formatDate(a.updated_at)}</p>
                                </div>
                            </div>

                            <!-- Actions -->
                            <div class="flex items-center justify-between">
                                <div class="flex gap-2 text-xs text-soc-muted">
                                    <span>Events lies: <span class="text-white">${a.event_count || 0}</span></span>
                                    <span>|</span>
                                    <span>Correlations: <span class="text-white">${a.correlation_count || 0}</span></span>
                                </div>
                                <div class="flex gap-2">
                                    ${a.status !== 'acknowledged' ? `<button @click="changeAlertStatusFromDetail(${a.id}, 'acknowledged')" class="px-3 py-1.5 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded-lg text-sm hover:bg-yellow-500/20 transition-colors">Acknowledge</button>` : ''}
                                    ${a.status !== 'investigating' ? `<button @click="changeAlertStatusFromDetail(${a.id}, 'investigating')" class="px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg text-sm hover:bg-blue-500/20 transition-colors">Investigate</button>` : ''}
                                    ${a.status !== 'resolved' ? `<button @click="changeAlertStatusFromDetail(${a.id}, 'resolved')" class="px-3 py-1.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded-lg text-sm hover:bg-green-500/20 transition-colors">Resolve</button>` : ''}
                                </div>
                            </div>

                            <!-- Related Events -->
                            <div>
                                <h4 class="text-sm font-medium text-white mb-3">Evenements lies (${relatedEvents.length})</h4>
                                <div class="bg-soc-bg rounded-lg border border-soc-border overflow-hidden">
                                    <table class="w-full text-left">
                                        <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border bg-soc-card">
                                            <th class="px-4 py-3">Type</th><th class="px-4 py-3">Source</th><th class="px-4 py-3">Cible</th><th class="px-4 py-3">Severite</th><th class="px-4 py-3">Date</th>
                                        </tr></thead>
                                        <tbody>${eventRows}</tbody>
                                    </table>
                                </div>
                            </div>

                            <!-- Related Correlations -->
                            <div>
                                <h4 class="text-sm font-medium text-white mb-3">Correlations liees (${correlations.length})</h4>
                                <div class="space-y-2">
                                    ${corrCards}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        },

        async renderCorrelations() {
            const r = await fetch('/correlation', { headers: this.headers });
            const groups = r.ok ? await r.json() : [];

            let cards = groups.length > 0 ? groups.map(g => {
                const typeColor = g.group_type === 'ip_source' ? 'text-soc-accent' : 'text-soc-warning';
                const mlBadge = g.ml_anomaly_score !== undefined ? `
                    <div class="mt-3 pt-3 border-t border-soc-border">
                        <div class="flex items-center justify-between text-xs">
                            <span class="text-soc-muted flex items-center gap-1">
                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                                ML Anomaly
                            </span>
                            <span class="font-mono ${g.ml_anomaly_score > 0.6 ? 'text-soc-danger' : g.ml_anomaly_score > 0.4 ? 'text-soc-warning' : 'text-soc-success'}">${(g.ml_anomaly_score * 100).toFixed(0)}%</span>
                        </div>
                        <div class="w-full bg-soc-bg rounded-full h-1.5 mt-1">
                            <div class="h-1.5 rounded-full ${g.ml_anomaly_score > 0.6 ? 'bg-soc-danger' : g.ml_anomaly_score > 0.4 ? 'bg-soc-warning' : 'bg-soc-success'}" style="width: ${g.ml_anomaly_score * 100}%"></div>
                        </div>
                    </div>
                ` : `
                    <div class="mt-3 pt-3 border-t border-soc-border">
                        <button onclick="document.querySelector('[x-data]').__x.\$data.mlEnrichGroup(${g.id})" class="text-xs text-soc-accent hover:underline flex items-center gap-1">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                            Analyser avec ML
                        </button>
                    </div>
                `;
                return `<div class="bg-soc-card border border-soc-border rounded-xl p-5 hover:border-soc-accent/50 transition-colors cursor-pointer" onclick="document.querySelector('[x-data]').__x.\$data.openCorrelationDetail(${g.id})">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2">
                            <svg class="w-5 h-5 ${typeColor}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                            <span class="text-sm font-medium text-white">Groupe #${g.id} - ${g.group_type}</span>
                        </div>
                        <span class="text-xs px-2 py-0.5 rounded ${g.is_resolved ? 'bg-soc-success/10 text-soc-success' : 'bg-soc-danger/10 text-soc-danger'}">${g.is_resolved ? 'resolved' : 'active'}</span>
                    </div>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between"><span class="text-soc-muted">Source IP</span><span class="text-white font-mono">${g.source_ip || '-'}</span></div>
                        <div class="flex justify-between"><span class="text-soc-muted">Evenements</span><span class="text-white">${g.event_count || 0}</span></div>
                        <div class="flex justify-between"><span class="text-soc-muted">Severite</span><span class="text-white">${g.severity || '-'}</span></div>
                    </div>
                    ${mlBadge}
                </div>`;
            }).join('') : `<div class="bg-soc-card border border-soc-border rounded-xl p-12 text-center">
                <svg class="w-16 h-16 mx-auto mb-4 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                <h3 class="text-lg font-medium text-white mb-2">Aucune correlation</h3>
                <p class="text-soc-muted text-sm">Les correlations seront creees automatiquement lors de la detection d'evenements lies par IP source ou fenetre temporelle.</p>
            </div>`;

            this.pageContent = `
                <div>
                    <!-- ML Summary Banner -->
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5 mb-6">
                        <div class="flex items-center gap-3 mb-3">
                            <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                            <h3 class="font-semibold text-white">Detection d'anomalies ML</h3>
                            <span class="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">Isolation Forest</span>
                        </div>
                        <p class="text-xs text-soc-muted mb-4">Analyse comportementale des evenements pour identifier des patterns anormaux non couverts par les regles.</p>
                        <div class="flex gap-3">
                            <button onclick="document.querySelector('[x-data]').__x.\$data.runMlDetection()" class="px-3 py-1.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-lg text-xs hover:bg-purple-500/20 transition-colors">
                                Lancer l'analyse ML
                            </button>
                        </div>
                        <div id="ml-summary-result" class="mt-4 hidden"></div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        ${cards}
                    </div>
                </div>
            `;
        },

        async mlEnrichGroup(groupId) {
            try {
                const r = await fetch(`/correlation/${groupId}/ml-enrich`, {
                    method: 'POST',
                    headers: this.headers
                });
                if (r.ok) {
                    await this.renderCorrelations();
                }
            } catch (e) {
                console.error('ML enrich error:', e);
            }
        },

        async runMlDetection() {
            const resultDiv = document.getElementById('ml-summary-result');
            if (resultDiv) {
                resultDiv.innerHTML = '<p class="text-xs text-soc-muted">Analyse en cours...</p>';
                resultDiv.classList.remove('hidden');
            }

            try {
                const r = await fetch('/correlation/ml-summary', { headers: this.headers });
                if (r.ok) {
                    const data = await r.json();
                    if (resultDiv) {
                        resultDiv.innerHTML = `
                            <div class="grid grid-cols-4 gap-3 text-center">
                                <div class="bg-soc-bg rounded-lg p-3">
                                    <p class="text-2xl font-bold text-white">${data.total}</p>
                                    <p class="text-xs text-soc-muted">Events analyses</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-3">
                                    <p class="text-2xl font-bold text-soc-danger">${data.anomalies}</p>
                                    <p class="text-xs text-soc-muted">Anomalies</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-3">
                                    <p class="text-2xl font-bold text-soc-warning">${(data.anomaly_rate * 100).toFixed(1)}%</p>
                                    <p class="text-xs text-soc-muted">Taux anomalie</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-3">
                                    <p class="text-2xl font-bold text-soc-accent">${(data.avg_score * 100).toFixed(0)}</p>
                                    <p class="text-xs text-soc-muted">Score moyen</p>
                                </div>
                            </div>
                        `;
                    }
                }
            } catch (e) {
                if (resultDiv) {
                    resultDiv.innerHTML = '<p class="text-xs text-soc-danger">Erreur lors de l\'analyse ML</p>';
                }
            }
        },

        async renderReports() {
            this.pageContent = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- CSV Exports -->
                    <div class="bg-soc-card border border-soc-border rounded-xl">
                        <div class="px-5 py-4 border-b border-soc-border">
                            <h3 class="font-semibold text-white">Exports CSV</h3>
                            <p class="text-xs text-soc-muted mt-1">Telecharger les donnees au format CSV</p>
                        </div>
                        <div class="p-5 space-y-3">
                            <a href="/reports/export/alerts/csv" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group">
                                <svg class="w-5 h-5 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                                <div class="flex-1">
                                    <p class="text-sm text-white">Alertes</p>
                                    <p class="text-xs text-soc-muted">Toutes les alertes avec severite et statut</p>
                                </div>
                                <svg class="w-4 h-4 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                            </a>
                            <a href="/reports/export/events/csv" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group">
                                <svg class="w-5 h-5 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                                <div class="flex-1">
                                    <p class="text-sm text-white">Evenements</p>
                                    <p class="text-xs text-soc-muted">Historique des evenements telemetrique</p>
                                </div>
                                <svg class="w-4 h-4 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                            </a>
                            <a href="/reports/export/assets/csv" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group">
                                <svg class="w-5 h-5 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                                <div class="flex-1">
                                    <p class="text-sm text-white">Actifs</p>
                                    <p class="text-xs text-soc-muted">Inventaire complet des actifs</p>
                                </div>
                                <svg class="w-4 h-4 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                            </a>
                        </div>
                    </div>

                    <!-- JSON Exports -->
                    <div class="bg-soc-card border border-soc-border rounded-xl">
                        <div class="px-5 py-4 border-b border-soc-border">
                            <h3 class="font-semibold text-white">Exports JSON</h3>
                            <p class="text-xs text-soc-muted mt-1">Donnees structurees pour analyse</p>
                        </div>
                        <div class="p-5 space-y-3">
                            <a href="/reports/export/alerts/json" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group">
                                <svg class="w-5 h-5 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
                                <div class="flex-1">
                                    <p class="text-sm text-white">Alertes JSON</p>
                                    <p class="text-xs text-soc-muted">Alertes structurees avec metadata</p>
                                </div>
                                <svg class="w-4 h-4 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                            </a>
                        </div>
                    </div>
                </div>
            `;
        },

        // ===================== UTILS =====================

        formatDate(dateStr) {
            if (!dateStr) return '-';
            try {
                const d = new Date(dateStr);
                return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' });
            } catch (e) {
                return dateStr;
            }
        }
    };
}
