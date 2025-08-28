# LLMAgentCreator Frontend

A modern Next.js 15 frontend application for creating, managing, and interacting with AI agents. Built with React 18, TypeScript, and Tailwind CSS, providing an intuitive visual interface for designing agent workflows and real-time chat interactions.

## 🚀 Features

- **Visual Agent Designer**: Drag-and-drop interface for creating agent workflows using React Flow
- **Real-time Chat Interface**: Interactive chat with AI agents with typing indicators and message history
- **User Authentication**: Secure login and registration system with JWT token management
- **Agent Management**: Create, edit, and delete AI agents with custom configurations
- **Session Management**: Track and manage conversation sessions with agents
- **Responsive Design**: Mobile-friendly interface built with Tailwind CSS
- **Type Safety**: Full TypeScript integration for better development experience
- **Modern React**: Built with React 18 and Next.js 15 App Router for optimal performance

## 🏗️ Architecture

The frontend follows a modern Next.js architecture with clear component organization:

```
frontend/
├── app/                        # Next.js 15 App Router
│   ├── agents/                # Agent management pages
│   │   ├── [id]/              # Dynamic agent routes
│   │   │   ├── chat/          # Agent chat interface
│   │   │   │   └── page.tsx   # Chat page component
│   │   │   ├── CustomNode.tsx # Custom node component for workflow
│   │   │   └── page.tsx       # Agent detail/edit page
│   │   └── create/            # Agent creation
│   │       └── page.tsx       # Agent creation form
│   ├── login/                 # Authentication pages
│   │   └── page.tsx           # Login form
│   ├── register/              # User registration
│   │   └── page.tsx           # Registration form
│   ├── globals.css            # Global styles and Tailwind imports
│   ├── layout.tsx             # Root layout component
│   └── page.tsx               # Homepage/dashboard
├── components/                 # Reusable React components
│   └── ChatWindow.tsx         # Chat interface component
├── lib/                       # Utility libraries
│   └── api.ts                 # API client and HTTP utilities
├── Dockerfile                 # Container configuration
├── next.config.ts             # Next.js configuration
├── package.json               # Dependencies and scripts
├── tailwind.config.js         # Tailwind CSS configuration
├── tsconfig.json              # TypeScript configuration
└── eslint.config.mjs          # ESLint configuration
```

## 🛠️ Technology Stack

- **Framework**: Next.js 15.5.0 with App Router for modern React development
- **UI Library**: React 18.3.1 with React DOM for component rendering
- **Language**: TypeScript 5 for type safety and better developer experience
- **Styling**: Tailwind CSS 4 for utility-first responsive design
- **Visual Editor**: React Flow Renderer 10.3.17 for drag-and-drop workflow creation
- **UI Components**: Headless UI React 2.2.7 for accessible, unstyled components
- **Utilities**: UUID 11.1.0 for generating unique identifiers
- **Build Tool**: Turbopack for fast development and builds
- **Linting**: ESLint 9 with Next.js configuration for code quality

## 📋 Prerequisites

- Node.js 18+ (recommended: Node.js 20 LTS)
- npm, yarn, or pnpm package manager
- Docker (optional, for containerized development)

## 🔧 Installation & Setup

### Option 1: Docker Development (Recommended)

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd LLMAgentCreator
   ```

2. **Start all services**:

   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Option 2: Local Development

1. **Navigate to frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   # Using npm
   npm install

   # Using yarn
   yarn install

   # Using pnpm
   pnpm install
   ```

3. **Set up environment variables** (if needed):

   ```bash
   # Create .env.local file for local environment variables
   touch .env.local
   ```

   Add any required environment variables:

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NODE_ENV=development
   NEXT_TELEMETRY_DISABLED=1
   ```

4. **Start the development server**:

   ```bash
   # Using npm
   npm run dev

   # Using yarn
   yarn dev

   # Using pnpm
   pnpm dev
   ```

5. **Access the application**:
   - Open http://localhost:3000 in your browser

## 🎨 Component Architecture

### Page Components

- **`app/page.tsx`**: Homepage/dashboard displaying user's agents
- **`app/login/page.tsx`**: User authentication form
- **`app/register/page.tsx`**: User registration form
- **`app/agents/create/page.tsx`**: Agent creation form with workflow designer
- **`app/agents/[id]/page.tsx`**: Agent detail and editing interface
- **`app/agents/[id]/chat/page.tsx`**: Real-time chat interface with agents

### Reusable Components

- **`components/ChatWindow.tsx`**: Interactive chat component with message history
- **`app/agents/[id]/CustomNode.tsx`**: Custom node component for React Flow workflow

### Utilities

- **`lib/api.ts`**: HTTP client for API communication with authentication

## 🔌 API Integration

The frontend communicates with the backend through a centralized API client in `lib/api.ts`:

### API Client Features

- **Authentication**: Automatic JWT token handling
- **Error Handling**: Centralized error management
- **Type Safety**: TypeScript interfaces for API responses
- **Base URL Configuration**: Environment-based API endpoint configuration

### Example API Usage

```typescript
import { apiFetch } from "../lib/api";

// Get user's agents
const agents = await apiFetch("/agents");

