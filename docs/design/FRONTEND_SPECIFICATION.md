# Frontend Specification - ML Model Serving Platform

## Project Overview

A Next.js frontend application for an ML Model Serving Platform that allows users to upload, manage, monitor, and deploy machine learning models. This application connects to a FastAPI backend with JWT authentication and supports social login (Google, GitHub).

**Tech Stack:**
- Next.js 14+ (App Router)
- TypeScript
- shadcn/ui (UI components)
- Tailwind CSS (styling)
- Framer Motion (animations)
- React Hook Form + Zod (forms & validation)
- Axios (API calls)
- shadcn Charts (data visualization)
- NextAuth.js (social authentication)

**Design Philosophy:**
You have full creative freedom for visual design, colors, spacing, and layout aesthetics. Focus on creating a modern, professional, and intuitive interface. This specification defines **what** needs to be present, not **how** it should look.

---

## Architecture Overview

### Project Structure
```
ml-platform-frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── models/
│   │   │   ├── page.tsx
│   │   │   ├── upload/
│   │   │   │   └── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   ├── predictions/
│   │   │   └── page.tsx
│   │   └── settings/
│   │       └── page.tsx
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/               # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── table.tsx
│   │   ├── badge.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── select.tsx
│   │   ├── textarea.tsx
│   │   ├── toast.tsx
│   │   ├── toaster.tsx
│   │   ├── separator.tsx
│   │   ├── skeleton.tsx
│   │   ├── progress.tsx
│   │   ├── avatar.tsx
│   │   └── chart.tsx      # shadcn charts
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── RegisterForm.tsx
│   ├── models/
│   │   ├── ModelCard.tsx
│   │   ├── ModelList.tsx
│   │   ├── ModelUploadForm.tsx
│   │   └── ModelDetailsPanel.tsx
│   ├── predictions/
│   │   ├── PredictionForm.tsx
│   │   ├── PredictionResult.tsx
│   │   └── PredictionHistory.tsx
│   └── dashboard/
│       ├── StatsCard.tsx
│       ├── RecentActivity.tsx
│       └── UsageChart.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   ├── models.ts
│   │   └── predictions.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useModels.ts
│   │   └── usePredictions.ts
│   ├── utils/
│   │   ├── format.ts
│   │   └── validation.ts
│   └── types/
│       ├── auth.ts
│       ├── model.ts
│       └── prediction.ts
├── contexts/
│   └── AuthContext.tsx
└── middleware.ts
```

---

## Core Functionality & Features

### 1. Authentication System

#### Login Page (`/login`)
- **Purpose:** Allow users to authenticate via email/password or social providers

**Required Elements:**
- Email input field (with validation feedback)
- Password input field (masked, with show/hide toggle)
- "Remember me" checkbox (optional)
- "Login" button (with loading state)
- "Forgot password?" link (can be placeholder for now)
- Link to registration page
- Error message display area
- **Social Login Buttons:**
  - "Continue with Google" button (with Google icon)
  - "Continue with GitHub" button (with GitHub icon)
- Visual separator between email/password and social login (e.g., "or" divider)

**Behavior:**
- Form validation before submission (show inline errors)
- POST to `/api/v1/auth/login` with `username` and `password` for email login
- For social login: Use NextAuth.js to handle OAuth flow
- Store JWT token securely (httpOnly cookies preferred, fallback to localStorage)
- Redirect to dashboard on success
- Show toast notification on failure
- Smooth page transition animation

**Design Freedom:**
- Layout arrangement (side-by-side, centered, with illustration, etc.)
- Color scheme and branding
- Button styles and hover effects
- Spacing and typography

#### Register Page (`/register`)
- **Purpose:** New user registration via email or social providers

**Required Elements:**
- Email input field (with format validation)
- Username/Display name input field (optional but recommended)
- Password input field (with strength indicator visualization)
- Confirm password field
- Password requirements hint (e.g., "8+ characters, uppercase, lowercase, number")
- "Register" button (with loading state)
- Link to login page
- Terms of service/Privacy policy checkbox with links
- **Social Registration Buttons:**
  - "Continue with Google" button
  - "Continue with GitHub" button
- Visual separator between traditional and social registration
- Success/error message display

**Behavior:**
- Real-time validation (show errors on blur or change)
- Password strength indicator updates as user types
- POST to `/api/v1/auth/register` for email registration
- Social registration via NextAuth.js (auto-creates account)
- Auto-login after successful registration
- Show success toast and redirect to dashboard
- Display validation errors inline

**Design Freedom:**
- Multi-step form vs single page
- Visual treatment of password strength
- Layout and visual hierarchy
- Animation and micro-interactions

---

### 2. Dashboard Layout (Protected Routes)

#### Sidebar Navigation
**Required Elements:**
- Logo/Brand name (positioned at top)
- Navigation menu items:
  - Dashboard/Home (with icon)
  - Models (with icon)
  - Predictions (with icon)
  - Settings (with icon)
- User profile section (positioned at bottom):
  - User avatar/initial
  - User name/email
  - Logout button or dropdown menu
- Mobile: Collapsible with hamburger menu

