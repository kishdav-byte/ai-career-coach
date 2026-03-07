// js/modules/interview.js
import { getSession } from './auth.js';

let currentSessionVoice = null;
let questionCount = 0;
let interviewHistory = [];
let currentQuestionText = "";
let thinkingBubbleId = null;
let thinkingIntervalId = null;

export function getVoiceSettings() {
    const voiceSelect = document.getElementById('voice-select');
    let voice = voiceSelect ? voiceSelect.value : null;

    if (!voice || voice === 'random') {
        if (!currentSessionVoice) {
            const variants = ['alloy', 'onyx', 'nova', 'fable'];
            currentSessionVoice = variants[Math.floor(Math.random() * variants.length)];
        }
        voice = currentSessionVoice;
    }
    return { voice, speed: '+0%' };
}

export function startCountdown(onFinish) {
    const loader = document.getElementById('interviewLoader');
    if (loader) loader.classList.remove('hidden');

    const intro = document.getElementById('interview-intro');
    if (intro) intro.classList.add('hidden');

    document.getElementById('chat-interface').classList.add('hidden');

    let timeLeft = 12;
    const totalTime = 12;
    const ring = document.getElementById('progressRing');
    const number = document.getElementById('countdownNumber');
    const status = document.getElementById('countdownStatus');
    const circumference = 552;

    const timer = setInterval(() => {
        timeLeft--;
        if (number) number.innerText = timeLeft;
        if (ring) {
            const offset = circumference - (timeLeft / totalTime) * circumference;
            ring.style.strokeDashoffset = offset;
        }
        if (status) {
            if (timeLeft === 9) status.innerText = "Analyzing User Experience...";
            if (timeLeft === 6) status.innerText = "Drafting Interview Roadmap...";
            if (timeLeft === 3) status.innerText = "Selecting Interview Persona...";
        }
        if (timeLeft <= 0) {
            clearInterval(timer);
            if (loader) loader.classList.add('hidden');
            document.getElementById('chat-interface').classList.remove('hidden');
            if (onFinish) onFinish();
        }
    }, 1000);
}

export function showThinkingState(addMessageFn) {
    if (thinkingBubbleId && document.getElementById(thinkingBubbleId)) return;

    const listeningStates = [
        "Assessing STAR Alignment...",
        "Checking for Key Metrics...",
        "Formulating Feedback...",
        "Analyzing Tone & Pace...",
        "Reviewing your response..."
    ];

    thinkingBubbleId = addMessageFn(
        `<div class="flex items-center gap-3"><div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div><span class="text-sm text-slate-400">Reviewing your response...</span></div>`,
        'system',
        true
    );

    thinkingIntervalId = setInterval(() => {
        const bubble = document.getElementById(thinkingBubbleId);
        if (bubble) {
            const textSpan = bubble.querySelector('span');
            if (textSpan) {
                const randomPhrase = listeningStates[Math.floor(Math.random() * listeningStates.length)];
                textSpan.innerText = randomPhrase;
            }
        } else {
            clearInterval(thinkingIntervalId);
        }
    }, 2000);
}

export function hideThinkingState() {
    if (thinkingIntervalId) clearInterval(thinkingIntervalId);
    if (thinkingBubbleId) {
        const bubble = document.getElementById(thinkingBubbleId);
        if (bubble) bubble.remove();
        thinkingBubbleId = null;
    }
}
