// SAFE INITIALIZATION PATTERN
const supabaseUrl = 'https://nvfjmqacxzlmfamiynuu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52ZmptcWFjeHpsbWZhbWl5bnV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUxMzk3MzAsImV4cCI6MjA4MDcxNTczMH0.W3J-E2ldrc99btVeChF0SauTQxr_48uFwImVaoHfOXI';

// Check if Supabase library is loaded, then create client
if (typeof window.supabase === 'undefined' || typeof window.supabase.createClient === 'function') {
    // Library loaded from CDN, create client
    window.supabaseClient = window.supabase ? window.supabase.createClient(supabaseUrl, supabaseKey) : null;
    window.supabase = window.supabaseClient;
} else if (!window.supabase) {
    console.error('Supabase library not loaded! Add CDN script to app.html');
}

// Helper functions (Global Scope)
let currentSessionVoice = null;

function getVoiceSettings() {
    const voiceSelect = document.getElementById('voice-select');
    let voice = voiceSelect ? voiceSelect.value : null;

    // Sticky Random Logic (One voice per session)
    if (!voice || voice === 'random') {
        if (!currentSessionVoice) {
            const variants = ['alloy', 'onyx', 'nova', 'fable'];
            currentSessionVoice = variants[Math.floor(Math.random() * variants.length)];
            console.log("Selected Random Voice for Session:", currentSessionVoice);
        }
        voice = currentSessionVoice;
    }

    const speed = '+0%'; // Default speed
    return { voice, speed };
}

// --- DYNAMIC TOOL BELT CONFIG ---
const TOOL_CONFIG = {
    // Prep
    'tool-card-scanner': { type: 'free' },
    'tool-card-rewrite': { type: 'credit', price: '$9.99', creditKey: 'credits_resume', label: 'Credit' },
    'tool-card-cover': { type: 'credit', price: '$6.99', creditKey: 'credits_cover', label: 'Credit' },
    'tool-card-linkedin': { type: 'credit', price: '$6.99', creditKey: 'credits_linkedin', label: 'Credit' },

    // Interview
    'tool-card-mock': { type: 'subscription', price: '$9.99/mo', creditKey: 'credits_interview', label: 'Session' },
    'tool-card-star': { type: 'free' }, // STAR Drill is free capability
    'tool-card-inquisitor': { type: 'credit', price: '$6.99', creditKey: 'credits_inquisitor', label: 'Credit' },

    // Post
    'tool-card-followup': { type: 'credit', price: '$6.99', creditKey: 'credits_followup', label: 'Credit' },
    'tool-card-closer': { type: 'credit', price: '$6.99', creditKey: 'credits_negotiation', label: 'Credit' },
    'tool-card-plan': { type: 'credit', price: '$8.99', creditKey: 'credits_30_60_90', label: 'Plan' },
    'tool-card-lab': { type: 'free' } // Hub is free
};

// Global scope definition for verifyInterviewAccess to allow external calls
function verifyInterviewAccess(session) {
    if (!session) return;

    const lockedState = document.getElementById('interview-locked-state');
    const activeState = document.getElementById('interview-active-state');
    const startBtn = document.getElementById('start-interview-btn');

    // Safety check if elements exist (might not be on app page)
    if (!lockedState || !activeState) return;

    const credits = (session.credits_interview || 0) + (session.credits || 0); // Include Universal Credits
    const isUnlimited = session.is_unlimited || false;

    // Logic: 
    // If credits > 0 OR user is unlimited -> Show Start Screen (unlocked)

    const statusDot = document.getElementById('status-dot');

    if (credits > 0 || isUnlimited) {
        lockedState.classList.add('hidden');
        activeState.classList.remove('hidden');

        // Enable Start Button
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }

        // Status Indicator: Glowing Green
        if (statusDot) {
            statusDot.className = 'w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse';
        }
    } else {
        // Locked
        lockedState.classList.remove('hidden');
        activeState.classList.add('hidden');

        // Status Indicator: Grey
        if (statusDot) {
            statusDot.className = 'w-2 h-2 rounded-full bg-slate-600';
        }
    }
}

// LinkedIn Visual Unlock Logic (Global Scope for checkAccess to call)
function verifyLinkedInAccess(session) {
    if (!session) return;

    // New Overlay Ref
    const overlay = document.getElementById('linkedin-unlock-overlay');
    const optimizeBtn = document.getElementById('optimize-linkedin-btn');
    // We no longer toggle the sidebar inputs - they are always open (Freemium Style)

    if (!overlay) return;

    // Prevent Flicker: If session data is incomplete (e.g. valid session but missing credit keys from old cache),
    // do NOT force lock yet. Wait for checkAccess() to populate fresh data.
    if (session.credits_linkedin === undefined && session.credits === undefined && !session.is_unlimited) {
        return;
    }

    const credits = (session.credits_linkedin || 0) + (session.credits || 0);
    const isUnlimited = session.is_unlimited || false;

    if (credits > 0 || isUnlimited) {
        overlay.classList.add('hidden');
        if (optimizeBtn) {
            optimizeBtn.innerHTML = 'OPTIMIZE PROFILE';
            optimizeBtn.classList.remove('bg-green-600', 'hover:bg-green-500');
            optimizeBtn.classList.add('bg-blue-600', 'hover:bg-blue-500');
            optimizeBtn.onclick = null; // Revert to default binding (handled elsewhere)
        }
    } else {
        overlay.classList.remove('hidden');
        if (optimizeBtn) {
            optimizeBtn.innerHTML = `<i class="fas fa-lock"></i> UNLOCK ($6.99)`;
            optimizeBtn.classList.remove('bg-green-600', 'hover:bg-green-500'); // Ensure green is removed
            optimizeBtn.classList.add('bg-blue-600', 'hover:bg-blue-500');

            // Direct Checkout Trigger
            optimizeBtn.onclick = async () => {
                const btn = document.getElementById('optimize-linkedin-btn');
                if (btn) {
                    btn.textContent = 'Redirecting...';
                    btn.disabled = true;
                }
                const { data: { user } } = await supabase.auth.getUser();
                initiateCheckout('strategy_linkedin', user ? user.email : null, user ? user.id : null);
            };
        }
    }
}

// Session Helper (Duplicated from dashboard for standalone app usage)
// Session Helper (Duplicated from dashboard for standalone app usage)
const SESSION_KEY = 'aceinterview_session';
function getSession() {
    const sessionStr = localStorage.getItem(SESSION_KEY);
    if (!sessionStr) return null;
    try {
        // Support both Raw Token (Edge Case) and Session Object (Standard)
        // If raw token, wrap it in a pseudo-session object to prevent crashes
        let session;
        try {
            session = JSON.parse(sessionStr);
        } catch (e) {
            // Assume string is token
            return { access_token: sessionStr, email: null, subscription_status: 'unknown' };
        }

        // Check expiry (7 days - Matching Dashboard)
        const SESSION_DURATION = 7 * 24 * 60 * 60 * 1000;
        // FIX: Default to now if missing
        const loggedInAt = session.logged_in_at || Date.now();
        if (Date.now() - loggedInAt > SESSION_DURATION) {
            localStorage.removeItem(SESSION_KEY);
            return null;
        }
        return session;
    } catch (e) {
        return null;
    }
}

async function checkAccess(requiredType = 'credits_interview', autoPrompt = true) {
    const { data: { user } } = await supabase.auth.getUser();

    // 1. Handle "Not Logged In"
    if (!user) {
        window.location.href = '/login';
        return false;
    }

    // 2. Get Data from 'users' table
    const { data: userData, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', user.id)
        .single();

    if (error || !userData) {
        console.error('Data Load Error:', error);
        return false;
    }

    // 3. Waterfall Logic (Check Specific -> Then Universal)
    const specificBalance = userData[requiredType] || 0;
    const universalBalance = userData.credits || 0; // Fallback to generic credits
    const isSubscribed = userData.subscription_status === 'active';

    console.log(`User: ${user.email} | Specific: ${specificBalance} | Universal: ${universalBalance}`);

    // Update local session for compatibility
    let session = getSession() || {};
    session.email = user.email;
    session.name = user.user_metadata?.name || user.email;
    session.subscription_status = userData.subscription_status;
    session.is_unlimited = userData.is_unlimited;
    session.credits = universalBalance;
    session.credits_interview = userData.credits_interview || 0;
    session.credits_resume = userData.credits_resume || 0;
    session.credits_cover = userData.credits_cover || 0;
    session.credits_linkedin = userData.credits_linkedin || 0;
    session.credits_30_60_90 = userData.credits_30_60_90 || 0;
    session.credits_negotiation = userData.credits_negotiation || 0;
    session.credits_inquisitor = userData.credits_inquisitor || 0;
    session.credits_followup = userData.credits_followup || 0;
    session.role = userData.role;
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));

    // Update credit display
    updateCreditDisplay(session);

    // ADMIN CHECK: Reveal Hidden Tools
    if (userData.role === 'admin') {
        console.log("👑 Admin Access Detected: Unhiding Tools");
        const adminTools = document.getElementById('admin-tools-container');
        if (adminTools) {
            adminTools.style.display = 'block';

            // Logic to exclusively show the requested admin tool
            const hash = window.location.hash;
            const adminHashes = ['#career-plan', '#linkedin', '#cover-letter', '#resume-builder'];

            if (hash && adminHashes.includes(hash)) {
                // Hide all other admin sections first
                adminHashes.forEach(id => {
                    const el = document.querySelector(id);
                    if (el) el.classList.remove('active');
                });

                // Show target
                setTimeout(() => {
                    const target = document.querySelector(hash);
                    if (target) {
                        target.classList.add('active');
                        target.scrollIntoView({ behavior: 'smooth' });
                    }
                }, 100);
            }
        }
    }

    // 4. Decision Gate
    if (isSubscribed || specificBalance > 0 || universalBalance > 0) {
        // Unlock UI if it exists
        const interviewOverlay = document.getElementById('interview-unlock-overlay');
        if (interviewOverlay) interviewOverlay.classList.add('hidden');

        // UPDATE BUTTON: Active State (Interview)
        const startBtn = document.getElementById('start-interview-btn');
        if (startBtn) {
            startBtn.innerHTML = `START SESSION`;
            startBtn.classList.remove('bg-green-600', 'hover:bg-green-500');
            startBtn.classList.add('bg-blue-600', 'hover:bg-blue-500');
            startBtn.onclick = null; // Remove direct checkout if it was added
        }

        // UPDATE BUTTON: Active State (LinkedIn)
        const linkedinBtn = document.getElementById('optimize-linkedin-btn');
        if (linkedinBtn) {
            linkedinBtn.innerHTML = `OPTIMIZE PROFILE`;
            linkedinBtn.classList.remove('bg-green-600', 'hover:bg-green-500');
            linkedinBtn.classList.add('bg-blue-600', 'hover:bg-blue-500');
            linkedinBtn.classList.remove('bg-green-600', 'hover:bg-green-500');
            linkedinBtn.classList.add('bg-blue-600', 'hover:bg-blue-500');
            // Original Onclick is likely bound in HTML or elsewhere, so we just reset visual
        }

        // Also run the dedicated LinkedIn verification (Overlay Logic) with FRESH session
        verifyLinkedInAccess(session);

        return true;
    } else {
        // LOCKED STATE

        // Check if we are on a page with the new overlay
        const interviewOverlay = document.getElementById('interview-unlock-overlay');

        if (interviewOverlay) {
            // ALWAYS Update UI if overlay exists (Non-intrusive)
            interviewOverlay.classList.remove('hidden');

            // UPDATE BUTTON: Locked State
            const startBtn = document.getElementById('start-interview-btn');
            if (startBtn) {
                startBtn.innerHTML = `<i class="fas fa-lock"></i> UNLOCK ($9.99)`;
                startBtn.classList.remove('bg-blue-600', 'hover:bg-blue-500');
                startBtn.classList.add('bg-green-600', 'hover:bg-green-500');

                // Direct Checkout Trigger
                startBtn.onclick = async () => {
                    const startBtn = document.getElementById('start-interview-btn');
                    if (startBtn) {
                        startBtn.textContent = 'Redirecting...';
                        startBtn.disabled = true;
                    }
                    const { data: { user } } = await supabase.auth.getUser();
                    initiateCheckout('strategy_interview_sim', user ? user.email : null, user ? user.id : null);
                };
            }

            // UPDATE BUTTON: Locked State (LinkedIn)
            // NOTE: This runs if we are on the LinkedIn View (controlled by url/hash check usually, or we just update both if elements exist)
            const linkedinBtn = document.getElementById('optimize-linkedin-btn');
            if (linkedinBtn) {
                linkedinBtn.innerHTML = `<i class="fas fa-lock"></i> UNLOCK ($6.99)`;
                linkedinBtn.classList.remove('bg-blue-600', 'hover:bg-blue-500');
                linkedinBtn.classList.add('bg-green-600', 'hover:bg-green-500');

                // Direct Checkout Trigger
                linkedinBtn.onclick = async () => {
                    const btn = document.getElementById('optimize-linkedin-btn');
                    if (btn) {
                        btn.textContent = 'Redirecting...';
                        btn.disabled = true;
                    }
                    const { data: { user } } = await supabase.auth.getUser();
                    initiateCheckout('strategy_linkedin', user ? user.email : null, user ? user.id : null);
                };
            }

            // Wire up the button if not already done (Idempotent)
            const unlockBtn = document.getElementById('btn-unlock-interview-overlay');
            if (unlockBtn) {
                unlockBtn.onclick = async () => {
                    // Standard Checkout Flow
                    const { data: { user } } = await supabase.auth.getUser();
                    initiateCheckout('strategy_interview_sim', user ? user.email : null, user ? user.id : null);
                };
            }
        } else {
            // Fallback to Alert for other pages (e.g. Dashboard)
            // ONLY if autoPrompt is true
            if (autoPrompt) {
                if (confirm('You have 0 credits. Upgrade now to start your Mock Interview? ($9.99)')) {
                    const { data: { user } } = await supabase.auth.getUser();
                    if (user) {
                        initiateCheckout('strategy_interview_sim', user.email, user.id);
                    } else {
                        const session = getSession();
                        initiateCheckout('strategy_interview_sim', session ? session.email : null, session ? session.user_id : null);
                    }
                }
            }
        }

        // GLOBAL LOCK CHECK: Make sure LinkedIn Overlay is updated in ALL locked scenarios
        verifyLinkedInAccess(session);
        return false;
    }
}




