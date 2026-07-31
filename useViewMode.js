import { useState, useEffect } from 'react';

export function useViewMode() {
    const STORAGE_KEY = 'tpi_dashboard_view_mode';
    const [viewMode, setViewMode] = useState('command-center'); // Default fallback

    // 1. Detect screen width on initial mount
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved === 'career-hub' || saved === 'command-center') {
            setViewMode(saved);
        } else {
            const defaultMode = window.innerWidth < 768 ? 'career-hub' : 'command-center';
            setViewMode(defaultMode);
        }
    }, []);

    // 2. Manual toggle handler (updates state and localStorage)
    const toggleViewMode = (mode) => {
        if (mode === 'career-hub' || mode === 'command-center') {
            setViewMode(mode);
            localStorage.setItem(STORAGE_KEY, mode);
        }
    };

    // 3. Handle window resize (only overwrites if NO explicit user selection exists)
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const handleResize = () => {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (!saved) {
                const currentMode = window.innerWidth < 768 ? 'career-hub' : 'command-center';
                setViewMode(currentMode);
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return [viewMode, toggleViewMode];
}
