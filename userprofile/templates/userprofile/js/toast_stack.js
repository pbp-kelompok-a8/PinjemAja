function showToastStack(items, duration = 4000) {
    let stack = document.getElementById('toast-stack');
    if (!stack) {
        stack = document.createElement('div');
        stack.id = 'toast-stack';
        document.body.appendChild(stack);
    }
    items.forEach((item) => {
        const el = document.createElement('div');
        el.className = 'toast-item toast-item-' + (item.type || 'normal');
        const title = document.createElement('strong');
        title.textContent = item.title;
        const msg = document.createElement('div');
        msg.textContent = item.message;
        el.append(title, msg);
        stack.appendChild(el);
        setTimeout(() => el.remove(), duration);
    });
}