function updateCreditDisplay(session) {
    if (!session) return;

    // Trigger Dynamic Tool Belt Update (Safe Call)
    if (typeof updateToolBelt === 'function') {
        updateToolBelt(session);
    }

    const countEl = document.getElementById('rb-credit-count');
    const displayEl = document.getElementById('rb-credit-display');
    const generateBtn = document.getElementById('rb-generate-btn');

    // UNLIMITED LOGIC
    if (session.is_unlimited) {
        if (countEl) countEl.textContent = "∞";
        if (displayEl) displayEl.style.display = 'flex';

        if (generateBtn) {
            generateBtn.innerHTML = `Generate Rewrite <small>(Unlimited)</small>`;
            generateBtn.disabled = false;
        }
        return;
    }

    if (countEl && session.credits !== undefined) {
        countEl.textContent = session.credits;
        if (displayEl) displayEl.style.display = 'flex';

        // Gate "Generate" Button
        if (generateBtn) {
            if (session.credits > 0) {
                generateBtn.innerHTML = `Generate Rewrite <small>(1 Credit)</small>`;
                generateBtn.disabled = false;
            } else {
                generateBtn.innerHTML = `Generate Rewrite <small>(1 Credit Needed)</small>`;
            }
        }
    }
}

// --- DYNAMIC TOOL BELT LOGIC ---


function updateToolBelt(session) {
    if (!session) return;
    const isUnlimited = session.is_unlimited || session.subscription_status === 'active';
    const universalCredits = session.credits || 0; // Universal Credits

    Object.entries(TOOL_CONFIG).forEach(([id, config]) => {
        const card = document.getElementById(id);
        if (!card) return;

        // Clear existing badges to prevent duplicates
        const existingBadge = card.querySelector('.dynamic-badge');
        if (existingBadge) existingBadge.remove();

        let badgeHtml = '';

        // 1. FREE TOOLS
        if (config.type === 'free') {
            badgeHtml = `<span class="dynamic-badge inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-slate-700 text-slate-300 ml-auto border border-slate-600">Free</span>`;
        }

        // 2. PAID TOOLS
        else {
            // Check specific credit balance OR universal credits OR subscription
            const specificBalance = session[config.creditKey] || 0;
            const isUnlocked = isUnlimited || (specificBalance > 0) || (universalCredits > 0);

            if (isUnlocked) {
                // Active / Unlocked
                let text = "Active";
                let subtext = "";

                if (config.type === 'subscription') {
                    // Subscription Logic (Mock Interview)
                    if (isUnlimited) {
                        text = "Unlimited";
                        // If we had reset date: subtext = "Resets ...";
                        if (session.current_period_end) {
                            const date = new Date(session.current_period_end * 1000).toLocaleDateString();
                            subtext = `Resets ${date}`;
                        }
                    } else if (specificBalance > 0) {
                        text = `${specificBalance} Left`;
                    } else if (universalCredits > 0) {
                        text = "Unlocked"; // via Universal
                    }
                } else {
                    // Credit Logic
                    if (isUnlimited) {
                        text = "Included";
                    } else if (specificBalance > 0) {
                        text = `${specificBalance} Left`;
                    } else {
                        text = "Use Credit"; // Universal
                    }
                }

                badgeHtml = `<div class="dynamic-badge ml-auto text-right">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-teal/20 text-teal border border-teal/30">
                        <i class="fas fa-check-circle mr-1"></i> ${text}
                    </span>
                    ${subtext ? `<div class="text-[9px] text-slate-500 mt-0.5 px-1">${subtext}</div>` : ''}
                 </div>`;
            } else {
                // Locked
                badgeHtml = `<span class="dynamic-badge inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-slate-400 ml-auto border border-slate-700 group-hover:border-slate-500 transition-colors">
                    <i class="fas fa-lock mr-1.5 text-xs"></i> ${config.price}
                </span>`;
            }
        }

        // Inject into the main flex container
        const mainFlex = card.querySelector('.flex.items-center');
        if (mainFlex) {
            mainFlex.insertAdjacentHTML('beforeend', badgeHtml);
        }
    });
}

// Global state variables for interview tracking
let questionCount = 0;
let interviewHistory = [];
let currentQuestionText = "";

// --- COUNTDOWN LOGIC ---
window.startCountdown = function () {
    const loader = document.getElementById('interviewLoader');
    if (loader) loader.classList.remove('hidden');

    // Ensure chat/intro keys are hidden
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
            finishSetup();
        }
    }, 1000);
};

window.finishSetup = function () {
    document.getElementById('interviewLoader').classList.add('hidden');
    document.getElementById('chat-interface').classList.remove('hidden');
};

// --- THINKING LOGIC HELPERS ---
let thinkingBubbleId = null;
let thinkingIntervalId = null;

window.showThinkingState = function () {
    // Only show if not already showing
    if (thinkingBubbleId && document.getElementById(thinkingBubbleId)) return;

    const listeningStates = [
        "Assessing STAR Alignment...",
        "Checking for Key Metrics...",
        "Formulating Feedback...",
        "Analyzing Tone & Pace...",
        "Reviewing your response..."
    ];

    // Create Bubble
    thinkingBubbleId = addMessage(
        `<div class="flex items-center gap-3"><div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div><span class="text-sm text-slate-400">Reviewing your response...</span></div>`,
        'system',
        true
    );

    // Start Cycle
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
};

window.hideThinkingState = function () {
    if (thinkingIntervalId) clearInterval(thinkingIntervalId);
    if (thinkingBubbleId) {
        const bubble = document.getElementById(thinkingBubbleId);
        if (bubble) bubble.remove();
        thinkingBubbleId = null;
    }
};

async function sendVoiceMessage(base64Audio) {
    if (!window.addMessage) {
        console.error("addMessage not found");
        return;
    }

    const loadingId = window.addMessage('Transcribing...', 'system');

    try {
        const session = getSession();
        const email = session ? session.email : null;

        // 1. STT: Transcribe Audio
        const transResponse = await fetch('/api/get-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session?.access_token}`
            },
            body: JSON.stringify({
                action: 'transcribe',
                audio: base64Audio,
                email: email
            })
        });
        const transResult = await transResponse.json();
        document.getElementById(loadingId).remove();

        if (transResult.transcript) {
            // Show transcript immediately
            window.addMessage(transResult.transcript, 'user');

            // 2. Chat: Send transcript to AI for analysis
            await window.sendChatMessage(transResult.transcript, false, true); // true = skipUI
        } else {
            window.addMessage('Error: ' + (transResult.error || 'Transcription failed'), 'system');
        }
    } catch (e) {
        if (document.getElementById(loadingId)) document.getElementById(loadingId).remove();
        window.addMessage('Error: ' + e.message, 'system');
    }
}

// --- PRODUCT DATA (OFFICIAL PRICING TABLE) ---
const PRODUCTS = [
    {
        id: 'monthly_plan',
        title: 'Ace Pro Monthly',
        price: '$49.99',
        desc: 'Unlimited Access + 50 Voice Sessions',
        stripeId: 'price_1Sbq1WIH1WTKNasqXrlCBDSD',
        tag: 'Best Value'
    },
    {
        id: 'strategy_bundle',
        title: 'Strategy Bundle',
        price: '$29.99',
        desc: '5 Universal Credits (Save ~$15)',
        stripeId: 'price_1SePqzlH1WTKNasq34FYIKNm',
        tag: 'Popular'
    },
    {
        id: 'executive_rewrite',
        title: 'Executive Rewrite',
        price: '$12.99',
        desc: 'Full Resume Content Rewrite',
        stripeId: 'price_1Sgsf9IH1WTKNasqxvk528yY'
    },
    {
        id: 'interview_sim',
        title: 'Interview Simulator',
        price: '$9.99',
        desc: 'Mock Interview Session + Scoring',
        stripeId: 'price_1SeRRnIH1WTKNasqQFCJDxH5'
    },
    {
        id: 'plan_30_60_90',
        title: '30-60-90 Day Plan',
        price: '$8.99',
        desc: 'Strategic Onboarding Plan',
        stripeId: 'price_1SePqzlH1WTKNasq34FYIKNm' // Using Bundle Placeholder till specific ID confirmed
    },
    {
        id: 'cover_letter',
        title: 'Cover Letter',
        price: '$6.99',
        desc: '1 Tailored PDF Document',
        stripeId: 'price_1Shc7tlH1WTKNasqQNu7O5fL'
    },
    {
        id: 'linkedin_optimize',
        title: 'LinkedIn Optimizer',
        price: '$6.99',
        desc: '1 Profile Refinement Report',
        stripeId: 'price_1ShWBJIH1WTKNasqd7p9VA5f'
    },
    {
        id: 'negotiation',
        title: 'The Closer',
        price: '$6.99',
        desc: '1 Negotiation Script',
        stripeId: 'price_1SePpZIH1WTKNasqLuNq4sSZ'
    },
    {
        id: 'inquisitor',
        title: 'The Inquisitor',
        price: '$6.99',
        desc: '1 Reverse Interview Guide',
        stripeId: 'price_1SeQGAIH1WTKNasqKwRR20TZ'
    },
    {
        id: 'follow_up',
        title: 'Value Follow-Up',
        price: '$6.99',
        desc: '1 Post-Interview Email Draft',
        stripeId: 'price_1SeQHYIH1WTKNasqpFyl2ef0'
    }
];

// --- SMART TILES RENDERER (Universal + Locker) ---
window.renderSmartTiles = function (user) {
    // 1. Prepare Mock Data Model (as requested)
    // In a real scenario, we would fetch these valid columns from Supabase
    const currentUser = {
        ...user,
        plan: (user.subscription_status === 'active' || user.is_unlimited) ? "ACE PRO" : "FREE",
        universal_credits: user.is_unlimited ? '∞' : (user.credits || 0),
        tool_vouchers: {
            "rewrite": user.credits_resume || 0,
            "mock_interview": user.credits_interview || 0,
            "linkedin_opt": user.credits_linkedin || 0,
            "cover_letter": user.credits_cover || 0,
            "plan_30_60_90": user.credits_30_60_90 || 0,
            "negotiation": user.credits_negotiation || 0,
            "follow_up": user.credits_followup || 0
        }
    };

    renderUniversalTile(currentUser);
    renderToolLocker(currentUser);
};

function renderUniversalTile(user) {
    const tile = document.getElementById('universal-tile');
    if (!tile) return;

    const isPro = user.plan === 'ACE PRO';
    const badgeClass = isPro ? 'bg-yellow-500 text-black' : 'bg-slate-600 text-slate-300';

    tile.innerHTML = `
        <div class="absolute top-0 left-0 w-full h-1 ${isPro ? 'bg-yellow-500' : 'bg-teal/20'}"></div>
        <div class="flex flex-col items-center justify-center h-full w-full p-4">
            <span class="text-[9px] font-black px-2 py-0.5 rounded-full ${badgeClass} mb-3 uppercase tracking-wider">
                PLAN: ${user.plan}
            </span>
            <div class="text-4xl font-bold text-white mb-1 tracking-tight">${user.universal_credits}</div>
            <div class="text-[9px] text-slate-500 uppercase tracking-widest text-center">
                Universal Balance
            </div>
            <p class="text-[8px] text-slate-600 mt-1">Usable on ANY tool</p>
        </div>
    `;
}

function renderToolLocker(user) {
    const tile = document.getElementById('tool-locker-tile');
    if (!tile) return;

    const vouchers = user.tool_vouchers;
    // Helper to row
    const row = (label, count) => `
        <div class="flex justify-between items-center py-1 border-b border-white/5 last:border-0 hover:bg-white/5 px-2 rounded transition-colors">
            <span class="text-[9px] text-slate-400 truncate w-20" title="${label}">${label}</span>
            <span class="text-[9px] font-bold ${count > 0 ? 'text-green-400' : 'text-slate-600'}">${count}</span>
        </div>
    `;

    tile.innerHTML = `
        <div class="absolute top-0 left-0 w-full h-1 bg-blue-500/20"></div>
        <div class="flex flex-col h-full w-full">
            <div class="p-3 border-b border-white/5 bg-white/5">
                <h3 class="text-slate-300 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
                    <i class="fas fa-toolbox text-blue-400"></i> Tool Locker
                </h3>
            </div>
            <div class="flex-1 overflow-y-auto custom-scroll p-2">
                <div class="grid grid-cols-2 gap-x-4 gap-y-0.5">
                    ${row('Rewrite', vouchers.rewrite)}
                    ${row('Mock Interview', vouchers.mock_interview)}
                    ${row('Cover Letter', vouchers.cover_letter)}
                    ${row('30-60-90 Plan', vouchers.plan_30_60_90)}
                    ${row('Salary Neg.', vouchers.negotiation)}
                    ${row('LinkedIn Opt', vouchers.linkedin_opt)}
                    ${row('Strat Follow-up', vouchers.follow_up)}
                </div>
            </div>
        </div>
    `;
}

