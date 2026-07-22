frappe.pages['sag-local-tools'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('SAG Local Tools'),
        single_column: true
    });

    const state = {
        tools: [],
        filtered: [],
        selected: null,
        lastResult: null,
        filter: 'all',
        recentFiles: []
    };

    const css = `
        .sag-local-wrap{direction:rtl;font-family:inherit;padding:14px 0 28px;color:#1f2937}
        .sag-local-hero{background:linear-gradient(135deg,#0b2d4f,#071a33);color:#fff;border-radius:18px;padding:20px 22px;margin-bottom:16px;box-shadow:0 12px 28px rgba(15,23,42,.18)}
        .sag-local-hero h2{margin:0 0 6px;font-weight:800;color:#fff}
        .sag-local-hero p{margin:0;color:#d8e2ef}
        .sag-local-grid{display:grid;grid-template-columns:minmax(290px,390px) 1fr;gap:16px;align-items:start}
        .sag-local-card{background:#fff;border:1px solid #e5e7eb;border-radius:16px;box-shadow:0 8px 22px rgba(15,23,42,.06);overflow:hidden}
        .sag-local-card-head{padding:13px 15px;border-bottom:1px solid #edf0f3;display:flex;align-items:center;justify-content:space-between;gap:10px;background:#fbfcfe}
        .sag-local-card-title{font-size:15px;font-weight:800;color:#111827}
        .sag-local-card-body{padding:15px}
        .sag-local-toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:14px}
        .sag-local-search{width:100%;border:1px solid #d1d5db;border-radius:12px;padding:10px 12px;outline:none;margin-bottom:10px;background:#fff}
        .sag-local-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
        .sag-local-tab{border:1px solid #d7dce2;background:#fff;border-radius:999px;padding:6px 10px;cursor:pointer;font-size:12px;color:#334155}
        .sag-local-tab.active{background:#0b2d4f;color:#fff;border-color:#0b2d4f}
        .sag-local-list{max-height:680px;overflow:auto;padding-left:2px;padding-right:2px}
        .sag-local-tool{border:1px solid #edf0f3;border-radius:13px;padding:10px 11px;margin-bottom:8px;cursor:pointer;background:#fff;transition:.15s}
        .sag-local-tool:hover{border-color:#bfd0e4;background:#f8fbff}
        .sag-local-tool.active{border-color:#0b2d4f;background:#eef6ff}
        .sag-local-tool-name{font-weight:800;color:#111827;font-size:13px;direction:ltr;display:inline-block}
        .sag-local-tool-desc{font-size:12px;color:#64748b;margin-top:5px;line-height:1.5;max-height:58px;overflow:hidden}
        .sag-local-plugin{font-size:11px;color:#64748b;background:#f1f5f9;border-radius:999px;padding:2px 7px;margin-inline-start:5px}
        .sag-local-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
        .sag-local-label{display:block;font-size:12px;color:#64748b;margin-bottom:6px;font-weight:700}
        .sag-local-textarea{width:100%;min-height:260px;border:1px solid #d1d5db;border-radius:14px;padding:12px;direction:ltr;text-align:left;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:12px;resize:vertical;background:#fbfdff}
        .sag-local-pre{margin:0;white-space:pre-wrap;word-break:break-word;direction:ltr;text-align:left;background:#0b1220;color:#e5e7eb;border-radius:14px;padding:12px;min-height:180px;max-height:360px;overflow:auto;font-size:12px}
        .sag-local-schema{background:#f8fafc;color:#0f172a;border:1px solid #e2e8f0;min-height:260px}
        .sag-local-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;align-items:center}
        .sag-local-check{display:flex;gap:7px;align-items:center;font-size:12px;color:#475569;margin:0}
        .sag-local-muted{font-size:12px;color:#64748b}
        .sag-local-stat{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
        .sag-local-stat span{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:5px 9px;font-size:12px;color:#eef2ff}
        .sag-local-badge{display:inline-flex;align-items:center;border-radius:999px;padding:3px 8px;font-size:11px;font-weight:800;white-space:nowrap}
        .badge-read{background:#ecfdf5;color:#047857}
        .badge-write{background:#fff7ed;color:#c2410c}
        .badge-danger{background:#fef2f2;color:#b91c1c}
        .badge-code{background:#f5f3ff;color:#6d28d9}
        .badge-file{background:#eff6ff;color:#1d4ed8}
        .badge-viz{background:#f0fdfa;color:#0f766e}
        .badge-custom{background:#fdf2f8;color:#be185d}
        .sag-local-result-ok{border:1px solid rgba(16,185,129,.25)}
        .sag-local-result-bad{border:1px solid rgba(239,68,68,.35);color:#fecaca}
        .sag-local-warn{border:1px solid #fed7aa;background:#fff7ed;color:#9a3412;border-radius:13px;padding:10px 12px;margin-bottom:12px;font-size:12px;line-height:1.6}
        .sag-local-file-panel{display:none;border:1px dashed #93c5fd;background:#eff6ff;border-radius:13px;padding:11px;margin-bottom:12px}
        .sag-local-file-panel.active{display:block}
        .sag-local-file-controls{display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center}
        .sag-local-select{width:100%;border:1px solid #bfdbfe;border-radius:10px;padding:8px;background:#fff;direction:ltr;text-align:left}
        @media(max-width:1050px){.sag-local-grid,.sag-local-row{grid-template-columns:1fr}.sag-local-list{max-height:360px}}
    `;

    $(frappe.dom).find('#sag-local-tools-style').remove();
    $('<style id="sag-local-tools-style">').text(css).appendTo('head');

    page.main.html(`
        <div class="sag-local-wrap">
            <div class="sag-local-hero">
                <h2>تشغيل جميع أدوات Frappe Assistant محليًا</h2>
                <p>هذه الصفحة تعمل من داخل Desk وتعرض كل الأدوات المفعّلة للمستخدم: Core + OCR + Data Science + Visualization + Custom Tools.</p>
                <div class="sag-local-stat" id="sag-local-stats">
                    <span>المستخدم: ...</span><span>الأدوات: ...</span><span>الوضع: All Enabled Tools</span>
                </div>
                <div class="sag-local-toolbar">
                    <button class="btn btn-primary btn-sm" id="sag-refresh"><i class="fa fa-refresh"></i> تحديث الأدوات</button>
                    <button class="btn btn-default btn-sm" id="sag-open-admin"><i class="fa fa-cog"></i> SAG Admin</button>
                    <button class="btn btn-default btn-sm" id="sag-clear"><i class="fa fa-eraser"></i> مسح النتيجة</button>
                </div>
            </div>

            <div class="sag-local-warn">
                تنبيه: أدوات Data Science و OCR و SQL و Python قد تستهلك موارد عالية. أدوات الكتابة والحذف والتحليل الثقيل تحتاج تأكيد قبل التشغيل. عطّل أي أداة لا تريدها من SAG Admin &gt; Tools.
            </div>

            <div class="sag-local-grid">
                <div class="sag-local-card">
                    <div class="sag-local-card-head">
                        <div class="sag-local-card-title">الأدوات المتاحة</div>
                        <span class="sag-local-muted" id="sag-tool-count">0</span>
                    </div>
                    <div class="sag-local-card-body">
                        <input class="sag-local-search" id="sag-tool-search" placeholder="ابحث باسم الأداة... مثل extract_file_content أو run_python_code">
                        <div class="sag-local-tabs">
                            <button class="sag-local-tab active" data-filter="all">الكل</button>
                            <button class="sag-local-tab" data-filter="read_only">قراءة</button>
                            <button class="sag-local-tab" data-filter="write">كتابة</button>
                            <button class="sag-local-tab" data-filter="file_ocr">OCR/ملفات</button>
                            <button class="sag-local-tab" data-filter="code_analysis">Data Science</button>
                            <button class="sag-local-tab" data-filter="visualization">رسوم</button>
                            <button class="sag-local-tab" data-filter="custom">Custom</button>
                            <button class="sag-local-tab" data-filter="dangerous">خطرة</button>
                        </div>
                        <div class="sag-local-list" id="sag-tool-list">
                            <div class="text-muted">جاري تحميل الأدوات...</div>
                        </div>
                    </div>
                </div>

                <div class="sag-local-card">
                    <div class="sag-local-card-head">
                        <div>
                            <div class="sag-local-card-title" id="sag-selected-title">اختر أداة</div>
                            <div class="sag-local-muted" id="sag-selected-desc">اختر أداة من القائمة ثم عدّل JSON وشغّلها.</div>
                        </div>
                        <span id="sag-selected-badge" class="sag-local-badge badge-read">Tool</span>
                    </div>
                    <div class="sag-local-card-body">
                        <div class="sag-local-file-panel" id="sag-file-panel">
                            <label class="sag-local-label">مساعد ملفات OCR / Extract File Content</label>
                            <div class="sag-local-file-controls">
                                <select class="sag-local-select" id="sag-recent-files"><option value="">تحميل أحدث الملفات...</option></select>
                                <button class="btn btn-default btn-sm" id="sag-refresh-files"><i class="fa fa-refresh"></i> الملفات</button>
                                <button class="btn btn-primary btn-sm" id="sag-upload-file"><i class="fa fa-upload"></i> رفع ملف</button>
                            </div>
                            <div class="sag-local-muted" style="margin-top:7px">بعد اختيار أو رفع ملف سيتم تعبئة file_url داخل Arguments تلقائيًا.</div>
                        </div>
                        <div class="sag-local-row">
                            <div>
                                <label class="sag-local-label">Arguments JSON</label>
                                <textarea class="sag-local-textarea" id="sag-args" spellcheck="false">{}</textarea>
                                <div class="sag-local-actions">
                                    <button class="btn btn-primary" id="sag-run"><i class="fa fa-play"></i> تشغيل الأداة</button>
                                    <button class="btn btn-default" id="sag-example"><i class="fa fa-magic"></i> تعبئة مثال</button>
                                    <button class="btn btn-default" id="sag-format"><i class="fa fa-code"></i> تنسيق JSON</button>
                                    <label class="sag-local-check">
                                        <input type="checkbox" id="sag-confirm-action">
                                        تأكيد أدوات الكتابة / OCR / Data Science / Custom
                                    </label>
                                </div>
                            </div>
                            <div>
                                <label class="sag-local-label">Input Schema</label>
                                <pre class="sag-local-pre sag-local-schema" id="sag-schema">{}</pre>
                                <label class="sag-local-label" style="margin-top:12px">النتيجة</label>
                                <pre class="sag-local-pre" id="sag-result">لم يتم التشغيل بعد.</pre>
                                <div class="sag-local-actions">
                                    <button class="btn btn-default btn-sm" id="sag-copy-result"><i class="fa fa-copy"></i> نسخ النتيجة</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function pretty(value) {
        try {
            if (typeof value === 'string') {
                try { return JSON.stringify(JSON.parse(value), null, 2); } catch (e) { return value; }
            }
            return JSON.stringify(value, null, 2);
        } catch (e) {
            return String(value);
        }
    }

    function badge(category) {
        if (category === 'dangerous') return '<span class="sag-local-badge badge-danger">خطر</span>';
        if (category === 'write') return '<span class="sag-local-badge badge-write">كتابة</span>';
        if (category === 'code_analysis') return '<span class="sag-local-badge badge-code">Data Science</span>';
        if (category === 'file_ocr') return '<span class="sag-local-badge badge-file">OCR/ملفات</span>';
        if (category === 'visualization') return '<span class="sag-local-badge badge-viz">Visualization</span>';
        if (category === 'custom') return '<span class="sag-local-badge badge-custom">Custom</span>';
        return '<span class="sag-local-badge badge-read">قراءة</span>';
    }

    function setResult(value, ok) {
        state.lastResult = value;
        const el = $('#sag-result');
        el.text(pretty(value));
        el.removeClass('sag-local-result-ok sag-local-result-bad');
        el.addClass(ok ? 'sag-local-result-ok' : 'sag-local-result-bad');
    }

    function currentArgs() {
        try { return JSON.parse($('#sag-args').val() || '{}'); } catch (e) { return {}; }
    }

    function setArgs(obj) {
        $('#sag-args').val(pretty(obj || {}));
    }

    function showFilePanel() {
        const isFileTool = state.selected && state.selected.name === 'extract_file_content';
        $('#sag-file-panel').toggleClass('active', !!isFileTool);
        if (isFileTool && !state.recentFiles.length) loadRecentFiles(false);
    }

    function selectTool(name) {
        const tool = state.tools.find(t => t.name === name);
        if (!tool) return;
        state.selected = tool;
        $('.sag-local-tool').removeClass('active');
        $(`.sag-local-tool[data-tool="${frappe.utils.escape_html(name)}"]`).addClass('active');
        $('#sag-selected-title').text(tool.name + (tool.plugin ? '  ·  ' + tool.plugin : ''));
        $('#sag-selected-desc').text(tool.description || '');
        $('#sag-selected-badge').replaceWith(`<span id="sag-selected-badge">${badge(tool.category)}</span>`);
        $('#sag-schema').text(pretty(tool.inputSchema || {}));
        $('#sag-args').val(pretty(tool.example || {}));
        $('#sag-confirm-action').prop('checked', false);
        showFilePanel();
    }

    function renderTools() {
        const q = ($('#sag-tool-search').val() || '').toLowerCase().trim();
        const filter = state.filter;
        state.filtered = state.tools.filter(t => {
            const hay = [t.name, t.description, t.plugin, t.category].join(' ').toLowerCase();
            const matchesQ = !q || hay.includes(q);
            const matchesFilter = filter === 'all' || t.category === filter;
            return matchesQ && matchesFilter;
        });

        $('#sag-tool-count').text(state.filtered.length + ' / ' + state.tools.length);

        if (!state.filtered.length) {
            $('#sag-tool-list').html('<div class="text-muted">لا توجد أدوات مطابقة.</div>');
            return;
        }

        $('#sag-tool-list').html(state.filtered.map(t => `
            <div class="sag-local-tool ${state.selected && state.selected.name === t.name ? 'active' : ''}" data-tool="${escapeHtml(t.name)}">
                <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
                    <span class="sag-local-tool-name">${escapeHtml(t.name)}</span>
                    ${badge(t.category)}
                </div>
                <div style="margin-top:4px"><span class="sag-local-plugin">${escapeHtml(t.plugin || 'unknown')}</span></div>
                <div class="sag-local-tool-desc">${escapeHtml(t.description || '')}</div>
            </div>
        `).join(''));
    }

    function loadTools() {
        $('#sag-tool-list').html('<div class="text-muted">جاري تحميل الأدوات...</div>');
        frappe.call({
            method: 'shams_ai_gateway.api.local_tools.list_all_tools',
            freeze: false,
            callback: function(r) {
                if (!r.message || !r.message.success) {
                    setResult(r.message || r, false);
                    return;
                }
                state.tools = r.message.tools || [];
                const plugins = (r.message.enabled_plugins || []).join(', ');
                $('#sag-local-stats').html(`
                    <span>المستخدم: ${escapeHtml(r.message.user)}</span>
                    <span>الأدوات: ${state.tools.length}</span>
                    <span>Plugins: ${escapeHtml(plugins || '-')}</span>
                `);
                renderTools();
                if (!state.selected && state.tools.length) {
                    const preferred = state.tools.find(t => t.name === 'extract_file_content')
                        || state.tools.find(t => t.name === 'list_documents')
                        || state.tools[0];
                    selectTool(preferred.name);
                }
            },
            error: function(r) {
                setResult(r, false);
                $('#sag-tool-list').html('<div class="text-danger">فشل تحميل الأدوات. تأكد من الصلاحيات وتفعيل Plugins.</div>');
            }
        });
    }

    function runSelectedTool() {
        if (!state.selected) {
            frappe.msgprint(__('اختر أداة أولاً'));
            return;
        }
        let argsText = $('#sag-args').val() || '{}';
        try {
            JSON.parse(argsText);
        } catch (e) {
            frappe.msgprint({title: __('JSON غير صحيح'), message: e.message, indicator: 'red'});
            return;
        }
        const confirmAction = $('#sag-confirm-action').is(':checked') ? 1 : 0;
        $('#sag-run').prop('disabled', true).text('جاري التشغيل...');
        setResult('جاري التشغيل...', true);
        frappe.call({
            method: 'shams_ai_gateway.api.local_tools.run_tool',
            type: 'POST',
            args: {
                tool_name: state.selected.name,
                arguments: argsText,
                confirm_action: confirmAction
            },
            freeze: false,
            callback: function(r) {
                $('#sag-run').prop('disabled', false).html('<i class="fa fa-play"></i> تشغيل الأداة');
                const ok = !!(r.message && r.message.success);
                setResult(r.message || r, ok);
            },
            error: function(r) {
                $('#sag-run').prop('disabled', false).html('<i class="fa fa-play"></i> تشغيل الأداة');
                setResult(r, false);
            }
        });
    }

    function loadRecentFiles(showAlert) {
        frappe.call({
            method: 'shams_ai_gateway.api.local_tools.list_recent_files',
            args: { limit: 20 },
            callback: function(r) {
                if (!r.message || !r.message.success) return;
                state.recentFiles = r.message.files || [];
                const options = ['<option value="">اختر ملفًا...</option>'].concat(state.recentFiles.map(f => {
                    const label = `${f.file_name || f.name} — ${f.file_url || ''}`;
                    return `<option value="${escapeHtml(f.file_url || '')}" data-name="${escapeHtml(f.file_name || '')}">${escapeHtml(label)}</option>`;
                }));
                $('#sag-recent-files').html(options.join(''));
                if (showAlert) frappe.show_alert({message: __('تم تحميل قائمة الملفات'), indicator: 'green'});
            }
        });
    }

    function applyFileToArgs(fileUrl, fileName) {
        if (!fileUrl) return;
        const args = currentArgs();
        args.file_url = fileUrl;
        if (fileName) args.file_name = fileName;
        if (!args.operation) args.operation = 'extract';
        if (!args.output_format) args.output_format = 'text';
        if (!args.max_pages) args.max_pages = 5;
        setArgs(args);
    }

    function uploadFile() {
        if (!frappe.ui.FileUploader) {
            frappe.msgprint(__('FileUploader غير متاح في هذا الإصدار. ارفع الملف من File Manager ثم اختره من القائمة.'));
            return;
        }
        new frappe.ui.FileUploader({
            allow_multiple: false,
            on_success(file_doc) {
                const fileUrl = file_doc.file_url || (file_doc.message && file_doc.message.file_url);
                const fileName = file_doc.file_name || file_doc.name || '';
                applyFileToArgs(fileUrl, fileName);
                loadRecentFiles(false);
                frappe.show_alert({message: __('تم رفع الملف وتعبئة file_url'), indicator: 'green'});
            }
        });
    }

    page.main.on('click', '.sag-local-tool', function() {
        selectTool($(this).data('tool'));
    });

    page.main.on('input', '#sag-tool-search', renderTools);

    page.main.on('click', '.sag-local-tab', function() {
        $('.sag-local-tab').removeClass('active');
        $(this).addClass('active');
        state.filter = $(this).data('filter');
        renderTools();
    });

    page.main.on('click', '#sag-refresh', loadTools);
    page.main.on('click', '#sag-run', runSelectedTool);

    page.main.on('click', '#sag-example', function() {
        if (!state.selected) return;
        $('#sag-args').val(pretty(state.selected.example || {}));
    });

    page.main.on('click', '#sag-format', function() {
        try {
            $('#sag-args').val(pretty(JSON.parse($('#sag-args').val() || '{}')));
        } catch (e) {
            frappe.msgprint({title: __('JSON غير صحيح'), message: e.message, indicator: 'red'});
        }
    });

    page.main.on('click', '#sag-copy-result', function() {
        const text = $('#sag-result').text() || '';
        navigator.clipboard.writeText(text).then(() => frappe.show_alert({message: __('تم نسخ النتيجة'), indicator: 'green'}));
    });

    page.main.on('click', '#sag-clear', function() {
        setResult('لم يتم التشغيل بعد.', true);
    });

    page.main.on('click', '#sag-open-admin', function() {
        frappe.set_route('sag-admin');
    });

    page.main.on('click', '#sag-refresh-files', function() {
        loadRecentFiles(true);
    });

    page.main.on('click', '#sag-upload-file', uploadFile);

    page.main.on('change', '#sag-recent-files', function() {
        const fileUrl = $(this).val();
        const fileName = $(this).find('option:selected').data('name') || '';
        applyFileToArgs(fileUrl, fileName);
    });

    loadTools();
};