**Behavior:**
- Highlight active/current route
- Smooth animation when expanding/collapsing (mobile)
- Logout clears authentication and redirects to login
- Optional: Collapsible on desktop for more workspace

**Design Freedom:**
- Sidebar width and styling
- Icon choices and sizes
- Whether to show text labels always or on hover
- Placement (left, right, top)
- Visual treatment of active state

#### Top Navbar (optional - can be integrated into sidebar)
**Required Elements:**
- Current page title/breadcrumb
- Search bar (for searching models/predictions)
- Notification icon (can be placeholder)
- User menu dropdown (profile link, settings link, logout)

**Design Freedom:**
- Whether to have a top navbar or integrate everything into sidebar
- Layout and positioning
- Search bar prominence

---

### 3. Dashboard Home Page (`/dashboard`)

#### Purpose
Central overview showing key metrics, visualizations, and recent activity

#### Required Content Sections

**1. Stats Overview (Metrics Cards)**
Display 4 key metrics - each in its own card:
- **Total Models**: Count of user's models, with subtitle "Active models"
- **Total Predictions**: Count with subtitle "This month"
- **Active API Keys**: Count with subtitle "Valid keys"
- **Average Response Time**: Display in milliseconds with subtitle "Last 24 hours"

Each metric card should show:
- Large number (the metric value)
- Descriptive label/subtitle
- Icon (relevant to metric)
- Optional: Trend indicator (up/down arrow with percentage)

**2. Data Visualizations (using shadcn Charts)**

**Chart 1: Predictions Over Time**
- Type: Line chart or Area chart
- Data: Prediction count per day for last 7-14 days
- X-axis: Dates
- Y-axis: Number of predictions
- Should be interactive (tooltips on hover)
- Smooth animations on mount

**Chart 2: Models by Status**
- Type: Donut chart or Pie chart
- Data: Distribution of models by status (Active, Inactive, Deployed)
- Show counts and percentages
- Interactive with hover tooltips
- Legend showing each status

**3. Recent Activity Feed**
Display last 10-15 recent activities in a table or list:
- Timestamp (formatted as relative time, e.g., "2 hours ago")
- Action type (e.g., "Model uploaded", "Prediction made", "Model deployed")
- Model name or relevant entity
- Status indicator (icon or badge)
- Optional: Click row to view details

**Empty States:**
- Show helpful message when no data exists
- Provide quick action button (e.g., "Upload your first model")

#### API Calls
- GET `/api/v1/models/` (count and status distribution)
- GET `/api/v1/predictions/history` (count and time-series data)
- GET `/api/v1/users/me` (user information and stats)

**Design Freedom:**
- Layout arrangement (grid, flex, multi-column)
- Card styling and elevation
- Chart color schemes
- Typography and spacing
- Animation timing and style
- Responsive behavior (stack on mobile, grid on desktop)

---

### 4. Models Page (`/models`)

#### Purpose
View and manage all uploaded ML models

#### Required Elements

**Page Header:**
- Page title: "My Models" or "Models"
- Primary action: "Upload New Model" button (prominent, easy to find)
- Filter/sort controls:
  - Filter by status dropdown (All, Active, Inactive, Deployed)
  - Sort by dropdown (Name, Date created, Last used)
- Search input field

**Models Display:**
Display models in a grid or list layout. Each model item must show:
- Model name (prominent text)
- Model type badge (Classification, Regression, etc.)
- Upload date (formatted)
- Status indicator/badge (Active, Inactive, Deployed)
- Description (if available, truncated)
- Quick action buttons:
  - View details
  - Deploy/Undeploy toggle
  - Delete (with confirmation)

**Empty State:**
When no models exist:
- Illustration or icon
- Message: "No models uploaded yet"
- Call-to-action button: "Upload Your First Model"

**Interactions:**
- Hover effects on model cards/rows
- Click on model card/row to view details
- Filter updates display immediately
- Search filters results in real-time or on enter
- Delete requires confirmation dialog
- Loading states while fetching data

#### API Calls
- GET `/api/v1/models/` on page load and after filters change
- PATCH `/api/v1/models/{id}` for deploy/undeploy
- DELETE `/api/v1/models/{id}` for deletion

**Design Freedom:**
- Grid vs list vs table layout
- Card design and information hierarchy
- Number of columns in grid
- How to display actions (always visible, on hover, dropdown menu)
- Filter/search layout
- Animation and transitions
- Responsive behavior

---

### 5. Model Upload Page (`/models/upload`)

#### Purpose
Upload new ML models to the platform

#### Required Form Fields

1. **Model Name** (text input)
   - Required field
   - Validation: Max 100 characters, alphanumeric and spaces
   - Show character count

2. **Model Type** (select/dropdown)
   - Required field
   - Options: Classification, Regression, Clustering, Other
   - Clear labeling

3. **Description** (textarea)
   - Optional field
   - Max 500 characters
   - Show character count
   - Multi-line input (4+ rows)

4. **Model File Upload** (file input)
   - Required field
   - Accepted formats: .pkl, .h5, .pt, .pth, .joblib
   - Max file size: 100MB
   - Features:
     - Drag-and-drop zone
     - Click to browse alternative
     - Show selected file name and size
     - Upload progress bar with percentage
     - Cancel upload option
   - Validation errors (wrong format, size exceeded)

