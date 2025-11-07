# Product Tech Stack

**Last Updated:** November 7, 2025

This document outlines the complete technical stack used across all aspects of the AI Video Clipper product.

---

## Backend

### Core Framework
- **Python**: 3.11+
- **FastAPI**: 0.104.1 - Modern, fast web framework
- **Uvicorn**: 0.24.0 - ASGI server
- **SQLModel**: 0.0.14 - SQL database ORM (built on SQLAlchemy + Pydantic)

### Database
- **PostgreSQL**: 15 - Primary relational database
- **AsyncPG**: 0.29.0 - Async PostgreSQL driver
- **Alembic**: 1.13.0 - Database migrations

### Caching & Queue
- **Redis**: 7 - Cache and message broker
- **ARQ**: 0.25.0 - Async Redis Queue for background jobs

### Authentication & Security
- **python-jose**: 3.3.0 - JWT token handling
- **passlib**: 1.7.4 - Password hashing (bcrypt)
- **python-dotenv**: 1.0.0 - Environment variable management

### Cloud Services
- **AWS S3**: Video storage via boto3 (1.34.0)
- **AWS CloudFront**: CDN for video delivery
- **OpenAI Whisper API**: Speech-to-text transcription

### Video Processing (Planned)
- **PyAV**: 11.0.0 - FFmpeg bindings for Python
- **OpenCV**: 4.8.1.78 - Computer vision (headless)
- **MoviePy**: 1.0.3 - Video editing
- **PySceneDetect**: Scene detection library

### Audio Processing (Planned)
- **Librosa**: 0.10.1 - Audio analysis
- **Pydub**: 0.25.1 - Audio manipulation
- **SoundFile**: 0.12.1 - Audio I/O

### Development Tools
- **Ruff**: 0.1.9 - Fast Python linter and formatter
- **MyPy**: 1.8.0 - Static type checking
- **Pytest**: 7.4.3 - Testing framework
- **Pytest-asyncio**: 0.21.1 - Async test support
- **Pytest-cov**: 4.1.0 - Coverage reporting

### Utilities
- **HTTPX**: 0.25.2 - Async HTTP client
- **Aiofiles**: 23.2.1 - Async file operations
- **Pydantic Settings**: 2.1.0 - Settings management
- **Email Validator**: 2.1.0 - Email validation

---

## Frontend

### Core Framework
- **Next.js**: 14.0.4 - React framework with App Router
- **React**: 18.2.0 - UI library
- **TypeScript**: 5.3.3 - Type-safe JavaScript

### UI Components
- **Shadcn/ui**: Component library built on Radix UI
  - @radix-ui/react-dialog: 1.0.5
  - @radix-ui/react-dropdown-menu: 2.0.6
  - @radix-ui/react-label: 2.0.2
  - @radix-ui/react-select: 2.0.0
  - @radix-ui/react-separator: 1.0.3
  - @radix-ui/react-slider: 1.1.2
  - @radix-ui/react-slot: 1.0.2
  - @radix-ui/react-tabs: 1.0.4
  - @radix-ui/react-toast: 1.1.5

### Styling
- **Tailwind CSS**: 3.3.6 - Utility-first CSS framework
- **Tailwind Animate**: 1.0.7 - Animation utilities
- **Class Variance Authority**: 0.7.0 - Component variants
- **clsx**: 2.0.0 - Conditional classnames
- **Tailwind Merge**: 2.1.0 - Merge Tailwind classes

### Video & Audio
- **Video.js**: 8.6.1 - HTML5 video player
- **Remotion**: 4.0.80 - Video composition library
- **@remotion/player**: 4.0.80 - Remotion player component
- **Wavesurfer.js**: 7.4.4 - Audio waveform visualization
- **@wavesurfer/react**: 1.0.6 - React wrapper for Wavesurfer

### Timeline & Canvas
- **Konva**: 9.3.0 - 2D canvas library
- **React-Konva**: 18.2.10 - React bindings for Konva

