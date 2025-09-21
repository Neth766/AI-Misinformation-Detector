// Create animated particles
function createParticles() {
    const particles = document.getElementById('particles');
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 6 + 's';
        particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
        particles.appendChild(particle);
    }
}

// Analyze text function
async function analyzeText() {
    const textInput = document.getElementById('textInput');
    const resultDiv = document.getElementById('result');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    const text = textInput.value.trim();
    
    if (!text) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'result-container result-suspicious';
        resultDiv.innerHTML = '⚠️ Please enter some text to analyze for misinformation.';
        return;
    }
    
    // Show loading state
    resultDiv.style.display = 'block';
    resultDiv.className = 'result-container loading';
    resultDiv.innerHTML = '🔄 AI is analyzing the text for misinformation patterns...';
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '🔄 ANALYZING...';
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        
        let resultClass, emoji, message;
        
        if (data.label === 'RELIABLE') {
            resultClass = 'result-reliable';
            emoji = '✅';
            message = `This text appears to be RELIABLE and trustworthy (${data.confidence}% confidence)`;
        } else if (data.label === 'SUSPICIOUS') {
            resultClass = 'result-suspicious';
            emoji = '⚠️';
            message = `This text shows SUSPICIOUS patterns that may indicate misinformation (${data.confidence}% confidence)`;
        } else {
            resultClass = 'result-fake';
            emoji = '🚨';
            message = `DANGER: This text likely contains MISINFORMATION! (${data.confidence}% confidence)`;
        }
        
        resultDiv.className = 'result-container ' + resultClass;
        resultDiv.innerHTML = `
            ${emoji} ${message}
            <br><small>Always verify with multiple trusted sources!</small>
        `;
        
    } catch (error) {
        resultDiv.className = 'result-container result-fake';
        resultDiv.innerHTML = '❌ Error analyzing text. Please try again or check your connection.';
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '🚀 ANALYZE TEXT';
    }
}

// Event listeners
document.getElementById('analyzeBtn').addEventListener('click', analyzeText);

document.getElementById('textInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.ctrlKey) {
        analyzeText();
    }
});

// Initialize particles when page loads
document.addEventListener('DOMContentLoaded', createParticles);

// Add some interactive examples
const exampleTexts = [
    "Scientists have discovered a revolutionary cure that big pharma doesn't want you to know about!",
    "According to a peer-reviewed study published in Nature, researchers found promising results in clinical trials.",
    "SHOCKING: This one weird trick melts belly fat overnight! Doctors are furious!",
    "Breaking: Local health department confirms new safety protocols based on CDC guidelines."
];

// Enhanced placeholder with examples
document.getElementById('textInput').addEventListener('focus', function() {
    if (this.value === '') {
        this.placeholder = `Try these examples:

1. "Scientists have discovered a revolutionary cure that big pharma doesn't want you to know!"

2. "According to a peer-reviewed study published in Nature, researchers found promising results."

3. "SHOCKING: This one weird trick melts belly fat overnight!"

...or enter your own text to analyze for misinformation!`;
    }
});

document.getElementById('textInput').addEventListener('blur', function() {
    if (this.value === '') {
        this.placeholder = "Paste any suspicious text, news article, or claim here to analyze it for potential misinformation...";
    }
});

// Add click effects to persona cards
document.addEventListener('DOMContentLoaded', function() {
    const personaCards = document.querySelectorAll('.persona-card');
    
    personaCards.forEach(card => {
        card.addEventListener('click', function() {
            const claim = this.querySelector('.persona-claim').textContent;
            const textInput = document.getElementById('textInput');
            
            textInput.value = claim;
            textInput.focus();
            
            // Scroll to analyzer section
            document.querySelector('.analyzer-section').scrollIntoView({
                behavior: 'smooth'
            });
            
            // Add visual feedback
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
});