5. **Framework** (select/dropdown)
   - Optional field
   - Options: Scikit-learn, TensorFlow, PyTorch, XGBoost, Other
   - Default: None selected

6. **Version** (text input)
   - Optional field
   - Placeholder: "e.g., 1.0.0"
   - Pattern hint

**Form Actions:**
- "Upload Model" button (primary action, disabled until form is valid)
- "Cancel" button (secondary, returns to models list)

**Form Behavior:**
- Real-time validation (show errors inline as user fills)
- Disable submit button until all required fields valid
- Show upload progress bar during file upload
- POST to `/api/v1/models/` with multipart/form-data
- Success: Show success toast, redirect to model details page
- Error: Display error message, preserve form data

**Design Freedom:**
- Form layout (single column, two column, sections)
- Styling of file upload zone
- Progress indicator design
- Error message placement and styling
- Field grouping and spacing

---

### 6. Model Details Page (`/models/[id]`)

#### Purpose
View comprehensive information about a specific model and interact with it

#### Required Sections

**1. Model Header**
- Model name (large, prominent)
- Status badge (Active/Inactive/Deployed)
- Action buttons:
  - Deploy/Undeploy toggle
  - Download model file
  - Edit model details
  - Delete model (with confirmation)

**2. Model Information Panel**
Display key metadata (can be arranged in columns or sections):
- **Type:** Classification, Regression, etc.
- **Framework:** Scikit-learn, TensorFlow, etc.
- **Version:** Model version number
- **Uploaded:** Date and time
- **File Size:** In MB
- **Status:** Current status
- **Description:** Full text description
- **API Endpoint:** `/predict/{model_id}` with copy button
- **Total Predictions:** Count of predictions made
- **Last Used:** Relative time (e.g., "2 hours ago")

**3. Test Prediction Section**
Allow users to test the model directly:
- Section title: "Test This Model" or "Try It Out"
- Input field: Textarea for JSON input data
- "Example" button: Pre-fills with sample JSON structure
- "Run Prediction" button (primary action)
- Result display area:
  - Shows prediction output (JSON formatted)
  - Shows response time
  - Error display if prediction fails
- Loading state during prediction

**4. Prediction History**
Table showing recent predictions for this model:
- Columns needed:
  - Timestamp
  - Input data (truncated or preview)
  - Output data (truncated or preview)
  - Status (Success/Failed)
  - Response time
- Row actions: Click to view full details
- Pagination (if more than 20 results)
- "View All Predictions" link to predictions page filtered by this model

**Modal for Full Prediction Details:**
When clicking on a prediction row:
- Full input JSON (formatted, syntax highlighted)
- Full output JSON (formatted, syntax highlighted)
- Metadata (timestamp, status, response time)
- Close button

#### API Calls
- GET `/api/v1/models/{model_id}` on page load
- PATCH `/api/v1/models/{model_id}` for updates (name, description, status)
- DELETE `/api/v1/models/{model_id}` for deletion
- POST `/api/v1/predictions/` for test prediction
- GET `/api/v1/predictions/?model_id={id}` for prediction history

**Design Freedom:**
- Layout of information (tabs, sections, cards, columns)
- How to display JSON (code block, formatted display)
- Visual hierarchy
- Spacing and organization
- Interactive elements styling

---

### 7. Predictions Page (`/predictions`)

#### Purpose
View complete prediction history across all models with filtering

#### Required Elements

**Filters Section:**
- Date range selector (default: last 7 days)
  - Preset options: Today, Last 7 days, Last 30 days, Custom range
- Model filter: Dropdown to filter by specific model or "All Models"
- Status filter: Dropdown (All, Success, Failed)
- Search field: Search by prediction ID or input data
- "Apply Filters" or auto-apply on change

**Predictions Display:**
Table or list showing prediction entries with these columns/fields:
- Prediction ID (short identifier or hash)
- Model Name (linked to model details page)
- Timestamp (formatted date and time)
- Status badge (Success in green, Failed in red)
- Response Time (in milliseconds)
- Actions: "View Details" button or click row to open

**Table Features:**
- Sortable columns (at least by timestamp)
- Pagination (show 20-50 per page)
- Loading skeleton while fetching
- Empty state when no predictions match filters

**Prediction Details Modal/Dialog:**
Opens when clicking "View Details" or on row click:
- Full input data (JSON, syntax highlighted or well-formatted)
- Full output data (JSON, formatted)
- Metadata section:
  - Prediction ID
  - Model name (linked)
  - Timestamp
  - Status
  - Response time
  - Error message (if failed)
- Close button

**Empty State:**
When no predictions exist:
- Icon or illustration
- Message: "No predictions yet"
- Action button: "Go to Models" or "Make Your First Prediction"

#### API Calls
- GET `/api/v1/predictions/history` with query parameters (date range, model_id, status, skip, limit)
- GET `/api/v1/predictions/{id}` for individual prediction details (if needed)

