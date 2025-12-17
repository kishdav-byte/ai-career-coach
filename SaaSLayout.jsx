import React, { useState } from 'react';
import {
    LayoutGrid,
    FileText,
    Mic,
    Crosshair,
    LogOut,
    Menu,
    X
} from 'lucide-react';

const SaaSLayout = ({ children, user = { name: 'David Kish', initials: 'DK' } }) => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [currentPath, setCurrentPath] = useState(window.location.pathname);

    const navItems = [
        { name: 'Dashboard', icon: LayoutGrid, link: '/dashboard' },
        { name: 'The Clinic', icon: FileText, link: '/clinic' },
        { name: 'The Simulator', icon: Mic, link: '/simulator' },
        { name: 'Strategy', icon: Crosshair, link: '/strategy' },
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
                className={`fixed inset-y-0 left-0 w-[250px] bg-slate-900 border-r border-white/5 flex flex-col transition-transform duration-300 ease-in-out z-40 
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 lg:static`}
            >

                {/* Logo Area */}
                <div className="h-20 flex items-center px-8 mt-4 lg:mt-0">
                    <h1 className="font-bold text-xl tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                        AI Career Coach
                    </h1>
                </div>

                {/* Navigation Stack */}
                <nav className="flex-1 px-4 space-y-2 mt-4">
                    {navItems.map((item) => {
                        const isActive = currentPath === item.link;
                        const Icon = item.icon;

                        return (
                            <a
                                key={item.name}
                                href={item.link}
                                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all relative group
                  ${isActive
                                        ? 'bg-teal-500/10 text-[#20C997]'
                                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                {/* Active Indicator Strip */}
                                {isActive && (
                                    <div className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 bg-[#20C997] rounded-r-full shadow-[0_0_10px_rgba(32,201,151,0.5)]"></div>
                                )}

                                <Icon size={20} className={isActive ? 'text-[#20C997]' : 'text-slate-500 group-hover:text-white'} />
                                <span>{item.name}</span>
                            </a>
                        );
                    })}
                </nav>

                {/* Footer / User Profile */}
                <div className="p-4 border-t border-white/5 mt-auto"> {/* Added mt-auto to pin to bottom if flex-1 doesn't push enough, but flex-1 on nav should work */}
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

            {/* Main Content Wrapper */}
            <div className="flex-1 flex flex-col min-w-0 lg:ml-0 overflow-hidden">
                {/* Top Spacer for Mobile Header */}
                <div className="h-16 lg:hidden"></div>

                {/* Scrollable Content Area */}
                <main className="flex-1 overflow-y-auto p-4 lg:p-8">
                    {children}
                </main>
            </div>

            {/* Overlay for Mobile Sidebar */}
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
