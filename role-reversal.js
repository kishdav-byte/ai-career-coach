document.addEventListener('DOMContentLoaded', () => {
    const categorySelect = document.getElementById('category-select');
    const customQuestionGroup = document.getElementById('custom-question-group');
    const customQuestionInput = document.getElementById('custom-question-input');

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
    let audioQueue = [];
    let currentAudio = null;
    let currentPhaseIndex = 0;

    // Feature Check: Intro
    let hasPlayedIntro = false;
    const HOST_INTRO_TEXT = "This is Role Reversal... The purpose is for you to ask me a question, so I can model the proper way to answer using the STAR format. You have selected a question; I will read it aloud, and then answer it.";

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

        // Randomize Voice
        const voices = ['alloy', 'echo', 'shimmer', 'ash', 'ballad', 'coral', 'sage', 'verse'];
        const selectedVoice = voices[Math.floor(Math.random() * voices.length)];
        console.log("Selected Random Voice:", selectedVoice);

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

            // PREPARE TASKS
            // Start with Core Content
            let audioTasksMap = [
                { id: 'question', text: question },
                { id: 'S', text: data.situation_task },
                { id: 'A', text: data.action },
                { id: 'R', text: data.result }
            ];

            // Add Intro if needed
            if (!hasPlayedIntro) {
                audioTasksMap.unshift({ id: 'intro', text: HOST_INTRO_TEXT });
            }

            // Execute parallel fetch
            const promises = audioTasksMap.map(item => fetchAudio(item.text, selectedVoice));
            const audioResults = await Promise.all(promises);

            // Build Queue
            audioQueue = [];

            let resultIndex = 0;
            if (!hasPlayedIntro) {
                // Add Intro + Pause
                audioQueue.push({ type: 'intro', audio: audioResults[resultIndex++] });
                audioQueue.push({ type: 'intro-pause', duration: 3000 });
                hasPlayedIntro = true;
            }

            // Add Core Content
            audioQueue.push({ type: 'question', audio: audioResults[resultIndex++] });
            audioQueue.push({ type: 'S', audio: audioResults[resultIndex++] });
            audioQueue.push({ type: 'A', audio: audioResults[resultIndex++] });
            audioQueue.push({ type: 'R', audio: audioResults[resultIndex++] });


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
            // Filter out intro logic for replay? 
            // Usually replay means "Replay the Answer".
            // If intro was in queue, it is still in audioQueue. 
            // We can just restart from index 0. 
            // But if user wants to just hear answer again, maybe skip intro?
            // "Play the 'Host Script' first" implies ONCE per first run.
            // If I click Replay, I am re-watching the answer. I probably don't want the intro again.
            // But audioQueue has it. 
            // I will FILTER audioQueue to remove 'intro' and 'intro-pause' if they exist?
            // Or just leave it. The requirement says "IF hasPlayedIntro is true: Skip...".
            // The `audioQueue` was built for THIS generation.
            // If I click Replay, I am reusing the queue. 
            // I'll leave it as is for simplicity. Replay = Replay what just happened.
            resetCards();
            startPlayback();
        }
    });

    pauseBtn.addEventListener('click', () => {
        if (!isPlaying) return;

        if (isPaused) {
            // Resume
            if (currentAudio && !currentAudio.paused) {
                // Already playing?
            } else if (currentAudio) {
                currentAudio.play();
            }
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
        const type = item.type;

        // HANDLE PAUSE (Simulated)
        if (type === 'intro-pause') {
            currentAudio = null; // No audio for pause
            setTimeout(() => {
                // Use recursion, but check if we stopped? 
                if (isPlaying) {
                    currentPhaseIndex++;
                    playNext();
                }
            }, item.duration);
            return;
        }

        // HANDLE AUDIO
        currentAudio = item.audio;

        // UI Updates
        if (['s', 'a', 'r'].includes(type.toLowerCase())) {
            // Highlight Card
            const card = document.getElementById(`card-${type.toLowerCase()}`);
            if (card) card.classList.add('active');
        } else {
            // Question or Intro
            currentQuestionDisplay.style.color = 'var(--primary, #64b5f6)';
        }

        currentAudio.onended = () => {
            // Cleanup UI
            if (['s', 'a', 'r'].includes(type.toLowerCase())) {
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