**Design Freedom:**
- Layout of filters (horizontal bar, sidebar, top section)
- Table vs card-based display
- Modal size and animation
- How to display JSON (expandable sections, copy buttons)
- Pagination style
- Loading states

---

### 8. Settings Page (`/settings`)

#### Purpose
Manage user account, profile, and API keys

#### Required Sections

**1. Profile Settings Section**
Display and edit user profile information:
- Email address (display only, non-editable)
- Username/Display name (editable text input)
- Profile picture/avatar (upload option - optional feature)
- "Update Profile" button
- Success/error feedback after update

**2. Change Password Section**
Form to change password:
- Current password input (required, masked)
- New password input (required, masked, with strength indicator)
- Confirm new password input (required, masked)
- Password requirements reminder
- "Update Password" button
- Separate from profile update

**3. Connected Accounts Section** (if social login used)
Show connected social accounts:
- List of providers (Google, GitHub)
- For each: Provider icon, "Connected" status or "Connect" button
- "Disconnect" option for connected accounts
- Note: "You need at least one way to sign in"

**4. API Keys Management Section**
Manage API keys for programmatic access:
- Section title: "API Keys"
- Description: "Generate keys for API access to your models"
- List of existing API keys, each showing:
  - Key name/label
  - Partial key (e.g., "sk_...abc123")
  - Created date
  - Last used date (if available)
  - Actions: Copy full key (if recently created), Delete
- "Generate New API Key" button

**New API Key Flow:**
- Click "Generate" opens modal/dialog
- Form asks for:
  - Key name (required)
  - Optional: Expiration date
- After generation:
  - Show full key once with warning "Save this key now - you won't see it again"
  - Copy button
  - Confirmation before closing

**5. Danger Zone Section**
Destructive actions:
- Clear visual separation (red border or background)
- Title: "Danger Zone"
- "Delete Account" button
- Requires confirmation modal with:
  - Warning message
  - Password confirmation
  - Final "Yes, delete my account" button

#### API Calls
- GET `/api/v1/users/me` on load
- PATCH `/api/v1/users/me` for profile updates
- POST `/api/v1/users/change-password` for password change
- GET `/api/v1/api-keys/` for keys list
- POST `/api/v1/api-keys/` to generate new key
- DELETE `/api/v1/api-keys/{key_id}` to delete key
- DELETE `/api/v1/users/me` for account deletion

**Design Freedom:**
- Layout (tabs, accordion, sections on one page)
- Visual treatment of danger zone
- Card vs form styling
- Spacing between sections
- Modal designs

---

## Component Specifications

### shadcn/ui Components

This project uses **shadcn/ui** for all base UI components. You have complete freedom in choosing variants, sizes, and styling. Below are the required components and their purpose:

#### Core Components Needed

**Form Components:**
- `button` - All action buttons (primary, secondary, destructive variants)
- `input` - Text, email, password inputs
- `textarea` - Multi-line text inputs
- `label` - Form field labels
- `select` - Dropdown selections
- `checkbox` - Checkboxes for terms, remember me, etc.

**Layout Components:**
- `card` - Container component for sections (with header, content, footer)
- `separator` - Visual dividers between sections
- `dialog` - Modal dialogs for confirmations, forms
- `dropdown-menu` - User menu, action menus

**Feedback Components:**
- `toast` - Notification system (success, error, info)
- `badge` - Status indicators (Active, Failed, Success, etc.)
- `progress` - Upload progress, loading indicators
- `skeleton` - Loading state placeholders
- `alert` - Important messages or warnings

**Data Display:**
- `table` - Data tables for predictions, history
- `avatar` - User profile pictures
- `tabs` - If using tabbed layouts (optional)

**Charts:**
- Use **shadcn Charts** (built on Recharts) for all data visualizations
- Components: `ChartContainer`, `ChartTooltip`, `LineChart`, `AreaChart`, `BarChart`, `PieChart`
- Full creative freedom on colors, styles, and layout

### Component Props & Behavior

You have complete freedom to:
- Choose any size variants (sm, md, lg, etc.)
- Select color schemes and themes
- Decide on layouts and positioning
- Customize animations and transitions
- Add additional shadcn components as needed

**Key Requirements:**
- Loading states: Show spinners or skeletons during async operations
- Disabled states: Disable buttons during form submission
- Error states: Highlight invalid form fields
- Success states: Show visual feedback after successful actions
- Hover states: Provide feedback on interactive elements

---

## API Integration

### API Client Setup (`lib/api/client.ts`)

```typescript
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

### NextAuth.js Setup (for Social Login)

```typescript
// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import GitHubProvider from 'next-auth/providers/github'
import CredentialsProvider from 'next-auth/providers/credentials'

export const authOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // Call your FastAPI backend login endpoint
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/login`, {
          method: 'POST',
          body: new URLSearchParams({
            username: credentials?.username || '',
            password: credentials?.password || '',
          }),
          headers: { "Content-Type": "application/x-www-form-urlencoded" }
        })
        
        const user = await res.json()
        
        if (res.ok && user) {
          return user
        }
        return null
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      if (account && user) {
        // For social login, you may need to create/link user in your backend
        // For credentials login, user object contains access_token
        return {
          ...token,
          accessToken: user.access_token || token.accessToken,
        }
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken
      return session
    },
  },
  pages: {
    signIn: '/login',
  },
}

const handler = NextAuth(authOptions)
export { handler as GET, handler as POST }
```

