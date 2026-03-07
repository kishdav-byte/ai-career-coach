/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./*.html",
        "./*.js",
        "./api/*.py",
        "./js/**/*.js",
        "./strategy/**/*.html",
        "./v2/**/*.html"
    ],
    theme: {
        extend: {
            colors: {
                navy: '#0A2540',
                teal: '#20C997',
                slate: {
                    900: '#0f172a',
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            }
        },
    },
    plugins: [],
}
