document.addEventListener('DOMContentLoaded', () => {
    const categorySelect = document.getElementById('category-select');
    const customQuestionGroup = document.getElementById('custom-question-group');
    const customQuestionInput = document.getElementById('custom-question-input');
    const voiceSelect = document.getElementById('voice-select');
    const generateBtn = document.getElementById('generate-btn');

    const setupPanel = document.getElementById('setup-panel');
    const playerArea = document.getElementById('player-area');
    const currentQuestionDisplay = document.getElementById('current-question-display');
    const replayBtn = document.getElementById('replay-btn');
    const pauseBtn = document.getElementById('pause-btn');

    // State
    let currentData = null;
    let isPlaying = false;
    let isPaused = false;
    let audioQueue = []; // Array of {phase, audio}
    let currentAudio = null;
    let currentPhaseIndex = 0;

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

        const selectedVoice = voiceSelect.value;
        const buttonOriginalText = generateBtn.innerHTML;

        // UI Loading State
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Answer & Audio...';

        try {
            // 1. Get Text Content
            const response = await fetch('/api/generate-model-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            currentData = data;
            currentQuestionDisplay.textContent = question;

            // Populate Text Cards
            document.getElementById('text-s').textContent = data.situation_task;
            document.getElementById('text-a').textContent = data.action;
            document.getElementById('text-r').textContent = data.result;

            // 2. Fetch Audio (Parallel)
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Synthesizing Voice...';

            const audioTasks = [
                fetchAudio(question, selectedVoice), // 0: Question
                fetchAudio(data.situation_task, selectedVoice), // 1: S
                fetchAudio(data.action, selectedVoice), // 2: A
                fetchAudio(data.result, selectedVoice)  // 3: R
            ];

            const audios = await Promise.all(audioTasks);

            // Store Audios for Playback
            audioQueue = [
                { type: 'question', audio: audios[0] },
                { type: 'S', audio: audios[1] },
                { type: 'A', audio: audios[2] },
                { type: 'R', audio: audios[3] }
            ];

            // Switch View
            setupPanel.style.display = 'none';
            playerArea.style.display = 'block';

            // Auto Play
            startPlayback();

        } catch (e) {
            alert("Error: " + e.message);
            generateBtn.disabled = false;
            generateBtn.innerHTML = buttonOriginalText;
        }
    });

    // Helper to fetch audio
    async function fetchAudio(text, voice) {
        const res = await fetch('/api/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, voice })
        });
        const json = await res.json();
        if (json.error) throw new Error(json.error);

        // Convert Base64 to Audio Object
        const audio = new Audio("data:audio/mp3;base64," + json.audio);
        return audio;
    }

    replayBtn.addEventListener('click', () => {
        if (!isPlaying && audioQueue.length > 0) {
            resetCards();
            startPlayback();
        }
    });

    pauseBtn.addEventListener('click', () => {
        if (!isPlaying) return;

        if (isPaused) {
            // Resume
            if (currentAudio) currentAudio.play();
            isPaused = false;
            pauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            // Pause
            if (currentAudio) currentAudio.pause();
            isPaused = true;
            pauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    });

    function startPlayback() {
        isPlaying = true;
        isPaused = false;
        currentPhaseIndex = 0;
        playNext();
    }

    function playNext() {
        if (currentPhaseIndex >= audioQueue.length) {
            isPlaying = false;
            return;
        }

        const item = audioQueue[currentPhaseIndex];
        currentAudio = item.audio;
        const type = item.type;

        // UI Updates
        if (type !== 'question') {
            // Highlight Card
            const card = document.getElementById(`card-${type.toLowerCase()}`);
            if (card) card.classList.add('active');
        } else {
            // Maybe highlight the question text? for now, just play.
            currentQuestionDisplay.style.color = 'var(--primary, #64b5f6)';
        }

        currentAudio.onended = () => {
            // Cleanup UI
            if (type !== 'question') {
                const card = document.getElementById(`card-${type.toLowerCase()}`);
                if (card) {
                    card.classList.remove('active');
                    card.classList.add('done');
                }
            } else {
                currentQuestionDisplay.style.color = ''; // Reset
            }

            // Next
            currentPhaseIndex++;
            playNext();
        };

        currentAudio.play().catch(e => console.error("Play error:", e));
    }

    function resetCards() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }
        ['s', 'a', 'r'].forEach(p => {
            const card = document.getElementById(`card-${p}`);
            card.className = 'phase-card'; // Reset classes
        });
        currentQuestionDisplay.style.color = '';
    }
});