### Auth API (`lib/api/auth.ts`)

```typescript
interface LoginRequest {
  username: string // email
  password: string
}

interface LoginResponse {
  access_token: string
  token_type: string
}

interface RegisterRequest {
  email: string
  password: string
}

export const authAPI = {
  login: (data: LoginRequest) => 
    apiClient.post<LoginResponse>('/api/v1/auth/login', new URLSearchParams(data)),
  
  register: (data: RegisterRequest) => 
    apiClient.post('/api/v1/auth/register', data),
  
  getMe: () => 
    apiClient.get('/api/v1/users/me'),
}
```

### Models API (`lib/api/models.ts`)

```typescript
interface Model {
  id: string
  name: string
  type: string
  description?: string
  framework?: string
  version?: string
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
  owner_id: string
}

interface CreateModelRequest {
  name: string
  type: string
  description?: string
  framework?: string
  version?: string
  file: File
}

export const modelsAPI = {
  getAll: () => 
    apiClient.get<Model[]>('/api/v1/models/'),
  
  getById: (id: string) => 
    apiClient.get<Model>(`/api/v1/models/${id}`),
  
  create: (data: CreateModelRequest) => {
    const formData = new FormData()
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined) formData.append(key, value)
    })
    return apiClient.post('/api/v1/models/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  
  update: (id: string, data: Partial<Model>) => 
    apiClient.patch(`/api/v1/models/${id}`, data),
  
  delete: (id: string) => 
    apiClient.delete(`/api/v1/models/${id}`),
}
```

### Predictions API (`lib/api/predictions.ts`)

```typescript
interface Prediction {
  id: string
  model_id: string
  input_data: any
  output_data: any
  status: 'success' | 'failed'
  response_time_ms: number
  created_at: string
}

interface CreatePredictionRequest {
  model_id: string
  input_data: any
}

export const predictionsAPI = {
  create: (data: CreatePredictionRequest) => 
    apiClient.post<Prediction>('/api/v1/predictions/', data),
  
  getHistory: (params?: { model_id?: string; limit?: number }) => 
    apiClient.get<Prediction[]>('/api/v1/predictions/history', { params }),
  
  getById: (id: string) => 
    apiClient.get<Prediction>(`/api/v1/predictions/${id}`),
}
```

---

## State Management

### Auth Context (`contexts/AuthContext.tsx`)

```typescript
interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

// Provider wraps the app
// Automatically checks for token on mount
// Provides auth state to all components
```

### Custom Hooks

**`useAuth` Hook**
- Returns auth context
- Use in components that need auth state

**`useModels` Hook**
```typescript
const useModels = () => {
  const [models, setModels] = useState<Model[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const fetchModels = async () => { /* ... */ }
  const deleteModel = async (id: string) => { /* ... */ }
  
  useEffect(() => { fetchModels() }, [])
  
  return { models, isLoading, error, refetch: fetchModels, deleteModel }
}
```

**`usePredictions` Hook**
- Similar to useModels
- Manages predictions state

---

## Animation Specifications (Framer Motion)

### Animation Philosophy
Use Framer Motion **sparingly and purposefully** for:
- Page transitions
- Modal/dialog entrance
- List item stagger effects
- Loading states
- Micro-interactions on important actions

**Design Freedom:**
- Choose animation duration, easing, and style
- Decide which elements to animate
- Create custom animations as needed
- Balance performance with visual appeal

### Recommended Animation Patterns

**Page Transitions:**
```typescript
// Example pattern - customize as desired
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
}
```

**List/Card Stagger:**
```typescript
// Stagger children animations
const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}
```

**Modal Entrance:**
```typescript
// Dialog fade and scale
const modalVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1 },
}
```

**Button Interactions:**
```typescript
// Subtle hover and tap feedback
<motion.button
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
/>
```

**Note:** These are suggestions only. You have full freedom to implement animations that enhance the user experience.

---

## Routing & Middleware

### Protected Routes
```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')
  const isAuthPage = request.nextUrl.pathname.startsWith('/login') || 
                     request.nextUrl.pathname.startsWith('/register')
  const isDashboardPage = request.nextUrl.pathname.startsWith('/dashboard') ||
                          request.nextUrl.pathname.startsWith('/models') ||
                          request.nextUrl.pathname.startsWith('/predictions') ||
                          request.nextUrl.pathname.startsWith('/settings')
  
  if (isDashboardPage && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  
  if (isAuthPage && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
```

### Route Groups
- `(auth)`: Public auth pages (login, register)
- `(dashboard)`: Protected dashboard pages with shared layout

---

## Responsive Design

### Breakpoint Strategy
Use Tailwind CSS responsive utilities. Suggested breakpoints:
- **Mobile:** < 640px (sm)
- **Tablet:** 640px - 1024px (md, lg)
- **Desktop:** > 1024px (xl, 2xl)

You have complete freedom to adjust breakpoints and responsive behavior.

