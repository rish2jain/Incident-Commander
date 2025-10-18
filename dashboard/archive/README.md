# Archived Dashboard Components

This directory contains the original dashboard components that have been replaced by the new refined React-based dashboard.

## Archived Files

### HTML/JavaScript Dashboard

- `enhanced_live_dashboard.html` - Original enhanced HTML dashboard with WebSocket integration
- `live_dashboard.html` - Basic live dashboard implementation
- `index.html` - Simple dashboard index page
- `dashboard.js` - JavaScript functionality for HTML dashboards

### Python Servers

- `server.py` - Original Flask/FastAPI server for dashboard
- `simple_server.py` - Simplified server implementation

## Migration Notes

The original HTML/JavaScript dashboard has been replaced with a modern React-based solution that provides:

### Improvements Made

1. **Modern Framework**: Migrated from vanilla HTML/JS to Next.js + React
2. **Component Architecture**: Modular, reusable components
3. **Type Safety**: Full TypeScript implementation
4. **Enhanced UI**: Glassmorphism effects, smooth animations
5. **Better Performance**: Optimized rendering and state management
6. **Accessibility**: WCAG compliant components
7. **Responsive Design**: Mobile-first approach
8. **Developer Experience**: Hot reload, type checking, linting

### Key Differences

| Feature          | Original                | New Refined                  |
| ---------------- | ----------------------- | ---------------------------- |
| Framework        | Vanilla HTML/JS         | Next.js + React              |
| Styling          | Custom CSS              | Tailwind CSS + Framer Motion |
| Type Safety      | None                    | Full TypeScript              |
| Components       | Monolithic              | Modular components           |
| State Management | Manual DOM manipulation | React state + hooks          |
| Build Process    | None                    | Next.js build system         |
| Development      | Manual refresh          | Hot reload                   |
| Testing          | None                    | Jest + Testing Library ready |

### Functionality Preserved

- Real-time WebSocket integration
- Agent activity feed
- Metrics display
- Incident management
- Scenario triggering
- Status indicators

### New Features Added

- Enhanced animations and transitions
- Improved accessibility
- Better mobile responsiveness
- Component-based architecture
- Theme support (dark/light)
- Better error handling
- Performance optimizations

## Usage of Archived Components

If you need to reference the original implementation:

1. **HTML Dashboard**: Open `enhanced_live_dashboard.html` in a browser
2. **Server**: Run `python server.py` to start the original server
3. **Styling**: Reference the CSS in the HTML files for original styling

## Migration Path

To migrate custom features from the archived components:

1. **Extract Logic**: Copy JavaScript functions from archived files
2. **Convert to React**: Transform DOM manipulation to React components
3. **Add Types**: Add TypeScript interfaces for data structures
4. **Style with Tailwind**: Convert CSS to Tailwind classes
5. **Add Animations**: Use Framer Motion for smooth transitions

## Backup Information

These files are kept for:

- **Reference**: Understanding original implementation
- **Rollback**: Emergency fallback if needed
- **Learning**: Comparing old vs new approaches
- **Migration**: Extracting any missed functionality

## Restoration

To temporarily restore the original dashboard:

```bash
# Copy archived files back to main dashboard directory
cp dashboard/archive/enhanced_live_dashboard.html dashboard/
cp dashboard/archive/server.py dashboard/

# Start the original server
cd dashboard
python server.py
```

**Note**: The original dashboard may not be compatible with the latest backend API changes. Use only for reference or emergency situations.
