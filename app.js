// Helper functions (Global Scope)
function getVoiceSettings() {
    const voice = document.getElementById('voice-select').value;
    const speed = '+0%'; // Default speed
    return { voice, speed };
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

async function checkAccess() {
    console.log("Checking access...");
    console.log("Checking access...");
    let session = getSession();

    // RECOVERY LOGIC (Matches Dashboard)
    if (!session) {
        const token = localStorage.getItem('supabase.auth.token');
        if (token) {
            console.log("Session missing but Token found. Attempting recovery...");
            try {
                const parts = token.split('.');
                if (parts.length === 3) {
                    const base64Url = parts[1];
                    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                    const payloadStr = atob(base64);
                    const payload = JSON.parse(payloadStr);

                    if (payload.email) {
                        session = {
                            email: payload.email,
                            name: payload.user_metadata?.name || 'User',
                            logged_in_at: Date.now(),
                            account_status: 'active', // Default to active to allow entry, verify later
                            resume_credits: 3,
                            interview_credits: 3,
                            rewrite_credits: 3 // Default for recovered session
                        };
                        localStorage.setItem(SESSION_KEY, JSON.stringify(session));
                        console.log("Session Recovered in App!");
                    }
                }
            } catch (e) {
                console.error("Recovery Error: " + e.message);
            }
        }
    }

    if (!session) {
        // Allow public pages? No, force login for app
        // But maybe we are on /app.html which should be protected
        // If we are on index.html or pricing.html, no need to redirect.
        const path = window.location.pathname;
        if (path === '/app.html' || path === '/app' || path.includes('admin')) {
            // Updated: Don't clear session aggresively, just redirect.
            // localStorage.removeItem(SESSION_KEY);
            // localStorage.removeItem('supabase.auth.token');
            console.warn("Access denied. Redirecting to login.");
            window.location.href = '/login.html';
        }
        return;
    }

    // Verify status with server (optional optimization: trust local storage first to avoid delay, then verify async)
    // But requirement says: "ALLOW IF: subscription_status === 'active' OR credits > 0."
    // We should fetch fresh status to be accurate.
    try {
        const response = await fetch('/api/auth/user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: session.email })
        });
        const result = await response.json();

        if (result.success && result.user) {
            // New Schema: subscription_status, is_unlimited
            const status = result.user.subscription_status;
            const unlimited = result.user.is_unlimited;

            // Only update local session
            session.subscription_status = status;
            session.is_unlimited = unlimited;
            session.resume_credits = result.user.resume_credits;
            session.interview_credits = result.user.interview_credits;
            session.rewrite_credits = result.user.rewrite_credits; // Store new credit type

            localStorage.setItem(SESSION_KEY, JSON.stringify(session));
            updateCreditDisplay(session); // Update UI immediately

            // ADMIN CHECK: Reveal Hidden Tools
            if (result.user.role === 'admin') {
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

            // Phase 20: Split Credits
            let resume_credits = result.user.resume_credits;
            let interview_credits = result.user.interview_credits;
            let rewrite_credits = result.user.rewrite_credits;
            let sim_credits = result.user.credits_interview_sim || 0; // New

            // Safe Parse
            if (resume_credits === null || resume_credits === undefined) resume_credits = 0;
            if (interview_credits === null || interview_credits === undefined) interview_credits = 0;
            if (rewrite_credits === null || rewrite_credits === undefined) rewrite_credits = 0;

            session.resume_credits = resume_credits;
            session.interview_credits = interview_credits;
            session.rewrite_credits = rewrite_credits;
            session.sim_credits = sim_credits;

            localStorage.setItem(SESSION_KEY, JSON.stringify(session));
            updateCreditDisplay(session); // UI Update
            verifyInterviewAccess(session); // Check Interview Tab Access

            console.log(`Session refreshed. Sim Credits=${sim_credits}`);

        }
    } catch (e) {
        console.log("Error checking access", e);
    }
}


function updateCreditDisplay(session) {
    if (!session) return;
    const countEl = document.getElementById('rb-credit-count');
    const displayEl = document.getElementById('rb-credit-display');
    const generateBtn = document.getElementById('rb-generate-btn');

    if (countEl && session.rewrite_credits !== undefined) {
        countEl.textContent = session.rewrite_credits;
        if (displayEl) displayEl.style.display = 'flex';

        // Gate "Generate" Button
        if (generateBtn) {
            if (session.rewrite_credits > 0) {
                generateBtn.innerHTML = `Generate Rewrite <small>(1 Credit)</small>`;
                generateBtn.disabled = false;
            } else {
                generateBtn.innerHTML = `Generate Rewrite <small>(1 Credit Needed)</small>`;
            }
        }
    }
}

// Global state variables for interview tracking
let questionCount = 0;
let interviewHistory = [];
let currentQuestionText = "";

async function sendVoiceMessage(base64Audio) {
    // Ensure addMessage is available (it's exposed from init)
    if (!window.addMessage) {
        console.error("addMessage not found");
        return;
    }

    const loadingId = window.addMessage('Processing audio...', 'system');
    const jobPosting = document.getElementById('interview-job-posting').value;
    const { voice, speed } = getVoiceSettings();

    questionCount++;

    try {
        const session = getSession();
        const email = session ? session.email : null;

        const response = await fetch('/api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'interview_chat',
                audio: base64Audio,
                jobPosting: jobPosting,
                voice: voice,
                speed: speed,
                email: email,
                questionCount: questionCount,
                ghostMode: localStorage.getItem('admin_ghost_mode') === 'true'
            })
        });
        const result = await response.json();
        document.getElementById(loadingId).remove();

        if (result.data && typeof result.data === 'object') {
            // Handle structured voice response
            window.addMessage(`(Transcript): ${result.data.transcript}`, 'user');

            let systemMsg = '';
            if (result.data.score !== undefined && result.data.score !== null) {
                systemMsg += `<div style="background-color: #fff3cd; color: #856404; padding: 5px 10px; border-radius: 4px; display: inline-block; margin-bottom: 10px; font-weight: bold;">
                    Score: ${result.data.score}/5
                </div><br>`;
            }
            systemMsg += `<strong>Feedback:</strong> ${result.data.feedback}`;
            if (result.data.improved_sample) {
                systemMsg += `<div class="improved-answer-box" style="background-color: #e8f5e9; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; border-radius: 4px;">
                    <strong>✨ Better Answer:</strong><br>
                    ${result.data.improved_sample}
                </div>`;
            }
            systemMsg += `<br><br><strong>Next Question:</strong> ${result.data.next_question}`;

            window.addMessage(systemMsg, 'system', true);

            // Play Audio
            if (result.data.audio) {
                const audioPlayer = document.getElementById('ai-audio-player');
                audioPlayer.src = `data:audio/mp3;base64,${result.data.audio}`;
                audioPlayer.style.display = 'block';
                audioPlayer.play().catch(e => {
                    console.error("Audio playback error:", e);
                    alert("Audio playback failed. Please interact with the page (click anywhere) and try again. Browser autoplay policies might be blocking it.");
                });
            }
        } else if (result.data) {
            // Fallback for text-only
            window.addMessage(result.data, 'system');
        } else {
            window.addMessage('Error: ' + (result.error || 'Unknown error'), 'system');
        }
    } catch (e) {
        document.getElementById(loadingId).remove();
        window.addMessage('Error: ' + e.message, 'system');
    }
}