### Responsive Behavior Requirements

**Mobile (< 640px):**
- Sidebar collapses to hamburger menu/drawer
- Model cards stack in single column
- Tables: Consider horizontal scroll or card-based view
- Forms use full width
- Stats cards stack vertically
- Charts: Full width, possibly simplified

**Tablet (640px - 1024px):**
- Sidebar can be narrow or toggle-able
- Model cards in 2 columns
- Dashboard stats in 2x2 grid
- Tables: Full features, may scroll if needed

**Desktop (> 1024px):**
- Full sidebar visible
- Model cards in 3+ columns (your choice)
- Dashboard stats in horizontal row (1x4)
- Multi-column layouts
- Optimal use of screen space

**Design Freedom:**
- Choose exact breakpoints
- Decide responsive strategies
- Implement progressive enhancement
- Optimize for touch on mobile

---

## Error Handling

### API Error Responses
```typescript
interface APIError {
  detail: string | { msg: string }[]
}
```

### Error Display Strategy
1. **Form validation errors**: Inline below input fields
2. **API errors**: Toast notification (top-right)
3. **Network errors**: Toast with retry button
4. **404 errors**: Empty state component
5. **500 errors**: Error boundary with refresh button

### Loading States
- Buttons: spinner inside button, disabled state
- Pages: centered spinner or skeleton components
- Tables: skeleton rows
- Cards: skeleton cards

---

## Form Validation

### Validation Rules

**Email:**
- Required
- Valid email format
- Max 255 characters

**Password (Register):**
- Required
- Min 8 characters
- Must contain: uppercase, lowercase, number

**Model Name:**
- Required
- Max 100 characters
- Alphanumeric and spaces only

**File Upload:**
- Required
- File size < 100MB
- Allowed extensions: .pkl, .h5, .pt, .pth, .joblib

### Validation Timing
- On blur (when field loses focus)
- On submit
- Real-time for password strength

---

## TypeScript Types

### User Type
```typescript
interface User {
  id: string
  email: string
  username?: string
  is_active: boolean
  created_at: string
}
```

### Model Type
```typescript
interface Model {
  id: string
  name: string
  type: 'classification' | 'regression' | 'clustering' | 'other'
  description?: string
  framework?: string
  version?: string
  status: 'active' | 'inactive' | 'deployed'
  file_path: string
  created_at: string
  updated_at: string
  owner_id: string
}
```

### Prediction Type
```typescript
interface Prediction {
  id: string
  model_id: string
  model_name?: string
  input_data: Record<string, any>
  output_data: Record<string, any>
  status: 'success' | 'failed'
  error_message?: string
  response_time_ms: number
  created_at: string
}
```

### API Key Type
```typescript
interface APIKey {
  id: string
  name: string
  key: string // full key only shown once
  key_preview: string // e.g., "sk_...abc123"
  created_at: string
  last_used?: string
}
```

---

## Environment Variables

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# App Configuration
NEXT_PUBLIC_APP_NAME=ML Model Serving Platform

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

---

## Accessibility Requirements

1. **Keyboard Navigation**
   - All interactive elements accessible via Tab key
   - Modal/dialog traps focus appropriately
   - Skip to main content link
   - Logical tab order

2. **Screen Reader Support**
   - Semantic HTML (nav, main, section, article, aside)
   - ARIA labels on icon-only buttons
   - Alt text on images
   - Form labels properly associated with inputs
   - Status messages announced

3. **Visual Accessibility**
   - Visible focus indicators on all interactive elements
   - Focus not hidden by animations
   - Sufficient color contrast (WCAG AA minimum)
   - Text resizable without breaking layout
   - Don't rely solely on color to convey information

4. **Interactive Elements**
   - Buttons clearly identifiable
   - Links distinguishable from text
   - Error messages associated with form fields
   - Loading states communicated to screen readers

**Note:** shadcn/ui components are built with accessibility in mind. Follow their patterns.

---

## Performance Optimization

1. **Code Splitting**
   - Dynamic imports for large components
   - Route-based code splitting (automatic with Next.js App Router)

2. **Data Fetching**
   - Use React Query or SWR for caching
   - Implement pagination for large lists
   - Debounce search inputs

3. **Image Optimization**
   - Use Next.js Image component
   - Lazy load images

4. **Bundle Size**
   - Tree-shake unused code
   - Use Framer Motion sparingly (only where needed)

---

## Testing Considerations

### Unit Tests
- Test utility functions (formatters, validators)
- Test API client functions
- Test custom hooks

### Component Tests
- Test form submissions
- Test button states
- Test modal open/close

### Integration Tests
- Test auth flow (login → dashboard)
- Test model upload flow
- Test prediction creation flow

### E2E Tests (Optional)
- Full user journey tests with Playwright/Cypress

---

## Development Workflow

### Phase 1: Setup & Authentication (Week 1)
1. Initialize Next.js 14+ project with TypeScript and App Router
2. Set up Tailwind CSS
3. Install and configure shadcn/ui CLI
4. Add required shadcn components: `npx shadcn-ui@latest add button input card dialog toast ...`
5. Install dependencies:
   ```bash
   npm install next-auth axios react-hook-form zod @hookform/resolvers
   npm install framer-motion lucide-react
   ```
