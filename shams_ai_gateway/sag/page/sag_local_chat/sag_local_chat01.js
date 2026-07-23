frappe.pages['sag-local-chat'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('SAG Local Chat'),
        single_column: true
    });

    page.set_title(__('SAG Local Chat'));

    const state = {
        boot: null,
        messages: [],
        busy: false,
        storage_key: 'sag_local_chat_history_v1'
    };

    const $root = $(page.body);
    $root.empty();

    const style = `
        <style>
            .sag-chat-wrap { direction: rtl; max-width: 1180px; margin: 0 auto; padding: 14px; }
            .sag-chat-top { display:flex; gap:12px; align-items:stretch; margin-bottom:12px; flex-wrap: wrap; }
            .sag-chat-card { background:#fff; border:1px solid #e6e8eb; border-radius:14px; padding:14px; box-shadow:0 2px 8px rgba(0,0,0,.04); }
            .sag-chat-status { flex:1; min-width: 300px; }
            .sag-chat-tools { width: 320px; max-width: 100%; }
            .sag-chat-title { font-size:18px; font-weight:700; margin-bottom:6px; }
            .sag-chat-sub { color:#667085; font-size:13px; line-height:1.7; }
            .sag-chat-messages { height: calc(100vh - 330px); min-height: 430px; overflow:auto; background:#f8fafc; border:1px solid #e6e8eb; border-radius:14px; padding:16px; }
            .sag-msg { display:flex; margin-bottom:14px; }
            .sag-msg.user { justify-content:flex-start; }
            .sag-msg.assistant { justify-content:flex-end; }
            .sag-bubble { max-width: 78%; border-radius:14px; padding:12px 14px; line-height:1.75; white-space:pre-wrap; word-break:break-word; }
            .sag-msg.user .sag-bubble { background:#e8f0fe; border:1px solid #d5e3ff; }
            .sag-msg.assistant .sag-bubble { background:#fff; border:1px solid #e6e8eb; }
            .sag-msg.error .sag-bubble { background:#fff1f1; border:1px solid #ffd0d0; color:#9b1c1c; }
            .sag-msg-meta { color:#98a2b3; font-size:11px; margin-top:6px; }
            .sag-composer { display:flex; gap:10px; margin-top:12px; align-items:flex-end; }
            .sag-input { flex:1; min-height:72px; resize:vertical; border:1px solid #d0d5dd; border-radius:12px; padding:12px; direction:rtl; }
            .sag-actions { display:flex; flex-direction:column; gap:8px; }
            .sag-btn { border:0; border-radius:10px; padding:10px 16px; font-weight:600; cursor:pointer; }
            .sag-btn-primary { background:#171717; color:#fff; }
            .sag-btn-secondary { background:#f2f4f7; color:#344054; }
            .sag-btn:disabled { opacity:.6; cursor:not-allowed; }
            .sag-examples { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
            .sag-chip { background:#f2f4f7; border:1px solid #e6e8eb; border-radius:999px; padding:6px 10px; font-size:12px; cursor:pointer; }
            .sag-tool-list { max-height:130px; overflow:auto; margin-top:8px; font-size:12px; line-height:1.8; color:#475467; direction:ltr; text-align:left; }
            .sag-trace { margin-top:10px; border-top:1px dashed #e6e8eb; padding-top:8px; direction:ltr; text-align:left; font-size:12px; color:#475467; white-space:normal; }
            .sag-loader { display:inline-block; width:10px; height:10px; border-radius:50%; background:#111; animation:facPulse .9s infinite alternate; margin-inline-start:6px; }
            @keyframes facPulse { from { opacity:.25; transform:scale(.8); } to { opacity:1; transform:scale(1.1); } }
            @media (max-width: 768px) { .sag-bubble { max-width: 94%; } .sag-chat-messages { height: 55vh; } .sag-chat-tools { width:100%; } }
        </style>`;

    const html = `
        ${style}
        <div class="sag-chat-wrap">
            <div class="sag-chat-top">
                <div class="sag-chat-card sag-chat-status">
                    <div class="sag-chat-title" data-role="title">SAG Local Chat</div>
                    <div class="sag-chat-sub" data-role="status">جاري تحميل إعدادات الشات...</div>
                    <div class="sag-examples">
                        <span class="sag-chip" data-example="اعرض أول 5 Customers">أول 5 Customers</span>
                        <span class="sag-chip" data-example="اعرض آخر 5 Sales Invoice">آخر 5 Sales Invoice</span>
                        <span class="sag-chip" data-example="ما هي الأدوات المتاحة؟">الأدوات المتاحة</span>
                        <span class="sag-chip" data-example="اعرض طلبات الموافقة المعلقة">الموافقات المعلقة</span>
                    </div>
                </div>
                <div class="sag-chat-card sag-chat-tools">
                    <div style="font-weight:700;">الأدوات المحلية</div>
                    <div class="sag-chat-sub" data-role="tool-summary">—</div>
                    <div class="sag-tool-list" data-role="tool-list"></div>
                </div>
            </div>
            <div class="sag-chat-messages" data-role="messages"></div>
            <div class="sag-composer">
                <textarea class="sag-input" data-role="input" placeholder="اكتب سؤالك هنا... مثال: اعرض آخر 5 فواتير مبيعات"></textarea>
                <div class="sag-actions">
                    <button class="sag-btn sag-btn-primary" data-role="send">إرسال</button>
                    <button class="sag-btn sag-btn-secondary" data-role="clear">مسح</button>
                </div>
            </div>
        </div>`;

    $root.html(html);

    const $messages = $root.find('[data-role="messages"]');
    const $input = $root.find('[data-role="input"]');
    const $send = $root.find('[data-role="send"]');
    const $clear = $root.find('[data-role="clear"]');

    function escapeHtml(text) {
        return $('<div/>').text(text || '').html();
    }

    function markdownLite(text) {
        text = escapeHtml(text || '');
        text = text.replace(/```([\s\S]*?)```/g, '<pre style="direction:ltr;text-align:left;background:#0b1020;color:#f8fafc;padding:10px;border-radius:8px;overflow:auto;">$1</pre>');
        text = text.replace(/`([^`]+)`/g, '<code style="direction:ltr;background:#f2f4f7;padding:2px 4px;border-radius:4px;">$1</code>');
        return text;
    }

    function renderMessages() {
        $messages.empty();
        if (!state.messages.length) {
            $messages.append(`
                <div class="sag-msg assistant">
                    <div class="sag-bubble">
                        مرحبًا، هذه صفحة شات محلية داخل ERPNext تستخدم مزود الذكاء الاصطناعي المحدد في <b>SAG Local Chat Settings</b> وتستدعي أدوات <b>Shams AI Gateway</b> محليًا حسب ما هو مفعّل من SAG Admin.
                    </div>
                </div>
            `);
        }
        state.messages.forEach((msg) => {
            const trace = msg.trace && msg.trace.length ? `
                <div class="sag-trace">
                    <b>Tool calls:</b> ${msg.trace.length}<br>
                    ${msg.trace.map(t => `${escapeHtml(t.tool_name || '')} — ${t.success ? 'OK' : 'ERR'} — ${t.execution_ms || 0}ms`).join('<br>')}
                </div>` : '';
            $messages.append(`
                <div class="sag-msg ${msg.role} ${msg.error ? 'error' : ''}">
                    <div class="sag-bubble">
                        ${markdownLite(msg.content)}
                        ${trace}
                        <div class="sag-msg-meta">${msg.role === 'user' ? 'أنت' : 'المساعد المحلي'} · ${msg.time || ''}</div>
                    </div>
                </div>
            `);
        });
        $messages.scrollTop($messages[0].scrollHeight);
    }

    function saveHistory() {
        if (!state.boot || !state.boot.settings || !state.boot.settings.keep_chat_history) return;
        try {
            localStorage.setItem(state.storage_key, JSON.stringify(state.messages.slice(-40)));
        } catch (e) {}
    }

    function loadHistory() {
        try {
            const raw = localStorage.getItem(state.storage_key);
            if (raw) state.messages = JSON.parse(raw) || [];
        } catch (e) { state.messages = []; }
    }

    function setBusy(busy) {
        state.busy = busy;
        $send.prop('disabled', busy);
        $input.prop('disabled', busy);
        $send.html(busy ? 'جاري الإرسال <span class="sag-loader"></span>' : 'إرسال');
    }

    function addMessage(role, content, extra={}) {
        state.messages.push({ role, content, time: frappe.datetime.now_datetime(), ...extra });
        renderMessages();
        saveHistory();
    }

    function getHistoryForServer() {
        return state.messages
            .filter(m => ['user', 'assistant'].includes(m.role) && !m.error)
            .slice(-20)
            .map(m => ({ role: m.role, content: m.content }));
    }

    function boot() {
        frappe.call({
            method: 'shams_ai_gateway.local_chat.chat_api.get_boot',
            callback: function(r) {
                if (!r.message || !r.message.success) {
                    $root.find('[data-role="status"]').text('تعذر تحميل إعدادات الشات.');
                    return;
                }
                state.boot = r.message;
                const s = state.boot.settings || {};
                page.set_title(__(s.chat_title || 'SAG Local Chat'));
                $root.find('[data-role="title"]').text(s.chat_title || 'SAG Local Chat');
                $root.find('[data-role="status"]').html(`المستخدم: <b>${escapeHtml(state.boot.user)}</b> · المزود: <b>${escapeHtml(s.provider)}</b> · الموديل: <b>${escapeHtml(s.model)}</b>`);
                $root.find('[data-role="tool-summary"]').text(`${state.boot.tool_count || 0} أداة متاحة حسب SAG Admin وصلاحيات المستخدم`);
                const names = (state.boot.tools || []).map(t => t.name).slice(0, 80);
                $root.find('[data-role="tool-list"]').html(names.map(n => `<div>${escapeHtml(n)}</div>`).join(''));
                loadHistory();
                renderMessages();
            },
            error: function() {
                $root.find('[data-role="status"]').text('حدث خطأ أثناء تحميل إعدادات الشات.');
            }
        });
    }

    function send() {
        const text = ($input.val() || '').trim();
        if (!text || state.busy) return;
        addMessage('user', text);
        $input.val('');
        setBusy(true);

        frappe.call({
            method: 'shams_ai_gateway.local_chat.chat_api.send_message',
            type: 'POST',
            args: {
                message: text,
                history: JSON.stringify(getHistoryForServer())
            },
            callback: function(r) {
                setBusy(false);
                const msg = r.message || {};
                if (!msg.success) {
                    addMessage('assistant', msg.error || 'حدث خطأ غير معروف.', { error: true });
                    return;
                }
                addMessage('assistant', msg.answer || '', { trace: msg.tool_trace || [] });
            },
            error: function(xhr) {
                setBusy(false);
                let errorText = 'حدث خطأ أثناء الاتصال بالسيرفر.';
                try {
                    if (xhr.responseJSON && xhr.responseJSON._server_messages) {
                        errorText = JSON.parse(JSON.parse(xhr.responseJSON._server_messages)[0]).message;
                    }
                } catch(e) {}
                addMessage('assistant', errorText, { error: true });
            }
        });
    }

    $send.on('click', send);
    $clear.on('click', function() {
        frappe.confirm('مسح سجل المحادثة من المتصفح؟', () => {
            state.messages = [];
            localStorage.removeItem(state.storage_key);
            renderMessages();
        });
    });
    $input.on('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    });
    $root.find('[data-example]').on('click', function() {
        $input.val($(this).attr('data-example')).focus();
    });

    boot();
};
