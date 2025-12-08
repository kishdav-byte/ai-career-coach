// Helper functions (Global Scope)
function getVoiceSettings() {
    const voice = document.getElementById('voice-select').value;
    const speed = '+0%'; // Default speed
    return { voice, speed };
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
        const response = await fetch('/api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'interview_chat', audio: base64Audio, jobPosting: jobPosting, voice: voice, speed: speed, questionCount: questionCount })
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

    // Helper: Safely add event listener (only if element exists)
    function addClickListener(id, handler) {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', handler);
    }

    // Tab Switching Logic
    const tabs = document.querySelectorAll('.tab-btn');
    const panes = document.querySelectorAll('.tab-pane');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all
            tabs.forEach(t => t.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked tab and corresponding pane
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            // Auto-populate Cover Letter from Resume Builder (only on tools page)
            if (tabId === 'cover-letter') {
                const rbJobDesc = document.getElementById('rb-job-desc');
                const clJobDesc = document.getElementById('cl-job-desc');
                if (rbJobDesc && clJobDesc && rbJobDesc.value && !clJobDesc.value) {
                    clJobDesc.value = rbJobDesc.value;
                }

                const clResume = document.getElementById('cl-resume');
                const rbName = document.getElementById('rb-name');
                if (clResume && rbName && !clResume.value) {
                    // Construct resume text from builder
                    const name = rbName.value;
                    const email = document.getElementById('rb-email')?.value || '';
                    const phone = document.getElementById('rb-phone')?.value || '';
                    const summary = document.getElementById('rb-summary')?.value || '';
                    const skills = document.getElementById('rb-skills')?.value || '';

                    let text = `Name: ${name}\nContact: ${email} | ${phone}\n\nSummary:\n${summary}\n\nExperience:\n`;

                    document.querySelectorAll('.experience-item').forEach(item => {
                        const role = item.querySelector('.rb-exp-role')?.value || '';
                        const company = item.querySelector('.rb-exp-company')?.value || '';
                        const dates = item.querySelector('.rb-exp-dates')?.value || '';
                        const desc = item.querySelector('.rb-exp-desc')?.value || '';
                        if (role) text += `- ${role} at ${company} (${dates}): ${desc}\n`;
                    });

                    text += `\nEducation:\n`;
                    document.querySelectorAll('.education-item').forEach(item => {
                        const school = item.querySelector('.rb-edu-school')?.value || '';
                        const degree = item.querySelector('.rb-edu-degree')?.value || '';
                        if (school) text += `- ${degree} from ${school}\n`;
                    });

                    text += `\nSkills: ${skills}`;
                    clResume.value = text;
                }
            }
        });
    });

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
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'analyze_resume', resume: resumeText })
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
                <div class="upsell-disclaimer-box" style="margin-bottom: 20px; background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px;">
                     ⚠️ <strong>IMPORTANT:</strong> AI-generated content should always be reviewed and customized to ensure it accurately represents your experience and authentic voice. This is a tool to help implement improvements, not a replacement for your personal review and final approval.
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
                                    <span>Avg. Candidate</span>
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
                                <strong>Status:</strong> ${data.benchmark.text}<br>
                                    <span style="font-size:0.9em; color:#666">
                                        ✅ ${data.benchmark.ahead_reasons[0]}<br>
                                            ⚠️ Gap: ${data.benchmark.gap_reasons[0]}
                                    </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 1.5 RED FLAGS (Detailed) -->
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

                <!-- 9. UPSELL (Coming Soon) -->
                <div class="upsell-section-new">
                    <h3 class="upsell-header-large">💡 NEED HELP IMPLEMENTING THESE CHANGES?</h3>
                    <p class="upsell-subheader">See what needs fixing but don't have time to rewrite yourself?</p>

                    <div class="upsell-blue-box">
                        <span class="blue-box-title">✨ AI-ASSISTED RESUME REWRITE - COMING SOON</span>
                        <p class="blue-box-desc">We'll rewrite your resume implementing all the recommendations above:</p>
                        
                        <ul class="blue-box-list">
                            <li><span class="check-icon">✓</span> Add missing metrics (with placeholders to fill)</li>
                            <li><span class="check-icon">✓</span> Strengthen weak verbs and bullet points</li>
                            <li><span class="check-icon">✓</span> Integrate missing keywords naturally</li>
                            <li><span class="check-icon">✓</span> Fix formatting and consistency issues</li>
                            <li><span class="check-icon">✓</span> Optimize for ATS scanning</li>
                            <li><span class="check-icon">✓</span> Remove duplicate/redundant content</li>
                        </ul>

                        <span class="blue-box-footer">Delivered as editable text for you to review, customize, and approve before using.</span>

                        <button class="upsell-action-btn" disabled style="background:#ccc; cursor:not-allowed;">Get AI Resume Rewrite - Coming Soon</button>
                    </div>
                </div>

                <!-- 10. INTERVIEW TIP -->
                <div class="report-section interview-tip">
                    <h4>💡 Interview Readiness</h4>
                    <p>${data.interview_tip || "Practice your STAR method answers."}</p>
                </div>


            </div>
            `;
            container.innerHTML = html;
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
            if (jobPosting.trim()) {
                primeAudio();
                primeAudio();
                questionCount = 0; // Reset counter to 0 for welcome message
                interviewHistory = []; // Reset history
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

            if (!isStart) {
                questionCount++;
            }

            try {
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'interview_chat', message: message, jobPosting: jobPosting, voice: voice, speed: speed, isStart: isStart, questionCount: questionCount })
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

                        if (isStart) {
                            systemMsg += `<br><br>${result.data.next_question || result.data.text || ''}`;
                        } else if (questionCount > 5) {
                            systemMsg += `<br><br><strong>Conclusion:</strong> ${result.data.next_question || result.data.text || ''}`;
                            // Trigger Report Generation
                            setTimeout(generateInterviewReport, 2000);
                        } else {
                            systemMsg += `<br><br><strong>Question ${questionCount} of 5:</strong> ${result.data.next_question || result.data.text || ''}`;
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
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'generate_report', history: interviewHistory })
                });
                const result = await response.json();
                document.getElementById(loadingId).remove();

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
            alert('Payment integration coming soon. Email support@tryaceinterview.com to request resume rewrite for $9.99');
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

    // Career Tools Page (Career Planner, LinkedIn, Cover Letter, Resume Builder)
    if (document.getElementById('generate-plan-btn')) {
        // Tab 3: Career Planner
        document.getElementById('generate-plan-btn').addEventListener('click', async () => {
            const jobTitle = document.getElementById('job-title').value;
            const company = document.getElementById('company').value;
            const jobPosting = document.getElementById('job-posting').value;
            if (jobTitle && company) {
                const outputDiv = document.getElementById('planner-result');
                outputDiv.innerHTML = '<div class="loading-spinner"></div>';

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
            if (typeof data === 'string') {
                // Fallback for string response
                container.innerHTML = marked.parse(data);
                return;
            }

            let html = '<div class="career-plan-container">';

            const phases = [
                { key: 'day_30', title: '30 Days: Learn & Connect' },
                { key: 'day_60', title: '60 Days: Contribute & Build' },
                { key: 'day_90', title: '90 Days: Lead & Innovate' }
            ];

            phases.forEach(phase => {
                const items = data[phase.key] || [];
                html += `
                    <div class="plan-card">
                        <h3>${phase.title}</h3>
                        <ul>
                            ${items.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    `;
            });

            html += '</div>';
            container.innerHTML = html;
        }
        // Tab 4: LinkedIn Optimizer
        document.getElementById('optimize-linkedin-btn').addEventListener('click', async () => {
            const aboutMe = document.getElementById('linkedin-input').value;
            if (!aboutMe) return alert('Please paste your About Me section.');

            const resultsArea = document.getElementById('linkedin-results-area');
            const recsDiv = document.getElementById('linkedin-recommendations');
            const sampleDiv = document.getElementById('linkedin-refined-sample');

            // Show loading
            resultsArea.style.display = 'block';
            recsDiv.innerHTML = '<div class="loading-spinner"></div>';
            sampleDiv.innerHTML = '<div class="loading-spinner"></div>';

            try {
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'linkedin_optimize', aboutMe })
                });
                const result = await response.json();

                if (result.data) {
                    // Handle JSON response
                    let data = result.data;
                    if (typeof data === 'string') {
                        try {
                            data = JSON.parse(data);
                        } catch (e) {
                            // Fallback if not JSON
                            recsDiv.innerHTML = "Could not parse recommendations.";
                            sampleDiv.innerHTML = marked.parse(data);
                            return;
                        }
                    }

                    // Render Recommendations
                    if (data.recommendations && Array.isArray(data.recommendations)) {
                        recsDiv.innerHTML = `<ul>${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}</ul>`;
                    } else {
                        recsDiv.innerHTML = '<p>No specific recommendations provided.</p>';
                    }

                    // Render Refined Sample
                    if (data.refined_sample) {
                        sampleDiv.innerHTML = marked.parse(data.refined_sample);
                    } else {
                        sampleDiv.innerHTML = '<p>No sample generated.</p>';
                    }

                } else {
                    recsDiv.innerHTML = 'Error generating optimization.';
                    sampleDiv.innerHTML = '';
                }
            } catch (e) {
                console.error(e);
                recsDiv.innerHTML = 'Error generating optimization.';
                sampleDiv.innerHTML = '';
            }
        });

        // Tab 5: Cover Letter
        document.getElementById('generate-cl-btn').addEventListener('click', async () => {
            const jobDesc = document.getElementById('cl-job-desc').value;
            const resume = document.getElementById('cl-resume').value;
            if (!jobDesc || !resume) return alert('Please fill in both fields.');

            // Get user data for header
            const userData = {
                name: document.getElementById('rb-name').value || "Your Name",
                email: document.getElementById('rb-email').value || "email@example.com",
                phone: document.getElementById('rb-phone').value || "Phone",
                location: document.getElementById('rb-location').value || "Location",
                linkedin: document.getElementById('rb-linkedin').value || ""
            };

            const resultEl = document.getElementById('cl-result');
            resultEl.innerHTML = '<em>Generating professional cover letter...</em>';
            resultEl.style.display = 'block';
            resultEl.scrollIntoView({ behavior: 'smooth' });

            try {
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'cover_letter', jobDesc, resume })
                });
                const result = await response.json();

                if (result.data) {
                    renderCoverLetter(result.data, userData, 'cl-result');
                    // Scroll again to show the full result
                    document.getElementById('cl-result').scrollIntoView({ behavior: 'smooth' });
                } else {
                    resultEl.innerHTML = `<strong style="color:red">Error: ${result.error}</strong>`;
                }
            } catch (e) {
                const resultEl = document.getElementById('cl-result');
                if (resultEl) {
                    resultEl.innerHTML = `<strong style="color:red">Error: ${e.message}</strong>`;
                }
            }
        });

        function renderCoverLetter(text, user, elementId) {
            const container = document.getElementById(elementId);

            // Format body text (newlines to paragraphs)
            const bodyHtml = text.split('\n').map(line => line.trim() ? `<p>${line}</p>` : '<br>').join('');

            const html = `
                    <div class="cl-preview" id="cl-preview-content">
                        <div class="cl-header">
                            <h1>${user.name}</h1>
                            <div class="cl-contact">
                                <span>${user.location}</span> |
                                <span>${user.email}</span> |
                                <span>${user.phone}</span>
                                ${user.linkedin ? `| <span>${user.linkedin}</span>` : ''}
                            </div>
                        </div>
                        <hr class="cl-divider">
                            <div class="cl-body">
                                ${bodyHtml}
                            </div>
                    </div>
                    <div class="preview-actions" style="margin-top: 10px; text-align: center;">
                        <button id="cl-print-btn" class="secondary-btn">Print / Save PDF</button>
                        <button id="cl-gdocs-btn" class="secondary-btn" style="margin-left: 10px;">Copy for Google Docs</button>
                    </div>
                    `;

            container.innerHTML = html;

            // Force display block just in case
            container.style.display = 'block';

            // Add Event Listeners for the new buttons
            document.getElementById('cl-print-btn').addEventListener('click', () => {
                const printArea = document.getElementById('print-area');
                const content = document.getElementById('cl-preview-content').cloneNode(true);
                printArea.innerHTML = '';
                printArea.appendChild(content);
                window.print();
            });

            document.getElementById('cl-gdocs-btn').addEventListener('click', async () => {
                const content = document.getElementById('cl-preview-content');
                try {
                    const type = "text/html";
                    const blob = new Blob([content.outerHTML], { type });
                    const data = [new ClipboardItem({ [type]: blob })];
                    await navigator.clipboard.write(data);

                    const btn = document.getElementById('cl-gdocs-btn');
                    const originalText = btn.textContent;
                    btn.textContent = 'Copied!';
                    setTimeout(() => btn.textContent = originalText, 2000);
                } catch (err) {
                    console.error('Failed to copy: ', err);
                    alert('Failed to copy. Please select text manually.');
                }
            });
        }
        // Tab 6: Resume Builder

        // Sample Data Button
        document.getElementById('rb-sample-btn').addEventListener('click', () => {
            // Personal Info
            document.getElementById('rb-name').value = "Sample User";
            document.getElementById('rb-email').value = "SampleUser@Sample.com";
            document.getElementById('rb-phone').value = "864-555-1212";
            document.getElementById('rb-linkedin').value = "https://www.linkedin.com";
            document.getElementById('rb-location').value = "Norwood, New Jersey";

            // Summary
            document.getElementById('rb-summary').value = "Profile Overview Accomplished Senior Project Manager with over eight years of experience leading cross-functional teams in the technology and software development sectors. Proven track record of delivering complex enterprise solutions on time and under budget while adhering to strict quality standards. Expert in Agile and Waterfall methodologies, adept at facilitating communication between technical engineering teams and non-technical stakeholders. strong focus on risk management, resource allocation, and strategic planning to drive operational efficiency. Dedicated to continuous process improvement and fostering a collaborative team environment that encourages innovation. Successfully managed portfolios valued at over $5 million, consistently exceeding client expectations and business objectives. Passionate about mentorship and developing junior staff members into future organizational leaders. committed to leveraging data-driven insights to solve problems and optimize project workflows.";

            // Experience
            const expContainer = document.getElementById('rb-experience-list');
            expContainer.innerHTML = ''; // Clear existing

            const expDiv = document.createElement('div');
            expDiv.classList.add('experience-item');
            expDiv.innerHTML = `
                    <input type="text" class="rb-exp-role" placeholder="Job Title" value="Senior Project Manager">
                        <input type="text" class="rb-exp-company" placeholder="Company" value="Apex Innovations, Inc.">
                            <input type="text" class="rb-exp-dates" placeholder="Dates (e.g. 2020 - Present)" value="January 2018 – Present">
                                <textarea class="rb-exp-desc" placeholder="Job responsibilities and achievements...">I spearhead the end-to-end planning and execution of multiple high-stakes software development projects, ensuring full alignment with organizational strategic goals. My role involves leading a diverse team of 15 developers, designers, and QA analysts through the full software development life cycle (SDLC). I facilitate all Agile ceremonies, including daily stand-ups, sprint planning, and retrospective meetings, to maintain high project velocity. Last year, I successfully oversaw the launch of a flagship mobile application that acquired 50,000 active users within the first three months of release. I took the initiative to reduce project delivery time by 20% by implementing streamlined workflow automation and enhanced communication tools. Managing stakeholder expectations is a daily priority, achieved through transparent progress reporting and proactive risk assessment updates. I currently oversee a departmental budget of $2.5 million, consistently delivering projects within a 5% variance of the initial financial scope. Additionally, I actively mentor junior project managers to foster a culture of continuous learning and professional development within the department.</textarea>
                                <button class="secondary-btn remove-btn" style="background: #dc3545; padding: 5px 10px; margin-top: 5px;">Remove</button>
                                `;
            expContainer.appendChild(expDiv);
            expDiv.querySelector('.remove-btn').addEventListener('click', () => expDiv.remove());

            // Education
            const eduContainer = document.getElementById('rb-education-list');
            eduContainer.innerHTML = ''; // Clear existing

            const eduDiv = document.createElement('div');
            eduDiv.classList.add('education-item');
            eduDiv.innerHTML = `
                                <input type="text" class="rb-edu-school" placeholder="School/University" value="Rutgers University">
                                    <input type="text" class="rb-edu-degree" placeholder="Degree/Major" value="Bachelor of Science in Business Administration">
                                        <input type="text" class="rb-edu-year" placeholder="Graduation Year" value="2015">
                                            <button class="secondary-btn remove-btn" style="background: #dc3545; padding: 5px 10px; margin-top: 5px;">Remove</button>
                                            `;
            eduContainer.appendChild(eduDiv);
            eduDiv.querySelector('.remove-btn').addEventListener('click', () => eduDiv.remove());

            // Skills (Inferred)
            document.getElementById('rb-skills').value = "Agile, Waterfall, Risk Management, Strategic Planning, SDLC, Team Leadership, Budget Management";
        });

        // Dynamic Fields
        document.getElementById('rb-add-exp-btn').addEventListener('click', () => {
            const container = document.getElementById('rb-experience-list');
            const div = document.createElement('div');
            div.classList.add('experience-item');
            div.innerHTML = `
                                            <input type="text" class="rb-exp-role" placeholder="Job Title">
                                                <input type="text" class="rb-exp-company" placeholder="Company">
                                                    <input type="text" class="rb-exp-dates" placeholder="Dates (e.g. 2020 - Present)">
                                                        <textarea class="rb-exp-desc" placeholder="Job responsibilities and achievements..."></textarea>
                                                        <button class="secondary-btn remove-btn" style="background: #dc3545; padding: 5px 10px; margin-top: 5px;">Remove</button>
                                                        `;
            container.appendChild(div);

            div.querySelector('.remove-btn').addEventListener('click', () => div.remove());
        });

        document.getElementById('rb-add-edu-btn').addEventListener('click', () => {
            const container = document.getElementById('rb-education-list');
            const div = document.createElement('div');
            div.classList.add('education-item');
            div.innerHTML = `
                                                        <input type="text" class="rb-edu-school" placeholder="School/University">
                                                            <input type="text" class="rb-edu-degree" placeholder="Degree/Major">
                                                                <input type="text" class="rb-edu-year" placeholder="Graduation Year">
                                                                    <button class="secondary-btn remove-btn" style="background: #dc3545; padding: 5px 10px; margin-top: 5px;">Remove</button>
                                                                    `;
            container.appendChild(div);

            div.querySelector('.remove-btn').addEventListener('click', () => div.remove());
        });

        // Template Switching
        const templateBtns = document.querySelectorAll('.template-btn');
        const previewContainer = document.getElementById('resume-preview-container');

        templateBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active button
                templateBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Update preview class
                const template = btn.getAttribute('data-template');
                previewContainer.className = `resume-preview ${template}`;
            });
        });

        // Generate Resume
        document.getElementById('rb-generate-btn').addEventListener('click', async () => {
            const btn = document.getElementById('rb-generate-btn');
            const originalText = btn.textContent;
            btn.textContent = 'Generating...';
            btn.disabled = true;

            // Get active template
            const activeTemplateBtn = document.querySelector('.template-btn.active');
            const templateName = activeTemplateBtn ? activeTemplateBtn.getAttribute('data-template') : 'modern';

            // Get Job Description
            const jobDescription = document.getElementById('rb-job-desc').value;

            // Collect Data
            const userData = {
                personal: {
                    name: document.getElementById('rb-name').value,
                    email: document.getElementById('rb-email').value,
                    phone: document.getElementById('rb-phone').value,
                    linkedin: document.getElementById('rb-linkedin').value,
                    location: document.getElementById('rb-location').value
                },
                summary: document.getElementById('rb-summary').value,
                experience: [],
                education: [],
                skills: document.getElementById('rb-skills').value
            };

            // Collect Experience
            document.querySelectorAll('.experience-item').forEach(item => {
                userData.experience.push({
                    role: item.querySelector('.rb-exp-role').value,
                    company: item.querySelector('.rb-exp-company').value,
                    dates: item.querySelector('.rb-exp-dates').value,
                    description: item.querySelector('.rb-exp-desc').value
                });
            });

            // Collect Education
            document.querySelectorAll('.education-item').forEach(item => {
                userData.education.push({
                    school: item.querySelector('.rb-edu-school').value,
                    degree: item.querySelector('.rb-edu-degree').value,
                    year: item.querySelector('.rb-edu-year').value
                });
            });

            try {
                // Save to LocalStorage
                localStorage.setItem('user_profile', JSON.stringify(userData));
                console.log("Profile saved to LocalStorage");

                const response = await fetch('/api/optimize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_data: userData,
                        template_name: templateName,
                        job_description: jobDescription
                    })
                });

                const result = await response.json();

                if (result) {
                    renderResume(result);
                }
            } catch (error) {
                console.error(error);
                alert('Failed to generate resume.');
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });

        function renderResume(data) {
            const preview = document.getElementById('resume-preview-container');

            let expHtml = data.experience.map(job => `
                                                                    <div class="job-item">
                                                                        <div class="job-header">
                                                                            <span class="job-role">${job.role}</span>
                                                                            <span class="job-dates">${job.dates}</span>
                                                                        </div>
                                                                        <div class="job-company">${job.company}</div>
                                                                        <div class="job-desc">${formatJobDescription(job.description)}</div>
                                                                    </div>
                                                                    `).join('');

            let eduHtml = data.education.map(edu => `
                                                                    <div class="edu-item">
                                                                        <div class="edu-header">
                                                                            <span class="edu-school">${edu.school}</span>
                                                                            <span class="edu-year">${edu.year}</span>
                                                                        </div>
                                                                        <div class="edu-degree">${edu.degree}</div>
                                                                    </div>
                                                                    `).join('');

            preview.innerHTML = `
                                                                    <h1>${data.personal.name}</h1>
                                                                    <div class="contact-info">
                                                                        ${data.personal.location} | ${data.personal.email} | ${data.personal.phone} | ${data.personal.linkedin}
                                                                    </div>

                                                                    <h2>Professional Summary</h2>
                                                                    <p>${data.summary}</p>

                                                                    <h2>Experience</h2>
                                                                    ${expHtml}

                                                                    <h2>Education</h2>
                                                                    ${eduHtml}

                                                                    <h2>Skills</h2>
                                                                    <p>${data.skills}</p>
                                                                    `;
        }

        function formatJobDescription(desc) {
            if (!desc) return '';

            // Check if it looks like a list
            const trimmed = desc.trim();
            const isList = trimmed.startsWith('-') || trimmed.startsWith('*') || trimmed.startsWith('•') ||
                trimmed.includes('\n-') || trimmed.includes('\n*') || trimmed.includes('•');

            if (isList) {
                // Split by newlines or bullets, handling various formats
                // This regex splits by newline followed by optional whitespace and a bullet char
                const items = trimmed.split(/(?:\r\n|\r|\n)(?:\s*[-*•]\s*)?|(?:\s*•\s*)/)
                    .map(item => item.replace(/^[-*•]\s*/, '').trim()) // Clean up leading bullets/space
                    .filter(item => item.length > 0);

                return `<ul>${items.map(item => `<li>${item}</li>`).join('')}</ul>`;
            }

            return desc.replace(/\n/g, '<br>');
        }

        // Print/PDF
        // Print/PDF
        document.getElementById('rb-print-btn').addEventListener('click', () => {
            const printArea = document.getElementById('print-area');
            const content = document.getElementById('resume-preview-container').cloneNode(true);
            printArea.innerHTML = '';
            printArea.appendChild(content);
            window.print();
            // Optional: Clear print area after printing (though user won't see it)
            // printArea.innerHTML = ''; 
        });

        // Copy for Google Docs
        document.getElementById('rb-gdocs-btn').addEventListener('click', async () => {
            const content = document.getElementById('resume-preview-container');

            try {
                // Create a temporary blob to copy as rich text
                const type = "text/html";
                const blob = new Blob([content.outerHTML], { type });
                const data = [new ClipboardItem({ [type]: blob })];

                await navigator.clipboard.write(data);

                const btn = document.getElementById('rb-gdocs-btn');
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy: ', err);
                alert('Failed to copy to clipboard. Please select the text manually and copy.');
            }
        });

        // Load Profile Data from LocalStorage
        function loadProfile() {
            console.log("Loading profile from LocalStorage...");
            try {
                const storedData = localStorage.getItem('user_profile');
                if (storedData) {
                    const data = JSON.parse(storedData);
                    console.log("Profile data loaded:", data);

                    if (data && Object.keys(data).length > 0) {
                        // Personal Info
                        if (data.personal) {
                            console.log("Setting personal info:", data.personal);
                            document.getElementById('rb-name').value = data.personal.name || '';
                            document.getElementById('rb-email').value = data.personal.email || '';
                            document.getElementById('rb-phone').value = data.personal.phone || '';
                            document.getElementById('rb-linkedin').value = data.personal.linkedin || '';
                            document.getElementById('rb-location').value = data.personal.location || '';
                        }

                        // Summary
                        document.getElementById('rb-summary').value = data.summary || '';

                        // Experience
                        if (data.experience && data.experience.length > 0) {
                            const container = document.getElementById('rb-experience-list');
                            container.innerHTML = ''; // Clear default

                            data.experience.forEach(job => {
                                const div = document.createElement('div');
                                div.classList.add('experience-item');
                                div.innerHTML = `
                                                                        <input type="text" class="rb-exp-role" placeholder="Job Title" value="${job.role || ''}">
                                                                            <input type="text" class="rb-exp-company" placeholder="Company" value="${job.company || ''}">
                                                                                <input type="text" class="rb-exp-dates" placeholder="Dates (e.g. 2020 - Present)" value="${job.dates || ''}">
                                                                                    <textarea class="rb-exp-desc" placeholder="Job responsibilities and achievements...">${job.description || ''}</textarea>
                                                                                    <button class="secondary-btn remove-btn" style="background: #dc3545; padding: 5px 10px; margin-top: 5px;">Remove</button>
                                                                                    `;
                                container.appendChild(div);
                                div.querySelector('.remove-btn').addEventListener('click', () => div.remove());
                            });
                        }

                        // Education
                        if (data.education && data.education.length > 0) {
                            const container = document.getElementById('rb-education-list');
                            container.innerHTML = ''; // Clear default

                            data.education.forEach(edu => {
                                const div = document.createElement('div');
                                div.classList.add('education-item');
                                div.innerHTML = `
                                                                                    <input type="text" class="rb-edu-school" placeholder="School/University" value="${edu.school || ''}">
                                                                                        <input type="text" class="rb-edu-degree" placeholder="Degree/Major" value="${edu.degree || ''}">
                                                                                            <input type="text" class="rb-edu-year" placeholder="Graduation Year" value="${edu.year || ''}">
                                                                                                <button class="secondary-btn remove-btn" style="background: #dc3545; padding: 5px 10px; margin-top: 5px;">Remove</button>
                                                                                                `;
                                container.appendChild(div);
                                div.querySelector('.remove-btn').addEventListener('click', () => div.remove());
                            });
                        }

                        // Skills
                        document.getElementById('rb-skills').value = data.skills || '';
                    }
                } else {
                    console.log("No profile found in LocalStorage.");
                }
            } catch (e) {
                console.error("Error loading profile:", e);
            }
        }

        loadProfile();
    } // End of Career Tools Page
} // End of init function

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

window.init = init;