function init() {
    console.log("AI Career Coach App v9.1 Loaded");
    const versionDisplay = document.createElement('div');
    versionDisplay.style.position = 'fixed';
    versionDisplay.style.bottom = '10px';
    versionDisplay.style.right = '10px';
    versionDisplay.style.fontSize = '12px';
    versionDisplay.style.color = '#888';
    versionDisplay.textContent = 'v9.0';
    document.body.appendChild(versionDisplay);

    // Run Access Check
    checkAccess();

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
        document.title = "Interview Coach - AI Career Coach";
    } else if (adminHashes.includes(hash)) {
        // Do not activate Resume section. Wait for Admin Check to reveal specific tool.
        // We can set title here though
        document.title = "Admin Tool - AI Career Coach";

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
        document.title = "Resume Analysis - AI Career Coach";
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

    // New Function: Verify Interview Access
    function verifyInterviewAccess(session) {
        if (!session) return;

        const lockedState = document.getElementById('interview-locked-state');
        const activeState = document.getElementById('interview-active-state');
        const startBtn = document.getElementById('start-interview-btn');
        const chatInterface = document.getElementById('chat-interface');

        // Safety check if elements exist (might not be on app page)
        if (!lockedState || !activeState) return;

        const credits = session.sim_credits || 0;
        const isUnlimited = session.is_unlimited || false;

        if (credits > 0 || isUnlimited) {
            // UNLOCKED
            lockedState.style.display = 'none';
            activeState.style.display = 'block';
            chatInterface.style.display = 'none'; // Hide chat until started

            if (startBtn) {
                startBtn.innerHTML = `Start Interview (${isUnlimited ? 'Unlimited' : '1 Credit'})`;
                startBtn.disabled = false;
            }
        } else {
            // LOCKED
            lockedState.style.display = 'block';
            activeState.style.display = 'none';
            chatInterface.style.display = 'none';
        }
    }

    // Bind Unlock Button for Interview Logic
    const unlockInterviewBtn = document.getElementById('btn-unlock-interview');
    if (unlockInterviewBtn) {
        unlockInterviewBtn.addEventListener('click', async () => {
            const session = getSession();
            if (!session) return window.location.href = '/login.html';

            initiateCheckout('strategy_interview_sim', session.email);
        });
    }

    // Helper to reuse checkout logic
    async function initiateCheckout(planType, email) {
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = 'Processing...';

        try {
            const res = await fetch('/api/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('supabase.auth.token')}`
                },
                body: JSON.stringify({
                    plan_type: planType,
                    email: email,
                    successUrl: window.location.origin + '/app.html?status=success#interview', // redirect back to interview tab
                    cancelUrl: window.location.href
                })
            });
            const json = await res.json();
            if (json.error) throw new Error(json.error);

            window.location.href = json.url;

        } catch (e) {
            alert("Checkout Error: " + e.message);
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
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
                            const session = getSession();
                            const response = await fetch('/api/create-checkout-session', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    email: session ? session.email : null,
                                    feature: 'rewrite', // Use backend env var
                                    successUrl: window.location.origin + '/app.html?status=success#resume-builder',
                                    cancelUrl: window.location.href
                                })
                            });
                            const result = await response.json();
                            if (result.url) {
                                window.location.href = result.url;
                            } else {
                                alert("Checkout Error: " + (result.error || "Unknown"));
                            }
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
    document.getElementById('resume-print-btn').addEventListener('click', () => {
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
        } else {
            alert('Pop-up blocked. Please allow pop-ups for this site to use the print feature.');
        }
    });

    // Resume Analysis Copy Button
    document.getElementById('resume-copy-btn').addEventListener('click', async () => {
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

    // Tab 2: Interview Coach
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');

    document.getElementById('send-chat-btn').addEventListener('click', () => {
        primeAudio();
        sendChatMessage();
    });
    document.getElementById('start-interview-btn').addEventListener('click', () => {
        const jobPosting = document.getElementById('interview-job-posting').value;
        const chatInterface = document.getElementById('chat-interface');
        const activeState = document.getElementById('interview-active-state');

        if (jobPosting.trim()) {
            primeAudio();
            primeAudio();
            questionCount = 0; // Reset counter to 0 for welcome message
            interviewHistory = []; // Reset history

            // Show Chat Interface, Hide Setup Form (Standard flow)
            // Or keep setup form visible? Better UX to switch view.
            if (activeState) activeState.style.display = 'none';
            if (chatInterface) chatInterface.style.display = 'block';

            sendChatMessage("I have provided the job description. Please start the interview.", true);
        } else {
            alert("Please paste a job description first.");
        }
    });



    function primeAudio() {
        const audioPlayer = document.getElementById('ai-audio-player');
        // Attempt to play and immediately pause to unlock audio context
        audioPlayer.play().catch(() => { });
        audioPlayer.pause();
    }
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    // Voice Logic - Global Scope
    let mediaRecorder;
    let audioChunks = [];

    window.toggleRecording = async function () {
        const recordBtn = document.getElementById('record-btn');
        console.log("toggleRecording called");

        if (mediaRecorder && mediaRecorder.state === 'recording') {
            console.log("Stopping recording...");
            mediaRecorder.stop();
            recordBtn.textContent = '🎤';
            recordBtn.style.background = '#dc3545'; // Red (default)
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
                recordBtn.textContent = '⏹️';
                recordBtn.style.background = '#28a745'; // Green (recording)
            } catch (err) {
                console.error("Error accessing microphone:", err);
                alert("Could not access microphone. Please allow permissions. Error: " + err.message);
            }
        }
    };

    // sendVoiceMessage moved to global scope


    async function sendChatMessage(msg = null, isStart = false) {
        const message = msg || chatInput.value;
        if (!message) return;

        // Add user message
        addMessage(message, 'user');
        chatInput.value = '';

        // Call API
        // Note: In a real app, we'd send chat history. For prototype, we just send the last message.
        // To make it better, we could grab the last few messages from the DOM.

        // Simple loading indicator
        const loadingId = addMessage('Thinking...', 'system');
        const jobPosting = document.getElementById('interview-job-posting').value;
        const { voice, speed } = getVoiceSettings();


        try {
            // Get Email from Session for Credit Deduction
            let email = null;
            try {
                const sessionItem = localStorage.getItem(SESSION_KEY);
                if (sessionItem) {
                    const sessionObj = JSON.parse(sessionItem);
                    email = sessionObj.email || sessionObj.user?.email;
                }
            } catch (e) { console.error("Error fetching email from session", e); }

            const response = await fetch('/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'interview_chat',
                    message: message,
                    jobPosting: jobPosting,
                    voice: voice,
                    speed: speed,
                    isStart: isStart,
                    questionCount: questionCount + 1,
                    email: email,
                    ghostMode: localStorage.getItem('admin_ghost_mode') === 'true'
                })
            });
            const result = await response.json();

            // Remove loading
            document.getElementById(loadingId).remove();

            if (result.data) {
                // Check if it's a JSON string (sometimes happens if mixed mode) or just text
                if (typeof result.data === 'object') {
                    // Standardized UI rendering (same as sendVoiceMessage)
                    let systemMsg = '';
                    if (result.data.score !== undefined && result.data.score !== null) {
                        systemMsg += `< div style = "background-color: #fff3cd; color: #856404; padding: 5px 10px; border-radius: 4px; display: inline-block; margin-bottom: 10px; font-weight: bold;" >
            Score: ${result.data.score}/5
                        </div > <br>`;
                    }
                    if (result.data.feedback) {
                        systemMsg += `<strong>Feedback:</strong> ${result.data.feedback}`;
                    }

                    if (result.data.improved_sample) {
                        systemMsg += `<div class="improved-answer-box" style="background-color: #e8f5e9; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; border-radius: 4px;">
                            <strong>✨ Better Answer:</strong><br>
                            ${result.data.improved_sample}
                        </div>`;
                    }

                    // Store History only when we receive actual feedback with a score
                    // (not for confirmations like "yes I'm ready")
                    if (result.data.score !== undefined && result.data.score !== null && result.data.feedback) {
                        console.log('Storing answer with score:', result.data.score);
                        interviewHistory.push({
                            question: currentQuestionText,
                            answer: message,
                            score: result.data.score,
                            feedback: result.data.feedback
                        });
                        console.log('Interview history now has', interviewHistory.length, 'items');
                    }

                    // Update current question text for next turn
                    currentQuestionText = result.data.next_question || result.data.text || '';

                    if (!isStart) {
                        questionCount++;
                    }

                    if (isStart) {
                        systemMsg += `<br><br>${result.data.next_question || result.data.text || ''}`;
                    } else if (questionCount >= 5) {
                        systemMsg += `<br><br><strong>Conclusion:</strong> ${result.data.next_question || result.data.text || ''}`;
                        // Trigger Report Generation
                        setTimeout(generateInterviewReport, 2000);
                    } else {
                        systemMsg += `<br><br>${result.data.next_question || result.data.text || ''}`;
                    }

                    // If we only got text back (fallback), just show it
                    if (!result.data.feedback && !result.data.next_question) {
                        systemMsg = result.data.text || JSON.stringify(result.data);
                    }

                    addMessage(systemMsg, 'system', true);

                    // Play Audio if present
                    if (result.data.audio) {
                        console.log("Audio data received, attempting to play...");
                        const audioPlayer = document.getElementById('ai-audio-player');
                        audioPlayer.src = `data:audio/mp3;base64,${result.data.audio}`;
                        audioPlayer.style.display = 'block';
                        audioPlayer.play().catch(e => {
                            console.error("Audio playback error:", e);
                            alert("Audio playback failed. Please interact with the page (click anywhere) and try again. Browser autoplay policies might be blocking it.");
                        });
                    } else {
                        console.warn("No audio data in response");
                    }
                } else {
                    addMessage(result.data, 'system');
                }
            } else {
                addMessage('Error: ' + (result.error || 'Unknown error'), 'system');
            }
        } catch (e) {
            document.getElementById(loadingId).remove();
            addMessage('Error: ' + e.message, 'system');
        }
    }

    async function generateInterviewReport() {
        const loadingId = addMessage('Generating Final Interview Report...', 'system');

        try {
            const session = getSession();
            const email = session ? session.email : null;

            const response = await fetch('/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'generate_report', email: email, history: interviewHistory })
            });
            document.getElementById(loadingId).remove();

            // Disable input to prevent further messages
            document.getElementById('chat-input').disabled = true;
            document.getElementById('chat-input').placeholder = "Interview Complete";
            document.getElementById('send-btn').disabled = true;
            document.getElementById('record-btn').disabled = true;

            // Calculate overall score
            let totalScore = 0;
            let scoreCount = 0;
            interviewHistory.forEach(item => {
                if (item.score !== undefined && item.score !== null) {
                    totalScore += item.score;
                    scoreCount++;
                }
            });
            const avgScore = scoreCount > 0 ? (totalScore / scoreCount).toFixed(1) : 'N/A';

            // Determine conditional message based on score
            let motivationMessage = '';
            if (avgScore >= 4.5) {
                motivationMessage = 'Great score! One more session will make you interview-ready.';
            } else if (avgScore < 3.0) {
                motivationMessage = 'Practice makes perfect. Most users improve significantly with each session.';
            } else {
                motivationMessage = 'Most users need 2-3 practice sessions to consistently score 4+ and feel confident for their real interview.';
            }

            // Build question breakdown HTML
            let questionBreakdown = '';
            interviewHistory.forEach((item, idx) => {
                const score = item.score !== undefined ? item.score : 'N/A';
                // Get first sentence of feedback
                const briefFeedback = item.feedback ? item.feedback.split('.')[0] + '.' : 'Feedback not available.';
                questionBreakdown += `<div class="result-question-item">✓ Question ${idx + 1}: <strong>${score}/5</strong> - ${briefFeedback}</div>`;
            });

            console.log('Building results with', interviewHistory.length, 'scored answers');
            console.log('Average score calculated:', avgScore);

            // Only include strengths/improvements sections if we have meaningful data
            // For now, we'll skip these sections since we don't have reliable data
            let strengthsSection = '';
            let improvementsSection = '';

            // If AI report contains structured data, we could parse it here
            // For now, these sections are hidden to avoid showing placeholder content

            // Build the full results + upsell HTML
            const resultsHtml = `
            <div class="interview-results-container">
                <div class="results-section">
                    <div class="results-header">
                        <span class="results-icon">🎯</span>
                        <h3>INTERVIEW COMPLETE - YOUR RESULTS</h3>
                    </div>

                    <div class="overall-score">
                        <span class="score-label">Overall Score:</span>
                        <span class="score-value">${avgScore}/5</span>
                    </div>

                    <div class="question-breakdown">
                        <h4>Question Breakdown:</h4>
                        ${questionBreakdown || '<p>No question data available.</p>'}
                    </div>
                    ${strengthsSection}
                    ${improvementsSection}
                </div>

                <div class="upsell-section">
                    <div class="upsell-header">
                        <span class="upsell-icon">💡</span>
                        <h3>READY TO IMPROVE YOUR SCORE?</h3>
                    </div>

                    <p class="upsell-motivation">${motivationMessage}</p>

                    <div class="score-comparison">
                        <span>Your current score: <strong>${avgScore}/5</strong></span>
                        <span>Target score: <strong>4.5+/5</strong></span>
                    </div>

                    <p class="upsell-cta-text">Keep practicing to master your interview answers.</p>

                    <div class="upsell-cards">
                        <div class="upsell-card">
                            <div class="card-icon">🔁</div>
                            <h4>PRACTICE 5 MORE QUESTIONS</h4>
                            <div class="price">$9.99 - Additional Session</div>
                            <ul class="features">
                                <li>5 new interview questions</li>
                                <li>Same voice-based scoring</li>
                                <li>STAR format feedback</li>
                                <li>Track your improvement</li>
                            </ul>
                            <button class="upsell-btn" onclick="showPaymentAlert()">Practice Again - $9.99</button>
                        </div>

                        <div class="upsell-card featured">
                            <div class="best-value-badge">BEST VALUE</div>
                            <div class="card-icon">♾️</div>
                            <h4>UNLIMITED PRACTICE</h4>
                            <div class="price">$49/month</div>
                            <ul class="features">
                                <li>Unlimited interview sessions</li>
                                <li>Practice until you're ready</li>
                                <li>Track improvement over time</li>
                                <li>All question types included</li>
                                <li>Cancel anytime</li>
                            </ul>
                            <button class="upsell-btn featured" onclick="showPaymentAlert()">Get Unlimited Access - $49/mo</button>
                        </div>
                    </div>

                    <a href="/app" class="return-link">← Return to Dashboard</a>
                </div>
            </div>
            `;

            addMessage(resultsHtml, 'system', true);

        } catch (e) {
            document.getElementById(loadingId).remove();
            addMessage("Error generating report: " + e.message, 'system');
        }
    }

    // Payment alert function for upsell buttons
    window.showPaymentAlert = function () {
        // Redirect to pricing page
        window.location.href = '/pricing.html';
    };

    function addMessage(text, sender, isHtml = false) {
        const div = document.createElement('div');
        div.classList.add('message', sender);
        div.id = 'msg-' + Date.now();
        if (isHtml) {
            div.innerHTML = text;
        } else {
            div.textContent = text;
        }
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return div.id;
    }
    // Expose addMessage to global scope for sendVoiceMessage
    window.addMessage = addMessage;
} // End of Interview Page (Resume Analysis + Interview Coach)


