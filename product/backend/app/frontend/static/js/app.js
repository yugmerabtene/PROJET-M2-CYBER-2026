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

        // Init
        init() {
            this.checkHealth();
            if (this.token) {
                this.fetchUser();
            }
            setInterval(() => this.checkHealth(), 30000);
            setInterval(() => this.fetchDashboardData(), 15000);
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
                const r = await fetch('/auth/me', { headers: this.authHeaders() });
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

        authHeaders() {
            return { 'Authorization': `Bearer ${this.token}` };
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
                'reports': { title: 'Rapports', subtitle: 'Exports et preuves de validation', render: this.renderReports },
            };
            const route = routes[page] || routes['dashboard'];
            this.pageTitle = route.title;
            this.pageSubtitle = route.subtitle;
            this.currentPage = page;
            try {
                await route.render();
            } catch (e) {
                this.pageContent = `<div class="bg-soc-danger/10 border border-soc-danger rounded-lg p-6"><p class="text-soc-danger">Erreur de chargement: ${e.message}</p></div>`;
            }
            this.loading = false;
        },

        async refreshData() {
            this.navigateTo(this.currentPage);
        },

        async fetchDashboardData() {
            if (!this.isAuthenticated) return;
            try {
                const r = await fetch('/reports/dashboard', { headers: this.authHeaders() });
                if (r.ok) {
                    const d = await r.json();
                    this.alertsCount = d.active_alerts || 0;
                }
            } catch (e) {}
        },

        // ===================== RENDERERS =====================

        async renderDashboard() {
            const [dash, alerts, events, assets] = await Promise.all([
                fetch('/reports/dashboard', { headers: this.authHeaders() }).then(r => r.json()),
                fetch('/alerts', { headers: this.authHeaders() }).then(r => r.json()),
                fetch('/telemetry/events', { headers: this.authHeaders() }).then(r => r.ok ? r.json() : []),
                fetch('/assets', { headers: this.authHeaders() }).then(r => r.ok ? r.json() : [])
            ]);

            this.alertsCount = dash.active_alerts || 0;

            const recentAlerts = (alerts || []).slice(0, 5);
            const recentEvents = (events || []).slice(0, 5);

            let alertRows = recentAlerts.length > 0 ? recentAlerts.map(a => {
                const sevColor = { critical: 'bg-red-500/10 text-red-400 border-red-500/20', high: 'bg-orange-500/10 text-orange-400 border-orange-500/20', medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', low: 'bg-blue-500/10 text-blue-400 border-blue-500/20' }[a.severity] || 'bg-gray-500/10 text-gray-400';
                const statusColor = { new: 'text-red-400', acknowledged: 'text-yellow-400', investigating: 'text-blue-400', resolved: 'text-green-400', closed: 'text-gray-400' }[a.status] || 'text-gray-400';
                return `<tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors">
                    <td class="px-4 py-3"><span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${sevColor}">${a.severity.toUpperCase()}</span></td>
                    <td class="px-4 py-3 text-sm">${a.title}</td>
                    <td class="px-4 py-3 text-sm text-soc-mono">${a.source_ip || '-'}</td>
                    <td class="px-4 py-3"><span class="text-sm ${statusColor} capitalize">${a.status}</span></td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${this.formatDate(a.created_at)}</td>
                </tr>`;
            }).join('') : `<tr><td colspan="5" class="px-4 py-8 text-center text-soc-muted">Aucune alerte</td></tr>`;

            this.pageContent = `
                <!-- Metric Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-soc-muted text-sm">Evenements</span>
                            <svg class="w-5 h-5 text-soc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                        </div>
                        <p class="text-3xl font-bold text-white">${dash.total_events || 0}</p>
                        <p class="text-xs text-soc-muted mt-1">Dernier: ${dash.last_heartbeat ? this.formatDate(dash.last_heartbeat) : 'N/A'}</p>
                    </div>
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-soc-muted text-sm">Alertes actives</span>
                            <svg class="w-5 h-5 text-soc-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                        </div>
                        <p class="text-3xl font-bold text-soc-danger">${dash.active_alerts || 0}</p>
                        <p class="text-xs text-soc-muted mt-1">Critical: ${dash.critical_alerts || 0} | High: ${dash.high_alerts || 0}</p>
                    </div>
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-soc-muted text-sm">Actifs</span>
                            <svg class="w-5 h-5 text-soc-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                        </div>
                        <p class="text-3xl font-bold text-white">${dash.total_assets || 0}</p>
                        <p class="text-xs text-soc-muted mt-1">Agents actifs: ${dash.total_agents || 0}</p>
                    </div>
                    <div class="bg-soc-card border border-soc-border rounded-xl p-5">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-soc-muted text-sm">Correlations</span>
                            <svg class="w-5 h-5 text-soc-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                        </div>
                        <p class="text-3xl font-bold text-white">${dash.total_correlations || 0}</p>
                        <p class="text-xs text-soc-muted mt-1">Alertes totales: ${dash.total_alerts || 0}</p>
                    </div>
                </div>

                <!-- Two Column -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Recent Alerts -->
                    <div class="bg-soc-card border border-soc-border rounded-xl">
                        <div class="px-5 py-4 border-b border-soc-border flex items-center justify-between">
                            <h3 class="font-semibold text-white">Alertes recentes</h3>
                            <button @click="navigate('alerts')" class="text-xs text-soc-accent hover:underline">Voir tout</button>
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
                            <button @click="navigate('events')" class="text-xs text-soc-accent hover:underline">Voir tout</button>
                        </div>
                        <div class="p-5 space-y-3">
                            ${recentEvents.length > 0 ? recentEvents.map(e => `
                                <div class="flex items-start gap-3 p-3 bg-soc-bg rounded-lg border border-soc-border">
                                    <div class="w-2 h-2 rounded-full mt-1.5 ${e.severity === 'critical' ? 'bg-soc-danger' : e.severity === 'high' ? 'bg-soc-warning' : 'bg-soc-accent'}"></div>
                                    <div class="flex-1 min-w-0">
                                        <p class="text-sm text-white truncate">${e.message || e.event_type}</p>
                                        <p class="text-xs text-soc-muted">${e.source_ip || '?'} → ${e.target_ip || '?'} | ${e.event_type}</p>
                                    </div>
                                    <span class="text-xs text-soc-muted whitespace-nowrap">${this.formatDate(e.observed_at)}</span>
                                </div>
                            `).join('') : '<p class="text-soc-muted text-center py-8">Aucun evenement</p>'}
                        </div>
                    </div>
                </div>
            `;
        },

        async renderAlerts() {
            const r = await fetch('/alerts', { headers: this.authHeaders() });
            const alerts = r.ok ? await r.json() : [];

            let rows = alerts.length > 0 ? alerts.map(a => {
                const sevColor = { critical: 'bg-red-500/10 text-red-400 border-red-500/20', high: 'bg-orange-500/10 text-orange-400 border-orange-500/20', medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', low: 'bg-blue-500/10 text-blue-400 border-blue-500/20' }[a.severity] || 'bg-gray-500/10 text-gray-400';
                return `<tr class="border-t border-soc-border hover:bg-soc-bg/50 transition-colors">
                    <td class="px-4 py-3"><span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${sevColor}">${a.severity.toUpperCase()}</span></td>
                    <td class="px-4 py-3 text-sm text-white">${a.title}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${a.source_ip || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${a.target_ip || '-'}</td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${a.rule_name || '-'}</td>
                    <td class="px-4 py-3"><span class="text-sm capitalize ${a.status === 'new' ? 'text-red-400' : a.status === 'resolved' ? 'text-green-400' : 'text-soc-muted'}">${a.status}</span></td>
                    <td class="px-4 py-3 text-sm text-soc-muted">${this.formatDate(a.created_at)}</td>
                </tr>`;
            }).join('') : `<tr><td colspan="7" class="px-4 py-12 text-center text-soc-muted">
                <svg class="w-12 h-12 mx-auto mb-3 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                Aucune alerte generee pour le moment
            </td></tr>`;

            this.pageContent = `
                <div class="bg-soc-card border border-soc-border rounded-xl">
                    <div class="px-5 py-4 border-b border-soc-border flex items-center justify-between">
                        <h3 class="font-semibold text-white">Toutes les alertes (${alerts.length})</h3>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left">
                            <thead><tr class="text-xs text-soc-muted uppercase border-b border-soc-border">
                                <th class="px-4 py-3">Severite</th><th class="px-4 py-3">Titre</th><th class="px-4 py-3">Source</th><th class="px-4 py-3">Cible</th><th class="px-4 py-3">Regle</th><th class="px-4 py-3">Statut</th><th class="px-4 py-3">Date</th>
                            </tr></thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </div>
            `;
        },

        async renderEvents() {
            const r = await fetch('/telemetry/events', { headers: this.authHeaders() });
            const events = r.ok ? await r.json() : [];

            let items = events.length > 0 ? events.slice(0, 50).map(e => {
                const dotColor = { critical: 'bg-soc-danger', high: 'bg-soc-warning', medium: 'bg-soc-accent', low: 'bg-soc-success' }[e.severity] || 'bg-soc-muted';
                return `<div class="flex items-start gap-4 p-4 bg-soc-bg rounded-lg border border-soc-border hover:border-soc-border/60 transition-colors">
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
            const r = await fetch('/assets', { headers: this.authHeaders() });
            const assets = r.ok ? await r.json() : [];

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
                Aucun actif decouvert. Le scan de decouverte n'a pas encore ete effectue.
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

        async renderCorrelations() {
            const r = await fetch('/correlation', { headers: this.authHeaders() });
            const groups = r.ok ? await r.json() : [];

            let cards = groups.length > 0 ? groups.map(g => {
                const typeColor = g.correlation_type === 'ip_source' ? 'text-soc-accent' : 'text-soc-warning';
                return `<div class="bg-soc-card border border-soc-border rounded-xl p-5 hover:border-soc-border/60 transition-colors">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2">
                            <svg class="w-5 h-5 ${typeColor}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                            <span class="text-sm font-medium text-white">${g.correlation_type}</span>
                        </div>
                        <span class="text-xs px-2 py-0.5 rounded ${g.status === 'active' ? 'bg-soc-danger/10 text-soc-danger' : 'bg-soc-success/10 text-soc-success'}">${g.status}</span>
                    </div>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between"><span class="text-soc-muted">Source IP</span><span class="text-white font-mono">${g.source_ip || '-'}</span></div>
                        <div class="flex justify-between"><span class="text-soc-muted">Evenements</span><span class="text-white">${g.event_count || 0}</span></div>
                        <div class="flex justify-between"><span class="text-soc-muted">Alertes</span><span class="text-soc-danger">${g.alert_count || 0}</span></div>
                        <div class="flex justify-between"><span class="text-soc-muted">Severite</span><span class="text-white">${g.severity || '-'}</span></div>
                    </div>
                </div>`;
            }).join('') : `<div class="bg-soc-card border border-soc-border rounded-xl p-12 text-center">
                <svg class="w-16 h-16 mx-auto mb-4 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                <h3 class="text-lg font-medium text-white mb-2">Aucune correlation</h3>
                <p class="text-soc-muted text-sm">Les correlations seront creees automatiquement lors de la detection d'evenements lies par IP source ou fenetre temporelle.</p>
            </div>`;

            this.pageContent = `
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${cards}
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
