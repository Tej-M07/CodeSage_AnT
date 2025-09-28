// =============================================
// ENTERPRISE ANTI-CHEAT SYSTEM
// =============================================
console.log('🛡️ Loading Anti-Cheat System...');

class AntiCheatSystem {
    constructor() {
        this.strikes = 0;
        this.maxStrikes = 3;
        this.isActive = false;
        this.violations = [];
        this.warningModal = null;
        this.terminatedModal = null;
        
        console.log('🛡️ Anti-Cheat System initialized');
    }

    init() {
        try {
            // Initialize modals
            this.warningModal = new bootstrap.Modal(document.getElementById('cheatWarningModal'));
            this.terminatedModal = new bootstrap.Modal(document.getElementById('terminatedModal'));
            
            // Start monitoring
            this.startMonitoring();
            
            console.log('✅ Anti-Cheat System ready');
            this.addSystemMessage('🛡️ Interview security monitoring active. Stay in this window at all times.');
            
        } catch (error) {
            console.error('❌ Anti-Cheat initialization error:', error);
        }
    }

    startMonitoring() {
        this.isActive = true;
        console.log('🛡️ Anti-cheat monitoring started');
        
        // Window focus/blur detection
        window.addEventListener('blur', () => this.handleWindowSwitch());
        window.addEventListener('focus', () => this.handleWindowReturn());
        
        // Page visibility API (more reliable)
        document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
        
        // Keyboard shortcuts detection
        document.addEventListener('keydown', (event) => this.handleKeyboardShortcuts(event));
        
        // Mouse leave detection
        document.addEventListener('mouseleave', () => this.handleMouseLeave());
        
        console.log('🛡️ All anti-cheat listeners attached');
    }

    handleWindowSwitch() {
        if (!this.isActive) return;
        
        console.log('🚨 Window switch detected!');
        this.logViolation('window_blur', 'User switched away from interview window');
        this.triggerViolationWarning('Window Switch Detected', 'You switched away from the interview window.');
    }

    handleVisibilityChange() {
        if (!this.isActive) return;
        
        if (document.hidden) {
            console.log('🚨 Tab switch detected!');
            this.logViolation('tab_switch', 'User switched to different tab or minimized window');
            this.triggerViolationWarning('Tab Switch Detected', 'You switched to a different tab or minimized the window.');
        }
    }

    handleKeyboardShortcuts(event) {
        if (!this.isActive) return;
        
        // Detect Alt+Tab, Cmd+Tab, Ctrl+Tab, etc.
        if ((event.altKey && event.key === 'Tab') ||
            (event.metaKey && event.key === 'Tab') ||
            (event.ctrlKey && event.key === 'Tab')) {
            
            event.preventDefault();
            console.log('🚨 Forbidden shortcut detected!');
            this.logViolation('keyboard_shortcut', `Keyboard shortcut detected: ${event.key} with modifiers`);
            this.triggerViolationWarning('Forbidden Shortcut', 'Window switching shortcuts are not allowed during the interview.');
        }
    }

    handleMouseLeave() {
        if (!this.isActive) return;
        
        // Only trigger if mouse leaves the entire document area
        setTimeout(() => {
            if (!document.hasFocus()) {
                console.log('🚨 Focus lost detected!');
                this.logViolation('mouse_leave', 'Mouse left interview area and window lost focus');
            }
        }, 100);
    }

    handleWindowReturn() {
        if (!this.isActive) return;
        console.log('🛡️ User returned to interview window');
    }

    logViolation(type, description) {
        const violation = {
            type: type,
            description: description,
            timestamp: new Date().toISOString(),
            currentCode: window.editor ? window.editor.getValue() : 'No code',
            strikeNumber: this.strikes + 1
        };
        
        this.violations.push(violation);
        console.log('🚨 Security violation logged:', violation);
        
        // Send to backend for logging
        fetch('/api/log-violation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(violation)
        }).catch(err => console.log('Failed to log violation to server:', err));
    }

    triggerViolationWarning(title, message) {
        this.strikes++;
        console.log(`🚨 Strike ${this.strikes}/${this.maxStrikes}: ${title}`);
        
        // Update modal content
        document.getElementById('warningTitle').textContent = title;
        document.getElementById('warningMessage').textContent = message;
        document.getElementById('currentStrike').textContent = this.strikes;
        
        if (this.strikes >= this.maxStrikes) {
            this.terminateInterview();
            return;
        }
        
        // Show warning modal with countdown
        this.warningModal.show();
        this.startWarningCountdown();
        
        // Add violation message to chat
        this.addSystemMessage(`🚨 Security Warning: ${title} (Strike ${this.strikes}/${this.maxStrikes})`);
        
        // Voice warning if voice is active
        if (window.voiceInterview && window.voiceInterview.active) {
            window.speakAI(`Security warning! You have ${this.maxStrikes - this.strikes} strikes remaining.`);
        }
    }

    startWarningCountdown() {
        let countdown = 5;
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            countdownEl.textContent = countdown;
            countdown--;
            
            if (countdown < 0) {
                clearInterval(timer);
                this.warningModal.hide();
            }
        }, 1000);
    }

    terminateInterview() {
        this.isActive = false;
        console.log('🚫 Interview terminated due to security violations');
        
        // Show termination modal
        this.terminatedModal.show();
        
        // Stop voice interview if active
        if (window.voiceInterview && window.voiceInterview.active) {
            window.stopVoiceInterview();
        }
        
        // Add final message
        this.addSystemMessage('🚫 Interview terminated due to security violations. Final report generated.');
        
        // Send final violation report
        fetch('/api/terminate-interview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                reason: 'security_violations',
                strikes: this.strikes,
                violations: this.violations,
                finalCode: window.editor ? window.editor.getValue() : 'No code'
            })
        });
    }

    addSystemMessage(message) {
        // Try to add message to chat if addMessage function exists
        if (typeof window.addMessage === 'function') {
            window.addMessage('system', message);
        } else {
            console.log('System message:', message);
        }
    }

    // Manual test function
    test() {
        console.log('🧪 Testing anti-cheat system...');
        this.triggerViolationWarning('Manual Test', 'Testing the security system manually');
    }
}

// Create global anti-cheat instance
window.antiCheatSystem = new AntiCheatSystem();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🛡️ DOM ready, initializing anti-cheat...');
    window.antiCheatSystem.init();
});

// For backwards compatibility
window.antiCheat = window.antiCheatSystem;

console.log('✅ Anti-Cheat System loaded successfully');