6. Configure NextAuth.js for Google and GitHub OAuth
7. Create basic layout structure (sidebar, navbar)
8. Build authentication pages (Login, Register) with social login
9. Implement AuthContext or use NextAuth session
10. Set up API client with interceptors
11. Test authentication flows (email + social)

### Phase 2: Dashboard & Models (Week 2)
1. Build dashboard home page with stats cards
2. Integrate shadcn Charts for visualizations
3. Create models list page with grid/card layout
4. Build model card components
5. Implement model upload page with file upload
6. Add progress tracking for uploads
7. Test model CRUD operations
8. Polish responsive behavior

### Phase 3: Predictions & Details (Week 3)
1. Build predictions history page with table
2. Create prediction details dialog/modal
3. Build comprehensive model details page
4. Implement prediction testing on model page
5. Add JSON display with syntax highlighting
6. Create filtering and search functionality
7. Test complete prediction workflow

### Phase 4: Settings & Polish (Week 4)
1. Build settings page with sections
2. Implement profile update functionality
3. Add API key management system
4. Integrate social account connections
5. Add change password functionality
6. Polish all animations and transitions
7. Complete responsive testing (mobile, tablet, desktop)
8. Accessibility audit
9. Performance optimization
10. Final bug fixes and edge case handling

### Initial Setup Commands
```bash
# Create Next.js project
npx create-next-app@latest ml-platform-frontend --typescript --tailwind --app

# Navigate to project
cd ml-platform-frontend

# Install shadcn/ui
npx shadcn-ui@latest init

# Add necessary shadcn components
npx shadcn-ui@latest add button card input label textarea select dialog dropdown-menu badge toast table separator skeleton progress avatar

# Install additional dependencies
npm install next-auth axios react-hook-form zod @hookform/resolvers framer-motion lucide-react recharts
```

---

## Component Implementation Priority

### Critical (Build First)
1. Auth pages (Login, Register)
2. Dashboard layout (Sidebar, Navbar)
3. Models list and upload
4. Basic UI components (Button, Input, Card)

### Important (Build Second)
1. Dashboard home with stats
2. Model details page
3. Predictions history
4. Toast notifications

### Nice-to-Have (Build Last)
1. Settings page
2. API key management
3. Advanced animations
4. Charts and visualizations

---

## API Endpoint Reference

### Authentication
- `POST /api/v1/auth/login` - Login with username/password
- `POST /api/v1/auth/register` - Register new user
- `GET /api/v1/users/me` - Get current user info

### Models
- `GET /api/v1/models/` - List all models
- `POST /api/v1/models/` - Upload new model
- `GET /api/v1/models/{id}` - Get model details
- `PATCH /api/v1/models/{id}` - Update model
- `DELETE /api/v1/models/{id}` - Delete model

### Predictions
- `POST /api/v1/predictions/` - Create prediction
- `GET /api/v1/predictions/history` - Get prediction history
- `GET /api/v1/predictions/{id}` - Get prediction details

### API Keys
- `GET /api/v1/api-keys/` - List API keys
- `POST /api/v1/api-keys/` - Generate new API key
- `DELETE /api/v1/api-keys/{id}` - Delete API key

---

## Design Guidelines

### Visual Style Principles
- **Modern & Professional:** Clean interface suitable for technical users
- **Data-First:** Emphasize clarity, readability, and information hierarchy
- **Purposeful:** Every element serves a function
- **Consistent:** Maintain patterns across the application

### Design Freedom
You have **complete creative control** over:
- **Color palette** - Choose any colors that work well together
- **Typography** - Select appropriate fonts and sizes
- **Spacing** - Determine padding, margins, and gaps
- **Shadows & borders** - Decide on depth and separation
- **Layout arrangements** - Choose optimal positioning
- **Icon style** - Select icon library (lucide-react recommended)
- **Brand identity** - Create logo and visual identity

### What to Focus On
Rather than prescriptive design rules, focus on these outcomes:
- **Clear hierarchy:** Important elements stand out
- **Easy scanning:** Users can quickly find information
- **Intuitive interactions:** Buttons and actions are obvious
- **Smooth experience:** No jarring transitions or confusing flows
- **Professional appearance:** Suitable for enterprise use

### Component Consistency
Maintain consistency within your chosen design:
- Reuse the same button styles throughout
- Keep spacing patterns consistent
- Use the same card style everywhere
- Maintain consistent typography scale
- Apply uniform border radius and shadows

**Trust your design instincts!** Modern design practices and shadcn/ui defaults will guide you well.

---

## Key User Flows

### 1. First-Time User Flow
1. Land on landing page (optional) or login
2. Click "Register"
3. Fill registration form
4. Auto-login after registration
5. Redirected to dashboard (shows empty state)
6. See "Upload Your First Model" prompt
7. Click upload button
8. Fill model upload form
9. Upload completes
10. Redirected to model details page
11. Test prediction on model details page

