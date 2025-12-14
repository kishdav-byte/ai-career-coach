// ARCHIVED FRONTEND LOGIC
// Extracted from app.js

/* 
   BLOCK 1: Tab Switching Logic (formerly inside init() -> tabs.forEach)
*/
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

/* 
   BLOCK 2: Main Tools Logic (Career Planner, LinkedIn, Cover Letter, Resume Builder)
   (formerly at end of init())
*/
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
