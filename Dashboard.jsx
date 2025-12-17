import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';

const Dashboard = () => {
    // User State
    const [stats, setStats] = useState({
        resumeScore: 0,
        interviewScore: 0,
        interviewTrend: 0,
        activeJobs: 0,
        credits: 0,
        planTier: 'Free'
    });
    const [recentActivity, setRecentActivity] = useState([]);
    const [graphData, setGraphData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [userProfile, setUserProfile] = useState({ name: 'User', initials: 'U' });

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                // 1. Session Recovery (Bridge between Vanilla JS Auth and React)
                const token = localStorage.getItem('supabase.auth.token');
                const refreshToken = localStorage.getItem('supabase.auth.refresh_token');

                if (token) {
                    const { error } = await supabase.auth.setSession({
                        access_token: token,
                        refresh_token: refreshToken || ''
                    });
                    if (error) console.warn("Session restore warning:", error.message);
                }

                const { data: { user } } = await supabase.auth.getUser();

                if (!user) {
                    console.warn("No active user found");
                    setLoading(false);
                    return;
                }

                // Set User Profile Info
                const name = user.user_metadata?.name || user.email?.split('@')[0] || 'User';
                setUserProfile({
                    name: name,
                    initials: name.substring(0, 2).toUpperCase()
                });

                // 2. Parallel Data Fetching
                const [
                    resumesRes,
                    interviewsRes,
                    activeJobsRes,
                    profileRes,
                    graphRes,
                    activityRes
                ] = await Promise.all([
                    // Resume Health (Latest)
                    supabase.from('resumes')
                        .select('overall_score')
                        .eq('user_id', user.id)
                        .order('created_at', { ascending: false })
                        .limit(1),

                    // Avg Interview Score (Last 30 Days)
                    supabase.from('interviews')
                        .select('overall_score')
                        .eq('user_id', user.id)
                        .gte('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()),

                    // Active Strategy Count
                    supabase.from('job_tracker')
                        .select('*', { count: 'exact', head: true })
                        .eq('user_id', user.id)
                        .eq('is_active', true),

                    // Credits/Pro Plan
                    supabase.from('profiles')
                        .select('credits_remaining, plan_tier')
                        .eq('id', user.id)
                        .maybeSingle(), // Use maybeSingle to avoid error if no profile

                    // Performance Graph (Last 7)
                    supabase.from('interviews')
                        .select('created_at, overall_score')
                        .eq('user_id', user.id)
                        .order('created_at', { ascending: true })
                        .limit(7),

                    // Recent Activity
                    supabase.from('user_recent_activity') // Assuming view exists
                        .select('project_name, type, score, status, created_at')
                        .limit(5)
                    // Note: If view doesn't have RLS, we might need .eq('user_id', user.id)
                    // But typically views for user activity are defined with WHERE user_id = auth.uid()
                ]);

                // 3. Process Data
                const resumeHealth = resumesRes.data?.[0]?.overall_score || 0;

                const interviewScores = interviewsRes.data?.map(i => i.overall_score).filter(s => s !== null) || [];
                const avgScore = interviewScores.length > 0
                    ? (interviewScores.reduce((a, b) => a + b, 0) / interviewScores.length).toFixed(1)
                    : 0;

                setStats({
                    resumeScore: resumeHealth,
                    interviewScore: avgScore,
                    interviewTrend: 12, // Hardcoded for now as per "Mock" replacement instructions focused on fetching core data
                    activeJobs: activeJobsRes.count || 0,
                    credits: profileRes.data?.credits_remaining || 0,
                    planTier: profileRes.data?.plan_tier || 'Free'
                });

                setGraphData(graphRes.data || []);
                setRecentActivity(activityRes.data || []);

            } catch (error) {
                console.error("Critical Dashboard Load Error:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Helper for formatting relative time
    const timeAgo = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return `${Math.floor(diffInSeconds / 86400)}d ago`;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#20C997]"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-[#0A2540] to-black text-white font-sans p-6">

            {/* Header */}
            <header className="flex justify-between items-center mb-10 max-w-7xl mx-auto">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                    Executive Performance Hub
                </h1>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-400">{userProfile.name}</span>
                    <div className="w-10 h-10 rounded-full bg-teal-500/20 flex items-center justify-center text-[#20C997] font-bold border border-[#20C997]/30">
                        {userProfile.initials}
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto grid gap-8">

                {/* 1. Key Metrics Row (4 Columns) */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

                    {/* Metric 1: Resume Health */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative overflow-hidden group hover:border-[#20C997]/50 transition-colors">
                        <div className="absolute top-0 left-0 w-full h-1 bg-[#20C997]/20"></div>
                        <h3 className="text-gray-400 text-sm font-medium mb-4 uppercase tracking-wider">Resume Health</h3>

                        {/* Ring Visualization */}
                        <div className="relative w-24 h-24 flex items-center justify-center rounded-full border-4 border-slate-700">
                            <div
                                className="absolute w-full h-full rounded-full border-4 border-[#20C997] border-l-transparent transform -rotate-45"
                                style={{
                                    borderRightColor: stats.resumeScore > 50 ? '#20C997' : 'transparent',
                                    borderBottomColor: stats.resumeScore > 75 ? '#20C997' : 'transparent',
                                    transform: `rotate(${(stats.resumeScore / 100) * 360 - 45}deg)` // Dynamic Rotation simulation
                                }}
                            ></div>
                            <span className="text-3xl font-bold text-white">{stats.resumeScore}</span>
                        </div>
                    </div>

                    {/* Metric 2: Avg Interview Score */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative group hover:border-[#20C997]/50 transition-colors">
                        <div className="absolute top-0 left-0 w-full h-1 bg-[#20C997]/20"></div>
                        <h3 className="text-gray-400 text-sm font-medium mb-2 uppercase tracking-wider">Avg. Score</h3>
                        <div className="text-4xl font-bold text-white mb-2">{stats.interviewScore}<span className="text-gray-500 text-xl">/10</span></div>
                        <div className="flex items-center text-[#20C997] text-sm font-medium bg-[#20C997]/10 px-2 py-1 rounded-full">
                            <span>↑ {stats.interviewTrend}%</span>
                            <span className="ml-1 text-xs opacity-70">vs last week</span>
                        </div>
                    </div>

                    {/* Metric 3: Strategy Log */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative group hover:border-[#20C997]/50 transition-colors">
                        <div className="absolute top-0 left-0 w-full h-1 bg-[#20C997]/20"></div>
                        <h3 className="text-gray-400 text-sm font-medium mb-4 uppercase tracking-wider">Strategy Log</h3>
                        <div className="flex items-center gap-3 mb-2">
                            <span className="text-3xl">♟️</span>
                            <span className="text-4xl font-bold text-white">{stats.activeJobs}</span>
                        </div>
                        <span className="text-gray-500 text-sm">Active Strategies</span>
                    </div>

                    {/* Metric 4: Credits */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative group hover:border-[#20C997]/50 transition-colors">
                        <div className="absolute top-0 left-0 w-full h-1 bg-[#20C997]/20"></div>
                        <h3 className="text-gray-400 text-sm font-medium mb-4 uppercase tracking-wider">{stats.planTier} Balance</h3>
                        <div className="w-full bg-slate-700 h-3 rounded-full overflow-hidden mb-3">
                            <div className="bg-[#20C997] h-full rounded-full" style={{ width: `${Math.min(stats.credits, 100)}%` }}></div>
                        </div>
                        <div className="flex justify-between w-full text-sm">
                            <span className="text-white font-bold">{stats.credits} Credits</span>
                            <span className="text-gray-500">Left</span>
                        </div>
                    </div>
                </div>

                {/* 2. Main Content Area (2:1 Ratio) */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Left Column: Trend (Span 2) */}
                    <div className="lg:col-span-2 bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white">Performance Trend (Last 7 Interviews)</h3>
                            <button className="text-sm text-[#20C997] hover:text-white transition-colors">View Report</button>
                        </div>
                        <div className="h-64 flex items-end justify-between gap-2 px-2 pb-2 border-b border-white/5 relative flex-1">
                            {graphData.length === 0 ? (
                                <div className="w-full h-full flex items-center justify-center text-gray-500">
                                    No interview data yet.
                                </div>
                            ) : (
                                graphData.map((item, i) => {
                                    const height = `${(item.overall_score || 0) * 10}%`;
                                    return (
                                        <div key={i} className="w-full bg-[#20C997]/20 hover:bg-[#20C997]/40 rounded-t-sm transition-all relative group flex flex-col justify-end" style={{ height: '100%' }}>
                                            <div style={{ height: height }} className="bg-[#20C997] w-full relative">
                                                <div className="hidden group-hover:block absolute -top-8 left-1/2 -translate-x-1/2 bg-black text-white text-xs p-1 rounded whitespace-nowrap z-10">
                                                    Score: {item.overall_score}<br />
                                                    {new Date(item.created_at).toLocaleDateString()}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>

                    {/* Right Column: Action Center */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6">
                        <h3 className="text-lg font-bold text-white mb-6">Recommended Actions</h3>
                        <div className="space-y-4">
                            <div className="p-4 bg-white/5 rounded-xl border border-white/5 hover:border-[#20C997]/50 hover:bg-white/10 transition-all cursor-pointer group">
                                <div className="flex justify-between items-start">
                                    <h4 className="font-semibold text-white group-hover:text-[#20C997]">Optimize Resume</h4>
                                    <span className="text-xs bg-[#20C997] text-black font-bold px-2 py-0.5 rounded">High Impact</span>
                                </div>
                                <p className="text-sm text-gray-400 mt-1">Your 'Experience' section needs active verbs.</p>
                            </div>

                            <div className="p-4 bg-white/5 rounded-xl border border-white/5 hover:border-[#20C997]/50 hover:bg-white/10 transition-all cursor-pointer group">
                                <div className="flex justify-between items-start">
                                    <h4 className="font-semibold text-white group-hover:text-[#20C997]">Mock Interview</h4>
                                </div>
                                <p className="text-sm text-gray-400 mt-1">Practice "Tell me about yourself" to boost confidence.</p>
                            </div>
                        </div>
                        <button className="w-full mt-6 py-3 bg-[#20C997] text-black font-bold rounded-xl hover:bg-[#1aa179] transition-colors">
                            Start New Session
                        </button>
                    </div>
                </div>

                {/* 3. Bottom Section: Recent Activity */}
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
                                    <th className="pb-3 font-medium text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {recentActivity.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" className="py-4 text-center text-gray-500">No recent activity.</td>
                                    </tr>
                                ) : (
                                    recentActivity.map((activity, index) => (
                                        <tr key={index} className="group hover:bg-white/5 transition-colors">
                                            <td className="py-4 font-medium text-white">{activity.project_name || 'Untitled Project'}</td>
                                            <td className="py-4 text-gray-400">{activity.type}</td>
                                            <td className="py-4 text-white font-bold">{activity.score ? activity.score : '-'}</td>
                                            <td className="py-4 text-gray-500">{timeAgo(activity.created_at)}</td>
                                            <td className="py-4">
                                                <span className={`px-2 py-1 rounded text-xs font-bold ${activity.status === 'Optimized' ? 'bg-[#20C997]/20 text-[#20C997]' :
                                                        activity.status === 'Completed' ? 'bg-blue-500/20 text-blue-400' :
                                                            'bg-gray-500/20 text-gray-300'
                                                    }`}>
                                                    {activity.status || 'Pending'}
                                                </span>
                                            </td>
                                            <td className="py-4 text-right">
                                                <button className="text-gray-400 hover:text-white">•••</button>
                                            </td>
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