### 2. Returning User Flow
1. Visit login page
2. Enter credentials
3. Click login
4. Redirected to dashboard
5. See stats and recent activity
6. Navigate to models page
7. View model list
8. Click on a model
9. View model details
10. Make prediction

### 3. Model Management Flow
1. Go to models page
2. Click "Upload New Model"
3. Fill form and upload file
4. Wait for upload progress
5. Redirected to model details
6. Deploy model (toggle status)
7. Copy prediction endpoint
8. Test model with sample data
9. View prediction history

---

## Edge Cases to Handle

1. **Empty States**
   - No models uploaded
   - No predictions made
   - No API keys generated
   - No search results

2. **Error States**
   - Login fails (wrong credentials)
   - Registration fails (email exists)
   - Upload fails (file too large, wrong format)
   - Network error (API down)
   - Token expired (401 error)

3. **Loading States**
   - Page loading (initial data fetch)
   - Button loading (form submission)
   - Table loading (fetching more data)
   - Upload progress

4. **Validation States**
   - Invalid email format
   - Weak password
   - Required field empty
   - File size exceeded

---

## Success Criteria

A successful implementation will:

✅ Allow users to register and login securely  
✅ Display dashboard with meaningful stats  
✅ Enable model upload with progress tracking  
✅ Show list of uploaded models  
✅ Allow viewing detailed model information  
✅ Enable making predictions through the UI  
✅ Show prediction history  
✅ Manage API keys  
✅ Work responsively on mobile, tablet, desktop  
✅ Have smooth animations without performance issues  
✅ Handle errors gracefully with user feedback  
✅ Maintain authentication state across page refreshes  

---

## Next Steps for Development

1. **Project Initialization**
   ```bash
   npx create-next-app@latest ml-platform-frontend --typescript --tailwind --app
   cd ml-platform-frontend
   npm install framer-motion axios react-hook-form zod @hookform/resolvers
   npm install recharts lucide-react
   ```

2. **Create Base Structure**
   - Set up folder structure as outlined
   - Create layout files
   - Configure TypeScript paths

3. **Build UI Component Library**
   - Button, Input, Card, Badge, Modal, Toast
   - Test each component in isolation

4. **Implement Authentication**
   - Build auth pages
   - Set up API client with interceptors
   - Create AuthContext

5. **Build Core Features**
   - Follow phase-by-phase plan
   - Test each feature before moving to next

---

## Additional Notes

- **Security**: Never log sensitive data (tokens, passwords)
- **Performance**: Monitor bundle size, optimize images
- **User Experience**: Fast loading, clear feedback, intuitive navigation
- **Maintainability**: Reusable components, consistent patterns, TypeScript types
- **Scalability**: Component-based architecture, separated concerns

---

## Questions to Consider During Development

1. Should we implement real-time updates for predictions? (WebSocket)
2. Do we need role-based access control (admin vs user)?
3. Should models have version history?
4. Do we need model sharing between users?
5. Should we implement dark mode?
6. Do we need email verification for registration?
7. Should we add two-factor authentication?

**For MVP: Skip these features. Focus on core functionality.**

---

## Conclusion

This specification provides a complete functional blueprint for building the frontend of the ML Model Serving Platform. It's specifically designed for AI-assisted development tools like **Vercel v0**.

### What's Defined
✅ **Functionality:** Every feature, button, input, and interaction  
✅ **Data flow:** API endpoints, request/response structures  
✅ **User journeys:** Complete flows from login to prediction  
✅ **Technical stack:** Next.js 14, shadcn/ui, NextAuth.js, Framer Motion  
✅ **Requirements:** What must be present on each page  

### What's Flexible
🎨 **Visual design:** Colors, fonts, spacing - full creative freedom  
🎨 **Layout:** Arrange components as you see fit  
🎨 **Styling:** Make it beautiful in your own way  
🎨 **Animations:** Choose timing, easing, and effects  
🎨 **Icons:** Select appropriate icons from your preferred library  

### Key Philosophy
This spec answers **"WHAT"** needs to be built, not **"HOW"** it should look. Build a modern, professional, intuitive ML platform interface with the confidence that you have all the functional requirements clearly defined.

### Starting Point
1. **Set up the project** with the provided commands
2. **Configure OAuth** providers (Google, GitHub)
3. **Build authentication first** - it's the foundation
4. **Iterate through phases** - test as you go
5. **Trust your design instincts** - shadcn/ui provides excellent defaults

The architecture is modular, scalable, and follows Next.js 14 App Router best practices. Focus on delivering a great user experience with smooth interactions and clear information hierarchy.

**Good luck building! 🚀**

---

### Quick Reference: Tech Stack Summary
- **Framework:** Next.js 14+ (App Router, TypeScript)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **Authentication:** NextAuth.js (Google, GitHub, Credentials)
- **Forms:** React Hook Form + Zod
- **API Client:** Axios
- **Animations:** Framer Motion
- **Charts:** shadcn Charts (Recharts)
- **Icons:** lucide-react (recommended)

### OAuth Setup Notes
You'll need to register your application with:
- **Google Cloud Console:** For Google OAuth credentials
- **GitHub Developer Settings:** For GitHub OAuth app
- Backend may need updates to handle social auth tokens (create/link users)
