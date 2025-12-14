document.addEventListener('DOMContentLoaded', () => {
    const categorySelect = document.getElementById('category-select');
    const customQuestionGroup = document.getElementById('custom-question-group');
    const customQuestionInput = document.getElementById('custom-question-input');
    const generateBtn = document.getElementById('generate-btn');

    const setupPanel = document.getElementById('setup-panel');
    const playerArea = document.getElementById('player-area');
    const currentQuestionDisplay = document.getElementById('current-question-display');
    const replayBtn = document.getElementById('replay-btn');

    // State
    let currentData = null;
    let isPlaying = false;

    // Toggle Custom Input
    categorySelect.addEventListener('change', () => {
        if (categorySelect.value === 'Custom') {
            customQuestionGroup.style.display = 'block';
        } else {
            customQuestionGroup.style.display = 'none';
        }
    });

    // Generate Logic
    generateBtn.addEventListener('click', async () => {
        let question = "";
        if (categorySelect.value === 'Custom') {
            question = customQuestionInput.value.trim();
        } else {
            // Preset questions based on category
            const presets = {
                'Leadership': "Tell me about a time you led a team through a difficult challenge.",
                'Conflict Resolution': "Describe a situation where you had a conflict with a colleague and how you resolved it.",
                'Failure': "Tell me about a time you failed and what you learned from it.",
                'Innovation': "Give an example of a time you introduced a new process or idea.",
                'Project Management': "Describe a project where you had to manage tight deadlines and multiple stakeholders."
            };
            question = presets[categorySelect.value];
        }

        if (!question) {
            alert("Please enter a question.");
            return;
        }

        // UI Loading State
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

        try {
            const response = await fetch('/api/generate-model-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            const data = await response.json();

            if (data.error) throw new Error(data.error);

            // Success
            currentData = data;
            currentQuestionDisplay.textContent = question;

            // Populate Cards
            document.getElementById('text-s').textContent = data.situation_task;
            document.getElementById('text-a').textContent = data.action;
            document.getElementById('text-r').textContent = data.result;

            // Switch View
            setupPanel.style.display = 'none';
            playerArea.style.display = 'block';

            // Auto Play
            playSequence();

        } catch (e) {
            alert("Error: " + e.message);
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Model Answer';
        }
    });

    replayBtn.addEventListener('click', () => {
        if (!isPlaying && currentData) {
            playSequence();
        }
    });

    function playSequence() {
        if (isPlaying) return;
        isPlaying = true;
        resetCards();

        // Sequence: S -> A -> R
        speakPhase('S', currentData.situation_task, () => {
            markDone('S');
            speakPhase('A', currentData.action, () => {
                markDone('A');
                speakPhase('R', currentData.result, () => {
                    markDone('R');
                    isPlaying = false;
                });
            });
        });
    }

    function speakPhase(phase, text, onComplete) {
        const card = document.getElementById(`card-${phase.toLowerCase()}`);
        card.classList.add('active');

        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            utterance.onend = () => {
                card.classList.remove('active');
                if (onComplete) onComplete();
            };

            window.speechSynthesis.speak(utterance);
        } else {
            console.warn("Browser does not support TTS");
            // Fallback for no TTS: just wait based on text length
            setTimeout(() => {
                card.classList.remove('active');
                if (onComplete) onComplete();
            }, text.length * 50);
        }
    }

    function markDone(phase) {
        const card = document.getElementById(`card-${phase.toLowerCase()}`);
        card.classList.add('done');
    }

    function resetCards() {
        window.speechSynthesis.cancel();
        ['s', 'a', 'r'].forEach(p => {
            const card = document.getElementById(`card-${p}`);
            card.className = 'phase-card'; // Reset classes
        });
    }
});
