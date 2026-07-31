import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import { useViewMode } from './useViewMode';

// --- CAREER HUB MOBILE COMPONENT ---
const CareerHub = () => {
    const [activeGroup, setActiveGroup] = useState(null);

    const toggleHubGroup = (group) => {
        setActiveGroup(prev => prev === group ? null : group);
    };

    return (
        <div className="space-y-4 pb-12 max-w-md mx-auto w-full">
            
            {/* 1. The Clinic Card */}
            <div className="w-full">
                <button
                    onClick={() => toggleHubGroup('clinic')}
                    className="w-full bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-5 text-left flex items-center justify-between group active:scale-[0.98] transition-all outline-none"
                >
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 group-hover:scale-105 transition-transform">
                            <i className="fas fa-file-alt text-xl"></i>
                        </div>
                        <div>
                            <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition-colors">The Clinic</h3>
                            <p className="text-xs text-slate-400 mt-0.5">Resume Scans & Executive Optimization</p>
                        </div>
                    </div>
                    <div className="text-slate-500 group-hover:text-blue-400 transition-colors">
                        <i className={`fas fa-chevron-right transition-transform duration-200 ${activeGroup === 'clinic' ? 'rotate-90' : ''}`}></i>
                    </div>
                </button>
                {activeGroup === 'clinic' && (
                    <div className="mt-2 ml-2 space-y-2 border-l border-white/5 pl-2 transition-all">
                        <a href="/resume-analyzer" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-blue-500/30 rounded-xl transition-all group">
                            <i className="fas fa-microscope text-blue-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">Resume Scanner</span>
                        </a>
                        <a href="/resume-rewriter" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-yellow-500/30 rounded-xl transition-all group">
                            <i className="fas fa-pen-nib text-yellow-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">Executive Rewrite</span>
                        </a>
                        <a href="/app#linkedin" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-blue-400/30 rounded-xl transition-all group">
                            <i className="fab fa-linkedin text-blue-300 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">LinkedIn Optimizer</span>
                        </a>
                    </div>
                )}
            </div>

            {/* 2. The Simulator Card */}
            <div className="w-full">
                <button
                    onClick={() => toggleHubGroup('simulator')}
                    className="w-full bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-5 text-left flex items-center justify-between group active:scale-[0.98] transition-all outline-none"
                >
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-teal-500/10 flex items-center justify-center text-teal group-hover:scale-105 transition-transform">
                            <i className="fas fa-microphone text-xl"></i>
                        </div>
                        <div>
                            <h3 className="text-base font-bold text-white group-hover:text-teal transition-colors">The Simulator</h3>
                            <p className="text-xs text-slate-400 mt-0.5">Voice Interviews & STAR Calibrators</p>
                        </div>
                    </div>
                    <div className="text-slate-500 group-hover:text-teal transition-colors">
                        <i className={`fas fa-chevron-right transition-transform duration-200 ${activeGroup === 'simulator' ? 'rotate-90' : ''}`}></i>
                    </div>
                </button>
                {activeGroup === 'simulator' && (
                    <div className="mt-2 ml-2 space-y-2 border-l border-white/5 pl-2 transition-all">
                        <a href="/app" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-teal/30 rounded-xl transition-all group">
                            <i className="fas fa-microphone-alt text-teal text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">Mock Interview Simulator</span>
                        </a>
                        <a href="/role-reversal" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-cyan-500/30 rounded-xl transition-all group">
                            <i className="fas fa-undo text-cyan-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">Role Reversal Practice</span>
                        </a>
                        <a href="/star-drill" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-yellow-400/30 rounded-xl transition-all group">
                            <i className="fas fa-star text-yellow-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">STAR Method Drill</span>
                        </a>
                    </div>
                )}
            </div>

            {/* 3. The Strategy Card */}
            <div className="w-full">
                <button
                    onClick={() => toggleHubGroup('strategy')}
                    className="w-full bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-5 text-left flex items-center justify-between group active:scale-[0.98] transition-all outline-none"
                >
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400 group-hover:scale-105 transition-transform">
                            <i className="fas fa-crosshairs text-xl"></i>
                        </div>
                        <div>
                            <h3 className="text-base font-bold text-white group-hover:text-purple-400 transition-colors">The Strategy</h3>
                            <p className="text-xs text-slate-400 mt-0.5">Onboard Plans, Negotiation & Logs</p>
                        </div>
                    </div>
                    <div className="text-slate-500 group-hover:text-purple-400 transition-colors">
                        <i className={`fas fa-chevron-right transition-transform duration-200 ${activeGroup === 'strategy' ? 'rotate-90' : ''}`}></i>
                    </div>
                </button>
                {activeGroup === 'strategy' && (
                    <div className="mt-2 ml-2 space-y-2 border-l border-white/5 pl-2 transition-all">
                        <a href="/jobs-history" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-blue-400/30 rounded-xl transition-all group">
                            <i className="fas fa-th-list text-blue-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">Job Tracker</span>
                        </a>
                        <a href="/strategy/30-60-90" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-cyan-400/30 rounded-xl transition-all group">
                            <i className="fas fa-calendar-alt text-cyan-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">30-60-90 Day Plan</span>
                        </a>
                        <a href="/strategy/closer" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-emerald-400/30 rounded-xl transition-all group">
                            <i className="fas fa-handshake text-emerald-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">The Closer (Negotiator)</span>
                        </a>
                        <a href="/strategy/inquisitor" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-amber-400/30 rounded-xl transition-all group">
                            <i className="fas fa-question-circle text-amber-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">The Inquisitor (Reverse Qs)</span>
                        </a>
                        <a href="/strategy/follow-up" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-indigo-400/30 rounded-xl transition-all group">
                            <i className="fas fa-paper-plane text-indigo-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">Value Follow-Up Email</span>
                        </a>
                        <a href="/strategy-lab" className="flex items-center gap-3 p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/50 hover:border-purple-400/30 rounded-xl transition-all group">
                            <i className="fas fa-chess-knight text-purple-400 text-sm group-hover:scale-110 transition-transform"></i>
                            <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">Strategy Lab Dashboard</span>
                        </a>
                    </div>
                )}
            </div>

        </div>
    );
};

