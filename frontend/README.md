# AutoCurate Frontend

A modern Next.js frontend for the AutoCurate AI-powered knowledge feed.

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
```

3. Run the development server:
```bash
npm run dev
```

## Features

- ✅ User onboarding with preference survey
- ✅ Personalized dashboard with curated content
- ✅ Interactive content rating system
- ✅ Search and filtering capabilities
- ✅ Responsive design with dark/light mode
- ✅ Real-time updates and notifications

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: React Query + Context API
- **Forms**: React Hook Form + Zod validation
- **Animations**: Framer Motion
- **Icons**: Lucide React

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── dashboard/         # Dashboard pages
│   ├── onboarding/        # User onboarding flow
│   ├── search/            # Search and discovery
│   └── settings/          # User settings
├── components/
│   ├── ui/                # Reusable UI components
│   ├── forms/             # Form components
│   ├── layout/            # Layout components
│   └── features/          # Feature-specific components
├── lib/                   # Utilities and configurations
├── hooks/                 # Custom React hooks
├── services/              # API services
└── types/                 # TypeScript definitions
```

## Development

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checks
```
