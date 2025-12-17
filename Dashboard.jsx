import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';

const Dashboard = () => {
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
                const { count: jobCount } = await supabase.from('job_tracker')
                    .select('*', { count: 'exact', head: true })
                    .eq('user_id', user.id)
                    .eq('is_active', true);

                // 3. Get Plan Details
                const { data: profile } = await supabase.from('profiles')
                    .select('plan_tier, credits_remaining')
                    .eq('id', user.id)
                    .single();

                // 4. Get Interview Avg (Last 30 days)
                const { data: interviews } = await supabase.from('interviews')
                    .select('overall_score, created_at')
                    .eq('user_id', user.id)
                    .gte('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString());

                // --- ADDITIONAL DATA FOR UI (Graph & Activity) to prevent blank sections ---
                const { data: graph } = await supabase.from('interviews')
                    .select('created_at, overall_score')
                    .eq('user_id', user.id)
                    .order('created_at', { ascending: true })
                    .limit(7);

                const { data: activity } = await supabase.from('user_recent_activity')
                    .select('*')
                    .eq('user_id', user.id)
                    .limit(5);

                // UPDATE STATE
                setStats({
                    resumeScore: resumes?.[0]?.overall_score || 0,
                    activeJobs: jobCount || 0,
                    credits: profile?.credits_remaining || 0,
                    plan: profile?.plan_tier || 'Free',
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
    }, []);

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
            <header className="flex justify-between items-center mb-10 max-w-7xl mx-auto">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                    Executive Performance Hub
                </h1>
                <div className="flex items-center gap-4">
                    {loading ? <Skeleton className="w-24 h-4" /> : <span className="text-sm text-gray-400">{userProfile.name}</span>}
                    <div className="w-10 h-10 rounded-full bg-teal-500/20 flex items-center justify-center text-[#20C997] font-bold border border-[#20C997]/30">
                        {userProfile.initials}
                    </div>
                </div>
            </header>

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
                                <div className="bg-[#20C997] h-full rounded-full" style={{ width: `${Math.min(stats.credits, 100)}%` }}></div>
                            </div>
                        )}
                        {loading ? (
                            <div className="flex justify-between w-full"><Skeleton className="w-10 h-4" /><Skeleton className="w-10 h-4" /></div>
                        ) : (
                            <div className="flex justify-between w-full text-sm">
                                <span className="text-white font-bold">{stats.credits} Credits</span>
                                <span className="text-gray-500">Left</span>
                            </div>
                        )}
                    </div>

                </div>

                {/* 2. Main Content Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Left: Trend Graph */}
                    <div className="lg:col-span-2 bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white">Performance Trend (Last 7 Sessions)</h3>
                        </div>
                        <div className="h-64 flex items-end justify-between gap-2 px-2 pb-2 border-b border-white/5 relative flex-1">
                            {loading ? (
                                <div className="w-full h-full flex items-end gap-2">
                                    {[1, 2, 3, 4, 5, 6, 7].map(i => <Skeleton key={i} className="w-full h-[50%]" />)}
                                </div>
                            ) : graphData.length === 0 ? (
                                <div className="w-full h-full flex items-center justify-center text-gray-500">
                                    No Data Yet
                                </div>
                            ) : (
                                graphData.map((item, i) => {
                                    const height = `${Math.min((item.overall_score || 0) * 10, 100)}%`;
                                    const dateLabel = new Date(item.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                                    return (
                                        <div key={i} className="w-full flex flex-col justify-end items-center gap-2 h-full group">
                                            <div className="w-full bg-[#20C997]/20 hover:bg-[#20C997]/40 rounded-t-sm transition-all relative flex flex-col justify-end" style={{ height: '100%' }}>
                                                <div style={{ height: height }} className="bg-[#20C997] w-full relative group-hover:bg-[#1aa179] transition-colors rounded-t-sm">
                                                    <div className="opacity-0 group-hover:opacity-100 absolute -top-10 left-1/2 -translate-x-1/2 bg-black border border-white/10 text-white text-xs p-2 rounded whitespace-nowrap z-10 pointer-events-none transition-opacity">
                                                        Score: {item.overall_score}/10<br />{dateLabel}
                                                    </div>
                                                </div>
                                            </div>
                                            <span className="text-[10px] text-gray-500">{dateLabel}</span>
                                        </div>
                                    )
                                })
                            )}
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
                </div>

            </div>
        </div>
    );
};

export default Dashboard;

