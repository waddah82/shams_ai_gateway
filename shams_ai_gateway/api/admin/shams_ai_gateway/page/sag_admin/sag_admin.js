frappe.pages['sag-admin'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'SAG Admin',
        single_column: true
    });

    // Initialize shared namespace before loading submodules
    frappe.sag_admin = {
        page: page,
        state: {
            toggleInProgress: {},
            refreshInProgress: false,
            autoRefreshEnabled: true,
            viewMode: 'plugins',
            activeTab: 'tools',
            availableRoles: [],
            openConfigPanels: {},
            promptsData: [],
            skillsData: [],
        },
    };

    const ns = frappe.sag_admin;

    // Load CSS and inject HTML, then load JS submodules
    frappe.require("/assets/shams_ai_gateway/css/sag_admin.css");

    page.main.html(`
        <div class="sag-admin-container">
            <!-- Server Status Card -->
            <div class="sag-card">
                <div class="sag-card-header">
                    <div class="sag-card-title">
                        <span id="server-status-icon" class="sag-status-indicator"></span>
                        <span id="server-status-text">Shams AI Gateway</span>
                        <span id="server-status-pill" class="sag-status-pill" role="status" aria-live="polite"></span>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-primary" id="toggle-server">
                            <span id="toggle-server-text">Loading...</span>
                        </button>
                        <button class="btn btn-sm btn-default" id="open-settings">
                            <i class="fa fa-cog"></i> Settings
                        </button>
                    </div>
                </div>

                <!-- Quick Settings -->
                <div class="row">
                    <div class="col-md-12">
                        <div class="sag-settings-group">
                            <label class="sag-settings-label">MCP Endpoint</label>
                            <div class="sag-endpoint-row">
                                <div class="sag-settings-value sag-endpoint-url" id="sag-mcp-endpoint">
                                    Loading...
                                </div>
                                <button type="button" class="btn btn-xs btn-default sag-copy-endpoint" id="copy-endpoint" aria-label="Copy MCP endpoint URL" title="Copy endpoint URL">
                                    <i class="fa fa-copy" aria-hidden="true"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Stats Grid -->
            <div class="sag-stats-grid">
                <div class="sag-stat-card sag-stat-card--plugins">
                    <h3>Plugins</h3>
                    <div id="plugin-stats">
                        <div class="sag-stat-value">-</div>
                        <div class="sag-stat-label">Loading...</div>
                    </div>
                </div>
                <div class="sag-stat-card sag-stat-card--tools">
                    <h3>Tools Available</h3>
                    <div id="tool-stats">
                        <div class="sag-stat-value">-</div>
                        <div class="sag-stat-label">Loading...</div>
                    </div>
                </div>
                <div class="sag-stat-card sag-stat-card--activity">
                    <h3>Today's Activity</h3>
                    <div id="activity-stats">
                        <div class="sag-stat-value">-</div>
                        <div class="sag-stat-label">Tool executions today</div>
                    </div>
                </div>
                <div class="sag-stat-card sag-stat-card--prompts">
                    <h3>Prompt Templates</h3>
                    <div id="template-stats">
                        <div class="sag-stat-value">-</div>
                        <div class="sag-stat-label">Loading...</div>
                    </div>
                </div>
                <div class="sag-stat-card sag-stat-card--skills">
                    <h3>Skills</h3>
                    <div id="skill-stats">
                        <div class="sag-stat-value">-</div>
                        <div class="sag-stat-label">Loading...</div>
                    </div>
                </div>
            </div>

            <!-- Main Registry Card with Top-Level Tabs -->
            <div class="sag-card" style="padding-bottom: 0;">

                <!-- Top-Level Tab Navigation -->
                <div class="sag-top-tabs" role="tablist" aria-label="SAG Admin sections">
                    <button class="sag-top-tab active" data-tab="tools" role="tab" id="tab-tools" aria-selected="true" aria-controls="tab-panel-tools" tabindex="0">
                        <i class="fa fa-wrench" aria-hidden="true"></i> Tools
                    </button>
                    <button class="sag-top-tab" data-tab="prompts" role="tab" id="tab-prompts" aria-selected="false" aria-controls="tab-panel-prompts" tabindex="-1">
                        <i class="fa fa-file-text-o" aria-hidden="true"></i> Prompt Templates
                    </button>
                    <button class="sag-top-tab" data-tab="skills" role="tab" id="tab-skills" aria-selected="false" aria-controls="tab-panel-skills" tabindex="-1">
                        <i class="fa fa-graduation-cap" aria-hidden="true"></i> Skills
                    </button>
                </div>

                <!-- TOOLS TAB PANEL -->
                <div class="sag-tab-panel active" id="tab-panel-tools" role="tabpanel" aria-labelledby="tab-tools" tabindex="0">
                    <div class="sag-card-header" style="margin-top: 0;">
                        <div class="sag-card-title">
                            <i class="fa fa-tools"></i>
                            Tool Registry
                        </div>
                        <div class="sag-header-right">
                            <span id="sag-last-refreshed" class="sag-last-refreshed" aria-live="polite"></span>
                            <button class="btn btn-sm btn-default" id="refresh-tools">
                                <i class="fa fa-refresh" aria-hidden="true"></i> <span class="sag-btn-label">Refresh</span>
                            </button>
                        </div>
                    </div>

                    <!-- View Mode Tabs -->
                    <div class="sag-view-tabs" role="tablist" aria-label="Tool registry view mode">
                        <button type="button" class="sag-view-tab active" data-view="plugins" role="tab" aria-selected="true" tabindex="0">
                            <i class="fa fa-cube" aria-hidden="true"></i> Plugins
                        </button>
                        <button type="button" class="sag-view-tab" data-view="tools" role="tab" aria-selected="false" tabindex="-1">
                            <i class="fa fa-wrench" aria-hidden="true"></i> Individual Tools
                        </button>
                    </div>

                    <!-- Filter + Bulk Actions Bar (shown in tools view) -->
                    <div class="sag-filter-bar" id="tools-filter-bar" style="display: none;">
                        <input type="text" class="sag-filter-input" id="tool-search"
                               placeholder="Search tools..." aria-label="Search tools">
                        <select class="sag-filter-select" id="category-filter" aria-label="Filter by category">
                            <option value="">All Categories</option>
                            <option value="read_only">Read Only</option>
                            <option value="write">Write</option>
                            <option value="read_write">Read & Write</option>
                            <option value="privileged">Privileged</option>
                        </select>
                        <select class="sag-filter-select" id="plugin-filter" aria-label="Filter by plugin">
                            <option value="">All Plugins</option>
                        </select>
                        <span id="bulk-scope-count" class="sag-bulk-scope" aria-live="polite"></span>
                        <button class="btn btn-xs btn-success" id="bulk-enable-btn" disabled>
                            <i class="fa fa-check" aria-hidden="true"></i> <span class="sag-btn-label">Enable matching</span>
                        </button>
                        <button class="btn btn-xs btn-warning" id="bulk-disable-btn" disabled>
                            <i class="fa fa-times" aria-hidden="true"></i> <span class="sag-btn-label">Disable matching</span>
                        </button>
                    </div>

                    <div id="tool-registry" style="max-height: 500px; overflow-y: auto;">
                        <div class="sag-skeleton-wrap"><div class="sag-skeleton-card"><div class="sag-skeleton-line sag-skeleton-line--title"></div><div class="sag-skeleton-line sag-skeleton-line--body"></div></div><div class="sag-skeleton-card"><div class="sag-skeleton-line sag-skeleton-line--title"></div><div class="sag-skeleton-line sag-skeleton-line--body"></div></div><div class="sag-skeleton-card"><div class="sag-skeleton-line sag-skeleton-line--title"></div><div class="sag-skeleton-line sag-skeleton-line--body"></div></div></div>
                    </div>
                </div>

                <!-- PROMPT TEMPLATES TAB PANEL -->
                <div class="sag-tab-panel" id="tab-panel-prompts" role="tabpanel" aria-labelledby="tab-prompts" tabindex="0">
                    <div class="sag-card-header" style="margin-top: 0;">
                        <div style="display: flex; gap: 8px; flex: 1; align-items: center;">
                            <input type="text" class="sag-filter-input" id="prompt-search"
                                   placeholder="Search templates..." style="flex: 1; max-width: 300px;">
                            <select class="sag-filter-select" id="prompt-status-filter">
                                <option value="">All Statuses</option>
                                <option value="Published">Published</option>
                                <option value="Draft">Draft</option>
                                <option value="Deprecated">Deprecated</option>
                                <option value="Archived">Archived</option>
                            </select>
                        </div>
                        <button class="btn btn-sm btn-default" id="refresh-prompts" aria-label="Refresh prompt templates">
                            <i class="fa fa-refresh" aria-hidden="true"></i> <span class="sag-btn-label">Refresh</span>
                        </button>
                    </div>
                    <div id="prompt-templates-list" style="max-height: 600px; overflow-y: auto;">
                        <div class="sag-skeleton-wrap"><div class="sag-skeleton-card"><div class="sag-skeleton-line sag-skeleton-line--title"></div><div class="sag-skeleton-line sag-skeleton-line--body"></div></div><div class="sag-skeleton-card"><div class="sag-skeleton-line sag-skeleton-line--title"></div><div class="sag-skeleton-line sag-skeleton-line--body"></div></div></div>
                    </div>
                </div>

                <!-- SKILLS TAB PANEL -->
                <div class="sag-tab-panel" id="tab-panel-skills" role="tabpanel" aria-labelledby="tab-skills" tabindex="0">
                    <div class="sag-card-header" style="margin-top: 0;">
                        <div style="display: flex; gap: 8px; flex: 1; align-items: center;">
                            <input type="text" class="sag-filter-input" id="skill-search"
                                   placeholder="Search skills..." style="flex: 1; max-width: 300px;">
                            <select class="sag-filter-select" id="skill-type-filter">
                                <option value="">All Types</option>
                                <option value="Tool Usage">Tool Usage</option>
                                <option value="Workflow">Workflow</option>
                            </select>
                            <select class="sag-filter-select" id="skill-status-filter">
                                <option value="">All Statuses</option>
                                <option value="Published">Published</option>
                                <option value="Draft">Draft</option>
                                <option value="Deprecated">Deprecated</option>
                            </select>
                        </div>
                        <div style="display:flex;gap:8px;align-items:center;">
                            <button class="btn btn-sm btn-primary" id="sync-skill-files" aria-label="Synchronize skill Markdown files">
                                <i class="fa fa-file-text-o" aria-hidden="true"></i> <span class="sag-btn-label">Sync Markdown</span>
                            </button>
                            <button class="btn btn-sm btn-default" id="refresh-skills" aria-label="Refresh skills">
                                <i class="fa fa-refresh" aria-hidden="true"></i> <span class="sag-btn-label">Refresh</span>
                            </button>
                        </div>
                    </div>
                    <div id="skills-list" style="max-height: 600px; overflow-y: auto;">
                        <div class="sag-skeleton-wrap"><div class="sag-skeleton-card"><div class="sag-skeleton-line sag-skeleton-line--title"></div><div class="sag-skeleton-line sag-skeleton-line--body"></div></div><div class="sag-skeleton-card"><div class="sag-skeleton-line sag-skeleton-line--title"></div><div class="sag-skeleton-line sag-skeleton-line--body"></div></div></div>
                    </div>
                </div>

            </div>

            <!-- Recent Activity -->
            <div class="sag-card">
                <div class="sag-card-header">
                    <div class="sag-card-title">
                        <i class="fa fa-history" aria-hidden="true"></i>
                        Recent Activity
                    </div>
                    <a href="/app/assistant-audit-log" class="sag-view-all">View full log <i class="fa fa-arrow-right" aria-hidden="true"></i></a>
                </div>
                <div id="recent-activity">
                    <div style="padding: 20px; text-align: center; color: var(--text-muted);">
                        <i class="fa fa-spinner fa-spin"></i> Loading activity...
                    </div>
                </div>
            </div>
        </div>
    `);

    // Load JS submodules, then wire event handlers and start data loading
    frappe.require([
        "/assets/shams_ai_gateway/js/sag_admin_utils.js",
        "/assets/shams_ai_gateway/js/sag_admin_tools.js",
        "/assets/shams_ai_gateway/js/sag_admin_prompts.js",
        "/assets/shams_ai_gateway/js/sag_admin_skills.js"
    ]).then(function() {

        // =====================================================================
        // Event handlers
        // =====================================================================

        // Server toggle
        $('#toggle-server').on('click', ns.toggleServer);
        $('#open-settings').on('click', function() {
            frappe.set_route('Form', 'Shams AI Gateway Settings');
        });

        // Copy MCP endpoint URL to clipboard
        $('#copy-endpoint').on('click', function() {
            const url = $('#sag-mcp-endpoint').text().trim();
            if (!url || url === 'Loading...') return;
            frappe.utils.copy_to_clipboard(url);
        });

        // Tool registry refresh
        $('#refresh-tools').on('click', function() {
            ns.state.lastRefreshedAt = new Date();
            if (typeof ns.updateLastRefreshedLabel === 'function') ns.updateLastRefreshedLabel();
            ns.loadStats();
            ns.loadRecentActivity();
            ns.loadToolRegistry();
        });

        // View mode tab handlers (Plugins / Individual Tools)
        ns.activateViewTab = function($tab) {
            const viewMode = $tab.data('view');
            if (viewMode === ns.state.viewMode) return;

            $('.sag-view-tab')
                .removeClass('active')
                .attr({ 'aria-selected': 'false', tabindex: '-1' });
            $tab
                .addClass('active')
                .attr({ 'aria-selected': 'true', tabindex: '0' });

            ns.state.viewMode = viewMode;

            if (viewMode === 'tools') {
                $('#tools-filter-bar').show();
            } else {
                $('#tools-filter-bar').hide();
            }

            ns.loadToolRegistry();
        };

        $('.sag-view-tab').on('click', function() {
            ns.activateViewTab($(this));
        });

        // Filter handlers (for tools view)
        $('#tool-search').on('input', frappe.utils.debounce(function() {
            if (ns.state.viewMode === 'tools') {
                ns.renderToolsList();
            }
        }, 300));

        $('#category-filter, #plugin-filter').on('change', function() {
            if (ns.state.viewMode === 'tools') {
                ns.renderToolsList();
                if (typeof ns.updateBulkScopeCount === 'function') {
                    ns.updateBulkScopeCount();
                }
            }
        });

        // Bulk action button handlers (scoped to current filter bar selection)
        $('#bulk-enable-btn').on('click', function() {
            const category = $('#category-filter').val();
            const plugin = $('#plugin-filter').val();
            ns.bulkToggleByCategory(category, plugin, true);
        });

        $('#bulk-disable-btn').on('click', function() {
            const category = $('#category-filter').val();
            const plugin = $('#plugin-filter').val();
            ns.bulkToggleByCategory(category, plugin, false);
        });

        // Top-level tab switching
        ns.switchTab = function(tabName) {
            if (ns.state.activeTab === tabName) return;
            ns.state.activeTab = tabName;

            $('.sag-top-tab')
                .removeClass('active')
                .attr({ 'aria-selected': 'false', tabindex: '-1' });
            $(`.sag-top-tab[data-tab="${tabName}"]`)
                .addClass('active')
                .attr({ 'aria-selected': 'true', tabindex: '0' });

            $('.sag-tab-panel').removeClass('active');
            $(`#tab-panel-${tabName}`).addClass('active');

            if (tabName === 'prompts' && ns.state.promptsData.length === 0) {
                ns.loadPromptTemplatesView();
            } else if (tabName === 'skills' && ns.state.skillsData.length === 0) {
                ns.loadSkillsView();
            }
        };

        $('.sag-top-tab').on('click', function() {
            ns.switchTab($(this).data('tab'));
        });

        // Arrow-key navigation for tab lists (WAI-ARIA pattern)
        function handleTabKeydown(e, $tabs, activate) {
            const key = e.key;
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(key)) return;
            e.preventDefault();
            const count = $tabs.length;
            const currentIndex = $tabs.index(e.currentTarget);
            let nextIndex = currentIndex;
            if (key === 'ArrowRight') nextIndex = (currentIndex + 1) % count;
            else if (key === 'ArrowLeft') nextIndex = (currentIndex - 1 + count) % count;
            else if (key === 'Home') nextIndex = 0;
            else if (key === 'End') nextIndex = count - 1;
            const $next = $tabs.eq(nextIndex);
            $next.trigger('focus');
            activate($next);
        }

        $('.sag-top-tabs').on('keydown', '.sag-top-tab', function(e) {
            handleTabKeydown(e, $('.sag-top-tab'), function($tab) {
                ns.switchTab($tab.data('tab'));
            });
        });

        $('.sag-view-tabs').on('keydown', '.sag-view-tab', function(e) {
            handleTabKeydown(e, $('.sag-view-tab'), function($tab) {
                ns.activateViewTab($tab);
            });
        });

        // Prompt Templates filter handlers
        $('#prompt-search').on('input', frappe.utils.debounce(function() {
            if (ns.state.activeTab === 'prompts') ns.renderPromptTemplatesList();
        }, 300));

        $('#prompt-status-filter').on('change', function() {
            if (ns.state.activeTab === 'prompts') ns.renderPromptTemplatesList();
        });

        $('#refresh-prompts').on('click', ns.loadPromptTemplatesView);

        // Skills filter handlers
        $('#skill-search').on('input', frappe.utils.debounce(function() {
            if (ns.state.activeTab === 'skills') ns.renderSkillsList();
        }, 300));

        $('#skill-type-filter, #skill-status-filter').on('change', function() {
            if (ns.state.activeTab === 'skills') ns.renderSkillsList();
        });

        $('#refresh-skills').on('click', ns.loadSkillsView);

        // =====================================================================
        // Initial data load
        // =====================================================================
        ns.state.lastRefreshedAt = new Date();
        ns.loadServerStatus();
        ns.loadStats();
        ns.loadToolRegistry();
        ns.loadRecentActivity();

        // "Updated Xs ago" ticker — cheap, local-only
        ns.updateLastRefreshedLabel = function() {
            const ts = ns.state.lastRefreshedAt;
            if (!ts) return;
            const seconds = Math.max(0, Math.round((Date.now() - ts.getTime()) / 1000));
            let label;
            if (seconds < 5) label = 'Updated just now';
            else if (seconds < 60) label = `Updated ${seconds}s ago`;
            else label = `Updated ${Math.round(seconds / 60)}m ago`;
            $('#sag-last-refreshed').text(label);
        };
        setInterval(ns.updateLastRefreshedLabel, 5000);
        ns.updateLastRefreshedLabel();

        // Auto-refresh every 30 seconds (respects autoRefreshEnabled flag)
        setInterval(function() {
            if (!ns.state.autoRefreshEnabled || Object.keys(ns.state.toggleInProgress).length > 0) {
                return;
            }

            ns.state.lastRefreshedAt = new Date();
            ns.updateLastRefreshedLabel();
            ns.loadServerStatus();
            ns.loadStats();
            ns.loadRecentActivity();
            // Note: We intentionally don't auto-refresh loadToolRegistry() here
            // to avoid interfering with user toggle interactions
        }, 30000);
    });
};
