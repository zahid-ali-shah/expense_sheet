// Theme variables that we'll manage
const THEME_VARIABLES = [
    'primary-color',
    'secondary-color',
    'accent-color',
    'background-color',
    'error-color',
    'surface-color',
    'on-primary-color',
    'on-secondary-color'
];

class ThemeSwitcher {
    constructor() {
        this.themeDropdown = document.getElementById('theme-dropdown');
        this.init();
    }

    init() {
        this.loadUserTheme();
        this.setupEventListeners();
        this.setupThemeObserver();
    }

    setupEventListeners() {
        // Theme dropdown change handler
        if (this.themeDropdown) {
            this.themeDropdown.addEventListener('change', (e) => this.handleThemeChange(e));
        }

        // Add preview on hover functionality
        if (this.themeDropdown) {
            this.themeDropdown.addEventListener('mouseover', (e) => {
                if (e.target.tagName === 'OPTION') {
                    this.previewTheme(e.target.value);
                }
            });

            this.themeDropdown.addEventListener('mouseout', () => {
                this.loadUserTheme(); // Restore current theme
            });
        }
    }

    setupThemeObserver() {
        // Observer to handle dynamic theme changes
        const targetNode = document.documentElement;
        const config = { attributes: true, attributeFilter: ['style'] };
        
        const callback = (mutationList) => {
            for (const mutation of mutationList) {
                if (mutation.type === 'attributes') {
                    this.updateThemedElements();
                }
            }
        };

        const observer = new MutationObserver(callback);
        observer.observe(targetNode, config);
    }

    async loadUserTheme() {
        try {
            const response = await fetch('/api/theme/');
            if (!response.ok) throw new Error('Failed to load theme');
            
            const theme = await response.json();
            this.setTheme(theme);
            this.selectCurrentTheme(theme.name);
            this.showThemeLoadedNotification(theme.name);
        } catch (error) {
            console.error('Error loading theme:', error);
            this.showThemeError('Failed to load theme');
        }
    }

    setTheme(theme) {
        // Set all theme variables
        THEME_VARIABLES.forEach(variable => {
            const value = theme[variable.replace(/-/g, '_')] || '';
            document.documentElement.style.setProperty(`--${variable}`, value);
        });

        // Update meta theme-color for mobile browsers
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme.primary_color);
        }

        this.updateThemedElements();
    }

    updateThemedElements() {
        // Update elements that need special handling with theme changes
        // For example, updating charts, canvas elements, or third-party components
        document.dispatchEvent(new CustomEvent('themeChanged', {
            detail: {
                primaryColor: getComputedStyle(document.documentElement)
                    .getPropertyValue('--primary-color').trim()
            }
        }));
    }

    async handleThemeChange(event) {
        const themeId = event.target.value;
        const themeName = event.target.options[event.target.selectedIndex].text;

        try {
            const response = await fetch(`/api/theme/${themeId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) throw new Error('Failed to set theme');

            await this.loadUserTheme();
            this.showThemeChangedNotification(themeName);
        } catch (error) {
            console.error('Error changing theme:', error);
            this.showThemeError('Failed to change theme');
            // Revert dropdown to previous selection
            this.loadUserTheme();
        }
    }

    async previewTheme(themeId) {
        try {
            const response = await fetch(`/api/theme/${themeId}/`);
            if (!response.ok) throw new Error('Failed to load theme preview');
            
            const theme = await response.json();
            this.setTheme(theme);
        } catch (error) {
            console.error('Error previewing theme:', error);
        }
    }

    selectCurrentTheme(themeName) {
        if (!this.themeDropdown) return;

        for (let i = 0; i < this.themeDropdown.options.length; i++) {
            if (this.themeDropdown.options[i].text === themeName) {
                this.themeDropdown.selectedIndex = i;
                break;
            }
        }
    }

    showThemeChangedNotification(themeName) {
        this.showNotification(`Theme changed to ${themeName}`, 'success');
    }

    showThemeLoadedNotification(themeName) {
        this.showNotification(`Theme ${themeName} loaded`, 'info');
    }

    showThemeError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Create or get existing snackbar
        let snackbar = document.getElementById('theme-snackbar');
        if (!snackbar) {
            snackbar = document.createElement('div');
            snackbar.id = 'theme-snackbar';
            document.body.appendChild(snackbar);
        }

        // Set appropriate class based on type
        snackbar.className = `snackbar ${type}`;
        snackbar.textContent = message;

        // Show snackbar
        snackbar.classList.add('show');

        // Hide after 3 seconds
        setTimeout(() => {
            snackbar.classList.remove('show');
        }, 3000);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }
}

// Initialize theme switcher when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeSwitcher = new ThemeSwitcher();
});