// --- RENDER LOGIC (Dossier Groups) ---
window.renderUpgradeHub = function (containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Grouping Logic - Matching Dossier Field Groups
    const groups = [
        {
            title: 'Unlock Pro',
            icon: 'fas fa-star',
            color: 'text-yellow-500', // Matches Pro Badge
            ids: ['monthly_plan', 'strategy_bundle']
        },
        {
            title: 'Expert Services',
            icon: 'fas fa-user-tie', // Matches Dossier Role Blue
            color: 'text-blue-400',
            ids: ['executive_rewrite', 'interview_sim', 'plan_30_60_90']
        },
        {
            title: 'Toolkit',
            icon: 'fas fa-toolbox',
            color: 'text-green-400', // Matches Dossier Salary Green
            ids: ['cover_letter', 'linkedin_optimize', 'negotiation', 'inquisitor', 'follow_up']
        }
    ];

    let html = '';

    groups.forEach(group => {
        const groupItems = PRODUCTS.filter(p => group.ids.includes(p.id));
        if (groupItems.length === 0) return;

        html += `
        <div class="space-y-3">
             <label class="text-xs font-bold ${group.color} uppercase tracking-widest flex items-center gap-2">
                <i class="${group.icon}"></i> ${group.title}
             </label>
             <div class="space-y-2">
                ${groupItems.map(p => {
            const isHighlight = p.id === 'monthly_plan';
            const bgClass = isHighlight ? 'bg-teal/10 border-teal/30 hover:bg-teal/20' : 'bg-slate-800/50 border-slate-700 hover:bg-slate-800';
            const textClass = isHighlight ? 'text-teal' : 'text-slate-300';

            return `
                    <button onclick="initiateCheckout('${p.id}', null, null)"
                        class="w-full ${bgClass} border rounded-lg p-3 flex justify-between items-center transition-all group text-left">
                        <div>
                            <div class="text-xs font-bold ${textClass} group-hover:text-white transition-colors flex items-center gap-2">
                                ${p.title}
                                ${isHighlight ? '<span class="bg-teal text-black text-[8px] px-1.5 py-0.5 rounded font-black tracking-tighter">PRO</span>' : ''}
                            </div>
                            <div class="text-[10px] text-slate-500 group-hover:text-slate-400 mt-0.5">${p.desc}</div>
                        </div>
                        <div class="text-xs font-bold text-white bg-black/20 px-2 py-1 rounded border border-white/5 group-hover:border-white/20">
                            ${p.price}
                        </div>
                    </button>
            `;
        }).join('')}
             </div>
        </div>
        `;
    });

    container.innerHTML = html;
};

// Accordion Toggle Helper
window.toggleUpgradeGroup = function (key) {
    const el = document.getElementById(`group-upg-${key}`);
    const icon = document.getElementById(`icon-upg-${key}`);
    if (el) el.classList.toggle('hidden');
    if (icon) icon.classList.toggle('-rotate-90');
};

// Helper to reuse checkout logic (Global Scope)
async function initiateCheckout(productKey, userEmail, userId) {
    console.log('Initiating checkout for:', productKey);

    const btn = document.querySelector('.btn-unlock');
    if (btn) {
        btn.innerText = 'Redirecting...';
        btn.disabled = true;
    }

    try {
        // 1. Dynamic Pricing Lookup
        const product = PRODUCTS.find(p => p.id === productKey);
        // Fallback to legacy keys if not in array (e.g. from old buttons)
        const legacyMap = {
            'strategy_interview_sim': 'price_1SeRRnIH1WTKNasqQFCJDxH5',
            'monthly_plan': 'price_1Sbq1WIH1WTKNasqXrlCBDSD',
            'monthly_unlimited': 'price_1Sbq1WIH1WTKNasqXrlCBDSD',
            'strategy_plan': 'price_1SePlolH1WTKNasq64loXSAv',
            'strategy_closer': 'price_1SePpZIH1WTKNasqLuNq4sSZ',
            'strategy_followup': 'price_1SeQHYIH1WTKNasqpFyl2ef0',
            'strategy_rewrite': 'price_1Sgsf9IH1WTKNasqxvk528yY',
            'strategy_bundle': 'price_1SePqzlH1WTKNasq34FYIKNm',
            'strategy_linkedin': 'price_1ShWBJIH1WTKNasqd7p9VA5f'
        };

        const actualPriceId = product ? product.stripeId : legacyMap[productKey];

        if (!actualPriceId) {
            console.error("Invalid Product Key:", productKey);
            alert("Error: invalid product selection.");
            if (btn) {
                btn.innerText = 'Unlock';
                btn.disabled = false;
            }
            return;
        }

        // Determine Mode (Subscription vs Payment)
        const isSubscription = actualPriceId === 'price_1Sbq1WIH1WTKNasqXrlCBDSD';
        const mode = isSubscription ? 'subscription' : 'payment';

        console.log('Using Stripe Price ID:', actualPriceId, 'Mode:', mode);

        // Get User if missing (Dashboard Context)
        if (!userEmail || !userId) {
            const session = getSession();
            // Also try Supabase Auth directly if session is stale
            if (!session) {
                const { data: { user } } = await supabase.auth.getUser();
                if (user) {
                    userEmail = user.email;
                    userId = user.id;
                }
            } else {
                userEmail = session.email;
                userId = session.user_id; // Check if we store user_id in session
            }
        }

        // 2. Call Supabase Edge Function (STRICTLY)
        // 2. Call Python API (Replaces Edge Function)
        const token = localStorage.getItem('supabase.auth.token');
        if (!token) throw new Error("User not authenticated");

        const res = await fetch('/api/create-checkout-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                plan_type: productKey,
                userId: userId,
                email: userEmail,
                successUrl: window.location.href,
                mode: mode
            })
        });

        const data = await res.json();
        if (data.error) throw new Error(data.error);



        if (data?.url) {
            window.location.href = data.url;
        } else {
            throw new Error('Stripe did not return a checkout URL.');
        }

    } catch (err) {
        console.error('Checkout Failed Detail:', err);
        alert('Payment Error: ' + (err.message || err));

        if (btn) {
            btn.innerText = 'Unlock';
            btn.disabled = false;
        }
    }
}