const Dashboard = () => {
    const [viewMode, setViewMode] = useViewMode();
    // User State
    const [stats, setStats] = useState({
        resumeScore: 0,
        activeJobs: 0,
        credits: 0,
        plan: 'Free',
        interviewAvg: 0
    });
    const [recentActivity, setRecentActivity] = useState([]);
    const [graphData, setGraphData] = useState([]);
    const [graphType, setGraphType] = useState('interviews'); // 'interviews' or 'resumes'
    const [loading, setLoading] = useState(true);
    const [userProfile, setUserProfile] = useState({ name: 'David Kish', initials: 'DK' });

    useEffect(() => {
        async function fetchDashboardData() {
            setLoading(true);
            try {
                // 0. Get User First
                const { data: { user } } = await supabase.auth.getUser();

                if (!user) {
                    console.log("No user found");
                    setLoading(false);
                    return;
                }

                // Set Profile immediately
                const name = user.user_metadata?.name || user.email?.split('@')[0] || 'User';
                setUserProfile({
                    name: name,
                    initials: name.substring(0, 2).toUpperCase()
                });

                // --- PROMPT LOGIC (With User Filters) ---
                // 1. Get Resume Score
                const { data: resumes } = await supabase.from('resumes')
                    .select('overall_score')
                    .eq('user_id', user.id)
                    .order('created_at', { ascending: false })
                    .limit(1);

                // 2. Get Strategy Count (Active Jobs)
                const { count: jobCount } = await supabase.from('user_jobs')
                    .select('*', { count: 'exact', head: true })
                    .eq('user_id', user.id);

                // 3. Get Plan Details (Updated: Query 'users' table)
                const { data: profile } = await supabase.from('users')
                    .select('subscription_status, credits, is_unlimited, subscription_period_end')
                    .eq('id', user.id)
                    .single();

                // 4. Get Interview Avg (Last 30 days)
                const { data: interviews } = await supabase.from('interviews')
                    .select('overall_score, created_at')
                    .eq('user_id', user.id)
                    .gte('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString());

                // --- ADDITIONAL DATA FOR UI (Graph & Activity) to prevent blank sections ---
                const table = graphType === 'interviews' ? 'interviews' : 'resumes';
                const { data: graph } = await supabase.from(table)
                    .select('created_at, overall_score')
                    .eq('user_id', user.id)
                    .order('created_at', { ascending: true })
                    .limit(7);

                const { data: activity } = await supabase.from('user_recent_activity')
                    .select('*')
                    .eq('user_id', user.id)
                    .limit(5);

                const isUnlimited = profile?.is_unlimited || profile?.subscription_status === 'pro';

                // UPDATE STATE
                setStats({
                    resumeScore: resumes?.[0]?.overall_score || 0,
                    activeJobs: jobCount || 0,
                    credits: profile?.credits || 0,
                    isUnlimited: isUnlimited,
                    subscriptionPeriodEnd: profile?.subscription_period_end,
                    plan: isUnlimited ? 'PRO PLAN' : (profile?.subscription_status || 'Free Plan'),
                    interviewAvg: interviews && interviews.length ? (interviews.reduce((a, b) => a + b.overall_score, 0) / interviews.length).toFixed(1) : 0
                });

                if (graph) setGraphData(graph);
                if (activity) setRecentActivity(activity);

            } catch (error) {
                console.error('Error loading dashboard:', error);
            } finally {
                setLoading(false);
            }
        }

        fetchDashboardData();
    }, [graphType]);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        localStorage.removeItem('supabase.auth.token');
        localStorage.removeItem('aceinterview_session');
        window.location.href = '/login.html';
    };

    const timeAgo = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return `${Math.floor(diffInSeconds / 86400)}d ago`;
    };

    const Skeleton = ({ className }) => (
        <div className={`bg-slate-800 animate-pulse rounded ${className}`}></div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-[#0A2540] to-black text-white font-sans p-6">

            {/* Header */}
            <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-10 max-w-7xl mx-auto w-full">
                <div>
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Executive Performance Hub
                    </h1>
                </div>
                
                {/* View Mode Toggle Pill */}
                <div className="flex items-center bg-slate-900/60 border border-white/10 rounded-full p-0.5 text-[10px] md:text-xs font-medium self-center sm:self-auto z-10">
                    <button
                        onClick={() => setViewMode('command-center')}
                        className={`px-3 py-1 rounded-full transition-all duration-200 font-semibold ${viewMode === 'command-center' ? 'bg-slate-800 text-white border border-slate-700/50 shadow-sm font-bold' : 'text-slate-400 hover:text-white'}`}
                    >
                        Command Center
                    </button>
                    <button
                        onClick={() => setViewMode('career-hub')}
                        className={`px-3 py-1 rounded-full transition-all duration-200 font-semibold ${viewMode === 'career-hub' ? 'bg-teal-500 text-slate-900 font-bold shadow-sm' : 'text-slate-400 hover:text-white'}`}
                    >
                        Career Hub
                    </button>
                </div>

                <div className="flex items-center gap-4 self-end sm:self-auto">
                    {loading ? <Skeleton className="w-24 h-4" /> : <span className="text-sm text-gray-400">{userProfile.name}</span>}
                    <button
                        onClick={handleLogout}
                        title="Sign Out"
                        className="w-10 h-10 rounded-full bg-teal-500/20 flex items-center justify-center text-[#20C997] font-bold border border-[#20C997]/30 hover:bg-teal-500/30 hover:border-[#20C997]/60 transition-all cursor-pointer"
                    >
                        {userProfile.initials}
                    </button>
                </div>
            </header>

            {viewMode === 'command-center' ? (
                <>
                    <div className="max-w-7xl mx-auto grid gap-8">

                {/* 1. Key Metrics Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

                    {/* Metric 1: Resume Health */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative overflow-hidden group hover:border-[#20C997]/50 transition-colors">
                        <div className="absolute top-0 left-0 w-full h-1 bg-[#20C997]/20"></div>
                        <h3 className="text-gray-400 text-sm font-medium mb-4 uppercase tracking-wider">Resume Health</h3>
                        {loading ? (
                            <Skeleton className="w-24 h-24 rounded-full" />
                        ) : (
                            <div className="relative w-24 h-24 flex items-center justify-center rounded-full border-4 border-slate-700">
                                <div
                                    className="absolute w-full h-full rounded-full border-4 border-[#20C997] border-l-transparent transform -rotate-45"
                                    style={{
                                        borderRightColor: stats.resumeScore > 50 ? '#20C997' : 'transparent',
                                        borderBottomColor: stats.resumeScore > 75 ? '#20C997' : 'transparent',
                                        transform: `rotate(${(stats.resumeScore / 100) * 360 - 45}deg)`
                                    }}
                                ></div>
                                <span className="text-3xl font-bold text-white">{stats.resumeScore}</span>
                            </div>
                        )}
                    </div>

                    {/* Metric 2: Avg Interview Score (Updated Accessor) */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative group hover:border-[#20C997]/50 transition-colors">
                        <div className="absolute top-0 left-0 w-full h-1 bg-[#20C997]/20"></div>
                        <h3 className="text-gray-400 text-sm font-medium mb-2 uppercase tracking-wider">Avg. Score</h3>
                        {loading ? (
                            <div className="flex flex-col items-center gap-2">
                                <Skeleton className="w-16 h-10" />
                                <Skeleton className="w-24 h-6" />
                            </div>
                        ) : (
                            <>
                                <div className="text-4xl font-bold text-white mb-2">{stats.interviewAvg}<span className="text-gray-500 text-xl">/10</span></div>
                                {/* Placeholder Trend or Dynamic if we had it */}
                                <div className="text-xs text-gray-500">Last 30 Days</div>
                            </>
                        )}
                    </div>

                    {/* Metric 3: Active Strategies */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative group hover:border-[#20C997]/50 transition-colors">
                        <div className="absolute top-0 left-0 w-full h-1 bg-[#20C997]/20"></div>
                        <h3 className="text-gray-400 text-sm font-medium mb-4 uppercase tracking-wider">Strategy Log</h3>
                        {loading ? (
                            <>
                                <Skeleton className="w-16 h-10 mb-2" />
                                <Skeleton className="w-20 h-4" />
                            </>
                        ) : (
                            <>
                                <div className="flex items-center gap-3 mb-2">
                                    <span className="text-3xl">♟️</span>
                                    <span className="text-4xl font-bold text-white">{stats.activeJobs}</span>
                                </div>
                                <span className="text-gray-500 text-sm">Active Strategies</span>
                            </>
                        )}
                    </div>

                    {/* Metric 4: Credits/Plan (Updated Accessor) */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative group hover:border-[#20C997]/50 transition-colors">
                        <div className="absolute top-0 left-0 w-full h-1 bg-[#20C997]/20"></div>
                        <h3 className="text-gray-400 text-sm font-medium mb-4 uppercase tracking-wider">{loading ? <Skeleton className="w-20 h-4" /> : stats.plan}</h3>
                        {loading ? (
                            <Skeleton className="w-full h-3 mb-3" />
                        ) : (
                            <div className="w-full bg-slate-700 h-3 rounded-full overflow-hidden mb-3">
                                <div
                                    className={`bg-[#20C997] h-full rounded-full transition-all duration-500 ${stats.isUnlimited ? 'shadow-[0_0_10px_rgba(32,201,151,0.5)]' : ''}`}
                                    style={{ width: `${stats.isUnlimited ? 100 : Math.min((stats.credits / 50) * 100, 100)}%` }}
                                ></div>
                            </div>
                        )}
                        {loading ? (
                            <div className="flex justify-between w-full"><Skeleton className="w-10 h-4" /><Skeleton className="w-10 h-4" /></div>
                        ) : (
                            <div className="flex justify-between w-full text-sm">
                                <span className="text-white font-bold">{stats.isUnlimited ? 'Unlimited Access' : `${stats.credits} Credits`}</span>
                                {stats.subscriptionPeriodEnd ? (() => {
                                    const days = Math.ceil((new Date(stats.subscriptionPeriodEnd) - new Date()) / (1000 * 60 * 60 * 24));
                                    return days > 0 ? <span className="text-gray-500">Resets in {days} days</span> : <span className="text-gray-500">Left</span>;
                                })() : <span className="text-gray-500">Left</span>}
                            </div>
                        )}
                    </div>

                </div>

                {/* 2. Main Content Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Left: Trend Graph */}
                    <div className="lg:col-span-2 bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white">Performance Summary</h3>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setGraphType('interviews')}
                                    className={`text-xs px-2 py-1 rounded transition-all ${graphType === 'interviews' ? 'bg-teal-500/10 text-[#20C997] border border-[#20C997]/20 font-bold' : 'text-gray-500 hover:text-white'}`}
                                >
                                    Interviews
                                </button>
                                <button
                                    onClick={() => setGraphType('resumes')}
                                    className={`text-xs px-2 py-1 rounded transition-all ${graphType === 'resumes' ? 'bg-teal-500/10 text-[#20C997] border border-[#20C997]/20 font-bold' : 'text-gray-500 hover:text-white'}`}
                                >
                                    Resume
                                </button>
                            </div>
                        </div>
                        <div className="h-64 flex items-end justify-between gap-2 px-2 pb-2 border-b border-white/5 relative flex-1 overflow-hidden">
                            {loading ? (
                                <Skeleton className="absolute inset-0 m-4" />
                            ) : graphData.length > 0 ? (
                                graphData.map((item, idx) => {
                                    const maxScore = graphType === 'resumes' ? 100 : 10;
                                    const heightPerc = Math.min((item.overall_score / maxScore) * 100, 100);
                                    const dateLabel = new Date(item.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                                    return (
                                        <div
                                            key={idx}
                                            className="flex-1 max-w-[40px] bg-gradient-to-t from-[#20C997]/10 to-[#20C997]/40 hover:to-[#20C997]/60 rounded-t-sm transition-all relative group cursor-pointer"
                                            style={{ height: `${heightPerc}%` }}
                                        >
                                            <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-black/80 border border-white/10 text-white text-[10px] p-2 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                                Score: {item.overall_score}/{maxScore}<br />
                                                {dateLabel}
                                            </div>
                                        </div>
                                    );
                                })
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-gray-500 text-sm italic">
                                    No data recorded yet.
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right: Actions */}
                <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-white mb-6">Recommended Actions</h3>
                    <div className="space-y-4">
                        <div className="p-4 bg-white/5 rounded-xl border border-white/5 hover:border-[#20C997]/50 hover:bg-white/10 transition-all cursor-pointer group">
                            <div className="flex justify-between items-start">
                                <h4 className="font-semibold text-white group-hover:text-[#20C997]">Optimize Resume</h4>
                                <span className="text-xs bg-[#20C997] text-black font-bold px-2 py-0.5 rounded">High Impact</span>
                            </div>
                            <p className="text-sm text-gray-400 mt-1">Check your latest score.</p>
                        </div>
                        <div className="p-4 bg-white/5 rounded-xl border border-white/5 hover:border-[#20C997]/50 hover:bg-white/10 transition-all cursor-pointer group">
                            <div className="flex justify-between items-start">
                                <h4 className="font-semibold text-white group-hover:text-[#20C997]">Mock Interview</h4>
                            </div>
                            <p className="text-sm text-gray-400 mt-1">Practice makes perfect.</p>
                        </div>
                    </div>
                    <button className="w-full mt-6 py-3 bg-[#20C997] text-black font-bold rounded-xl hover:bg-[#1aa179] transition-colors">
                        Start New Session
                    </button>
                </div>
            </div>

            {/* 3. Recent Activity */}
            <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6">
                <h3 className="text-lg font-bold text-white mb-6">Recent Activity</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-white/5 text-gray-500 text-sm">
                                <th className="pb-3 font-medium">Project Name</th>
                                <th className="pb-3 font-medium">Type</th>
                                <th className="pb-3 font-medium">Score</th>
                                <th className="pb-3 font-medium">Date</th>
                                <th className="pb-3 font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {loading ? (
                                [1, 2, 3].map(i => (
                                    <tr key={i}>
                                        <td className="py-4"><Skeleton className="w-32 h-4" /></td>
                                        <td className="py-4"><Skeleton className="w-20 h-4" /></td>
                                        <td className="py-4"><Skeleton className="w-10 h-4" /></td>
                                        <td className="py-4"><Skeleton className="w-20 h-4" /></td>
                                        <td className="py-4"><Skeleton className="w-16 h-4" /></td>
                                    </tr>
                                ))
                            ) : recentActivity.length === 0 ? (
                                <tr><td colSpan="5" className="py-4 text-center text-gray-500">No activity found.</td></tr>
                            ) : (
                                recentActivity.map((a, i) => (
                                    <tr key={i} className="group hover:bg-white/5 transition-colors">
                                        <td className="py-4 font-medium text-white">{a.project_name || 'Untitled'}</td>
                                        <td className="py-4 text-gray-400">{a.type}</td>
                                        <td className="py-4 text-white font-bold">{a.score || '-'}</td>
                                        <td className="py-4 text-gray-500">{timeAgo(a.created_at)}</td>
                                        <td className="py-4"><span className="px-2 py-1 rounded text-xs font-bold bg-[#20C997]/20 text-[#20C997]">{a.status || 'Completed'}</span></td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </>
        ) : (
            <CareerHub />
        )}

        </div>
    );
};

export default Dashboard;

