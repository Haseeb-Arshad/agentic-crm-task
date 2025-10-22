class AICRMApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000'; // You'll need to create this API server
        this.initializeElements();
        this.bindEvents();
        this.autoResizeTextarea();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        this.actionModal = document.getElementById('actionModal');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalBody = document.getElementById('modalBody');
        this.closeModal = document.getElementById('closeModal');
        this.loadingOverlay = document.getElementById('loadingOverlay');
    }

    bindEvents() {
        // Chat input events
        this.chatInput.addEventListener('input', () => {
            this.sendButton.disabled = !this.chatInput.value.trim();
            this.autoResizeTextarea();
        });

        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Quick action buttons
        document.querySelectorAll('.action-card').forEach(card => {
            card.addEventListener('click', () => {
                const action = card.dataset.action;
                this.openActionModal(action);
            });
        });

        // Suggestion clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.suggestions li')) {
                const suggestion = e.target.textContent.replace(/[""]/g, '');
                this.chatInput.value = suggestion;
                this.sendButton.disabled = false;
                this.chatInput.focus();
            }
        });

        // Modal events
        this.closeModal.addEventListener('click', () => this.closeActionModal());
        this.actionModal.addEventListener('click', (e) => {
            if (e.target === this.actionModal) {
                this.closeActionModal();
            }
        });

        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.actionModal.style.display === 'block') {
                this.closeActionModal();
            }
        });
    }

    autoResizeTextarea() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        this.chatInput.value = '';
        this.sendButton.disabled = true;
        this.autoResizeTextarea();

        // Show loading
        this.showLoading();

        try {
            // Send to backend
            const response = await this.callBackend(message);
            this.addMessage(response, 'assistant', 'success');
        } catch (error) {
            console.error('Error:', error);
            this.addMessage(`Sorry, I encountered an error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async callBackend(query) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.response || data.message || 'Request processed successfully';
            
        } catch (error) {
            // If the backend is not running, show a helpful message
            if (error.message.includes('fetch')) {
                throw new Error('Unable to connect to the AI CRM backend. Please make sure the API server is running on port 8000.');
            }
            throw error;
        }
    }

    addMessage(content, sender, type = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Handle different content types
        if (typeof content === 'string') {
            // Convert line breaks to HTML
            contentDiv.innerHTML = content.replace(/\n/g, '<br>');
        } else {
            contentDiv.textContent = JSON.stringify(content, null, 2);
        }
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    openActionModal(action) {
        const modalContent = this.getModalContent(action);
        this.modalTitle.textContent = modalContent.title;
        this.modalBody.innerHTML = modalContent.body;
        this.actionModal.style.display = 'block';

        // Bind form submission
        const form = this.modalBody.querySelector('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmission(action, form);
            });
        }
    }

    closeActionModal() {
        this.actionModal.style.display = 'none';
    }

    getModalContent(action) {
        const contents = {
            'create-contact': {
                title: 'Create New Contact',
                body: `
                    <form>
                        <div class="form-group">
                            <label for="email">Email *</label>
                            <input type="email" id="email" name="email" required>
                        </div>
                        <div class="form-group">
                            <label for="firstName">First Name</label>
                            <input type="text" id="firstName" name="firstName">
                        </div>
                        <div class="form-group">
                            <label for="lastName">Last Name</label>
                            <input type="text" id="lastName" name="lastName">
                        </div>
                        <div class="form-group">
                            <label for="phone">Phone</label>
                            <input type="tel" id="phone" name="phone">
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="document.getElementById('actionModal').style.display='none'">Cancel</button>
                            <button type="submit" class="btn btn-primary">Create Contact</button>
                        </div>
                    </form>
                `
            },
            'create-deal': {
                title: 'Create New Deal',
                body: `
                    <form>
                        <div class="form-group">
                            <label for="dealName">Deal Name</label>
                            <input type="text" id="dealName" name="dealName">
                        </div>
                        <div class="form-group">
                            <label for="amount">Amount ($)</label>
                            <input type="number" id="amount" name="amount" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="stage">Stage</label>
                            <select id="stage" name="stage">
                                <option value="">Select stage...</option>
                                <option value="appointmentscheduled">Appointment Scheduled</option>
                                <option value="qualifiedtobuy">Qualified to Buy</option>
                                <option value="presentationscheduled">Presentation Scheduled</option>
                                <option value="decisionmakerboughtin">Decision Maker Bought-In</option>
                                <option value="contractsent">Contract Sent</option>
                                <option value="closedwon">Closed Won</option>
                                <option value="closedlost">Closed Lost</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="associatedEmail">Associated Contact Email</label>
                            <input type="email" id="associatedEmail" name="associatedEmail">
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="document.getElementById('actionModal').style.display='none'">Cancel</button>
                            <button type="submit" class="btn btn-primary">Create Deal</button>
                        </div>
                    </form>
                `
            },
            'update-contact': {
                title: 'Update Contact',
                body: `
                    <form>
                        <div class="form-group">
                            <label for="updateEmail">Contact Email *</label>
                            <input type="email" id="updateEmail" name="email" required>
                        </div>
                        <div class="form-group">
                            <label for="updateFirstName">First Name</label>
                            <input type="text" id="updateFirstName" name="firstName">
                        </div>
                        <div class="form-group">
                            <label for="updateLastName">Last Name</label>
                            <input type="text" id="updateLastName" name="lastName">
                        </div>
                        <div class="form-group">
                            <label for="updatePhone">Phone</label>
                            <input type="tel" id="updatePhone" name="phone">
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="document.getElementById('actionModal').style.display='none'">Cancel</button>
                            <button type="submit" class="btn btn-primary">Update Contact</button>
                        </div>
                    </form>
                `
            },
            'send-email': {
                title: 'Send Confirmation Email',
                body: `
                    <form>
                        <div class="form-group">
                            <label for="emailTo">To Email</label>
                            <input type="email" id="emailTo" name="to" placeholder="Leave empty to use default recipient">
                        </div>
                        <div class="form-group">
                            <label for="emailSubject">Subject</label>
                            <input type="text" id="emailSubject" name="subject" placeholder="Leave empty for default subject">
                        </div>
                        <div class="form-group">
                            <label for="emailContent">Email Content (HTML)</label>
                            <textarea id="emailContent" name="html" rows="6" placeholder="Enter HTML content for the email..."></textarea>
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="document.getElementById('actionModal').style.display='none'">Cancel</button>
                            <button type="submit" class="btn btn-primary">Send Email</button>
                        </div>
                    </form>
                `
            }
        };

        return contents[action] || { title: 'Action', body: '<p>Action not found</p>' };
    }

    async handleFormSubmission(action, form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Remove empty values
        Object.keys(data).forEach(key => {
            if (!data[key]) delete data[key];
        });

        this.closeActionModal();
        this.showLoading();

        try {
            // Convert form data to natural language query
            const query = this.formDataToQuery(action, data);
            const response = await this.callBackend(query);
            this.addMessage(query, 'user');
            this.addMessage(response, 'assistant', 'success');
        } catch (error) {
            console.error('Error:', error);
            this.addMessage(`Error processing ${action}: ${error.message}`, 'assistant', 'error');
        } finally {
            this.hideLoading();
        }
    }

    formDataToQuery(action, data) {
        switch (action) {
            case 'create-contact':
                return `Create a contact for ${data.email}${data.firstName ? ` named ${data.firstName}` : ''}${data.lastName ? ` ${data.lastName}` : ''}${data.phone ? ` with phone ${data.phone}` : ''}`;
            
            case 'create-deal':
                let query = 'Create a deal';
                if (data.dealName) query += ` named "${data.dealName}"`;
                if (data.amount) query += ` worth $${data.amount}`;
                if (data.stage) query += ` in ${data.stage} stage`;
                if (data.associatedEmail) query += ` for contact ${data.associatedEmail}`;
                return query;
            
            case 'update-contact':
                let updateQuery = `Update contact ${data.email}`;
                const updates = [];
                if (data.firstName) updates.push(`first name to ${data.firstName}`);
                if (data.lastName) updates.push(`last name to ${data.lastName}`);
                if (data.phone) updates.push(`phone to ${data.phone}`);
                if (updates.length > 0) {
                    updateQuery += ` - set ${updates.join(', ')}`;
                }
                return updateQuery;
            
            case 'send-email':
                return `Send confirmation email${data.to ? ` to ${data.to}` : ''}${data.subject ? ` with subject "${data.subject}"` : ''} containing: ${data.html || 'default confirmation content'}`;
            
            default:
                return `Perform ${action} with data: ${JSON.stringify(data)}`;
        }
    }

    showLoading() {
        this.loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AICRMApp();
});