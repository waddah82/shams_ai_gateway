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
        attachments: [],
        busy: false,
        uploading: false,
        storage_key: 'sag_local_chat_history_v2'
    };

    const $root = $(wrapper).find('.layout-main-section');

    const style = `
        <style>
            .sag-chat-wrap { direction:rtl; font-family:inherit; }
            .sag-chat-top { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:12px; }
            .sag-chat-card { background:#fff; border:1px solid #e6e8eb; border-radius:14px; padding:14px; box-shadow:0 2px 6px rgba(16,24,40,.04); }
            .sag-chat-status { flex:1; min-width:280px; }
            .sag-chat-tools { width:330px; min-width:260px; }
            .sag-chat-title { font-size:18px; font-weight:700; margin-bottom:6px; }
            .sag-chat-sub { color:#667085; font-size:13px; line-height:1.7; }
            .sag-chat-messages { height:58vh; overflow:auto; background:#f8fafc; border:1px solid #e6e8eb; border-radius:14px; padding:16px; }
            .sag-msg { display:flex; margin-bottom:14px; }
            .sag-msg.user { justify-content:flex-start; }
            .sag-msg.assistant { justify-content:flex-end; }
            .sag-bubble { max-width: 78%; border-radius:14px; padding:12px 14px; line-height:1.75; white-space:pre-wrap; word-break:break-word; }
            .sag-msg.user .sag-bubble { background:#e8f0fe; border:1px solid #d5e3ff; }
            .sag-msg.assistant .sag-bubble { background:#fff; border:1px solid #e6e8eb; }
            .sag-msg.error .sag-bubble { background:#fff1f1; border:1px solid #ffd0d0; color:#9b1c1c; }
            .sag-msg-meta { color:#98a2b3; font-size:11px; margin-top:6px; }
            .sag-composer { display:flex; gap:10px; margin-top:12px; align-items:flex-end; }
            .sag-input-zone { flex:1; }
            .sag-input { width:100%; min-height:72px; resize:vertical; border:1px solid #d0d5dd; border-radius:12px; padding:12px; direction:rtl; }
            .sag-actions { display:flex; flex-direction:column; gap:8px; }
            .sag-btn { border:0; border-radius:10px; padding:10px 16px; font-weight:600; cursor:pointer; white-space:nowrap; }
            .sag-btn-primary { background:#171717; color:#fff; }
            .sag-btn-secondary { background:#f2f4f7; color:#344054; }
            .sag-btn-warning { background:#fff7e6; color:#92400e; border:1px solid #fed7aa; }
            .sag-btn:disabled { opacity:.6; cursor:not-allowed; }
            .sag-examples { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
            .sag-chip { background:#f2f4f7; border:1px solid #e6e8eb; border-radius:999px; padding:6px 10px; font-size:12px; cursor:pointer; }
            .sag-tool-list { max-height:130px; overflow:auto; margin-top:8px; font-size:12px; line-height:1.8; color:#475467; direction:ltr; text-align:left; }
            .sag-trace { margin-top:10px; border-top:1px dashed #e6e8eb; padding-top:8px; direction:ltr; text-align:left; font-size:12px; color:#475467; white-space:normal; }
            .sag-loader { display:inline-block; width:10px; height:10px; border-radius:50%; background:#111; animation:facPulse .9s infinite alternate; margin-inline-start:6px; }
            .sag-attach-bar { margin-top:8px; display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
            .sag-attach-list { margin-top:8px; display:flex; gap:8px; flex-wrap:wrap; }
            .sag-attach-item { border:1px solid #d0d5dd; background:#fff; border-radius:12px; padding:7px 10px; display:flex; gap:8px; align-items:center; max-width:100%; }
            .sag-attach-name { direction:ltr; text-align:left; max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#344054; font-size:12px; }
            .sag-attach-remove, .sag-attach-ocr { border:0; background:#f2f4f7; border-radius:8px; padding:4px 8px; cursor:pointer; font-size:12px; }
            .sag-attach-ocr { background:#eef4ff; color:#3538cd; }
            .sag-help { color:#667085; font-size:12px; margin-top:4px; }
            @keyframes facPulse { from { opacity:.25; transform:scale(.8); } to { opacity:1; transform:scale(1.1); } }
            @media (max-width: 768px) { .sag-bubble { max-width: 94%; } .sag-chat-messages { height: 55vh; } .sag-chat-tools { width:100%; } .sag-composer { flex-direction:column; align-items:stretch; } .sag-actions { flex-direction:row; } }
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
                        <span class="sag-chip" data-example="اقرأ الصورة المرفقة واستخرج النص منها ثم لخصها">OCR للصورة</span>
                        <span class="sag-chip" data-example="ما هي الأدوات المتاحة؟">الأدوات المتاحة</span>
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
                <div class="sag-input-zone">
                    <textarea class="sag-input" data-role="input" placeholder="اكتب سؤالك هنا... ويمكنك إرفاق صورة أو PDF ثم طلب قراءته بواسطة Mistral OCR"></textarea>
                    <div class="sag-attach-bar">
                        <button class="sag-btn sag-btn-secondary" data-role="attach">إرفاق صورة / PDF</button>
                        <span class="sag-help">يتم حفظ المرفق كملف خاص ثم استخراج النص عبر Mistral OCR عند الإرسال.</span>
                        <input type="file" data-role="file" accept="image/*,application/pdf,.pdf" multiple style="display:none;" />
                    </div>
                    <div class="sag-attach-list" data-role="attachments"></div>
                </div>
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
    const $attach = $root.find('[data-role="attach"]');
    const $file = $root.find('[data-role="file"]');
    const $attachments = $root.find('[data-role="attachments"]');

    function escapeHtml(text) { return $('<div/>').text(text || '').html(); }

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
                        مرحبًا، هذه صفحة شات محلية داخل ERPNext. يمكنك الآن إرفاق صورة أو PDF، وسيتم استخراج النص عبر <b>Mistral OCR</b> ثم استخدام أدوات <b>Shams AI Gateway</b> حسب ما هو مفعّل من SAG Admin.
                    </div>
                </div>
            `);
        }
        state.messages.forEach((msg) => {
            const trace = msg.trace && msg.trace.length ? `
                <div class="sag-trace">
                    <b>Tool/OCR calls:</b> ${msg.trace.length}<br>
                    ${msg.trace.map(t => `${escapeHtml(t.tool_name || t.ocr_provider || '')} — ${t.success ? 'OK' : 'ERR'} — ${t.execution_ms || 0}ms`).join('<br>')}
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

    function renderAttachments() {
        $attachments.empty();
        state.attachments.forEach((att, idx) => {
            const size = att.size_bytes ? ` · ${(att.size_bytes / 1024).toFixed(1)} KB` : '';
            $attachments.append(`
                <div class="sag-attach-item" data-idx="${idx}">
                    <span>📎</span>
                    <span class="sag-attach-name">${escapeHtml(att.file_name)}${size}</span>
                    <button class="sag-attach-ocr" data-ocr="${idx}">OCR الآن</button>
                    <button class="sag-attach-remove" data-remove="${idx}">حذف</button>
                </div>
            `);
        });
    }

    function saveHistory() {
        if (!state.boot || !state.boot.settings || !state.boot.settings.keep_chat_history) return;
        try { localStorage.setItem(state.storage_key, JSON.stringify(state.messages.slice(-40))); } catch (e) {}
    }

    function loadHistory() {
        try {
            const raw = localStorage.getItem(state.storage_key);
            if (raw) state.messages = JSON.parse(raw) || [];
        } catch (e) { state.messages = []; }
    }

    function setBusy(busy) {
        state.busy = busy;
        $send.prop('disabled', busy || state.uploading);
        $input.prop('disabled', busy);
        $attach.prop('disabled', busy || state.uploading);
        $send.html(busy ? 'جاري الإرسال <span class="sag-loader"></span>' : 'إرسال');
    }

    function setUploading(uploading) {
        state.uploading = uploading;
        $attach.prop('disabled', uploading || state.busy);
        $send.prop('disabled', uploading || state.busy);
        $attach.html(uploading ? 'جاري الرفع <span class="sag-loader"></span>' : 'إرفاق صورة / PDF');
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
                $root.find('[data-role="status"]').html(`المستخدم: <b>${escapeHtml(state.boot.user)}</b> · المزود: <b>${escapeHtml(s.provider)}</b> · الموديل: <b>${escapeHtml(s.model)}</b> · OCR: <b>Mistral</b>`);
                $root.find('[data-role="tool-summary"]').text(`${state.boot.tool_count || 0} أداة متاحة حسب SAG Admin وصلاحيات المستخدم`);
                const names = (state.boot.tools || []).map(t => t.name).slice(0, 80);
                $root.find('[data-role="tool-list"]').html(names.map(n => `<div>${escapeHtml(n)}</div>`).join(''));
                loadHistory();
                renderMessages();
            },
            error: function() { $root.find('[data-role="status"]').text('حدث خطأ أثناء تحميل إعدادات الشات.'); }
        });
    }

    function readFileAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    async function uploadSelectedFiles(files) {
        if (!files || !files.length) return;
        setUploading(true);
        try {
            for (const file of Array.from(files)) {
                const dataUrl = await readFileAsDataURL(file);
                await new Promise((resolve, reject) => {
                    frappe.call({
                        method: 'shams_ai_gateway.local_chat.chat_api.upload_chat_file',
                        type: 'POST',
                        args: { file_name: file.name, file_data: dataUrl },
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                state.attachments.push(r.message);
                                renderAttachments();
                                resolve();
                            } else {
                                reject(new Error((r.message && r.message.error) || 'فشل رفع الملف'));
                            }
                        },
                        error: function(xhr) { reject(xhr); }
                    });
                });
            }
        } catch (e) {
            frappe.msgprint('فشل رفع الملف. تأكد أن الملف صورة أو PDF وحجمه مناسب.');
        } finally {
            setUploading(false);
            $file.val('');
        }
    }

    function runOcr(idx) {
        const att = state.attachments[idx];
        if (!att) return;
        setBusy(true);
        frappe.call({
            method: 'shams_ai_gateway.local_chat.chat_api.ocr_file',
            type: 'POST',
            args: { file_docname: att.file_docname },
            callback: function(r) {
                setBusy(false);
                const msg = r.message || {};
                if (!msg.success) {
                    addMessage('assistant', msg.error || 'فشل OCR.', { error: true });
                    return;
                }
                addMessage('assistant', `تم استخراج النص من ${msg.file_name || att.file_name}:\n\n${msg.text || '[لا يوجد نص مستخرج]'}`, { trace: [msg] });
            },
            error: function() {
                setBusy(false);
                addMessage('assistant', 'حدث خطأ أثناء تشغيل Mistral OCR.', { error: true });
            }
        });
    }

    function send() {
        let text = ($input.val() || '').trim();
        if (!text && state.attachments.length) {
            text = 'اقرأ المرفقات واستخرج النص ثم لخّص المحتوى.';
        }
        if (!text || state.busy || state.uploading) return;
        const attached = state.attachments.slice();
        const attachedNames = attached.length ? '\n\nالمرفقات: ' + attached.map(a => a.file_name).join(', ') : '';
        addMessage('user', text + attachedNames);
        $input.val('');
        setBusy(true);

        frappe.call({
            method: 'shams_ai_gateway.local_chat.chat_api.send_message',
            type: 'POST',
            args: {
                message: text,
                history: JSON.stringify(getHistoryForServer()),
                attachments: JSON.stringify(attached)
            },
            callback: function(r) {
                setBusy(false);
                const msg = r.message || {};
                if (!msg.success) {
                    addMessage('assistant', msg.error || 'حدث خطأ غير معروف.', { error: true });
                    return;
                }
                addMessage('assistant', msg.answer || '', { trace: msg.tool_trace || [] });
                state.attachments = [];
                renderAttachments();
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
    $attach.on('click', function() { $file.trigger('click'); });
    $file.on('change', function(e) { uploadSelectedFiles(e.target.files); });
    $attachments.on('click', '[data-remove]', function() {
        const idx = parseInt($(this).attr('data-remove'), 10);
        state.attachments.splice(idx, 1);
        renderAttachments();
    });
    $attachments.on('click', '[data-ocr]', function() {
        const idx = parseInt($(this).attr('data-ocr'), 10);
        runOcr(idx);
    });
    $clear.on('click', function() {
        frappe.confirm('مسح سجل المحادثة من المتصفح؟', () => {
            state.messages = [];
            state.attachments = [];
            localStorage.removeItem(state.storage_key);
            renderMessages();
            renderAttachments();
        });
    });
    $input.on('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    });
    $root.find('[data-example]').on('click', function() { $input.val($(this).attr('data-example')).focus(); });

    boot();
};