// ADMIN TOOLS LOGIC (Restored)
// Only init listeners if elements exist (which they do now in app.html)
if (document.getElementById('generate-plan-btn')) {
    console.log("Initializing Admin Tools...");

    // Tab 3: Career Planner
    document.getElementById('generate-plan-btn').addEventListener('click', async () => {
        const jobTitle = document.getElementById('job-title').value;
        const company = document.getElementById('company').value;
        const jobPosting = document.getElementById('job-posting').value;
        if (jobTitle && company) {
            const outputDiv = document.getElementById('planner-result');
            outputDiv.innerHTML = '<div class="loading-spinner">Generating plan...</div>';

            try {
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
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
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'linkedin_optimize', aboutMe })
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
                headers: { 'Content-Type': 'application/json' },
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
                    headers: { 'Content-Type': 'application/json' },
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
        if (!session || (session.rewrite_credits || 0) < 1) {
            if (confirm("You need 1 Rewrite Credit to generate. Unlock Executive Rewrite for $9.99?")) {
                // Trigger Checkout
                const btn = document.getElementById('unlock-rewrite-btn');
                if (btn) btn.click(); // Reuse existing button logic if possible, or call API directly
                else {
                    // Fallback if button hidden
                    try {
                        const response = await fetch('/api/create-checkout-session', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                email: session ? session.email : null,
                                feature: 'rewrite',
                                successUrl: window.location.origin + '/app.html?status=success#resume-builder',
                                cancelUrl: window.location.href
                            })
                        });
                        const res = await response.json();
                        if (res.url) window.location.href = res.url;
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
                headers: { 'Content-Type': 'application/json' },
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
// CHECK PAYMENT SUCCESS (Resume Rewrite)
// -------------------------------------------------------------
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('status') === 'success') {
    console.log("Payment Successful! Unlocking Rewrite...");
    // 1. Show Success Message
    alert("Payment Successful! Resume Rewrite Unlocked. 🚀");

    // 2. Unlock Feature (Visual)
    // We can set a global flag or localStorage to persist this state
    localStorage.setItem('has_unlocked_rewrite', 'true');

    // Refresh User Data (Credits)
    checkAccess().then(() => {
        console.log("Credits refreshed.");
    });

    // 3. Switch to Resume Builder Tab (if not already there by hash)
    // The hash #resume-builder handles structure, but we ensure active class
    // We might want to remove the query param so a refresh doesn't trigger again
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
}

// Unlock Check on Load (Persistent)
if (localStorage.getItem('has_unlocked_rewrite') === 'true') {
    // If we had a mechanism to hide/show the 'Upsell' vs 'Editor', do it here.
    // For now, we assume the user can just access the tab. 
    // We might want to hide the "Unlock" button if it was on the Resume Analysis page?
    // The Unlock button is injected in renderResumeReport (lines 686).
    // We can't easily hide it here because renderResumeReport hasn't run yet.
    // But we can add a global style or class to body?
    document.body.classList.add('rewrite-unlocked');
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

// End of init function block (Cleaned up)

// Global Helper for Negotiation Tabs
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