// Create a new agent
const newAgent = await apiFetch("/agents", {
  method: "POST",
  body: JSON.stringify({
    name: "My Agent",
    description: "Agent description",
    workflow: workflowData,
  }),
});

// Send message to agent
const response = await apiFetch(`/sessions/${sessionId}/message`, {
  method: "POST",
  body: JSON.stringify({
    message: "Hello, agent!",
  }),
});
```

## 🎯 Key Features

### Visual Workflow Designer

Built with React Flow Renderer, allowing users to:

- Drag and drop nodes to create agent workflows
- Connect nodes to define conversation flow
- Configure node properties and parameters
- Real-time workflow validation

### Chat Interface

Interactive chat system featuring:

- Real-time message exchange with agents
- Message history and session management
- Typing indicators and message status
- Responsive design for mobile and desktop

### Authentication Flow

Secure authentication system with:

- JWT token-based authentication
- Automatic token refresh handling
- Protected routes and components
- Persistent login state

## 🧪 Development Scripts

```bash
# Start development server with Turbopack
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linting
npm run lint

# Type checking
npx tsc --noEmit
```

## 🔧 Configuration

### Next.js Configuration (`next.config.ts`)

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable experimental features
  experimental: {
    turbopack: true,
  },
  // API configuration
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
```

### TypeScript Configuration

The project uses strict TypeScript configuration with:

- Strict mode enabled
- Path mapping for cleaner imports
- Next.js plugin for optimal integration

### Tailwind CSS Configuration

Configured for:

- Custom color palette
- Responsive breakpoints
- Dark mode support (if implemented)
- Custom component classes

## 🎨 Styling Guidelines

### Tailwind CSS Usage

- Use utility classes for styling
- Create component-specific styles when needed
- Follow responsive-first design principles
- Maintain consistent spacing and typography

### Example Component Styling

```tsx
// Button component example
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
  Create Agent
</button>

// Card component example
<div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition-shadow duration-200">
  <h3 className="text-lg font-semibold text-gray-900 mb-2">Agent Name</h3>
  <p className="text-gray-600 text-sm">Agent description...</p>
</div>
```

## 🧪 Testing

### Setting Up Tests

```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom

# Create test configuration
touch jest.config.js
```

### Example Test

```typescript
import { render, screen } from "@testing-library/react";
import ChatWindow from "../components/ChatWindow";

describe("ChatWindow", () => {
  it("renders chat interface", () => {
    render(<ChatWindow sessionId="test-session" />);
    expect(
      screen.getByPlaceholderText("Type your message...")
    ).toBeInTheDocument();
  });
});
```

### Running Tests

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## 🚀 Deployment

### Docker Production Build

The included Dockerfile creates a production-ready container:

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Set production environment
ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

# Start application
CMD ["npm", "start"]
```

### Manual Production Deployment

1. **Build the application**:

   ```bash
   npm run build
   ```

2. **Start production server**:

   ```bash
   npm start
   ```

3. **Environment variables for production**:
   ```env
   NODE_ENV=production
   NEXT_PUBLIC_API_URL=https://your-api-domain.com
   PORT=3000
   ```

### Vercel Deployment (Recommended)

1. **Connect to Vercel**:

   ```bash
   npm install -g vercel
   vercel login
   vercel
   ```

2. **Configure environment variables** in Vercel dashboard

3. **Deploy**:
   ```bash
   vercel --prod
   ```

## 🔍 Troubleshooting

### Common Issues

1. **Build failures**:

   ```bash
   # Clear Next.js cache
   rm -rf .next
   npm run build
   ```

2. **TypeScript errors**:

   ```bash
   # Check TypeScript configuration
   npx tsc --noEmit

   # Update TypeScript dependencies
   npm update typescript @types/react @types/node
   ```

3. **API connection issues**:

   - Verify backend is running on port 8000
   - Check CORS configuration in backend
   - Verify API base URL in `lib/api.ts`

4. **Style not loading**:
   ```bash
   # Rebuild Tailwind CSS
   npx tailwindcss -i ./app/globals.css -o ./dist/output.css --watch
   ```

### Development Tools

- **React Developer Tools**: Browser extension for debugging React components
- **Next.js DevTools**: Built-in development tools and debugging
- **TypeScript Language Server**: IDE integration for type checking

## 📱 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Run linting and tests: `npm run lint && npm test`
6. Commit your changes: `git commit -am 'Add some feature'`
7. Push to the branch: `git push origin feature/your-feature`
8. Submit a pull request

### Code Style Guidelines

- Use TypeScript for all new components
- Follow React functional component patterns
- Use Tailwind CSS for styling
- Add proper TypeScript types for all props and functions
- Write descriptive component and function names
- Add JSDoc comments for complex functions

### Component Development

```tsx
// Example component structure
interface ComponentProps {
  title: string;
  children: React.ReactNode;
  onAction?: () => void;
}

export default function ExampleComponent({
  title,
  children,
  onAction,
}: ComponentProps) {
  return (
    <div className="component-container">
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="content">{children}</div>
      {onAction && (
        <button onClick={onAction} className="action-button">
          Action
        </button>
      )}
    </div>
  );
}
```

## 📄 License

[Add your license information here]

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting section above
- Review Next.js documentation: https://nextjs.org/docs
- Check React Flow documentation: https://reactflow.dev/
