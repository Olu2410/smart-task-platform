class TeamCollaboration {
    constructor() {
        this.notificationSocket = null;
        this.chatSockets = new Map();
        this.setupEventListeners();
    }

    // Notification System
    connectNotificationSocket(userId) {
        this.notificationSocket = new WebSocket(
            `ws://${window.location.host}/ws/notifications/${userId}/`
        );

        this.notificationSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleNotificationMessage(data);
        };

        this.notificationSocket.onclose = () => {
            console.log('Notification socket closed, reconnecting...');
            setTimeout(() => this.connectNotificationSocket(userId), 3000);
        };
    }

    handleNotificationMessage(data) {
        switch (data.type) {
            case 'new_notification':
                this.showNotification(data.notification);
                this.updateNotificationBadge(data.count || 1);
                break;
            case 'unread_count':
                this.updateNotificationBadge(data.count);
                break;
        }
    }

    showNotification(notification) {
        // Create toast notification
        const toast = this.createNotificationToast(notification);
        document.body.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    createNotificationToast(notification) {
        const toast = document.createElement('div');
        toast.className = `notification-toast ${notification.type}`;
        toast.innerHTML = `
            <div class="notification-header">
                <strong>${notification.title}</strong>
                <button class="close-btn">&times;</button>
            </div>
            <div class="notification-body">${notification.message}</div>
            <div class="notification-time">${new Date(notification.created_at).toLocaleTimeString()}</div>
        `;

        toast.querySelector('.close-btn').onclick = () => toast.remove();
        toast.onclick = () => {
            window.location.href = notification.url;
            toast.remove();
        };

        return toast;
    }

    updateNotificationBadge(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        }
    }

    // Team Chat System
    connectToChannel(channelId) {
        if (this.chatSockets.has(channelId)) {
            return this.chatSockets.get(channelId);
        }

        const socket = new WebSocket(
            `ws://${window.location.host}/ws/chat/${channelId}/`
        );

        socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleChatMessage(channelId, data);
        };

        socket.onclose = () => {
            this.chatSockets.delete(channelId);
        };

        this.chatSockets.set(channelId, socket);
        return socket;
    }

    handleChatMessage(channelId, data) {
        switch (data.type) {
            case 'message_history':
                this.renderMessageHistory(channelId, data.messages);
                break;
            case 'chat_message':
                this.appendMessage(channelId, data.message);
                break;
            case 'user_typing':
                this.showTypingIndicator(channelId, data.user_id, data.username, data.typing);
                break;
            case 'message_updated':
                this.updateMessage(channelId, data.message);
                break;
        }
    }

    sendMessage(channelId, content, parentMessageId = null) {
        const socket = this.chatSockets.get(channelId);
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'chat_message',
                message: content,
                parent_message_id: parentMessageId
            }));
        }
    }

    sendTypingIndicator(channelId, isTyping) {
        const socket = this.chatSockets.get(channelId);
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'typing',
                typing: isTyping
            }));
        }
    }

    // File Sharing
    async uploadFile(teamId, file, description = '') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('team', teamId);
        formData.append('description', description);

        try {
            const response = await fetch('/api/chat/files/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('File upload failed');
            }
        } catch (error) {
            console.error('File upload error:', error);
            throw error;
        }
    }

    // Utility Methods
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    setupEventListeners() {
        // Global notification click handler
        document.addEventListener('click', (e) => {
            if (e.target.closest('.notification-item')) {
                this.markNotificationAsRead(e.target.closest('.notification-item').dataset.id);
            }
        });
    }

    markNotificationAsRead(notificationId) {
        if (this.notificationSocket && this.notificationSocket.readyState === WebSocket.OPEN) {
            this.notificationSocket.send(JSON.stringify({
                type: 'mark_read',
                notification_id: notificationId
            }));
        }
    }
}

// Initialize collaboration features
document.addEventListener('DOMContentLoaded', () => {
    window.teamCollaboration = new TeamCollaboration();
    
    // Connect to notifications if user is authenticated
    const userId = document.body.dataset.userId;
    if (userId) {
        window.teamCollaboration.connectNotificationSocket(userId);
    }
});