function init() {
    console.log("Total Package Interview App v9.1 Loaded");
    const versionDisplay = document.createElement('div');
    versionDisplay.style.position = 'fixed';
    versionDisplay.style.bottom = '10px';
    versionDisplay.style.right = '10px';
    versionDisplay.style.fontSize = '12px';
    versionDisplay.style.color = '#888';
    versionDisplay.textContent = 'v9.0';
    document.body.appendChild(versionDisplay);

    // Run Access Check
    // Auto-Prompt ONLY if we are directly landing on the interview section to avoid dashboard annoyance
    const isInterviewContext = window.location.hash === '#interview' || window.location.hash === '#simulator';
    checkAccess('credits_interview', isInterviewContext);

    // Helper: Safely add event listener (only if el exists)
    function addClickListener(id, handler) {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', handler);
    }

    // Auto-analysis logic moved to end of init function

    // ---------------------------------------------------------
    // VIEW CONTROLLER (Phase 21: Cross-Nav Removal)
    // ---------------------------------------------------------
    const hash = window.location.hash;

    // Clear ALL active tabs first to prevent overlap
    const allPanes = document.querySelectorAll('.tab-pane');
    allPanes.forEach(pane => pane.classList.remove('active'));

    const resumeSection = document.getElementById('resume');
    const interviewSection = document.getElementById('interview');

    // Show based on Hash
    const adminHashes = ['#career-plan', '#linkedin', '#cover-letter', '#resume-builder'];

    if (hash === '#interview') {
        if (interviewSection) interviewSection.classList.add('active');
        document.title = "Interview Coach - Total Package Interview";
    } else if (adminHashes.includes(hash)) {
        // Do not activate Resume section. Wait for Admin Check to reveal specific tool.
        // We can set title here though
        document.title = "Admin Tool - Total Package Interview";

        // Temporarily activate it so we can see it if we are already logged in as admin?
        // Admin check later will unhide the *container* or specific elements, 
        // but we need the 'active' class on the pane for it to be visible in the layout.
        // The checkAccess function (lines 119-136) handles adding 'active', 
        // BUT it runs async. We might want to add 'active' here if we assume it's valid, 
        // or let the async check handle it. 
        // Given the bug, let's let checkAccess handle the specific admin tool activation 
        // to avoid showing it to non-admins.
    } else {
        // Default to Resume (or if hash is #resume)
        if (resumeSection) resumeSection.classList.add('active');
        document.title = "Resume Analysis - Total Package Interview";
    }

    // Initialize Global Variables
    if (!window.interviewHistory) window.interviewHistory = [];
    if (!window.questionCount) window.questionCount = 0;

    // Chat UI Helper Expose
    // This function is defined later in the DOMContentLoaded listener,
    // so we'll expose it there. For now, ensure it's not exposed prematurely.
    // window.addMessage = addMessage; // This line will be moved to DOMContentLoaded

    // Tab Switching Logic (This logic is now replaced by hash routing for main sections)
    // The tab-btn elements might still exist for sub-sections if any, but the main
    // 'resume' and 'interview' tabs are handled by the hash.
    // Navigation Logic for Sidebar
    const navItems = document.querySelectorAll('.nav-item');
    const panes = document.querySelectorAll('.tab-pane');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // Check if it's a real link (back to dash)
            if (!item.getAttribute('data-tab')) return;

            e.preventDefault();

            // Remove active class from all
            navItems.forEach(t => t.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked nav item and corresponding pane
            item.classList.add('active');
            const tabId = item.getAttribute('data-tab');
            const targetPane = document.getElementById(tabId);
            if (targetPane) targetPane.classList.add('active');

            // Allow hash update for bookmarking (optional, but good for refresh)
            window.location.hash = tabId;

            // Scroll to top
            window.scrollTo(0, 0);

            // SPECIAL: Init Interview Tab Logic if clicking on it
            if (tabId === 'interview') {
                const session = getSession();
                verifyInterviewAccess(session);
            }
        });
    });

    // Special: Verify LinkedIn on Load/Hash Change (since it's not a tab pane in the same way)
    // We hook into the existing hash change listener in app.html, but we can also check here based on view
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.target.id === 'view-linkedin-sidebar' && !mutation.target.classList.contains('hidden')) {
                // Remove premature check to prevent flicker. Rely on checkAccess() or user action.
                // const session = getSession();
                // verifyLinkedInAccess(session);
            }
        });
    });
    const linkedinSidebar = document.getElementById('view-linkedin-sidebar');
    if (linkedinSidebar) {
        observer.observe(linkedinSidebar, { attributes: true, attributeFilter: ['class'] });
    }

    // Initial Check if already on linkedin
    if (window.location.hash === '#linkedin') {
        const session = getSession();
        // verifyLinkedInAccess(session); // Disabled to prevent flicker
    }

    // Bind Unlock Button for Interview Logic
    const unlockInterviewBtn = document.getElementById('btn-unlock-interview');
    if (unlockInterviewBtn) {
        unlockInterviewBtn.addEventListener('click', async () => {
            const session = getSession();
            if (!session) return window.location.href = '/login';

            initiateCheckout('strategy_interview_sim', session.email);
        });
    }

    // Bind Unlock Button for LinkedIn Logic (Overlay Button)
    const unlockLinkedInBtn = document.getElementById('btn-unlock-linkedin-overlay');
    if (unlockLinkedInBtn) {
        unlockLinkedInBtn.addEventListener('click', async () => {
            const session = getSession();
            if (!session) return window.location.href = '/login';
            initiateCheckout('strategy_linkedin', session.email, session.user_id); // Pass ID!
        });
    }

    // Bind Optimize LinkedIn Action
    const optimizeLinkedinBtn = document.getElementById('optimize-linkedin-btn');
    if (optimizeLinkedinBtn) {
        optimizeLinkedinBtn.addEventListener('click', async () => {
            const inputEl = document.getElementById('linkedin-input');
            const input = inputEl ? inputEl.value : '';

            console.log("Capturing LinkedIn Input:", input.substring(0, 50) + "..."); // Debug Log

            if (!input.trim()) return alert("Please paste your 'About' section content.");

            // CHECK ACCESS BEFORE PROCEEDING
            const session = getSession();
            const credits = (session?.credits_linkedin || 0) + (session?.credits || 0);
            const isUnlimited = session?.is_unlimited || false;

            if (!isUnlimited && credits <= 0) {
                // Trigger Checkout
                if (confirm("Unlock this feature for $6.99?")) {
                    initiateCheckout('strategy_linkedin', session.email, session.user_id);
                }
                return;
            }

            // UI Loading State
            const originalText = optimizeLinkedinBtn.innerHTML;
            optimizeLinkedinBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> OPTIMIZING...';
            optimizeLinkedinBtn.disabled = true;

            const resultsArea = document.getElementById('linkedin-results-area');
            const placeholder = document.getElementById('linkedin-placeholder');
            const recommendationsEl = document.getElementById('linkedin-recommendations');
            const refinedEl = document.getElementById('linkedin-refined-sample');

            try {
                const session = getSession();
                const email = session ? session.email : null;

                const response = await fetch('/api', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${session?.access_token}`
                    },
                    body: JSON.stringify({
                        action: 'strategy_linkedin',
                        email: email,
                        aboutMe: input
                    })
                });

                const result = await response.json();

                if (result.error) {
                    alert('Error: ' + result.error);
                    if (result.redirect) window.location.href = result.redirect;
                } else {
                    // Success: Show Results
                    placeholder.classList.add('hidden');
                    resultsArea.classList.remove('hidden');

                    // Render Recommendations
                    if (result.recommendations && Array.isArray(result.recommendations)) {
                        recommendationsEl.innerHTML = result.recommendations.map(rec =>
                            `<div class="flex gap-2 items-start"><span class="text-blue-500">•</span> <p>${rec}</p></div>`
                        ).join('');
                    } else {
                        recommendationsEl.innerHTML = '<p>Profile analyzed. See refined version below.</p>';
                    }

                    // Render Refined Text
                    refinedEl.textContent = result.refined_content || "Optimization complete.";
                }

            } catch (error) {
                console.error(error);
                alert('Connection Error: ' + error.message);
            } finally {
                optimizeLinkedinBtn.innerHTML = originalText;
                optimizeLinkedinBtn.disabled = false;
            }
        });
    }




    // Handle Deep Linking on Load
    function handleDeepLink() {
        const hash = window.location.hash.substring(1); // remove #
        if (hash) {
            const targetNav = document.querySelector(`.nav-item[data-tab="${hash}"]`);
            if (targetNav) {
                targetNav.click();
            }
        }
    }
    handleDeepLink();

    // Helper function for API calls
    async function callApi(action, data, resultElementId) {
        const resultEl = document.getElementById(resultElementId);
        resultEl.innerHTML = '<em>Processing...</em>';
        resultEl.style.display = 'block';

        try {
            const response = await fetch('/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action, ...data }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.error) {
                resultEl.innerHTML = `<strong style="color:red">Error: ${result.error}</strong>`;
            } else {
                // Convert newlines to <br> for simple text display, or use a markdown parser if available
                // For now, simple text replacement
                resultEl.innerHTML = result.data.replace(/\n/g, '<br>');
            }
        } catch (error) {
            resultEl.innerHTML = `<strong style="color:red">Connection Error: ${error.message}</strong>`;
        }
    }

    // Tab 1: Resume Analysis (only on /app page)
    if (document.getElementById('analyze-resume-btn')) {
        document.getElementById('analyze-resume-btn').addEventListener('click', async () => {
            const resumeText = document.getElementById('resume-input').value;
            if (!resumeText) return alert('Please paste your resume.');

            const resultEl = document.getElementById('resume-result');
            const actionsEl = document.getElementById('resume-result-actions');
            resultEl.innerHTML = '<div class="loading-spinner"></div><p style="text-align:center">Analyzing... This may take up to 30 seconds.</p>';
            resultEl.style.display = 'block';
            actionsEl.style.display = 'none';

            try {
                const session = getSession();
                const email = session ? session.email : null;

                const response = await fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'analyze_resume', email: email, resume: resumeText })
                });
                const result = await response.json();

                if (result.error) {
                    resultEl.innerHTML = `<strong style="color:red">Error: ${result.error}</strong>`;
                } else if (!result.data) {
                    resultEl.innerHTML = `<strong style="color:red">Error: No data received.</strong>`;
                } else {
                    let data = result.data;

                    // Handle case where data is a string (rare with json_mode but possible)
                    if (typeof data === 'string') {
                        try {
                            // Try to fix markdown json if present
                            let clean = data.trim();
                            if (clean.startsWith('```json')) clean = clean.slice(7);
                            if (clean.startsWith('```')) clean = clean.slice(3);
                            if (clean.endsWith('```')) clean = clean.slice(0, -3);
                            data = JSON.parse(clean);
                        } catch (e) {
                            // Fallback to text display if not JSON
                            console.error("Could not parse JSON", e);
                            resultEl.innerHTML = data.replace(/\n/g, '<br>');
                            actionsEl.style.display = 'flex';
                            return;
                        }
                    }

                    // Render the UI
                    renderResumeReport(data, resultEl);
                    actionsEl.style.display = 'flex';
                }
            } catch (error) {
                resultEl.innerHTML = `<strong style="color:red">Connection Error: ${error.message}</strong>`;
            }
        });

        function renderResumeReport(data, container) {
            // Helper for priority colors
            const getPriorityColor = (p) => {
                const map = { 'HIGH': '#dc3545', 'MEDIUM': '#ffc107', 'LOW': '#28a745' };
                return map[p] || '#6c757d';
            };

            const html = `
                <div class="resume-report">
                
                <!-- 0. DISCLAIMER (Moved to Top) -->
                <div class="upsell-disclaimer-box" style="margin-bottom: 20px; background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; position:relative;">
                     ⚠️ <strong>IMPORTANT:</strong> AI-generated content should always be reviewed and customized to ensure it accurately represents your experience and authentic voice.
                     <button onclick="location.reload()" style="position:absolute; top:10px; right:10px; background:white; border:1px solid #ccc; padding:5px 10px; cursor:pointer; font-size:0.8rem; border-radius:4px;">🔄 Start Over</button>
                </div>

                <!-- 1. COMPARISON & SCORE -->
                <div class="report-section benchmark-section">
                    <h4>📊 Competitive Positioning</h4>
                    
                    <!-- Score moved to top, centered -->
                    <div style="display:flex; justify-content:center; margin-bottom:20px;">
                        <div class="score-circle-large">
                            <span>${data.overall_score}</span>
                            <label>Your Score</label>
                        </div>
                    </div>

                    <div class="benchmark-grid">
                        <div class="benchmark-bars" style="width:100%">
                            <div class="bar-group">
                                <div class="bar-label">
                                    <span>Industry Benchmark</span>
                                    <span>${data.benchmark.avg_score}/100</span>
                                </div>
                                <div class="progress-bar"><div class="fill avg" style="width: ${data.benchmark.avg_score}%"></div></div>
                            </div>
                            <div class="bar-group">
                                <div class="bar-label">
                                    <span>Top 10%</span>
                                    <span>${data.benchmark.top_10_score}/100</span>
                                </div>
                                <div class="progress-bar"><div class="fill top" style="width: ${data.benchmark.top_10_score}%"></div></div>
                            </div>
                            <div class="benchmark-text">
                                <strong>Status:</strong> ${data.benchmark.text.replace(/^Status:\s*/i, '')}<br>
                                    <span style="font-size:0.9em; color:#666">
                                        ✅ ${data.benchmark.ahead_reasons[0]}<br>
                                            ⚠️ Gap: ${data.benchmark.gap_reasons[0]}
                                    </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- [OMITTED SECTIONS KEPT SAME] -->
                ${data.red_flags && data.red_flags.length > 0 ? `
                        <div class="report-section red-flags">
                            <h4>🚩 Critical Issues (Fix Before Applying)</h4>
                            <div class="flag-list">
                                ${data.red_flags.map(flag => `
                                    <div class="flag-item">
                                        <h5>${flag.title}</h5>
                                        <p><strong>Problem:</strong> ${flag.issue}</p>
                                        ${flag.examples && flag.examples.length > 0 ? `
                                            <div class="flag-examples">
                                                <strong>Specifically:</strong>
                                                <ul>
                                                    ${flag.examples.map(ex => `<li>"${ex}"</li>`).join('')}
                                                </ul>
                                            </div>
                                        ` : ''}
                                        <div class="flag-fix"><strong>✅ How to Fix:</strong> ${flag.fix}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                <!-- 2. STRENGTHS -->
                <div class="report-section strengths">
                    <h4>💪 Key Strengths</h4>
                    <div class="grid-3">
                        ${(data.strengths || []).map(s => `
                                <div class="card-item">
                                    <h5>${s.title}</h5>
                                    <p>${s.description}</p>
                                </div>
                            `).join('')}
                    </div>
                </div>

                <!-- 3. IMPROVEMENTS WITH EXAMPLES -->
                <div class="report-section improvements">
                    <h4>🚀 High Impact Improvements</h4>
                    <div class="list-cards">
                        ${(data.improvements || []).map(i => `
                                <div class="list-item detailed">
                                    <div class="list-header">
                                        <span class="badge" style="background:${getPriorityColor(i.priority)}">${i.priority}</span>
                                        <strong>${i.title}</strong>
                                    </div>
                                    <div class="list-body">
                                        <p>${i.suggestion}</p>
                                        <div class="example-box">
                                            <div class="ex-row"><strong>Current:</strong> "${i.current}"</div>
                                            <div class="ex-arrow">⬇️ Better</div>
                                            <div class="ex-row better"><strong>Stronger:</strong> "${i.better.replace(/\[X\]/g, '<b class="place">PLACEHOLDER</b>')}"</div>
                                        </div>
                                        <div class="why-box">
                                            <strong>Why:</strong> ${i.why}
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                    </div>
                </div>

                <!-- 4. QUICK REWRITES -->
                <div class="report-section rewrites">
                    <h4>📝 Quick Rewrites (Copy These)</h4>
                    <div class="grid-1">
                        ${(data.rewrites || []).map((r, idx) => `
                                <div class="rewrite-card">
                                    <h5>${idx + 1}. ${r.type} Bullet</h5>
                                    <div class="rewrite-grid">
                                        <div class="rewrite-col old">
                                            <h6>Your Version</h6>
                                            <p>"${r.original}"</p>
                                        </div>
                                        <div class="rewrite-col new">
                                            <h6>Stronger Version</h6>
                                            <p>"${r.rewritten.replace(/\[.*?\]/g, match => `<span class="highlight-metric">${match}</span>`)}"</p>
                                        </div>
                                    </div>
                                    <p class="explanation">💡 ${r.explanation}</p>
                                    ${r.metric_question ? `<div class="metric-prompt"><strong>❓ NEEDS METRIC:</strong> ${r.metric_question}</div>` : ''}
                                </div>
                            `).join('')}
                    </div>
                </div>

                <!-- 5. KEYWORD ANALYSIS -->
                <div class="report-section keywords-detailed">
                    <h4>🔑 Keyword Analysis</h4>
                    <div class="keyword-grids">
                        <div class="k-col">
                            <h5>✅ Using Well</h5>
                            <ul class="k-list good">
                                ${(data.keywords.good || []).map(k => `
                                        <li>
                                            <strong>"${k.word}"</strong> (${k.count}x)
                                            <span class="tip">${k.context || ''}</span>
                                        </li>
                                    `).join('')}
                            </ul>
                        </div>
                        <div class="k-col">
                            <h5>❌ Missing High-Priority</h5>
                            <ul class="k-list missing">
                                ${(data.keywords.missing || []).map(k => `<li>"${k.word}" <span class="tip">(${k.advice})</span></li>`).join('')}
                            </ul>
                        </div>
                        <div class="k-col">
                            <h5>⚠️ Overused</h5>
                            <ul class="k-list overused">
                                ${(data.keywords.overused || []).map(k => `<li>"${k.word}" (${k.count}x) <br><span class="alts">Try: ${k.alternatives.join(', ')}</span></li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    ${data.role_gaps ? `
                        <div class="role-gaps">
                            <h5>🔑 Role-Specific Keyword Gaps</h5>
                            ${data.role_gaps.map(rg => `
                                <div class="gap-item">
                                    <div class="gap-role"><strong>${rg.role}</strong></div>
                                    
                                    ${rg.fixes ? rg.fixes.map(fix => `
                                         <div class="gap-fix-box">
                                            <div class="gap-row old"><strong>Generic:</strong> "${fix.existing_bullet}"</div>
                                            <div class="gap-row new"><strong>Enhanced:</strong> "${fix.enhanced_bullet}"</div>
                                            <div class="gap-reason">Added: ${fix.added_keywords.map(k => `<span class="tag med">${k}</span>`).join('')} - ${fix.reason}</div>
                                         </div>
                                    `).join('') : `
                                        <div class="gap-missing">Missing: ${rg.missing_keywords.map(w => `<span class="tag med">${w}</span>`).join('')}</div>
                                    `}
                                </div>
                            `).join('')}
                        </div>
                        ` : ''}
                </div>

                <!-- 6. FINAL STEPS (Consolidated Section) -->
                <div class="final-steps-wrapper" style="page-break-before: always;">
                    
                    <div class="grid-2">
                        <!-- ATS -->
                        <div class="report-section ats">
                            <h4>🤖 ATS Compatibility: ${(data.ats_compatibility || {}).score || 0}/10</h4>
                            <ul>
                                ${(data.ats_compatibility?.issues || []).map(issue => `<li>⚠️ ${issue}</li>`).join('')}
                            </ul>
                            <p><em>${(data.ats_compatibility || {}).recommendation}</em></p>
                        </div>
                        
                        <!-- FORMATTING -->
                        <div class="report-section formatting">
                            <h4>🎨 Formatting Fixes</h4>
                            <ul>
                                ${(data.formatting || []).map(f => `<li><strong>${f.issue}:</strong> ${f.fix}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <!-- ACTION PLAN -->
                    <div class="report-section action-plan">
                        <h4>⚡ Next Steps</h4>
                        <div class="action-group">
                            <h5>Quick Wins (30 mins)</h5>
                            <ul>${(data.action_plan?.quick_wins || []).map(w => `<li><input type="checkbox"> ${w}</li>`).join('')}</ul>
                        </div>
                        <div class="action-group">
                            <h5>Deep Work (2 hours)</h5>
                            <ul>${(data.action_plan?.medium_effort || []).map(w => `<li><input type="checkbox"> ${w}</li>`).join('')}</ul>
                        </div>
                    </div>

                </div>

                <!-- 9. UPSELL (Checkout Activated) -->
                <div class="upsell-section-new">
                    <h3 class="upsell-header-large">💡 NEED HELP IMPLEMENTING THESE CHANGES?</h3>
                    <p class="upsell-subheader">See what needs fixing but don't have time to rewrite yourself?</p>

                    <div class="upsell-blue-box" style="text-align:center;">
                        <span class="blue-box-title">✨ AI-ASSISTED RESUME REWRITE</span>
                        <p class="blue-box-desc">We'll rewrite your resume implementing all the recommendations above.</p>
                        
                        <!-- List kept concise or removed to focus on button -->

                        <button id="unlock-rewrite-btn" class="action-btn" style="background-color: #20C997; font-size:1.2rem; padding: 1rem 2rem; margin-top:1rem; width:100%;">Unlock One-Click Rewrite ($9.99)</button>
                        <p style="font-size:0.8rem; color:#666; margin-top:10px;">Secure payment via Stripe. Instant access.</p>
                    </div>
                </div>

                <!-- 10. INTERVIEW TIP -->
                <div class="report-section interview-tip">
                    <h4>💡 Interview Readiness</h4>
                    <p>${data.interview_tip || "Practice your STAR method answers."}</p>
                </div>
            `;
            container.innerHTML = html;

            // Activate Checkout Button
            setTimeout(() => {
                const checkoutBtn = document.getElementById('unlock-rewrite-btn');
                if (checkoutBtn) {
                    checkoutBtn.addEventListener('click', async () => {
                        checkoutBtn.disabled = true;
                        checkoutBtn.textContent = "Processing...";
                        try {
                            const token = localStorage.getItem('supabase.auth.token');
                            const res = await fetch('/api/create-checkout-session', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({
                                    plan_type: 'strategy_rewrite',
                                    successUrl: window.location.origin + '/app?status=success#resume-builder',
                                    mode: 'payment'
                                })
                            });
                            const result = await res.json();
                            if (result.url) window.location.href = result.url;
                            else throw new Error(result.error);

                            if (error) throw error;
                            if (data?.url) window.location.href = data.url;
                        } catch (e) {
                            console.error(e);
                            alert("Checkout failed.");
                        } finally {
                            checkoutBtn.disabled = false;
                            checkoutBtn.textContent = "Unlock One-Click Rewrite ($9.99)";
                        }
                    });
                }
            }, 500);

            // Hide Input Form
            const inputContainer = document.getElementById('resume-input');
            const analyzeBtn = document.getElementById('analyze-resume-btn');
            // Actually, we want to hide the whole inputs, maybe just style display none on them
            if (inputContainer) inputContainer.style.display = 'none';
            if (analyzeBtn) analyzeBtn.style.display = 'none';
            // Also the placeholder text p tag
            // A bit hacky to find it via DOM traversal, but okay for now or selecting specifically
            // The Start Over button in disclaimer handles the reset via reload.
        }


    }

    // Resume Analysis Print Button
    const printBtn = document.getElementById('resume-print-btn');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            const content = document.getElementById('resume-result').innerHTML;

            // Open a new window with styled content for printing
            const printWindow = window.open('', '_blank', 'width=800,height=600');
            if (printWindow) {
                printWindow.document.write(`
            < !DOCTYPE html >
                <html>
                    <head>
                        <title>Resume Analysis Report</title>
                        <style>
                            body {
                                font - family: Arial, sans-serif;
                            padding: 40px;
                            max-width: 800px;
                            margin: 0 auto;
                            line-height: 1.6;
                        }
                            h2 {
                                text - align: center;
                            margin-bottom: 30px;
                            color: #333;
                        }
                            .analysis-section {
                                padding: 20px;
                            margin: 20px 0;
                            border-radius: 8px; 
                        }
                            .analysis-section.strengths {
                                border - left: 5px solid #28a745;
                            background: #e8f5e9; 
                        }
                            .analysis-section.strengths h3 {
                                color: #28a745; 
                        }
                            .analysis-section.improvements {
                                border - left: 5px solid #007bff;
                            background: #e3f2fd; 
                        }
                            .analysis-section.improvements h3 {
                                color: #007bff; 
                        }
                            h3 {
                                margin - top: 0;
                            margin-bottom: 15px;
                        }
                            @media print {
                                body {padding: 20px; }
                            .analysis-section {
                                -webkit - print - color - adjust: exact !important;
                            print-color-adjust: exact !important;
                            }
                            .analysis-section.improvements {
                                page -break-before: always;
                            }
                        }
                        </style>
                    </head>
                    <body>
                        <h2>Resume Analysis Report</h2>
                        ${content}
                        <script>
                            window.onload = function() {
                                window.print();
                            // Close the window after a short delay (allows print dialog to open)
                            setTimeout(function() {window.close(); }, 500);
                        };
                        </script>
                    </body>
                </html>
        `);
                printWindow.document.close();
            }
        });
    }

    // Resume Analysis Copy Button
    const copyBtn = document.getElementById('resume-copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            const content = document.getElementById('resume-result');
            try {
                await navigator.clipboard.writeText(content.innerText);
                const btn = document.getElementById('resume-copy-btn');
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = originalText, 2000);
            } catch (err) {
                alert('Failed to copy. Please select text manually.');
            }
        });
    }

    // Tab 2: Interview Coach
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');

    const sendChatBtn = document.getElementById('send-chat-btn');
    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', () => {
            primeAudio();
            showThinkingState(); // Trigger UI for text input too
            sendChatMessage();
        });
    }
    const startInterviewBtn = document.getElementById('start-interview-btn');
    if (startInterviewBtn) {
        startInterviewBtn.addEventListener('click', async () => {
            // Permission Check (Silent check first, then prompt if failed)
            const hasAccess = await checkAccess('credits_interview', true);
            if (!hasAccess) return;

            // Prioritize Context Accordion inputs, fallback to sidebar
            const accordionJD = document.getElementById('job-description-input') ? document.getElementById('job-description-input').value : '';
            const sidebarJD = document.getElementById('interview-job-posting') ? document.getElementById('interview-job-posting').value : '';

            let jobPosting = accordionJD || sidebarJD;

            // MISSION BRIEF LOGIC: Construct composite string if structured data exists
            try {
                const mCtx = JSON.parse(localStorage.getItem('mission_context'));
                if (mCtx && mCtx.role && mCtx.company) {
                    jobPosting = `MISSION BRIEFING:\nTarget Role: ${mCtx.role} at ${mCtx.company}.\n\nMISSION PRIORITIES (FOCUS AREAS):\n${mCtx.jd || "No specific priorities set."}`;
                    console.log("Constructed Mission Brief Payload:", jobPosting);
                }
            } catch (e) { console.warn("Mission Context Parse Error", e); }

            const resumeText = document.getElementById('resume-text-input') ? document.getElementById('resume-text-input').value : '';

            const chatInterface = document.getElementById('chat-interface');
            const activeState = document.getElementById('interview-active-state');

            if (jobPosting.trim()) {
                primeAudio();
                primeAudio();
                questionCount = 0; // Correctly start at 0 for Turn 1
                interviewHistory = []; // Reset history

                // Show Chat Interface, Hide Intro & Setup
                // Show Chat Interface, Hide Intro & Setup
                if (activeState) activeState.classList.add('hidden');
                // Chat Interface will be revealed by finishSetup() after countdown

                // START COUNTDOWN (Parallel with API calls)
                startCountdown();

                // Reset Memory
                interviewHistory = [];
                lastAiQuestion = "Let's start with your work history. Can you tell me about your previous roles and why this position is the right next step for you?"; // Hardcoded Greeting Match

                const intro = document.getElementById('interview-intro');
                if (intro) intro.classList.add('hidden');

                // UI: Toggle Sidebar Buttons
                const startBtn = document.getElementById('start-interview-btn');
                const activeControls = document.getElementById('active-session-controls');
                if (startBtn) startBtn.classList.add('hidden');
                if (activeControls) activeControls.classList.remove('hidden');

                console.log("Starting Interview Flow...");
                await processJobDescription(); // Analyze JD before starting

                // Pass resume info & Company Name & Interviewer Intel & Role
                let companyName = "the target company";
                let roleTitle = "the open position"; // Default
                let interviewerIntel = "";

                try {
                    const mCtx = JSON.parse(localStorage.getItem('mission_context'));
                    if (mCtx) {
                        if (mCtx.company) companyName = mCtx.company;
                        if (mCtx.role) roleTitle = mCtx.role; // Use exact analyzed role
                        if (mCtx.notes) interviewerIntel = mCtx.notes;
                    }
                } catch (e) { }

                sendChatMessage("I have provided the job description. Please start the interview.", true, false, resumeText, companyName, interviewerIntel, roleTitle);
            } else {
                alert("Please paste a job description first.");
            }
        });
    }


    function primeAudio() {
        const audioPlayer = document.getElementById('ai-audio-player');
        // Attempt to play and immediately pause to unlock audio context
        audioPlayer.play().catch(() => { });
        audioPlayer.pause();
    }
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChatMessage();
        });
    }

    // JD Analyzer Logic
    let jobData = { role: "", company: "", summary: "" };

    async function processJobDescription() {
        const jdInput = document.getElementById('job-description-input') || document.getElementById('interview-job-posting');
        const rawText = jdInput ? jdInput.value : "";

        if (!rawText || rawText.length < 50) {
            console.log("JD too short, skipping analysis.");
            jobData = { role: "this role", company: "the company", summary: "" };
            return;
        }

        console.log("Analyzing JD...");
        // Show lightweight indicator if needed, but for now we just block briefly

        try {
            const response = await fetch('/api/analyze-jd', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_description: rawText })
            });

            jobData = await response.json();
            console.log("Analysis Complete:", jobData);

        } catch (error) {
            console.error("Analysis Failed", error);
            // Fallback defaults
            jobData = { role: "this role", company: "the company", summary: "" };
        }
    }

    // Voice Logic - Global Scope
    let mediaRecorder;
    let audioChunks = [];

    window.toggleRecording = async function () {
        const recordBtn = document.getElementById('record-btn');
        console.log("toggleRecording called");

        if (mediaRecorder && mediaRecorder.state === 'recording') {
            console.log("Stopping recording...");
            mediaRecorder.stop();
            if (recordBtn) {
                recordBtn.textContent = '🎤';
                recordBtn.style.background = '#dc3545'; // Red (default)
            }
        } else {
            console.log("Starting recording...");
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    console.log("Recording stopped, processing...");
                    showThinkingState(); // Trigger Thinking UI immediately
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.readAsDataURL(audioBlob);
                    reader.onloadend = () => {
                        const base64Audio = reader.result;
                        sendVoiceMessage(base64Audio);
                    };
                    // Stop all tracks to release microphone
                    stream.getTracks().forEach(track => track.stop());
                };

                mediaRecorder.start();
                if (recordBtn) {
                    recordBtn.textContent = '⏹️';
                    recordBtn.style.background = '#28a745'; // Green (recording)
                }
            } catch (err) {
                console.error("Error accessing microphone:", err);
                alert("Could not access microphone. Please allow permissions. Error: " + err.message);
            }
        }
    };

    // sendVoiceMessage moved to global scope


    // MEMORY PATCH: Frontend History Tracking (interviewHistory already declared at line 490)
    let lastAiQuestion = "Interviewer Greetings"; // Initial value

    async function sendChatMessage(msg = null, isStart = false, skipUI = false, resumeText = '', companyName = null, interviewerIntel = "", roleTitle = "") {
        const message = msg || (chatInput ? chatInput.value : '');
        if (!message) return;

        // Note: In a real app, we'd send chat history. For prototype, we just send the last message.
        // To make it better, we could grab the last few messages from the DOM.

        // Skip adding message to UI if it's the hidden start command
        if (!isStart && !skipUI) {
            // Add user message
            addMessage(message, 'user');
        }
        if (chatInput) chatInput.value = '';

        // REMOVED: Old Thinking Interval Logic (Refactored to showThinkingState)


        // Prioritize Accordion JD, fallback to sidebar
        const accordionJD = document.getElementById('job-description-input') ? document.getElementById('job-description-input').value : '';
        const sidebarJD = document.getElementById('interview-job-posting') ? document.getElementById('interview-job-posting').value : '';
        const jobPosting = accordionJD || sidebarJD || "No Job Description Provided.";

        const { voice, speed } = getVoiceSettings();

        // Get Email from Session for Credit Deduction
        let email = null;
        try {
            const sessionItem = localStorage.getItem(SESSION_KEY);
            if (sessionItem) {
                const sessionObj = JSON.parse(sessionItem);
                email = sessionObj.email || sessionObj.user?.email;
            }
        } catch (e) { console.error("Error fetching email from session", e); }

        const processedData = {
            message: message,
            jobPosting: jobPosting,
            resumeText: resumeText,
            companyName: companyName,
            interviewer_intel: interviewerIntel, // Pass Intel!
            isStart: isStart,
            questionCount: questionCount + 1,
            email: email,
            voice: voice, // Pass voice preference
            role_title: isStart ? jobData.role : roleTitle, // Use analyzed role if starting, else the passed roleTitle
            company_name: isStart ? jobData.company : undefined,
            role_summary: isStart ? jobData.summary : undefined
        };

        try {
            // NEW: BLOCKING ARCHITECTURE (Quality Fix)
            const session = getSession();
            const response = await fetch('/api/get-feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session?.access_token}`
                },
                body: JSON.stringify({
                    message: message,
                    jobPosting: jobPosting,
                    resumeText: resumeText,
                    companyName: companyName,
                    interviewer_intel: interviewerIntel,
                    history: interviewHistory,
                    isStart: isStart,
                    questionCount: questionCount, // Align with 0-index based turns
                    email: email,
                    voice: voice,
                    role_title: isStart ? jobData.role : undefined,
                    company_name: isStart ? jobData.company : undefined,
                    role_summary: isStart ? jobData.summary : undefined
                })
            });

            // Clear Thinking UI
            hideThinkingState();

            // Check errors
            if (!response.ok) {
                throw new Error("API Failed");
            }

            const data = await response.json();

            // MEMORY PATCH: Update History
            if (message && lastAiQuestion) {
                // Store the full turn data for the Auditor
                interviewHistory.push({
                    question: lastAiQuestion,
                    answer: message,
                    feedback: data.response?.feedback || '',
                    internal_score: data.response?.internal_score || 0
                });
                // Keep history reasonable (last 20 turns)
                if (interviewHistory.length > 20) interviewHistory.shift();
            }

            // MEMORY PATCH: Capture Next Question for next turn
            if (data.response && data.response.next_question) {
                lastAiQuestion = data.response.next_question;
                questionCount++; // Progress question counter
            }

            // --- REFEREE: CHECK FOR GAME OVER ---
            if (data.is_complete) {
                console.log("Referee: Interview Complete.");

                // 1. Audio Playback Delayed (Moved to Step B)

                // 2. Kill Mic immediately
                const recordBtn = document.getElementById('record-btn');
                if (recordBtn) {
                    recordBtn.disabled = true;
                    recordBtn.style.background = '#6c757d'; // Gray
                    recordBtn.textContent = '✅';
                }

                // 3. SEQUENCED REVEAL
                if (data.response) {
                    // Step A: Show Feedback Immediately
                    if (data.response.feedback) {
                        const feedbackHtml = `<div class="mb-4 p-3 bg-gray-800 rounded border border-gray-700">
                            <div class="text-xs text-indigo-400 font-bold mb-1 uppercase tracking-wider">Feedback</div>
                            <div class="text-sm leading-relaxed">${data.response.feedback}</div>
                        </div>`;
                        addMessage(feedbackHtml, 'system', true);
                    }

                    // Step B: Wait 5 Seconds -> Show Closing Message ("Thank you...") + Play Audio
                    setTimeout(() => {
                        // Play Audio NOW (Synced with "Thank You" text)
                        if (data.audio) {
                            const audio = new Audio("data:audio/mp3;base64," + data.audio);
                            audio.play().catch(e => console.error("Playback failed:", e));
                        }

                        if (data.response.next_question) {
                            const closingHtml = `<div class="text-white text-lg font-medium leading-relaxed">${data.response.next_question}</div>`;
                            addMessage(closingHtml, 'system', true);
                        }

                        // Step C: Wait another 5 Seconds -> Generate Report
                        setTimeout(() => {
                            const finalReportText = data.response.formatted_report || data.response.feedback || "No Report Generated";
                            const finalScore = data.average_score || data.response.average_score || 0;
                            generateInterviewReport(finalReportText, finalScore);
                        }, 5000);

                    }, 5000);
                }

                return; // STOP HERE
            }
            // ------------------------------------

            const aiData = data.response; // The structured JSON from backend
            const audioBase64 = data.audio;

            // 1. VISUAL UPDATE
            // Construct a nice display HTML
            let displayHtml = "";

            if (aiData.feedback) {
                displayHtml += `<div class="mb-4 p-3 bg-gray-800 rounded border border-gray-700">
                    <div class="text-xs text-indigo-400 font-bold mb-1 uppercase tracking-wider">Feedback</div>
                    <div class="text-sm leading-relaxed">${aiData.feedback}</div>
                </div>`;
            }

            // The main question bubbles
            if (aiData.next_question) {
                displayHtml += `<div class="text-white text-lg font-medium leading-relaxed">${aiData.next_question}</div>`;
            } else {
                // Fallback if structure missing
                displayHtml += `<div class="text-white">${JSON.stringify(aiData)}</div>`;
            }

            // 1.5 PUBLISH MESSAGE
            // ONLY if NOT complete (to avoid duplication with the Final Report Card)
            if (!data.is_complete) {
                // Use addMessage to show the response in a new bubble (system/AI)
                addMessage(displayHtml, 'system', true);

                // AUTO-TRIGGER FINAL REPORT (Option 1 Fix)
                // If closing message is detected, silently trigger the next turn to generate report
                // GUARD: Only trigger if we are at the END of the interview (Q6+)
                if (aiData.next_question && questionCount >= 6 && (
                    aiData.next_question.includes("Thank you") ||
                    aiData.next_question.includes("concludes") ||
                    aiData.next_question.includes("pleasure speaking")
                )) {
                    console.log("Referee: Closing message detected. Auto-triggering Final Report...");
                    setTimeout(() => {
                        sendChatMessage("GENERATE_REPORT", false, true); // skipUI=true (silent)
                    }, 2500); // 2.5s delay to let audio start
                }
            }

            // 2. AUDIO PLAYBACK (Base64)
            if (audioBase64) {
                console.log("[Audio] Received audio from backend.");
                try {
                    const audio = new Audio("data:audio/mp3;base64," + audioBase64);
                    audio.play().catch(e => console.error("Playback failed:", e));
                    console.log("Audio playing...");
                } catch (e) {
                    console.error("Audio setup error:", e);
                }
            } else {
                console.warn("[Audio] No audio returned from backend.");
            }

            // POST-STREAM STATE UPDATES
            currentQuestionText = aiData.next_question;

        } catch (e) {
            hideThinkingState();
            addMessage('Stream Error: ' + e.message, 'system');
        }
    }

    async function generateInterviewReport(existingReport = null, existingScore = 0) {
        const loadingId = addMessage('Saving Final Executive Coaching Report...', 'system');

        try {
            const session = getSession();
            // ... (setup variables) ...

            let result = {};

            if (existingReport) {
                // OPTIMIZATION: Reuse the report we already generated in the chat loop
                console.log("Reusing existing report for DB save...");
                result = {
                    data: {
                        report: existingReport,
                        average_score: existingScore // USE THE SCORE WE GOT FORM BACKEND
                    }
                };
            } else {
                // Fallback: Generate new one (Legacy path)
                const session = getSession();
                const email = session ? session.email : null;
                const interviewJobPosting = document.getElementById('interview-job-posting');
                const jobPosting = interviewJobPosting ? interviewJobPosting.value : '';

                const response = await fetch('/api', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getSession()?.access_token}`
                    },
                    body: JSON.stringify({
                        action: 'generate_report',
                        email: email,
                        history: interviewHistory,
                        jobPosting: jobPosting
                    })
                });
                result = await response.json();
            }

            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            // Disable input to prevent further messages
            const chatInputEl = document.getElementById('chat-input');
            if (chatInputEl) {
                chatInputEl.disabled = true;
                chatInputEl.placeholder = "Interview Complete";
            }

            const sendBtn = document.getElementById('send-chat-btn');
            if (sendBtn) sendBtn.disabled = true;

            const recordBtn = document.getElementById('record-btn');
            if (recordBtn) recordBtn.disabled = true;

            if (result.data && result.data.report) {

                // SAVE TO DB LOGIC
                // SAVE TO DB LOGIC
                try {
                    // Use Supabase Auth User (Source of Truth for RLS)
                    const { data: { user } } = await supabase.auth.getUser();

                    if (user) {
                        // Retrieve Context for Metadata
                        let jobTitle = "Interview";
                        let companyName = "Unknown Company";
                        try {
                            const mCtx = JSON.parse(localStorage.getItem('mission_context'));
                            if (mCtx) {
                                if (mCtx.role) jobTitle = mCtx.role;
                                if (mCtx.company) companyName = mCtx.company;
                            }
                        } catch (e) { }

                        // Extract individual question scores and rubric data
                        const questionScores = {};
                        const rubricData = {};

                        interviewHistory.forEach((turn, idx) => {
                            const questionNum = idx + 1;
                            const scoreKey = `q${questionNum}_score`;
                            questionScores[scoreKey] = turn.internal_score || 0;

                            // Aggregate rubric data if present
                            if (turn.rubric_data) {
                                rubricData[`Q${questionNum}`] = turn.rubric_data.checklist;
                            }
                        });

                        const { error } = await supabase
                            .from('interviews')
                            .insert({
                                user_id: user.id,
                                overall_score: result.data.average_score || 0,
                                transcript: JSON.stringify(interviewHistory),
                                questions: interviewHistory,
                                executive_report: result.data.report,
                                session_name: `Interview ${new Date().toLocaleDateString()}`,
                                job_title: jobTitle,
                                company: companyName,
                                // Individual question scores
                                q1_score: questionScores.q1_score || null,
                                q2_score: questionScores.q2_score || null,
                                q3_score: questionScores.q3_score || null,
                                q4_score: questionScores.q4_score || null,
                                q5_score: questionScores.q5_score || null,
                                q6_score: questionScores.q6_score || null,
                                // Rubric checklist data (JSONB)
                                rubric_data: Object.keys(rubricData).length > 0 ? rubricData : null
                            });


                        if (error) {
                            console.error("DB Save Error:", error);
                            alert("Warning: Could not save interview result to database. Error: " + error.message + " (Details: " + error.details + ")");
                        } else {
                            console.log("Interview Saved Successfully");
                            // Optional: Small toast or console log is enough usually, but let's be sure
                        }
                    } else {
                        console.error("Save Failed: No authenticated user found.");
                        alert("Warning: You do not appear to be logged in. Interview result was NOT saved.");
                    }
                } catch (dbErr) {
                    console.error("DB Save Exception:", dbErr);
                    alert("System Error: Could not save interview. " + dbErr.message);
                }

                // RENDER THE EXECUTIVE REPORT FROM AI
                addMessage(result.data.report, 'system', true);

                // Add a small return link after the report
                addMessage('<div class="mt-4"><a href="/dashboard" class="text-blue-500 hover:underline">← Return to Dashboard</a></div>', 'system', true);
            } else {
                addMessage("Error: Could not generate structured report. Please check your connection.", 'system');
            }

        } catch (e) {
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            addMessage("Error generating report: " + e.message, 'system');
        }
    }

    // Payment alert function for upsell buttons
    window.showPaymentAlert = function () {
        // Redirect to pricing page
        window.location.href = '/pricing';
    };

    function addMessage(text, sender, isHtml = false) {
        const div = document.createElement('div');
        // Map generic 'user'/'system' to our specific CSS classes
        const cssClass = sender === 'user' ? 'msg-user' : 'msg-system';
        div.classList.add('msg-bubble', cssClass);
        div.id = 'msg-' + Date.now();

        if (isHtml) {
            div.innerHTML = text;
        } else {
            div.textContent = text;
        }

        if (chatWindow) {
            chatWindow.appendChild(div);
            // Ensure we scroll the parent container, not just the window div if it's not the scroller
            // The scroller is #view-interview-main or .overflow-auto parent
            div.scrollIntoView({ behavior: 'smooth' });
        }
        return div.id;
    }
    // Expose functions to global scope for sendVoiceMessage and button handlers
    window.addMessage = addMessage;
    window.sendChatMessage = sendChatMessage;
    window.generateInterviewReport = generateInterviewReport;
} // End of Interview Page (Resume Analysis + Interview Coach)


// ADMIN TOOLS LOGIC (Restored)
// Only init listeners if elements exist (which they do now in app.html)
if (document.getElementById('generate-plan-btn')) {
    console.log("Initializing Admin Tools...");

    // Tab 3: Career Planner
    document.getElementById('generate-plan-btn').addEventListener('click', async () => {
        const jobTitleEl = document.getElementById('job-title');
        const companyEl = document.getElementById('company');
        const jobPostingEl = document.getElementById('job-posting');

        const jobTitle = jobTitleEl ? jobTitleEl.value : '';
        const company = companyEl ? companyEl.value : '';
        const jobPosting = jobPostingEl ? jobPostingEl.value : '';

        if (jobTitle && company) {
            const outputDiv = document.getElementById('planner-result');
            outputDiv.innerHTML = '<div class="loading-spinner">Generating plan...</div>';

            try {
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getSession()?.access_token}`
                    },
                    body: JSON.stringify({ action: 'career_plan', jobTitle, company, jobPosting })
                });
                const result = await response.json();

                if (result.data) {
                    renderCareerPlan(result.data, outputDiv);
                } else {
                    outputDiv.innerHTML = 'Error generating plan.';
                }
            } catch (e) {
                console.error(e);
                outputDiv.innerHTML = 'Error generating plan.';
            }
        }
    });

    function renderCareerPlan(data, container) {
        // Attempt to parse if string
        if (typeof data === 'string') {
            try {
                // Clean up potential markdown code blocks
                let clean = data.trim();
                if (clean.startsWith('```json')) clean = clean.slice(7);
                if (clean.startsWith('```')) clean = clean.slice(3);
                if (clean.endsWith('```')) clean = clean.slice(0, -3);

                if (clean.startsWith('{')) {
                    data = JSON.parse(clean);
                } else {
                    // Not JSON, render as markdown
                    container.innerHTML = marked.parse(data);
                    return;
                }
            } catch (e) {
                // Parsing failed, render as markdown
                container.innerHTML = marked.parse(data);
                return;
            }
        }

        let html = '<div class="career-plan-container">';
        const phases = [
            { key: 'day_30', title: '📅 30 Days: Learn & Connect' },
            { key: 'day_60', title: '🚀 60 Days: Contribute & Build' },
            { key: 'day_90', title: '⭐ 90 Days: Lead & Innovate' }
        ];

        phases.forEach(phase => {
            if (data[phase.key]) {
                html += `<div class="plan-phase card" style="margin-bottom:15px; padding:15px; border-left: 5px solid #4a90e2;">
                        <h3>${phase.title}</h3>
                        <ul style="padding-left:20px;">`;

                // Handle array or string content
                if (Array.isArray(data[phase.key])) {
                    data[phase.key].forEach(item => html += `<li>${item}</li>`);
                } else {
                    html += `<li>${data[phase.key]}</li>`;
                }

                html += `</ul></div>`;
            }
        });
        html += '</div>';
        container.innerHTML = html;
    }

    // Career Plan Print/Copy Logic
    if (document.getElementById('cp-print-btn')) {
        document.getElementById('cp-print-btn').addEventListener('click', () => {
            const content = document.getElementById('planner-result').innerHTML;
            if (!content || content.includes('Generating')) return alert('Please generate a plan first.');

            const printArea = document.getElementById('print-area');
            printArea.innerHTML = content;

            // Fix Title
            const originalTitle = document.title;
            const jobTitle = document.getElementById('job-title').value || 'New Role';
            document.title = `30 - 60 - 90 Day Plan - ${jobTitle} `;

            window.print();
            document.title = originalTitle;
        });

        document.getElementById('cp-copy-btn').addEventListener('click', async () => {
            const content = document.getElementById('planner-result').innerHTML;
            if (!content || content.includes('Generating')) return alert('Please generate a plan first.');

            try {
                const blob = new Blob([content], { type: 'text/html' });
                const data = [new ClipboardItem({ 'text/html': blob })];
                await navigator.clipboard.write(data);
                alert('Plan copied to clipboard!');
            } catch (err) {
                // Fallback
                const textArea = document.createElement("textarea");
                textArea.value = document.getElementById('planner-result').innerText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand("Copy");
                textArea.remove();
                alert('Copied as text.');
            }
        });
    }


    // Tab 4: LinkedIn Optimizer
    document.getElementById('optimize-linkedin-btn').addEventListener('click', async () => {
        const aboutMe = document.getElementById('linkedin-input').value;
        if (!aboutMe) return alert('Please paste your About Me section.');

        const resultsArea = document.getElementById('linkedin-results-area');
        const recsDiv = document.getElementById('linkedin-recommendations');
        const sampleDiv = document.getElementById('linkedin-refined-sample');

        resultsArea.style.display = 'block';
        recsDiv.innerHTML = 'Loading...';
        sampleDiv.innerHTML = 'Loading...';

        try {
            const response = await fetch('/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getSession()?.access_token}`
                },
                body: JSON.stringify({ action: 'strategy_linkedin', aboutMe })
            });
            const result = await response.json();

            if (result.data) {
                let data = result.data;
                if (typeof data === 'string') {
                    try { data = JSON.parse(data); } catch (e) {
                        recsDiv.innerHTML = "Could not parse recommendations.";
                        sampleDiv.innerHTML = marked.parse(data);
                        return;
                    }
                }
                if (data.recommendations) recsDiv.innerHTML = `< ul > ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}</ul > `;
                if (data.refined_sample) sampleDiv.innerHTML = marked.parse(data.refined_sample);
            }
        } catch (e) { console.error(e); alert("Error"); }
    });

    // Tab 5: Cover Letter (Simplified for restoration)
    document.getElementById('generate-cl-btn').addEventListener('click', async () => {
        const jobDesc = document.getElementById('cl-job-desc').value;
        const resume = document.getElementById('cl-resume').value;
        if (!jobDesc || !resume) return alert('Please fill in both fields.');

        const resultEl = document.getElementById('cl-result');
        resultEl.innerHTML = 'Generating...';
        resultEl.style.display = 'block';

        try {
            const response = await fetch('/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getSession()?.access_token}`
                },
                body: JSON.stringify({ action: 'cover_letter', jobDesc, resume })
            });
            const result = await response.json();
            if (result.data) resultEl.innerHTML = marked.parse(result.data);
        } catch (e) { resultEl.innerHTML = "Error"; }
    });

    // Tab 6: Resume Builder (Full Logic)

    // Helper: Render Experience Item
    function renderExperienceItem(data = {}) {
        const container = document.getElementById('rb-experience-list');
        const id = Date.now();
        const div = document.createElement('div');
        div.className = 'rb-item card';
        div.style.padding = '15px';
        div.style.marginBottom = '10px';
        div.innerHTML = `
            < div style = "display:flex; justify-content:space-between; margin-bottom:10px;" >
                    <strong>Experience</strong>
                    <button class="secondary-btn" onclick="this.parentElement.parentElement.remove()" style="padding:2px 8px; font-size:12px; color:red;">Delete</button>
                </div >
            <input type="text" class="rb-exp-role" placeholder="Role / Job Title" value="${data.role || ''}" style="margin-bottom:5px;">
                <input type="text" class="rb-exp-company" placeholder="Company" value="${data.company || ''}" style="margin-bottom:5px;">
                    <input type="text" class="rb-exp-dates" placeholder="Dates (e.g. 2020 - Present)" value="${data.dates || ''}" style="margin-bottom:5px;">
                        <textarea class="rb-exp-desc" placeholder="Description of responsibilities..." rows="3">${data.description || ''}</textarea>
                        `;
        container.appendChild(div);
    }

    // Helper: Render Education Item
    function renderEducationItem(data = {}) {
        const container = document.getElementById('rb-education-list');
        const div = document.createElement('div');
        div.className = 'rb-item card';
        div.style.padding = '15px';
        div.style.marginBottom = '10px';
        div.innerHTML = `
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                            <strong>Education</strong>
                            <button class="secondary-btn" onclick="this.parentElement.parentElement.remove()" style="padding:2px 8px; font-size:12px; color:red;">Delete</button>
                        </div>
                        <input type="text" class="rb-edu-degree" placeholder="Degree / Certificate" value="${data.degree || ''}" style="margin-bottom:5px;">
                            <input type="text" class="rb-edu-school" placeholder="School / University" value="${data.school || ''}" style="margin-bottom:5px;">
                                <input type="text" class="rb-edu-dates" placeholder="Dates (e.g. 2016 - 2020)" value="${data.dates || ''}">
                                    `;
        container.appendChild(div);
    }

    // Add Buttons
    document.getElementById('rb-add-exp-btn').addEventListener('click', () => renderExperienceItem());
    document.getElementById('rb-add-edu-btn').addEventListener('click', () => renderEducationItem());

    // Sample Data
    document.getElementById('rb-sample-btn').addEventListener('click', () => {
        document.getElementById('rb-name').value = "Jordan Taylor";
        document.getElementById('rb-email').value = "jordan.taylor@example.com";
        document.getElementById('rb-phone').value = "(555) 123-4567";
        document.getElementById('rb-linkedin').value = "linkedin.com/in/jordantaylor";
        document.getElementById('rb-location').value = "New York, NY";
        document.getElementById('rb-summary').value = "Results-oriented Product Manager with 5+ years of experience in SaaS specifically in the EdTech sector. Proven track record of leading cross-functional teams to deliver high-impact products.";
        document.getElementById('rb-skills').value = "Product Management, Agile, Jira, SQL, User Research, A/B Testing, Strategic Planning";
        document.getElementById('rb-job-desc').value = "We are looking for a Senior Product Manager to lead our Core Platform team. Experience in B2B SaaS and API-first products is required.";

        // Clear and Add Sample Items
        document.getElementById('rb-experience-list').innerHTML = '';
        document.getElementById('rb-education-list').innerHTML = '';

        renderExperienceItem({
            role: "Senior Product Manager",
            company: "TechFlow Solutions",
            dates: "2021 - Present",
            description: "Led the launch of the new analytics dashboard, increasing user engagement by 40%. Managed a team of 4 PMs."
        });
        renderExperienceItem({
            role: "Product Manager",
            company: "EduTech Inc.",
            dates: "2018 - 2021",
            description: "Spearheaded the mobile app redesign. Collaborated with engineering and design to improve onboarding flow."
        });

        renderEducationItem({
            degree: "MBA",
            school: "Stern School of Business",
            dates: "2016 - 2018"
        });
    });

    // IMPORT / PARSE RESUME LOGIC
    if (document.getElementById('rb-parse-btn')) {
        document.getElementById('rb-parse-btn').addEventListener('click', async () => {
            const text = document.getElementById('rb-paste-input').value;
            if (!text) return alert("Please paste your resume text first.");

            const btn = document.getElementById('rb-parse-btn');
            const originalText = btn.textContent;
            btn.textContent = "Analyzing & Extracting...";
            btn.disabled = true;

            try {
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getSession()?.access_token}`
                    },
                    body: JSON.stringify({ action: 'parse_resume', resume_text: text })
                });
                const result = await response.json();

                if (result.data) {
                    let data = result.data;
                    // Handle string response
                    if (typeof data === 'string') {
                        try {
                            // Clean markdown
                            let clean = data.trim();
                            if (clean.startsWith('```json')) clean = clean.slice(7);
                            if (clean.startsWith('```')) clean = clean.slice(3);
                            if (clean.endsWith('```')) clean = clean.slice(0, -3);
                            data = JSON.parse(clean);
                        } catch (e) {
                            console.error("Parse error", e);
                            alert("AI extraction failed to return valid data pattern. Please fill manually.");
                            return;
                        }
                    }

                    // Auto-Fill Fields
                    if (data.personal) {
                        document.getElementById('rb-name').value = data.personal.name || '';
                        document.getElementById('rb-email').value = data.personal.email || '';
                        document.getElementById('rb-phone').value = data.personal.phone || '';
                        document.getElementById('rb-linkedin').value = data.personal.linkedin || '';
                        document.getElementById('rb-location').value = data.personal.location || '';
                        document.getElementById('rb-summary').value = data.personal.summary || '';
                    }

                    if (data.skills && Array.isArray(data.skills)) {
                        document.getElementById('rb-skills').value = data.skills.join(', ');
                    }

                    // Experience
                    const expList = document.getElementById('rb-experience-list');
                    expList.innerHTML = '';
                    if (data.experience && Array.isArray(data.experience)) {
                        data.experience.forEach(exp => renderExperienceItem(exp));
                    }

                    // Education
                    const eduList = document.getElementById('rb-education-list');
                    eduList.innerHTML = '';
                    if (data.education && Array.isArray(data.education)) {
                        data.education.forEach(edu => renderEducationItem(edu));
                    }

                    alert("Resume imported successfully! Please review the fields below.");
                } else {
                    alert("Could not extract data. Please try again or fill manually.");
                }

            } catch (e) {
                console.error(e);
                alert("Error during import.");
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
    }


    // GENERATE BUTTON
    document.getElementById('rb-generate-btn').addEventListener('click', async () => {
        // CREDIT CHECK
        const session = getSession();
        if (!session || ((session.credits_resume || 0) + (session.credits || 0)) < 1) {
            if (confirm("You need 1 Rewrite Credit to generate. Unlock Executive Rewrite for $9.99?")) {
                // Trigger Checkout
                const btn = document.getElementById('unlock-rewrite-btn');
                if (btn) btn.click(); // Reuse existing button logic if possible, or call API directly
                else {
                    // Fallback if button hidden
                    try {
                        const token = localStorage.getItem('supabase.auth.token');
                        const res = await fetch('/api/create-checkout-session', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${token}`
                            },
                            body: JSON.stringify({
                                plan_type: 'strategy_rewrite',
                                successUrl: window.location.origin + '/app?status=success#resume-builder',
                                mode: 'payment'
                            })
                        });
                        const result = await res.json();
                        if (result.url) window.location.href = result.url;
                        else throw new Error(result.error);

                        if (error) throw error;
                        if (data?.url) window.location.href = data.url;
                    } catch (err) { alert("Checkout Error"); }
                }
            }
            return;
        }

        const btn = document.getElementById('rb-generate-btn');
        const originalText = btn.textContent;
        btn.textContent = "Optimizing & Generating...";
        btn.disabled = true;

        // Gather Data
        const userData = {
            personal: {
                name: document.getElementById('rb-name').value,
                email: document.getElementById('rb-email').value,
                phone: document.getElementById('rb-phone').value,
                linkedin: document.getElementById('rb-linkedin').value,
                location: document.getElementById('rb-location').value,
                summary: document.getElementById('rb-summary').value
            },
            experience: [],
            education: [],
            skills: document.getElementById('rb-skills').value.split(',').map(s => s.trim()).filter(s => s),
        };

        // Gather Experience
        document.querySelectorAll('#rb-experience-list .rb-item').forEach(item => {
            userData.experience.push({
                role: item.querySelector('.rb-exp-role').value,
                company: item.querySelector('.rb-exp-company').value,
                dates: item.querySelector('.rb-exp-dates').value,
                description: item.querySelector('.rb-exp-desc').value
            });
        });

        // Gather Education
        document.querySelectorAll('#rb-education-list .rb-item').forEach(item => {
            userData.education.push({
                degree: item.querySelector('.rb-edu-degree').value,
                school: item.querySelector('.rb-edu-school').value,
                dates: item.querySelector('.rb-edu-dates').value
            });
        });

        const jobDesc = document.getElementById('rb-job-desc').value;
        const template = document.querySelector('.template-btn.active') ? document.querySelector('.template-btn.active').getAttribute('data-template') : 'modern';

        try {
            // Call API
            const response = await fetch('/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getSession()?.access_token}`
                },
                body: JSON.stringify({
                    action: 'optimize',
                    user_data: userData,
                    job_description: jobDesc,
                    template_name: template
                })
            });
            const result = await response.json();

            if (result.error) {
                alert("Error: " + result.error);
            } else {
                // Render Result (Simple Preview for now)
                const preview = document.getElementById('resume-preview-container');
                let html = `<div class="resume-sheet ${template}">
                                        <h1>${result.personal?.name || userData.personal.name}</h1>
                                        <p class="contact-info">${userData.personal.email} | ${userData.personal.phone} | ${userData.personal.location}</p>
                                        <hr>
                                            <h3>Professional Summary</h3>
                                            <p>${result.personal?.summary || userData.personal.summary}</p> <!-- Use Optimized Summary -->

                                            <h3>Experience</h3>
                                            `;

                const exps = result.experience || userData.experience; // Use Optimized Exp if available
                exps.forEach(exp => {
                    html += `<div class="exp-item">
                            <div style="display:flex; justify-content:space-between;">
                                <strong>${exp.role}</strong>
                                <span>${exp.dates}</span>
                            </div>
                            <div style="font-style:italic;">${exp.company}</div>
                            <p>${exp.description}</p>
                        </div>`;
                });

                html += `<h3>Education</h3>`;
                userData.education.forEach(edu => {
                    html += `<div class="edu-item">
                            <div style="display:flex; justify-content:space-between;">
                                <strong>${edu.school}</strong>
                                <span>${edu.dates}</span>
                            </div>
                            <div>${edu.degree}</div>
                        </div>`;
                });

                html += `<h3>Skills</h3><p>${result.skills ? result.skills.join(', ') : userData.skills.join(', ')}</p>`;
                html += `</div>`;

                preview.innerHTML = html;
                preview.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (e) {
            console.error(e);
            alert("An error occurred during generation.");
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    });

    // Template Selection Logic
    document.querySelectorAll('.template-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.template-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // Print / Save PDF
    document.getElementById('rb-print-btn').addEventListener('click', () => {
        const content = document.getElementById('resume-preview-container').innerHTML;
        if (!content) return alert('Please generate a resume first.');

        const printArea = document.getElementById('print-area');
        printArea.innerHTML = content;

        // Fix Title for Print Header (Empty to clear top-left)
        const originalTitle = document.title;
        // Space is safer than empty string to ensure override
        document.title = " ";

        window.print();

        // Restore Title
        document.title = originalTitle;
        // Optional: Clear after print to avoid it showing up at bottom of page? 
        // Usually print-area is hidden in screen media.
    });

    // Copy for Google Docs
    document.getElementById('rb-gdocs-btn').addEventListener('click', async () => {
        const content = document.getElementById('resume-preview-container').innerHTML;
        if (!content) return alert('Please generate a resume first.');

        try {
            const blob = new Blob([content], { type: 'text/html' });
            const data = [new ClipboardItem({ 'text/html': blob })];
            await navigator.clipboard.write(data);
            alert('Resume copied! You can now paste it into Google Docs.');
        } catch (err) {
            console.error('Clipboard API failed', err);
            // Fallback
            const textArea = document.createElement("textarea");
            textArea.value = document.getElementById('resume-preview-container').innerText; // Text only fallback
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand("Copy");
            textArea.remove();
            alert('Copied as text (Formatting might be lost due to browser restrictions).');
        }
    });

}

// ---------------------------------------------------------
// STRATEGY SUITE TOOLS (Logic)
// ---------------------------------------------------------

// 1. The Inquisitor (Strategic Questions)
if (document.getElementById('generate-questions-btn')) {
    document.getElementById('generate-questions-btn').addEventListener('click', async () => {
        const jobDesc = document.getElementById('inq-job-desc').value;
        const level = document.getElementById('inq-interviewer-level').value;
        if (!jobDesc) return alert('Please enter a job description or title.');

        await callApi('strategic_questions', { jobDesc, interviewerLevel: level }, 'inq-result');
    });
}

// 2. The Closer (Negotiation Script)
if (document.getElementById('generate-negotiation-btn')) {
    document.getElementById('generate-negotiation-btn').addEventListener('click', async () => {
        const currentOffer = document.getElementById('neg-current-offer').value;
        const targetSalary = document.getElementById('neg-target-salary').value;
        const leverage = document.getElementById('neg-leverage').value;

        if (!currentOffer || !targetSalary) return alert('Please enter offer details.');

        const resultContainer = document.getElementById('neg-result-container');
        const emailEl = document.getElementById('neg-result-email');
        const phoneEl = document.getElementById('neg-result-phone');

        resultContainer.style.display = 'block';
        emailEl.innerHTML = '<em>Generating strategy...</em>';
        emailEl.style.display = 'block';
        phoneEl.style.display = 'none';

        try {
            const response = await fetch('/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'negotiation_script',
                    currentOffer,
                    targetSalary,
                    leverage
                })
            });
            const result = await response.json();

            if (result.error) {
                emailEl.innerHTML = `<strong style="color:red">Error: ${result.error}</strong>`;
            } else {
                // Store results globally for tab switching
                window.negEmailContent = result.email_draft.replace(/\n/g, '<br>');
                window.negPhoneContent = result.phone_script.replace(/\n/g, '<br>');

                emailEl.innerHTML = window.negEmailContent;
                phoneEl.innerHTML = window.negPhoneContent;

                // Reset Tabs
                showNegTab('email');
            }
        } catch (e) {
            emailEl.innerHTML = `<strong style="color:red">Connection Error: ${e.message}</strong>`;
        }
    });
}

// 3. Value-Add Follow Up
if (document.getElementById('generate-followup-btn')) {
    document.getElementById('generate-followup-btn').addEventListener('click', async () => {
        const name = document.getElementById('fu-name').value;
        const topic = document.getElementById('fu-topic').value;

        if (!name || !topic) return alert('Please fill in all fields.');

        await callApi('value_followup', { interviewerName: name, topic }, 'fu-result');
    });

}

// -------------------------------------------------------------
// CHECK PAYMENT SUCCESS (Dynamic based on Hash)
// -------------------------------------------------------------
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('status') === 'success') {
    const hash = window.location.hash;
    let featureName = "Resume Rewrite";
    let storageKey = "has_unlocked_rewrite";

    if (hash.includes('interview')) {
        featureName = "Interview Lab";
        storageKey = "has_unlocked_interview";
    } else if (hash.includes('linkedin')) {
        featureName = "LinkedIn Optimizer";
        storageKey = "has_unlocked_linkedin";
    }

    console.log(`Payment Successful! Unlocking ${featureName}...`);

    // 1. Show Success Message
    alert(`Payment Successful! ${featureName} Unlocked. 🚀`);

    // 2. Unlock Feature (Visual)
    localStorage.setItem(storageKey, 'true');

    // Refresh User Data (Credits) - Silent check
    checkAccess('credits_interview', false).then(() => {
        console.log("Credits refreshed.");
    });

    // 3. Clear Query Params but keep hash
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
}

