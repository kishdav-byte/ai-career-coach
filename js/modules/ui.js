// js/modules/ui.js
export const TOOL_CONFIG = {
    'tool-card-scanner': { type: 'free' },
    'tool-card-rewrite': { type: 'credit', price: '$9.99', creditKey: 'credits_resume', label: 'Credit' },
    'tool-card-cover': { type: 'credit', price: '$6.99', creditKey: 'credits_cover', label: 'Credit' },
    'tool-card-linkedin': { type: 'credit', price: '$6.99', creditKey: 'credits_linkedin', label: 'Credit' },
    'tool-card-mock': { type: 'subscription', price: '$9.99/mo', creditKey: 'credits_interview', label: 'Session' },
    'tool-card-star': { type: 'free' },
    'tool-card-inquisitor': { type: 'credit', price: '$6.99', creditKey: 'credits_inquisitor', label: 'Credit' },
    'tool-card-followup': { type: 'credit', price: '$6.99', creditKey: 'credits_followup', label: 'Credit' },
    'tool-card-closer': { type: 'credit', price: '$6.99', creditKey: 'credits_negotiation', label: 'Credit' },
    'tool-card-plan': { type: 'credit', price: '$8.99', creditKey: 'credits_30_60_90', label: 'Plan' },
    'tool-card-lab': { type: 'free' }
};

export const PRODUCTS = [
    { id: 'monthly_plan', title: 'Ace Pro Monthly', price: '$49.99', desc: 'Unlimited Access + 50 Voice Sessions', stripeId: 'price_1Sbq1WIH1WTKNasqXrlCBDSD', tag: 'Best Value' },
    { id: 'interview_credits_5', title: '5 Interview Sessions', price: '$39.99', desc: 'Full AI Voice Mock Interviews', stripeId: 'price_1ShWDfIH1WTKNasqXjJ8J9u9' },
    { id: 'resume_credits_1', title: '1 Resume Rewrite', price: '$9.99', desc: 'ATS-Optimized Executive Version', stripeId: 'price_1Shc9kH1WTKNasqNfJ6E1F6' },
    { id: 'cover_letter', title: 'Cover Letter', price: '$6.99', desc: '1 Tailored PDF Document', stripeId: 'price_1Shc7tlH1WTKNasqQNu7O5fL' },
    { id: 'linkedin_optimize', title: 'LinkedIn Optimizer', price: '$6.99', desc: '1 Profile Refinement Report', stripeId: 'price_1ShWBJIH1WTKNasqd7p9VA5f' },
    { id: 'negotiation', title: 'Negotiation Script', price: '$6.99', desc: '1 Compensation Strategy Guide', stripeId: 'price_1SeQGAIH1WTKNasqKwRR20TZ' },
    { id: 'follow_up', title: 'Value Follow-Up', price: '$6.99', desc: '1 Post-Interview Email Draft', stripeId: 'price_1SeQHYIH1WTKNasqpFyl2ef0' }
];

export function updateCreditDisplay(session) {
    if (!session) return;
    const countEl = document.getElementById('rb-credit-count');
    const displayEl = document.getElementById('rb-credit-display');
    const generateBtn = document.getElementById('rb-generate-btn');

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
        if (generateBtn) {
            if (session.credits > 0) {
                generateBtn.innerHTML = `Generate Rewrite <small>(1 Credit)</small>`;
                generateBtn.disabled = false;
            } else {
                generateBtn.innerHTML = `Generate Rewrite <small>(1 Credit Needed)</small>`;
                generateBtn.disabled = true;
            }
        }
    }
}

export function updateToolBelt(session) {
    if (!session) return;
    const isUnlimited = session.is_unlimited || session.subscription_status === 'active';
    const universalCredits = session.credits || 0;

    Object.entries(TOOL_CONFIG).forEach(([id, config]) => {
        const card = document.getElementById(id);
        if (!card) return;

        const existingBadge = card.querySelector('.dynamic-badge');
        if (existingBadge) existingBadge.remove();

        let badgeHtml = '';
        if (config.type === 'free') {
            badgeHtml = `<span class="dynamic-badge inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-slate-700 text-slate-300 ml-auto border border-slate-600">Free</span>`;
        } else {
            const specificBalance = session[config.creditKey] || 0;
            const isUnlocked = isUnlimited || (specificBalance > 0) || (universalCredits > 0);

            if (isUnlocked) {
                let text = "Active";
                if (config.type === 'subscription') {
                    if (isUnlimited) text = "Unlimited";
                    else if (specificBalance > 0) text = `${specificBalance} Left`;
                    else if (universalCredits > 0) text = "Unlocked";
                } else {
                    if (isUnlimited) text = "Included";
                    else if (specificBalance > 0) text = `${specificBalance} Left`;
                    else text = "Use Credit";
                }
                badgeHtml = `<div class="dynamic-badge ml-auto text-right">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-teal/20 text-teal border border-teal/30">
                        <i class="fas fa-check-circle mr-1"></i> ${text}
                    </span>
                 </div>`;
            } else {
                badgeHtml = `<span class="dynamic-badge inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-slate-400 ml-auto border border-slate-700 group-hover:border-slate-500 transition-colors">
                    <i class="fas fa-lock mr-1.5 text-xs"></i> ${config.price}
                </span>`;
            }
        }

        const mainFlex = card.querySelector('.flex.items-center');
        if (mainFlex) mainFlex.insertAdjacentHTML('beforeend', badgeHtml);
    });
}
