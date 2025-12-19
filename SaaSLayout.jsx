import React, { useState, useEffect } from 'react';
import {
    LayoutGrid,
    FileText,
    Mic,
    Crosshair,
    LogOut,
    Menu,
    X,
    ChevronDown,
    ChevronRight
} from 'lucide-react';

const SaaSLayout = ({ children, user = { name: 'David Kish', initials: 'DK' } }) => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [currentPath, setCurrentPath] = useState('');
    const [expandedCategories, setExpandedCategories] = useState(new Set(['The Clinic', 'The Simulator', 'Strategy']));

    useEffect(() => {
        if (typeof window !== 'undefined') {
            setCurrentPath(window.location.pathname);
        }
    }, []);

    const toggleCategory = (name) => {
        setExpandedCategories(prev => {
            const next = new Set(prev);
            if (next.has(name)) next.delete(name);
            else next.add(name);
            return next;
        });
    };

    const navItems = [
        { name: 'Dashboard', path: '/dashboard.html', icon: LayoutGrid },
        {
            name: 'The Clinic',
            icon: FileText,
            submenu: [
                { name: 'Resume Scanner', path: '/resume-analyzer.html' },
                { name: 'Executive Rewrite', path: '/resume-rewriter.html' },
                { name: 'LinkedIn Optimizer', path: '/app.html#linkedin' }
            ]
        },
        {
            name: 'The Simulator',
            icon: Mic,
            submenu: [
                { name: 'Mock Interview', path: '/app.html#interview' },
                { name: 'Role Reversal', path: '/role-reversal.html' },
                { name: 'STAR Method Drill', path: '/role-reversal.html' }
            ]
        },
        {
            name: 'Strategy',
            icon: Crosshair,
            submenu: [
                { name: 'Job Tracker', path: '/strategy/strategy-log.html' },
                { name: '30-60-90 Plan', path: '/strategy/30-60-90.html' },
                { name: 'Salary Negotiation', path: '/strategy/closer.html' }
            ]
        },
        {
            name: 'Upgrade Hub',
            isHeader: true,
            submenu: [
                { name: 'Go Unlimited', path: '/pricing.html#unlimited-plan', isSpecial: true },
                { name: 'Add Credits', path: '/pricing.html#credits-bundle' }
            ]
        }
    ];

    return (
        <div className="min-h-screen bg-slate-950 flex font-sans text-white">

            {/* Mobile Header */}
            <div className="lg:hidden fixed top-0 left-0 w-full h-16 bg-slate-900 border-b border-white/5 flex items-center justify-between px-4 z-50">
                <div className="font-bold text-lg tracking-tight">AI Career Coach</div>
                <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-gray-400 hover:text-white">
                    {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            {/* Sidebar */}
            <aside
                className={`fixed inset-y-0 left-0 w-[260px] bg-slate-900 border-r border-white/5 flex flex-col transition-transform duration-300 ease-in-out z-40 
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 lg:static`}
            >
                {/* Logo */}
                <div className="h-20 flex items-center px-6 mt-4 lg:mt-0">
                    <h1 className="font-bold text-xl tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                        AI Career Coach
                    </h1>
                </div>

                {/* Nav Items */}
                <nav className="flex-1 px-4 space-y-1 mt-4 overflow-y-auto custom-scrollbar">
                    {navItems.map((item, index) => {
                        const Icon = item.icon;

                        // 3. Header Section (e.g., Upgrade Hub)
                        if (item.isHeader) {
                            return (
                                <div key={index} className="pt-4 mt-4 border-t border-white/5">
                                    <div className="px-3 py-2 text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">
                                        {item.name}
                                    </div>
                                    <div className="space-y-1">
                                        {item.submenu.map((sub, subIndex) => (
                                            <a
                                                key={subIndex}
                                                href={sub.path}
                                                className={`w-full flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg transition-all group
                          ${sub.isSpecial ? 'bg-teal-500/10 text-[#20C997] font-bold border border-[#20C997]/20' : 'text-slate-400 hover:text-white hover:bg-white/5 font-medium'}`}
                                            >
                                                <span>{sub.name}</span>
                                            </a>
                                        ))}
                                    </div>
                                </div>
                            );
                        }

                        // 1. Leaf Node (No Submenu)
                        if (!item.submenu) {
                            const isActive = currentPath === item.path;
                            return (
                                <a
                                    key={index}
                                    href={item.path}
                                    className={`w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-lg transition-all relative group mb-1
                  ${isActive ? 'bg-teal-500/10 text-[#20C997]' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                                >
                                    <Icon size={18} className={isActive ? 'text-[#20C997]' : 'text-slate-500 group-hover:text-white'} />
                                    <span>{item.name}</span>
                                    {isActive && <div className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 bg-[#20C997] rounded-r-full"></div>}
                                </a>
                            );
                        }

                        // 2. Accordion (Has Submenu)
                        const isExpanded = expandedCategories.has(item.name);
                        return (
                            <div key={index} className="mb-2">
                                <button
                                    onClick={() => toggleCategory(item.name)}
                                    className="w-full flex items-center justify-between px-3 py-2.5 text-sm font-bold text-white rounded-lg hover:bg-white/5 transition-colors group"
                                >
                                    <div className="flex items-center gap-3">
                                        <Icon size={18} className="text-slate-500 group-hover:text-white" />
                                        <span>{item.name}</span>
                                    </div>
                                    {isExpanded ? <ChevronDown size={14} className="text-slate-500" /> : <ChevronRight size={14} className="text-slate-500" />}
                                </button>

                                {isExpanded && (
                                    <div className="ml-4 mt-1 space-y-0.5 border-l border-white/5 pl-2">
                                        {item.submenu.map((sub, subIndex) => {
                                            const isSubActive = currentPath === sub.path;
                                            return (
                                                <a
                                                    key={subIndex}
                                                    href={sub.path}
                                                    className={`block px-3 py-2 text-sm rounded-md transition-all relative
                          ${isSubActive ? 'text-[#20C997] bg-[#20C997]/5' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                                                >
                                                    {isSubActive && (
                                                        <div className="absolute -left-[9px] top-1/2 -translate-y-1/2 w-1 h-4 bg-[#20C997] rounded-full shadow-[0_0_8px_#20C997]"></div>
                                                    )}
                                                    {sub.name}
                                                </a>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </nav>

                {/* User Profile */}
                <div className="p-4 border-t border-white/5 mt-auto">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer group">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-teal-500/20 flex items-center justify-center text-[#20C997] text-xs font-bold border border-[#20C997]/30">
                                {user.initials}
                            </div>
                            <div className="flex flex-col">
                                <span className="text-sm font-medium text-white group-hover:text-[#20C997] transition-colors">{user.name}</span>
                                <span className="text-xs text-gray-500">Free Plan</span>
                            </div>
                        </div>
                        <button className="text-gray-500 hover:text-white transition-colors">
                            <LogOut size={16} />
                        </button>
                    </div>
                </div>

            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 lg:ml-0 overflow-hidden">
                <div className="h-16 lg:hidden"></div>
                <main className="flex-1 overflow-y-auto p-4 lg:p-8">
                    {children}
                </main>
            </div>

            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 lg:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                ></div>
            )}

        </div>
    );
};

export default SaaSLayout;
