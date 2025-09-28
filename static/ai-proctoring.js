// =============================================
// FREE AI PERSON DETECTION WITH COCO-SSD
// =============================================

class AIPersonDetector {
    constructor() {
        this.model = null;
        this.isActive = false;
        this.maxPersons = 1;
    }

    async init() {
        console.log('🤖 Loading COCO-SSD AI model...');
        
        // Load TensorFlow.js (free)
        const script1 = document.createElement('script');
        script1.src = 'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.2.0/dist/tf.min.js'\;
        document.head.appendChild(script1);
        await new Promise(resolve => script1.onload = resolve);

        // Load COCO-SSD model (free)
        const script2 = document.createElement('script');
        script2.src = 'https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd@2.2.2/dist/coco-ssd.min.js'\;
        document.head.appendChild(script2);
        await new Promise(resolve => script2.onload = resolve);

        // Initialize model
        this.model = await cocoSsd.load();
        console.log('✅ AI model loaded - ready for person detection!');
        
        return true;
    }

    async startDetection() {
        try {
            // Get webcam access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 640, height: 480 }
            });
            
            // Create video element
            this.video = document.createElement('video');
            this.video.srcObject = stream;
            this.video.autoplay = true;
            this.video.muted = true;
            this.video.style.display = 'none';
            document.body.appendChild(this.video);
            
            // Wait for video to load
            await new Promise(resolve => this.video.onloadedmetadata = resolve);
            
            this.isActive = true;
            console.log('📹 AI person detection started');
            
            // Add system message
            if (typeof window.addMessage === 'function') {
                window.addMessage('system', '🤖 AI proctoring active. Camera monitoring for multiple people.');
            }
            
            // Check every 10 seconds
            this.detectionInterval = setInterval(() => {
                this.detectPersons();
            }, 10000);
            
            // Initial check after 5 seconds
            setTimeout(() => this.detectPersons(), 5000);
            
        } catch (error) {
            console.error('❌ Camera access denied:', error);
            if (typeof window.addMessage === 'function') {
                window.addMessage('system', '⚠️ Camera access required for AI proctoring.');
            }
        }
    }

    async detectPersons() {
        if (!this.isActive || !this.model) return;
        
        try {
            // Run AI detection on video frame
            const predictions = await this.model.detect(this.video);
            
            // Count people (filter for person class with >50% confidence)
            const people = predictions.filter(pred => 
                pred.class === 'person' && pred.score > 0.5
            );
            
            console.log(`🔍 AI detected ${people.length} person(s)`);
            
            if (people.length > this.maxPersons) {
                this.handleCheatingDetected(people.length);
            }
            
        } catch (error) {
            console.error('❌ AI detection error:', error);
        }
    }

    handleCheatingDetected(personCount) {
        console.log('🚨 CHEATING DETECTED! Multiple people found');
        
        this.isActive = false;
        clearInterval(this.detectionInterval);
        
        // Stop camera
        if (this.video && this.video.srcObject) {
            this.video.srcObject.getTracks().forEach(track => track.stop());
        }
        
        // Show termination modal
        this.showAITerminationModal(personCount);
        
        // Stop voice if active
        if (window.voiceInterview && window.voiceInterview.active) {
            window.stopVoiceInterview();
        }
    }

    showAITerminationModal(count) {
        const modal = document.createElement('div');
        modal.className = 'modal fade show';
        modal.style.display = 'block';
        modal.style.backgroundColor = 'rgba(0,0,0,0.9)';
        
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content bg-danger text-white">
                    <div class="modal-header border-0">
                        <h5 class="modal-title">
                            <i class="fas fa-robot me-2"></i>
                            AI Security Alert
                        </h5>
                    </div>
                    <div class="modal-body text-center">
                        <div class="mb-3">
                            <i class="fas fa-users" style="font-size: 4rem;"></i>
                        </div>
                        <h4>Multiple People Detected</h4>
                        <p>Our AI system detected <strong>${count} people</strong> during your interview.</p>
                        <div class="alert alert-warning text-dark">
                            <strong>Interview Terminated</strong><br>
                            <small>AI-powered proctoring ensures fair assessment</small>
                        </div>
                        <p class="text-muted">Powered by TensorFlow.js COCO-SSD</p>
                    </div>
                    <div class="modal-footer border-0 justify-content-center">
                        <button type="button" class="btn btn-light text-dark" onclick="window.close()">
                            Close Interview
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Report to server
        fetch('/api/ai-violation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'multiple_persons_ai',
                count: count,
                model: 'COCO-SSD',
                timestamp: new Date().toISOString()
            })
        }).catch(err => console.log('Failed to report AI violation'));
    }
}

// Initialize AI person detector
window.aiPersonDetector = new AIPersonDetector();

// Auto-start when page loads
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🤖 Initializing AI Person Detection...');
    
    const success = await window.aiPersonDetector.init();
    if (success) {
        // Start detection after 3 seconds
        setTimeout(() => {
            window.aiPersonDetector.startDetection();
        }, 3000);
    }
});

console.log('✅ AI Proctoring System loaded');
