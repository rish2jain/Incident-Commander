# Autonomous Incident Commander - Modern Dashboard

**Professional Next.js dashboard with TypeScript integration, glassmorphism design, and real-time WebSocket connectivity for the AWS AI Agent Hackathon.**

## 🏆 **Hackathon-Winning Features**

- **Modern Next.js Architecture**: Professional React/TypeScript implementation with latest tooling
- **Glassmorphism Design**: Modern visual effects with backdrop blur and gradient overlays
- **Framer Motion Animations**: Smooth transitions and micro-interactions for professional feel
- **Real-Time WebSocket Integration**: Dynamic protocol detection (ws/wss) with automatic reconnection
- **Professional UI Components**: 13 React components with accessibility and responsive design
- **TypeScript Integration**: Enhanced type safety with improved ref handling and performance
- **Phase 2 Enterprise Features**: Advanced data tables with filtering, pagination, and sorting
- **Audio Notification System**: 4 sound packs with accessibility features
- **Cross-Platform Compatibility**: Works seamlessly across all modern browsers and devices

## Components

### DashboardHeader

Enhanced header component with:

- Animated logo and branding
- HyperText effect for status indicators
- Real-time system status with pulse animations
- User profile dropdown with glassmorphism
- Quick action buttons for scenario triggering
- Performance metrics display

### ActivityFeed

Real-time agent activity feed featuring:

- Agent-specific color coding and icons
- Confidence bars with gradient animations
- Status indicators (pending, in-progress, completed, failed)
- Smooth slide-in animations for new items
- Detailed action information with expandable details
- Auto-scrolling with custom scrollbar styling

### MetricsPanel

Live metrics dashboard with:

- Animated number counting effects
- Trend indicators (up/down/stable)
- Percentage change calculations
- Color-coded metric categories
- Hover effects and micro-interactions
- Real-time data updates

### RefinedDashboard

Complete dashboard layout combining:

- All component integrations
- WebSocket simulation for real-time updates
- Scenario triggering system
- Incident management workflow
- Responsive grid layout
- State management for dashboard data

## Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Usage

### Basic Implementation

```tsx
import RefinedDashboard from "./components/RefinedDashboard";

export default function App() {
  return <RefinedDashboard />;
}
```

### Individual Components

```tsx
import IncidentCommanderHeader from "./components/DashboardHeader";
import ActivityFeed from "./components/ActivityFeed";
import MetricsPanel from "./components/MetricsPanel";

export default function CustomDashboard() {
  return (
    <div>
      <IncidentCommanderHeader
        systemStatus="autonomous"
        onTriggerScenario={(scenario) => console.log(scenario)}
      />
      <div className="grid grid-cols-2 gap-6 p-6">
        <ActivityFeed actions={agentActions} />
        <MetricsPanel metrics={systemMetrics} />
      </div>
    </div>
  );
}
```

## Component Props

### DashboardHeader Props

```tsx
interface IncidentCommanderHeaderProps {
  title?: string;
  subtitle?: string;
  user?: UserInfo;
  stats?: SystemStats;
  systemStatus?: "autonomous" | "monitoring" | "incident" | "maintenance";
  onTriggerScenario?: (scenario: string) => void;
}
```

### ActivityFeed Props

```tsx
interface ActivityFeedProps {
  actions: AgentAction[];
  maxItems?: number;
  showConfidence?: boolean;
  className?: string;
}
```

### MetricsPanel Props

```tsx
interface MetricsPanelProps {
  metrics: MetricData[];
  title?: string;
  className?: string;
  animated?: boolean;
}
```

## Styling

The components use Tailwind CSS with custom design tokens:

```css
:root {
  --primary-blue: #0066ff;
  --primary-green: #00d084;
  --primary-red: #ff4757;
  --surface: rgba(255, 255, 255, 0.05);
  --border: rgba(255, 255, 255, 0.1);
}
```

## Animations

Built with Framer Motion for smooth, performant animations:

- **Slide-in effects** for new activity items
- **Scale animations** on hover interactions
- **Number counting** for metric updates
- **Pulse effects** for status indicators
- **Glassmorphism** backdrop blur effects

## Real-time Integration

Components are designed to work with WebSocket connections:

```tsx
// WebSocket integration example
const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "agent_action":
      setAgentActions((prev) => [data.action, ...prev]);
      break;
    case "incident_started":
      setCurrentIncident(data.incident);
      break;
    case "metrics_update":
      setMetrics(data.metrics);
      break;
  }
};
```

## Customization

### Theme Customization

```tsx
// Custom theme provider
import { ThemeProvider } from "next-themes";

<ThemeProvider attribute="class" defaultTheme="dark">
  <RefinedDashboard />
</ThemeProvider>;
```

### Color Schemes

```tsx
// Custom agent colors
const customAgentConfig = {
  detection: {
    color: "from-red-500 to-red-600",
    bgColor: "from-red-500/10 to-red-600/10",
    // ...
  },
};
```

## Performance

- **Optimized animations** with Framer Motion
- **Virtualized scrolling** for large activity feeds
- **Memoized components** to prevent unnecessary re-renders
- **Efficient state updates** with proper React patterns
- **Lazy loading** for heavy components

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details