### State Management & API
- **Zustand**: 4.4.7 - Lightweight state management
- **Axios**: 1.6.2 - HTTP client

### Icons
- **Lucide React**: 0.295.0 - Icon library

### Development Tools
- **ESLint**: 8.56.0 - JavaScript linter
- **ESLint Config Next**: 14.0.4 - Next.js ESLint config
- **TypeScript ESLint**: 6.15.0 - TypeScript linting
- **Prettier**: 3.1.1 - Code formatter
- **Vitest**: 1.0.4 - Unit testing framework
- **@vitejs/plugin-react**: 4.2.1 - React plugin for Vitest
- **Playwright**: 1.40.1 - E2E testing framework

### Build Tools
- **Autoprefixer**: 10.4.16 - CSS vendor prefixing
- **PostCSS**: 8.4.32 - CSS processing

---

## Infrastructure

### Containerization
- **Docker**: Container runtime
- **Docker Compose**: Multi-container orchestration

### CI/CD
- **GitHub Actions**: Continuous integration and deployment

### Cloud Infrastructure (Production)
- **AWS EC2/ECS**: Compute for backend and workers
- **AWS S3**: Object storage for videos
- **AWS CloudFront**: CDN for video delivery
- **AWS Secrets Manager**: Secure credential storage

### Monitoring & Logging (Planned)
- **Sentry**: Error tracking
- **Datadog/CloudWatch**: Application monitoring
- **Stripe**: Payment processing

---

## Development Environment

### Local Development
- **Docker Compose**: Local services (PostgreSQL, Redis)
- **Node.js**: 20+ for frontend development
- **Python**: 3.11+ for backend development

### Code Quality
- **Ruff**: Python linting and formatting
- **MyPy**: Python type checking
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting

### Testing
- **Pytest**: Backend unit and integration tests
- **Vitest**: Frontend unit tests
- **Playwright**: End-to-end tests

---

## Architecture Patterns

### Backend
- **RESTful API**: FastAPI routes
- **Dependency Injection**: FastAPI Depends
- **Service Layer**: Business logic separation
- **Repository Pattern**: Database abstraction (via SQLModel)
- **Background Jobs**: ARQ workers for async processing

### Frontend
- **App Router**: Next.js 14 App Router architecture
- **Server Components**: React Server Components where applicable
- **Client Components**: Interactive UI components
- **API Routes**: Next.js API routes for server-side logic

### Data Flow
1. **Upload**: Client → Frontend → S3 (presigned URL)
2. **Transcode**: ARQ Worker → FFmpeg → S3
3. **Transcribe**: ARQ Worker → Whisper API → Database
4. **Process**: User edits → Timeline → Export job
5. **Export**: ARQ Worker → FFmpeg → S3 → Download

---

## Security

### Authentication
- **JWT**: Access tokens (30 min expiry)
- **Refresh Tokens**: Long-lived (30 days)
- **OAuth 2.0**: Google OAuth integration
- **Password Hashing**: bcrypt

### Data Protection
- **HTTPS**: TLS 1.3 enforced
- **S3 Encryption**: AES-256 at rest
- **Database Encryption**: At rest encryption
- **Secrets Management**: AWS Secrets Manager

### Rate Limiting
- Uploads: 5 per hour per user
- API calls: 100 per minute per user
- Exports: 10 per hour per user

---

## Performance Targets

- **Upload speed**: <30s for 500MB
- **Transcription**: <3 min for 30-min video
- **Silence removal**: <30s for 30-min video
- **Export**: <10 min for 30-min video (1080p)
- **Page load**: <1s
- **Time to Interactive**: <2s

---

## Browser Support

### Desktop
- Chrome 100+
- Firefox 100+
- Safari 15+
- Edge 100+

### Mobile
- iOS Safari 15+
- Chrome Android 100+

---

## Future Considerations

### Potential Additions
- **GPU Workers**: For faster video processing
- **WebSocket**: Real-time progress updates
- **GraphQL**: Alternative API layer (if needed)
- **Microservices**: Split into smaller services as scale grows