// Unlock Check on Load (Persistent)
// Wrapped in DOMContentLoaded or body check to prevent null error
if (localStorage.getItem('has_unlocked_rewrite') === 'true') {
    if (document.body) {
        document.body.classList.add('rewrite-unlocked');
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            document.body.classList.add('rewrite-unlocked');
        });
    }
}

// -------------------------------------------------------------
// AUTO-ACTION: CHECK FOR KEY (Dashboard Import) - Moved to End
// -------------------------------------------------------------
const pendingText = localStorage.getItem('pending_resume_text');
if (pendingText) {
    // Debug Alert to verify we found it
    // alert("DEBUG: Found resume text! Length: " + pendingText.length);
    console.log("Found pending resume text. Auto-filling...");

    const resumeInput = document.getElementById('resume-input');
    if (resumeInput) {
        // Ensure tab is active
        const resumeSection = document.getElementById('resume');
        if (resumeSection && !resumeSection.classList.contains('active')) {
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            resumeSection.classList.add('active');
        }

        resumeInput.value = pendingText;

        // Trigger click automatically
        setTimeout(() => {
            const btn = document.getElementById('analyze-resume-btn');
            if (btn) {
                console.log("Auto-clicking analyze button...");
                btn.click();
            } else {
                console.error("Analyze button not found for auto-click");
                alert("Debug Error: Analyze button not found.");
            }

            // Clear storage AFTER click to be safe
            localStorage.removeItem('pending_resume_text');
            localStorage.removeItem('pending_resume_filename');

        }, 800); // Increased to 800ms
    } else {
        alert("Debug Error: Resume Input field not found!");
    }
}

