// js/modules/auth.js
const supabaseUrl = 'https://nvfjmqacxzlmfamiynuu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52ZmptcWFjeHpsbWZhbWl5bnV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUxMzk3MzAsImV4cCI6MjA4MDcxNTczMH0.W3J-E2ldrc99btVeChF0SauTQxr_48uFwImVaoHfOXI';

export const supabaseClient = window.supabase ? window.supabase.createClient(supabaseUrl, supabaseKey) : null;
export const SESSION_KEY = 'aceinterview_session';

export function getSession() {
    const sessionStr = localStorage.getItem(SESSION_KEY);
    if (!sessionStr) return null;
    try {
        let session;
        try {
            session = JSON.parse(sessionStr);
        } catch (e) {
            return { access_token: sessionStr, email: null, subscription_status: 'unknown' };
        }

        const SESSION_DURATION = 7 * 24 * 60 * 60 * 1000;
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

export function updateSession(updates) {
    const session = getSession();
    if (!session) return;
    const newSession = { ...session, ...updates };
    localStorage.setItem(SESSION_KEY, JSON.stringify(newSession));
    return newSession;
}
