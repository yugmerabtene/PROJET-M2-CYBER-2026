function app() {
    return {
        // i18n
        currentLang: localStorage.getItem('dw_lang') || 'fr',
        translations: {},
        
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
        dockerHealthRefreshTimer: null,
        attackLabConfig: {
            scenario: 'recon_nmap',
            target: 'serveur-endpoint',
            intensity: 'low',
            duration: 60,
        },
        attackPresetLabels: {
            'recon': 'Recon',
            'web': 'Web',
            'bruteforce': 'Bruteforce',
            'dos': 'DoS',
            'kill-chain': 'Kill Chain',
            'other': 'Autres',
        },

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

        // i18n
        async initI18n() {
            try {
                const response = await fetch(`/static/i18n/${this.currentLang}.json`);
                if (response.ok) {
                    this.translations = await response.json();
                }
            } catch (e) {
                console.warn('[i18n] Failed to load translations:', e);
            }
        },
        
        t(key) {
            return this.translations[key] || key;
        },
        
        async switchLang(lang) {
            this.currentLang = lang;
            localStorage.setItem('dw_lang', lang);
            await this.initI18n();
            // Re-render current page with new language
            await this.navigateTo(this.currentPage);
        },
        
        // Init
        init() {
            this.checkHealth();
            this.initI18n();
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
            if (this.dockerHealthRefreshTimer) {
                clearTimeout(this.dockerHealthRefreshTimer);
                this.dockerHealthRefreshTimer = null;
            }
            this.loading = true;
            const routes = {
                'dashboard': { title: 'Dashboard', subtitle: 'Vue d\'ensemble de la plateforme SOC', render: this.renderDashboard },
                'alerts': { title: 'Alertes', subtitle: 'Gestion et qualification des alertes SOC', render: this.renderAlerts },
                'events': { title: 'Evenements', subtitle: 'Journal des evenements telemetrique', render: this.renderEvents },
                'assets': { title: 'Actifs', subtitle: 'Inventaire des actifs supervises', render: this.renderAssets },
                'correlations': { title: 'Correlations', subtitle: 'Groupement d\'evenements lies', render: this.renderCorrelations },
                'attack-lab': { title: 'Attack Lab', subtitle: 'Pilotage des attaques et campagnes de test', render: this.renderAttackLab },
                'docker-health': { title: 'Docker Health', subtitle: 'Etat logique et métriques des services du lab', render: this.renderDockerHealth },
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
        showReportPreview: false,
        reportPreviewTitle: '',
        reportPreviewContent: '',

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

            const relatedAlerts = e.related_alerts || [];
            const relatedAlertCards = relatedAlerts.length > 0 ? relatedAlerts.map(a => `
                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border cursor-pointer hover:border-soc-accent/50 transition-colors" onclick="document.querySelector('[x-data]').__x.$data.closeEventDetail(); setTimeout(() => document.querySelector('[x-data]').__x.$data.openAlertDetail(${a.id}), 200)">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium text-white">Alerte #${a.id}</span>
                        <span class="text-xs px-2 py-0.5 rounded ${a.status === 'resolved' ? 'bg-soc-success/10 text-soc-success' : 'bg-soc-danger/10 text-soc-danger'}">${a.status}</span>
                    </div>
                    <p class="text-sm text-white mb-1">${a.title}</p>
                    <p class="text-xs text-soc-muted">${a.rule_name || '-'} | ${a.severity}</p>
                </div>
            `).join('') : '<p class="text-sm text-soc-muted">Aucune alerte liée</p>';

            const relatedCorrelations = e.related_correlations || [];
            const relatedCorrelationCards = relatedCorrelations.length > 0 ? relatedCorrelations.map(g => `
                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border cursor-pointer hover:border-soc-accent/50 transition-colors" onclick="document.querySelector('[x-data]').__x.$data.closeEventDetail(); setTimeout(() => document.querySelector('[x-data]').__x.$data.openCorrelationDetail(${g.id}), 200)">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium text-white">Corrélation #${g.id}</span>
                        <span class="text-xs px-2 py-0.5 rounded ${g.is_resolved ? 'bg-soc-success/10 text-soc-success' : 'bg-soc-warning/10 text-soc-warning'}">${g.group_type}</span>
                    </div>
                    <p class="text-xs text-soc-muted">Score: ${g.correlation_score || 0} | Events: ${g.event_count || 0} | ${g.severity}</p>
                </div>
            `).join('') : '<p class="text-sm text-soc-muted">Aucune corrélation liée</p>';

            const similarEvents = e.similar_events || [];
            const similarEventRows = similarEvents.length > 0 ? similarEvents.map(s => `
                <tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors cursor-pointer" onclick="document.querySelector('[x-data]').__x.$data.closeEventDetail(); setTimeout(() => document.querySelector('[x-data]').__x.$data.openEventDetail(${s.id}), 200)">
                    <td class="px-4 py-3 text-sm text-white">${s.event_type}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${s.source_ip || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${s.target_ip || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${this.formatDate(s.observed_at)}</td>
                </tr>
            `).join('') : '<tr><td colspan="4" class="px-4 py-8 text-center text-soc-muted">Aucun événement similaire</td></tr>';

            const eventTimelineItems = [
                ...relatedAlerts.map(a => ({
                    kind: 'alert',
                    label: `Alerte #${a.id}`,
                    title: a.title,
                    when: a.created_at,
                    tone: a.severity === 'critical' ? 'bg-soc-danger' : 'bg-soc-warning',
                })),
                ...similarEvents.map(s => ({
                    kind: 'event',
                    label: `Event #${s.id}`,
                    title: s.message || s.event_type,
                    when: s.observed_at,
                    tone: 'bg-soc-accent',
                })),
            ].sort((a, b) => new Date(a.when) - new Date(b.when));
            const eventTimeline = eventTimelineItems.length > 0 ? eventTimelineItems.map(item => `
                <div class="relative pl-6">
                    <div class="absolute left-0 top-1.5 w-2.5 h-2.5 rounded-full ${item.tone}"></div>
                    <div class="absolute left-1 top-4 bottom-[-12px] w-px bg-soc-border"></div>
                    <p class="text-xs text-soc-muted">${this.formatDate(item.when)} · ${item.label}</p>
                    <p class="text-sm text-white">${item.title}</p>
                </div>
            `).join('') : '<p class="text-sm text-soc-muted">Aucune timeline disponible</p>';

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

                            ${e.agent ? `
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Agent</p>
                                    <p class="text-sm text-white mt-1">${e.agent.sensor_id}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Hostname</p>
                                    <p class="text-sm text-white mt-1">${e.agent.hostname || '-'}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Mode</p>
                                    <p class="text-sm text-white mt-1">${e.agent.mode || '-'}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Reçu le</p>
                                    <p class="text-sm text-white mt-1">${this.formatDate(e.received_at)}</p>
                                </div>
                            </div>` : ''}

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

                            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                <div>
                                    <h4 class="text-sm font-medium text-white mb-3">Alertes liées (${relatedAlerts.length})</h4>
                                    <div class="space-y-2">${relatedAlertCards}</div>
                                </div>
                                <div>
                                    <h4 class="text-sm font-medium text-white mb-3">Corrélations liées (${relatedCorrelations.length})</h4>
                                    <div class="space-y-2">${relatedCorrelationCards}</div>
                                </div>
                            </div>

                            <div>
                                <h4 class="text-sm font-medium text-white mb-3">Événements similaires (${similarEvents.length})</h4>
                                <div class="bg-soc-bg rounded-lg border border-soc-border overflow-hidden">
                                    <table class="w-full text-left">
                                        <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border bg-soc-card">
                                            <th class="px-4 py-3">Type</th><th class="px-4 py-3">Source</th><th class="px-4 py-3">Cible</th><th class="px-4 py-3">Date</th>
                                        </tr></thead>
                                        <tbody>${similarEventRows}</tbody>
                                    </table>
                                </div>
                            </div>

                            <div>
                                <h4 class="text-sm font-medium text-white mb-3">Timeline contextuelle</h4>
                                <div class="bg-soc-bg rounded-lg border border-soc-border p-4 space-y-4">
                                    ${eventTimeline}
                                </div>
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

        closeReportPreview() {
            this.showReportPreview = false;
            this.reportPreviewTitle = '';
            this.reportPreviewContent = '';
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
                    </div>
                </div>
            `).join('') : '<p class="text-sm text-soc-muted">Aucune correlation liee</p>';

            const auditLogs = a.audit_logs || [];
            const auditRows = auditLogs.length > 0 ? auditLogs.map(log => `
                <tr class="border-t border-soc-border">
                    <td class="px-4 py-3 text-sm text-white">${log.action}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${log.actor || 'system'}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${log.details || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${this.formatDate(log.created_at)}</td>
                </tr>
            `).join('') : '<tr><td colspan="4" class="px-4 py-8 text-center text-soc-muted">Aucune trace d\'audit</td></tr>';

            let alertRawPayload = '-';
            if (a.raw_payload) {
                try {
                    alertRawPayload = `<pre class="text-xs text-soc-muted bg-soc-card p-3 rounded-lg border border-soc-border overflow-x-auto">${JSON.stringify(typeof a.raw_payload === 'string' ? JSON.parse(a.raw_payload) : a.raw_payload, null, 2)}</pre>`;
                } catch {
                    alertRawPayload = `<pre class="text-xs text-soc-muted bg-soc-card p-3 rounded-lg border border-soc-border overflow-x-auto">${a.raw_payload}</pre>`;
                }
            }

            const alertTimelineItems = [
                ...(a.audit_logs || []).map(log => ({
                    label: log.action,
                    title: log.details || log.action,
                    when: log.created_at,
                    tone: 'bg-soc-accent',
                })),
                ...relatedEvents.map(evt => ({
                    label: evt.event_type,
                    title: evt.message || evt.event_type,
                    when: evt.observed_at,
                    tone: evt.severity === 'critical' ? 'bg-soc-danger' : evt.severity === 'high' ? 'bg-soc-warning' : 'bg-soc-accent',
                })),
            ].sort((x, y) => new Date(x.when) - new Date(y.when));
            const alertTimeline = alertTimelineItems.length > 0 ? alertTimelineItems.map(item => `
                <div class="relative pl-6">
                    <div class="absolute left-0 top-1.5 w-2.5 h-2.5 rounded-full ${item.tone}"></div>
                    <div class="absolute left-1 top-4 bottom-[-12px] w-px bg-soc-border"></div>
                    <p class="text-xs text-soc-muted">${this.formatDate(item.when)} · ${item.label}</p>
                    <p class="text-sm text-white">${item.title}</p>
                </div>
            `).join('') : '<p class="text-sm text-soc-muted">Aucune timeline disponible</p>';

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

                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Première vue</p>
                                    <p class="text-sm text-white mt-1">${this.formatDate(a.first_seen || a.created_at)}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Dernière vue</p>
                                    <p class="text-sm text-white mt-1">${this.formatDate(a.last_seen || a.updated_at)}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Règle</p>
                                    <p class="text-sm text-white mt-1">${a.rule_name || '-'}</p>
                                </div>
                                <div class="bg-soc-bg rounded-lg p-4 border border-soc-border">
                                    <p class="text-xs text-soc-muted">Relations</p>
                                    <p class="text-sm text-white mt-1">${a.event_count || 0} events / ${a.correlation_count || 0} corr.</p>
                                </div>
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

                            <div>
                                <h4 class="text-sm font-medium text-white mb-2">Raw Payload</h4>
                                ${alertRawPayload}
                            </div>

                            <div>
                                <h4 class="text-sm font-medium text-white mb-3">Audit Trail (${auditLogs.length})</h4>
                                <div class="bg-soc-bg rounded-lg border border-soc-border overflow-hidden">
                                    <table class="w-full text-left">
                                        <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border bg-soc-card">
                                            <th class="px-4 py-3">Action</th><th class="px-4 py-3">Acteur</th><th class="px-4 py-3">Détails</th><th class="px-4 py-3">Date</th>
                                        </tr></thead>
                                        <tbody>${auditRows}</tbody>
                                    </table>
                                </div>
                            </div>

                            <div>
                                <h4 class="text-sm font-medium text-white mb-3">Timeline de l'alerte</h4>
                                <div class="bg-soc-bg rounded-lg border border-soc-border p-4 space-y-4">
                                    ${alertTimeline}
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
                const typeColor = g.group_type === 'ip_source' ? 'text-soc-accent' : g.group_type === 'session_flow' ? 'text-purple-400' : 'text-soc-warning';
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
                        <div class="flex justify-between"><span class="text-soc-muted">Score</span><span class="text-white">${g.correlation_score || 0}</span></div>
                    </div>
                </div>`;
            }).join('') : `<div class="bg-soc-card border border-soc-border rounded-xl p-12 text-center">
                <svg class="w-16 h-16 mx-auto mb-4 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                <h3 class="text-lg font-medium text-white mb-2">Aucune correlation</h3>
                <p class="text-soc-muted text-sm">Les correlations seront creees automatiquement lors de la detection d'evenements lies par IP source ou fenetre temporelle.</p>
            </div>`;

            this.pageContent = `
                <div>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        ${cards}
                    </div>
                </div>
            `;
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
                            <a href="/reports/export/correlations/csv" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group">
                                <svg class="w-5 h-5 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                                <div class="flex-1">
                                    <p class="text-sm text-white">Corrélations</p>
                                    <p class="text-xs text-soc-muted">Groupes et scores de corrélation</p>
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
                            <a href="/reports/export/events/json" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group">
                                <svg class="w-5 h-5 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                                <div class="flex-1">
                                    <p class="text-sm text-white">Evénements JSON</p>
                                    <p class="text-xs text-soc-muted">Historique structuré des événements</p>
                                </div>
                                <svg class="w-4 h-4 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                            </a>
                            <a href="/reports/export/assets/json" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group">
                                <svg class="w-5 h-5 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                                <div class="flex-1">
                                    <p class="text-sm text-white">Actifs JSON</p>
                                    <p class="text-xs text-soc-muted">Inventaire structuré avec metadata</p>
                                </div>
                                <svg class="w-4 h-4 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                            </a>
                            <a href="/reports/export/correlations/json" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group">
                                <svg class="w-5 h-5 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                                <div class="flex-1">
                                    <p class="text-sm text-white">Corrélations JSON</p>
                                    <p class="text-xs text-soc-muted">Groupes, scores et événements liés</p>
                                </div>
                                <svg class="w-4 h-4 text-soc-muted group-hover:text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                            </a>
                        </div>
                    </div>

                    <div class="md:col-span-2 bg-soc-card border border-soc-border rounded-xl">
                        <div class="px-5 py-4 border-b border-soc-border">
                            <h3 class="font-semibold text-white">Exports PDF</h3>
                            <p class="text-xs text-soc-muted mt-1">Résumé imprimable des ressources</p>
                        </div>
                        <div class="p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                            <a href="/reports/export/alerts/pdf" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group"><div class="flex-1"><p class="text-sm text-white">Alertes PDF</p><p class="text-xs text-soc-muted">Résumé imprimable</p></div></a>
                            <a href="/reports/export/events/pdf" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group"><div class="flex-1"><p class="text-sm text-white">Evénements PDF</p><p class="text-xs text-soc-muted">Résumé imprimable</p></div></a>
                            <a href="/reports/export/assets/pdf" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group"><div class="flex-1"><p class="text-sm text-white">Actifs PDF</p><p class="text-xs text-soc-muted">Résumé imprimable</p></div></a>
                            <a href="/reports/export/correlations/pdf" target="_blank" class="flex items-center gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-accent/50 transition-colors group"><div class="flex-1"><p class="text-sm text-white">Corrélations PDF</p><p class="text-xs text-soc-muted">Résumé imprimable</p></div></a>
                        </div>
                    </div>

                    <div class="md:col-span-2 bg-soc-card border border-soc-border rounded-xl">
                        <div class="px-5 py-4 border-b border-soc-border flex items-center justify-between">
                            <div>
                                <h3 class="font-semibold text-white">Aperçu Avant Export</h3>
                                <p class="text-xs text-soc-muted mt-1">Contrôler rapidement le contenu avant téléchargement</p>
                            </div>
                        </div>
                        <div class="p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                            <button @click="previewReport('/reports/export/alerts/json', 'Aperçu Alertes JSON')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Alertes JSON</button>
                            <button @click="previewReport('/reports/export/events/json', 'Aperçu Evénements JSON')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Evénements JSON</button>
                            <button @click="previewReport('/reports/export/assets/json', 'Aperçu Actifs JSON')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Actifs JSON</button>
                            <button @click="previewReport('/reports/export/correlations/json', 'Aperçu Corrélations JSON')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Corrélations JSON</button>
                            <button @click="previewReport('/reports/export/alerts/csv', 'Aperçu Alertes CSV')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Alertes CSV</button>
                            <button @click="previewReport('/reports/export/events/csv', 'Aperçu Evénements CSV')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Evénements CSV</button>
                            <button @click="previewReport('/reports/export/assets/csv', 'Aperçu Actifs CSV')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Actifs CSV</button>
                            <button @click="previewReport('/reports/export/correlations/csv', 'Aperçu Corrélations CSV')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Corrélations CSV</button>
                            <button @click="previewReport('/reports/export/alerts/pdf', 'Aperçu Alertes PDF (binaire)')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Alertes PDF</button>
                            <button @click="previewReport('/reports/export/events/pdf', 'Aperçu Evénements PDF (binaire)')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Evénements PDF</button>
                            <button @click="previewReport('/reports/export/assets/pdf', 'Aperçu Actifs PDF (binaire)')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Actifs PDF</button>
                            <button @click="previewReport('/reports/export/correlations/pdf', 'Aperçu Corrélations PDF (binaire)')" class="px-4 py-3 bg-soc-bg border border-soc-border rounded-lg text-sm text-white hover:border-soc-accent/50 text-left">Aperçu Corrélations PDF</button>
                        </div>
                    </div>
                </div>
            `;
        },

        async previewReport(path, title) {
            try {
                const r = await fetch(path, { headers: this.headers });
                const contentType = r.headers.get('content-type') || '';
                let text = '';
                if (contentType.includes('application/pdf')) {
                    const blob = await r.blob();
                    text = `[PDF binaire] Taille: ${blob.size} octets`;
                } else {
                    text = await r.text();
                }
                let content = text;
                if (contentType.includes('application/json')) {
                    try {
                        content = JSON.stringify(JSON.parse(text), null, 2);
                    } catch {}
                }
                this.reportPreviewTitle = title;
                this.reportPreviewContent = content.slice(0, 12000);
                this.showReportPreview = true;
            } catch (e) {
                this.reportPreviewTitle = title;
                this.reportPreviewContent = `Erreur d'aperçu: ${e.message}`;
                this.showReportPreview = true;
            }
        },

        // ===================== ATTACK LAB =====================
        async renderAttackLab() {
            try {
                const [scenarioResp, targetResp, presetResp] = await Promise.all([
                    fetch('/attack-lab/scenarios', { headers: this.headers }),
                    fetch('/attack-lab/targets', { headers: this.headers }),
                    fetch('/attack-lab/presets', { headers: this.headers })
                ]);
                const scenarios = scenarioResp.ok ? await scenarioResp.json() : [];
                const targetData = targetResp.ok ? await targetResp.json() : { targets: ['serveur-endpoint'] };
                const presets = presetResp.ok ? await presetResp.json() : [];
                const targets = targetData.targets || ['serveur-endpoint'];

                if (!targets.includes(this.attackLabConfig.target)) {
                    this.attackLabConfig.target = targets[0] || 'serveur-endpoint';
                }
                if (!scenarios.find(s => s.id === this.attackLabConfig.scenario) && scenarios[0]) {
                    this.attackLabConfig.scenario = scenarios[0].id;
                }
                
                let scenarioCards = scenarios.length > 0 ? scenarios.map(s => `
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5 hover:border-soc-accent/50 transition-colors">
                        <div class="flex items-center gap-3 mb-3">
                            <svg class="w-5 h-5 text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                            <h4 class="text-sm font-medium text-white">${s.name}</h4>
                        </div>
                        <p class="text-xs text-soc-muted mb-3">${s.description || s.id}</p>
                        <div class="flex items-center justify-between">
                            <span class="text-xs px-2 py-1 rounded bg-soc-bg text-soc-muted border border-soc-border">${s.tool}</span>
                            <button @click="launchAttack('${s.id}')" class="px-3 py-1.5 bg-soc-accent/10 text-soc-accent border border-soc-accent/20 rounded-lg text-xs hover:bg-soc-accent/20 transition-colors">${this.t('launch_attack')}</button>
                        </div>
                    </div>
                `).join('') : '<p class="text-soc-muted text-center py-8">Aucun scénario disponible</p>';

                const scenarioOptions = scenarios.map(s => `<option value="${s.id}" ${this.attackLabConfig.scenario === s.id ? 'selected' : ''}>${s.name}</option>`).join('');
                const targetOptions = targets.map(t => `<option value="${t}" ${this.attackLabConfig.target === t ? 'selected' : ''}>${t}</option>`).join('');
                const presetGroups = presets.reduce((acc, preset) => {
                    const category = preset.category || 'other';
                    if (!acc[category]) acc[category] = [];
                    acc[category].push(preset);
                    return acc;
                }, {});
                const presetSections = Object.entries(presetGroups).map(([category, groupPresets]) => `
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="text-sm font-medium text-white">Presets ${this.attackPresetLabels[category] || category}</h4>
                            <span class="text-xs px-2 py-1 rounded bg-soc-bg text-soc-muted border border-soc-border">${groupPresets.length}</span>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                            ${groupPresets.map(preset => `
                                <button @click="launchPreset('${preset.id}')" class="text-left bg-soc-bg border border-soc-border rounded-lg p-4 hover:border-soc-accent/50 transition-colors">
                                    <div class="flex items-center justify-between mb-2">
                                        <span class="text-sm font-medium text-white">${preset.name}</span>
                                        <span class="text-xs text-soc-accent">${preset.steps.length} étape(s)</span>
                                    </div>
                                    <p class="text-xs text-soc-muted mb-2">${preset.description}</p>
                                    <p class="text-xs text-soc-muted">${preset.steps.map(step => step.scenario).join(' -> ')}</p>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `).join('');
                
                this.pageContent = `
                    <div class="space-y-6">
                        <!-- Header with Language Selector -->
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 class="text-lg font-semibold text-white">${this.t('attack_lab')}</h3>
                                <p class="text-sm text-soc-muted mt-1">${this.t('launch_attack')} - ${this.t('target')}: serveur-endpoint</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="text-xs text-soc-muted">${this.t('language')}:</span>
                                <select @change="switchLang($event.target.value)" class="bg-soc-bg border border-soc-border text-white text-xs rounded-lg px-2 py-1.5">
                                    <option value="fr" ${this.currentLang === 'fr' ? 'selected' : ''}>${this.t('french')}</option>
                                    <option value="en" ${this.currentLang === 'en' ? 'selected' : ''}>${this.t('english')}</option>
                                    <option value="es" ${this.currentLang === 'es' ? 'selected' : ''}>${this.t('spanish')}</option>
                                    <option value="de" ${this.currentLang === 'de' ? 'selected' : ''}>${this.t('german')}</option>
                                    <option value="ar" ${this.currentLang === 'ar' ? 'selected' : ''}>${this.t('arabic')}</option>
                                    <option value="it" ${this.currentLang === 'it' ? 'selected' : ''}>${this.t('italian')}</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Attack Controls -->
                        <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                            <div class="flex items-center justify-between mb-4">
                                <h4 class="text-sm font-medium text-white">Paramétrage des attaques</h4>
                                <button @click="launchConfiguredAttack()" class="px-4 py-2 bg-soc-accent text-white rounded-lg text-sm hover:bg-blue-600 transition-colors">${this.t('launch_attack')}</button>
                            </div>
                            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <label class="block">
                                    <span class="text-xs text-soc-muted block mb-2">Scénario</span>
                                    <select id="attack-scenario" class="w-full bg-soc-bg border border-soc-border text-white text-sm rounded-lg px-3 py-2">${scenarioOptions}</select>
                                </label>
                                <label class="block">
                                    <span class="text-xs text-soc-muted block mb-2">Cible</span>
                                    <select id="attack-target" class="w-full bg-soc-bg border border-soc-border text-white text-sm rounded-lg px-3 py-2">${targetOptions}</select>
                                </label>
                                <label class="block">
                                    <span class="text-xs text-soc-muted block mb-2">Intensité</span>
                                    <select id="attack-intensity" class="w-full bg-soc-bg border border-soc-border text-white text-sm rounded-lg px-3 py-2">
                                        <option value="low" ${this.attackLabConfig.intensity === 'low' ? 'selected' : ''}>low</option>
                                        <option value="medium" ${this.attackLabConfig.intensity === 'medium' ? 'selected' : ''}>medium</option>
                                        <option value="high" ${this.attackLabConfig.intensity === 'high' ? 'selected' : ''}>high</option>
                                        <option value="stress" ${this.attackLabConfig.intensity === 'stress' ? 'selected' : ''}>stress</option>
                                    </select>
                                </label>
                                <label class="block">
                                    <span class="text-xs text-soc-muted block mb-2">Durée (s)</span>
                                    <input id="attack-duration" type="number" min="10" max="3600" value="${this.attackLabConfig.duration}" class="w-full bg-soc-bg border border-soc-border text-white text-sm rounded-lg px-3 py-2" />
                                </label>
                            </div>
                        </div>

                        <!-- Quick Actions -->
                        <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                            <h4 class="text-sm font-medium text-white mb-3">${this.t('quick_actions') || 'Actions rapides'}</h4>
                            <div class="flex gap-3">
                                <button @click="launchAttack('recon_nmap', 'low')" class="px-4 py-2 bg-soc-accent/10 text-soc-accent border border-soc-accent/20 rounded-lg text-sm hover:bg-soc-accent/20 transition-colors">${this.t('recon')} (Low)</button>
                                <button @click="launchAttack('bruteforce_hydra', 'medium')" class="px-4 py-2 bg-soc-warning/10 text-soc-warning border border-soc-warning/20 rounded-lg text-sm hover:bg-soc-warning/20 transition-colors">${this.t('brute_force')} (Med)</button>
                                <button @click="launchAttack('attack_chain_full', 'low')" class="px-4 py-2 bg-soc-danger/10 text-soc-danger border border-soc-danger/20 rounded-lg text-sm hover:bg-soc-danger/20 transition-colors">${this.t('kill_chain')}</button>
                                <button @click="stopAllAttacks()" class="px-4 py-2 bg-soc-danger/10 text-soc-danger border border-soc-danger/20 rounded-lg text-sm hover:bg-soc-danger/20 transition-colors">${this.t('stop_all')}</button>
                            </div>
                        </div>
                        
                        <!-- Scenarios Grid -->
                        <div>
                            <h4 class="text-sm font-medium text-white mb-3">${this.t('scenario')}s disponibles</h4>
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                ${scenarioCards}
                            </div>
                        </div>

                        <div>
                            <h4 class="text-sm font-medium text-white mb-3">Presets par catégorie</h4>
                            <div class="space-y-4">
                                ${presetSections || '<p class="text-xs text-soc-muted">Aucun preset disponible</p>'}
                            </div>
                        </div>
                        
                        <!-- Active Jobs -->
                        <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                            <div class="flex items-center justify-between mb-3">
                                <h4 class="text-sm font-medium text-white">${this.t('history')} - Jobs récents</h4>
                                <button @click="refreshAttackJobs()" class="text-xs text-soc-accent hover:underline">Actualiser</button>
                            </div>
                            <div id="attack-jobs-list" class="space-y-2">
                                <p class="text-xs text-soc-muted">Cliquez sur "Actualiser" pour voir les jobs</p>
                            </div>
                        </div>
                    </div>
                `;
            } catch (e) {
                this.pageContent = `<div class="bg-soc-danger/10 border border-soc-danger rounded-lg p-6"><p class="text-soc-danger">Erreur: ${e.message}</p></div>`;
            }
        },

        readAttackLabConfig() {
            const scenario = document.getElementById('attack-scenario');
            const target = document.getElementById('attack-target');
            const intensity = document.getElementById('attack-intensity');
            const duration = document.getElementById('attack-duration');
            if (scenario) this.attackLabConfig.scenario = scenario.value;
            if (target) this.attackLabConfig.target = target.value;
            if (intensity) this.attackLabConfig.intensity = intensity.value;
            if (duration) this.attackLabConfig.duration = parseInt(duration.value || '60', 10);
        },

        async launchConfiguredAttack() {
            this.readAttackLabConfig();
            await this.launchAttack(this.attackLabConfig.scenario, this.attackLabConfig.intensity, this.attackLabConfig.target, this.attackLabConfig.duration);
        },

        async launchPreset(presetId) {
            try {
                const r = await fetch('/attack-lab/presets', { headers: this.headers });
                const presets = r.ok ? await r.json() : [];
                const preset = presets.find(p => p.id === presetId);
                if (!preset) {
                    alert('Preset introuvable');
                    return;
                }

                for (const step of preset.steps) {
                    await this.launchAttack(
                        step.scenario,
                        step.intensity || this.attackLabConfig.intensity,
                        this.attackLabConfig.target,
                        this.attackLabConfig.duration
                    );
                }
            } catch (e) {
                alert(`Erreur preset: ${e.message}`);
            }
        },

        async launchAttack(scenario, intensity = 'low', target = 'serveur-endpoint', duration = 60) {
            try {
                const r = await fetch('/attack-lab/launch', {
                    method: 'POST',
                    headers: { ...this.headers, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ scenario, intensity, target, duration })
                });
                if (r.ok) {
                    const data = await r.json();
                    alert(`Attaque lancée: ${data.job_id}`);
                    setTimeout(() => this.refreshAttackJobs(), 1000);
                } else {
                    alert(`Erreur: ${await r.text()}`);
                }
            } catch (e) {
                alert(`Erreur: ${e.message}`);
            }
        },

        async stopAllAttacks() {
            try {
                const r = await fetch('/attack-lab/stop-all', {
                    method: 'POST',
                    headers: this.headers
                });
                if (r.ok) {
                    const data = await r.json();
                    alert(`${data.message}`);
                }
            } catch (e) {
                console.error('Stop all error:', e);
            }
        },

        async refreshAttackJobs() {
            try {
                const r = await fetch('/attack-lab/jobs', { headers: this.headers });
                if (r.ok) {
                    const jobs = await r.json();
                    const jobsDiv = document.getElementById('attack-jobs-list');
                    if (jobsDiv) {
                        if (jobs.length > 0) {
                            jobsDiv.innerHTML = jobs.map(j => `
                                <div class="bg-soc-bg rounded-lg p-3 border border-soc-border text-xs">
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-white font-medium">${j.scenario || j.job_id}</span>
                                        <span class="px-2 py-0.5 rounded ${j.status === 'running' ? 'bg-soc-success/10 text-soc-success' : j.status === 'completed' ? 'bg-soc-accent/10 text-soc-accent' : 'bg-soc-danger/10 text-soc-danger'}">${j.status}</span>
                                    </div>
                                    <div class="flex items-center justify-between gap-2">
                                        <p class="text-soc-muted">Job: ${j.job_id}</p>
                                        <span class="px-2 py-0.5 rounded bg-soc-accent/10 text-soc-accent border border-soc-accent/20">executed by serveur-attacker</span>
                                    </div>
                                </div>
                            `).join('');
                        } else {
                            jobsDiv.innerHTML = '<p class="text-xs text-soc-muted">Aucun job récent</p>';
                        }
                    }
                }
            } catch (e) {
                console.error('Refresh jobs error:', e);
            }
        },

        async renderDockerHealth() {
            const r = await fetch('/reports/docker-health', { headers: this.headers });
            const data = r.ok ? await r.json() : { status: 'error', services: [] };

            const overallClass = data.status === 'ok' ? 'text-soc-success' : 'text-soc-warning';
            const cards = (data.services || []).map(service => {
                const statusClass = service.status === 'ok'
                    ? 'bg-soc-success/10 text-soc-success border-soc-success/20'
                    : 'bg-soc-danger/10 text-soc-danger border-soc-danger/20';
                const m = service.metrics || {};
                const memoryBar = m.mem_used_percent !== undefined ? `
                    <div class="mt-3">
                        <div class="flex items-center justify-between text-xs mb-1">
                            <span class="text-soc-muted">Mémoire</span>
                            <span class="text-white font-mono">${m.mem_used_percent}%</span>
                        </div>
                        <div class="w-full bg-soc-bg rounded-full h-2 overflow-hidden">
                            <div class="h-2 ${m.mem_used_percent >= 85 ? 'bg-soc-danger' : m.mem_used_percent >= 65 ? 'bg-soc-warning' : 'bg-soc-success'}" style="width:${Math.min(m.mem_used_percent, 100)}%"></div>
                        </div>
                    </div>
                ` : '';
                const loadBar = m.load_1m !== undefined && m.cpu_count ? `
                    <div class="mt-3">
                        <div class="flex items-center justify-between text-xs mb-1">
                            <span class="text-soc-muted">Charge CPU</span>
                            <span class="text-white font-mono">${m.load_1m}/${m.cpu_count}</span>
                        </div>
                        <div class="w-full bg-soc-bg rounded-full h-2 overflow-hidden">
                            <div class="h-2 ${m.load_1m >= m.cpu_count ? 'bg-soc-danger' : m.load_1m >= (m.cpu_count * 0.7) ? 'bg-soc-warning' : 'bg-soc-accent'}" style="width:${Math.min(((m.load_1m / Math.max(m.cpu_count, 1)) * 100), 100)}%"></div>
                        </div>
                    </div>
                ` : '';
                const metricEntries = Object.entries(m).filter(([key]) => !['mem_used_percent','load_1m','cpu_count'].includes(key));
                const metrics = metricEntries.map(([key, value]) => `
                    <div class="flex items-center justify-between text-xs py-1 border-b border-soc-border/50 last:border-b-0">
                        <span class="text-soc-muted">${key}</span>
                        <span class="text-white font-mono ml-4 text-right">${Array.isArray(value) ? value.join(', ') : value}</span>
                    </div>
                `).join('') || '<p class="text-xs text-soc-muted">Aucune métrique</p>';

                return `
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="text-sm font-medium text-white">${service.name}</h4>
                            <span class="text-xs px-2 py-1 rounded border ${statusClass}">${service.status}</span>
                        </div>
                        <div class="space-y-1">${metrics}</div>
                        ${memoryBar}
                        ${loadBar}
                        ${service.error ? `<div class="mt-4 text-xs text-soc-danger">${service.error}</div>` : ''}
                    </div>
                `;
            }).join('');

            this.pageContent = `
                <div class="space-y-6">
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5 flex items-center justify-between">
                        <div>
                            <h3 class="text-lg font-semibold text-white">Docker Health</h3>
                            <p class="text-sm text-soc-muted mt-1">Etat logique des services Docker et métriques internes</p>
                        </div>
                        <div class="text-right flex items-center gap-4">
                            <button onclick="document.querySelector('[x-data]').__x.$data.renderDockerHealth()" class="px-3 py-2 bg-soc-bg border border-soc-border rounded-lg text-xs text-soc-muted hover:text-white transition-colors">Actualiser</button>
                            <div>
                            <p class="text-xs text-soc-muted">Etat global</p>
                            <p class="text-lg font-bold ${overallClass}">${data.status}</p>
                            </div>
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                        ${cards || '<p class="text-soc-muted">Aucun service détecté</p>'}
                    </div>
                </div>
            `;

            if (this.currentPage === 'docker-health') {
                this.dockerHealthRefreshTimer = setTimeout(() => this.renderDockerHealth(), 5000);
            }
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