// End of init() function - Global Helper for Negotiation Tabs
window.showNegTab = function (type) {
    const emailEl = document.getElementById('neg-result-email');
    const phoneEl = document.getElementById('neg-result-phone');
    const btns = document.querySelectorAll('.tabs-nav .secondary-btn');

    if (type === 'email') {
        emailEl.style.display = 'block';
        phoneEl.style.display = 'none';
        btns[0].classList.add('active');
        btns[1].classList.remove('active');
    } else {
        emailEl.style.display = 'none';
        phoneEl.style.display = 'block';
        btns[0].classList.remove('active');
        btns[1].classList.add('active');
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

window.init = init;

// --- AUTO-LOAD CONTEXT FROM DASHBOARD ---
document.addEventListener('DOMContentLoaded', () => {
    // Ghost Data Fix: Clear if not explicit War Room launch
    const isWarRoomLaunch = sessionStorage.getItem('warRoomLaunch');
    if (!isWarRoomLaunch) {
        console.log("Fresh Session: Clearing previous job data.");
        if (document.getElementById('interview-job-posting')) document.getElementById('interview-job-posting').value = "";
        if (document.getElementById('job-description-input')) document.getElementById('job-description-input').value = "";
        localStorage.removeItem('strategy_context');
    } else {
        sessionStorage.removeItem('warRoomLaunch');
    }
    // --- DEEP LINK HANDLER (URL Params) ---
    const urlParams = new URLSearchParams(window.location.search);
    const deepLinkId = urlParams.get('id');

    if (deepLinkId) {
        console.log("Deep Link Detected: Job " + deepLinkId);
        addMessage("Loading Mission Context...", 'system');

        // Fetch Job to get fresh data
        fetch('/api/jobs', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('supabase.auth.token')}` }
        }).then(res => res.json()).then(jobs => {
            const job = jobs.find(j => j.id === deepLinkId);
            if (job) {
                // Populate Inputs
                const inputs = ['interview-job-posting', 'job-description-input'];
                inputs.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.value = job.job_description || '';
                });

                // Set Context
                const context = {
                    job_id: job.id,
                    role: job.job_title,
                    company: job.company_name,
                    description: job.job_description,
                    notes: job.notes
                };
                localStorage.setItem('mission_context', JSON.stringify(context));

                addMessage(`**Mission Loaded:** ${job.job_title} at ${job.company_name}`, 'system');

                // Auto-Start if we have a JD
                if (job.job_description && job.job_description.length > 50) {
                    const startBtn = document.getElementById('start-interview-btn');
                    // DO NOT CLICK AUTOMATICALLY - Browser blocks audio
                    // startBtn.click(); 
                    if (startBtn) {
                        startBtn.innerHTML = '<i class="fas fa-play"></i> INITIALIZE MISSION';
                        startBtn.classList.remove('bg-blue-600');
                        startBtn.classList.add('bg-purple-600', 'animate-pulse');
                        addMessage("**Mission Ready.** Click 'Initialize Mission' to begin.", 'system');
                    }
                }
            }
        }).catch(e => console.error("Deep Link Fetch Error", e));
    }

    try {
        const activeJD = localStorage.getItem('activeJobDescription');
        if (activeJD) {
            console.log("Found Active JD from Dashboard. Injecting...");
            // Try both potential IDs just in case
            const inputs = ['interview-job-posting', 'job-description-input'];
            let found = false;
            inputs.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.value = activeJD;
                    found = true;
                    // Trigger input event for auto-resizers or validation
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });

            if (found) {
                // Auto-expand the context section if hidden
                const contextContainer = document.getElementById('context-container');
                if (contextContainer && contextContainer.classList.contains('hidden')) {
                    // Optional: window.toggleContext() if available or manual class removal
                    // For now, we just populate the data.
                }
            }
        }
    } catch (e) {
        console.error("Error auto-loading JD:", e);
    }
});

// --- UPGRADE HUB RENDERER ---
window.renderUpgradeHub = function (containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <!-- FEATURED: Monthly Unlimited -->
        <div class="bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-teal/30 hover:border-teal/60 transition-all relative overflow-hidden mb-6">
            <div class="absolute top-0 right-0 bg-teal text-slate-900 text-[10px] font-bold px-3 py-1 rounded-bl-lg">BEST VALUE</div>
            <h3 class="text-xl font-bold text-white mb-2">Monthly Unlimited</h3>
            <p class="text-xs text-slate-400 mb-4">Unlimited Text Tools + 50 Voice Sessions/mo</p>
            <div class="text-3xl font-bold text-white mb-4">$49.99 <span class="text-xs font-normal text-slate-500">/mo</span></div>
            <button onclick="initiateCheckout('monthly_unlimited')" class="w-full bg-teal hover:bg-teal/90 text-slate-900 font-bold py-3 rounded-lg transition-all shadow-[0_0_15px_rgba(20,184,166,0.3)]">
                Go Unlimited
            </button>
        </div>

        <!-- Strategy Bundle -->
        <div class="bg-slate-800 p-5 rounded-xl border border-slate-700 hover:border-purple-500/50 transition-all mb-4">
            <h3 class="text-lg font-bold text-white mb-1">Strategy Bundle</h3>
            <p class="text-xs text-slate-400 mb-3">5 Universal Credits (Save ~$15)</p>
            <div class="flex justify-between items-center">
                <div class="text-2xl font-bold text-white">$29.99</div>
                <button onclick="initiateCheckout('strategy_bundle')" class="bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 px-4 rounded-lg transition-all">
                    Purchase
                </button>
            </div>
        </div>

        <h4 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 mt-6">A La Carte Tools</h4>
        
        <div class="grid grid-cols-1 gap-3">
            <!-- Executive Rewrite -->
            <div class="bg-slate-800/50 p-4 rounded-lg border border-slate-700 flex justify-between items-center hover:border-yellow-500/30 transition-all">
                <div>
                    <h3 class="text-sm font-bold text-white">Executive Rewrite</h3>
                    <p class="text-[10px] text-slate-400">$12.99 / use</p>
                </div>
                <button onclick="initiateCheckout('strategy_rewrite')" class="text-xs bg-slate-700 hover:bg-yellow-500 hover:text-slate-900 border border-slate-600 text-white px-3 py-2 rounded font-bold transition-all">Buy</button>
            </div>

            <!-- Interview Simulator -->
            <div class="bg-slate-800/50 p-4 rounded-lg border border-slate-700 flex justify-between items-center hover:border-green-500/30 transition-all">
                <div>
                    <h3 class="text-sm font-bold text-white">Interview Simulator</h3>
                    <p class="text-[10px] text-slate-400">$9.99 / session</p>
                </div>
                <button onclick="initiateCheckout('strategy_interview_sim')" class="text-xs bg-slate-700 hover:bg-green-500 hover:text-white border border-slate-600 text-white px-3 py-2 rounded font-bold transition-all">Buy</button>
            </div>

            <!-- 30-60-90 Plan -->
            <div class="bg-slate-800/50 p-4 rounded-lg border border-slate-700 flex justify-between items-center hover:border-cyan-500/30 transition-all">
                <div>
                    <h3 class="text-sm font-bold text-white">30-60-90 Day Plan</h3>
                    <p class="text-[10px] text-slate-400">$8.99 / plan</p>
                </div>
                <button onclick="initiateCheckout('strategy_plan')" class="text-xs bg-slate-700 hover:bg-cyan-500 hover:text-white border border-slate-600 text-white px-3 py-2 rounded font-bold transition-all">Buy</button>
            </div>

            <!-- The Closer -->
            <div class="bg-slate-800/50 p-4 rounded-lg border border-slate-700 flex justify-between items-center hover:border-teal-500/30 transition-all">
                <div>
                    <h3 class="text-sm font-bold text-white">The Closer</h3>
                    <p class="text-[10px] text-slate-400">$6.99 / use</p>
                </div>
                <button onclick="initiateCheckout('strategy_closer')" class="text-xs bg-slate-700 hover:bg-teal-500 hover:text-white border border-slate-600 text-white px-3 py-2 rounded font-bold transition-all">Buy</button>
            </div>
            
            <!-- Value Follow Up -->
            <div class="bg-slate-800/50 p-4 rounded-lg border border-slate-700 flex justify-between items-center hover:border-rose-500/30 transition-all">
                <div>
                    <h3 class="text-sm font-bold text-white">Value Follow-Up</h3>
                    <p class="text-[10px] text-slate-400">$6.99 / use</p>
                </div>
                <button onclick="initiateCheckout('strategy_followup')" class="text-xs bg-slate-700 hover:bg-rose-500 hover:text-white border border-slate-600 text-white px-3 py-2 rounded font-bold transition-all">Buy</button>
            </div>
        </div>
    `;
};

// --- INITIALIZATION ---
// Automatically fetch profile and update tool belt on load
document.addEventListener('DOMContentLoaded', () => {
    // Only run if we are on a page that uses app.js logic (has supabase)
    if (window.supabase) {
        checkAccess('credits_interview', false).catch(e => console.log("Init Check Failed:", e));
    }
});
