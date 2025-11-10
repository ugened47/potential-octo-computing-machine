# Authentication Flow Diagrams

## Registration Flow

```mermaid
sequenceDiagram
    participant U as User/Client
    participant F as Frontend
    participant B as Backend API
    participant DB as Database
    participant S as Security Module

    U->>F: Fill registration form
    F->>F: Validate email format
    F->>F: Check password strength
    F->>B: POST /api/auth/register
    Note over F,B: {email, password, full_name}

    B->>B: Validate request schema
    B->>DB: Check if email exists

    alt Email already exists
        DB-->>B: User found
        B-->>F: 400 Bad Request
        F-->>U: "Email already registered"
    else New email
        DB-->>B: Email available
        B->>S: Hash password (bcrypt)
        S-->>B: Hashed password
        B->>DB: Create user record
        DB-->>B: User created
        B->>S: Generate access token (30min)
        S-->>B: Access token
        B->>S: Generate refresh token (30 days)
        S-->>B: Refresh token
        B-->>F: 201 Created
        Note over B,F: {user, access_token, refresh_token}
        F->>F: Store tokens in localStorage
        F-->>U: Redirect to dashboard
    end
```

## Login Flow

```mermaid
sequenceDiagram
    participant U as User/Client
    participant F as Frontend
    participant B as Backend API
    participant DB as Database
    participant S as Security Module

    U->>F: Enter email & password
    F->>B: POST /api/auth/login
    Note over F,B: {email, password}

    B->>DB: Find user by email

    alt User not found
        DB-->>B: No user
        B-->>F: 401 Unauthorized
        F-->>U: "Incorrect email or password"
    else User exists
        DB-->>B: User record
        B->>S: Verify password
        Note over B,S: Compare with bcrypt hash

        alt Password incorrect
            S-->>B: Password mismatch
            B-->>F: 401 Unauthorized
            F-->>U: "Incorrect email or password"
        else Password correct
            S-->>B: Password valid

            alt User inactive
                B-->>F: 403 Forbidden
                F-->>U: "Account is inactive"
            else User active
                B->>S: Generate access token
                S-->>B: Access token
                B->>S: Generate refresh token
                S-->>B: Refresh token
                B-->>F: 200 OK
                Note over B,F: {user, access_token, refresh_token}
                F->>F: Store tokens
                F-->>U: Redirect to dashboard
            end
        end
    end
```

## Token Refresh Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant B as Backend API
    participant DB as Database
    participant S as Security Module

    Note over F: Access token expired

    F->>F: Detect 401 error
    F->>F: Get refresh token
    F->>B: POST /api/auth/refresh
    Note over F,B: {refresh_token}

    B->>S: Decode refresh token

    alt Invalid token
        S-->>B: Decode failed
        B-->>F: 401 Unauthorized
        F->>F: Clear all tokens
        F->>F: Redirect to login
    else Valid token
        S-->>B: Token payload
        B->>B: Check token type = "refresh"

        alt Wrong token type
            B-->>F: 401 Unauthorized
            Note over B,F: Access token used instead
        else Correct type
            B->>B: Extract user ID from token
            B->>DB: Find user by ID

            alt User not found
                DB-->>B: No user
                B-->>F: 404 Not Found
                F->>F: Clear tokens
                F->>F: Redirect to login
            else User exists
                DB-->>B: User record

                alt User inactive
                    B-->>F: 403 Forbidden
                    F->>F: Clear tokens
                    F->>F: Redirect to login
                else User active
                    B->>S: Generate new access token
                    S-->>B: New access token
                    B->>S: Generate new refresh token
                    S-->>B: New refresh token
                    B-->>F: 200 OK
                    Note over B,F: {access_token, refresh_token}
                    F->>F: Update stored tokens
                    F->>F: Retry original request
                end
            end
        end
    end
```

## Protected Endpoint Access

```mermaid
sequenceDiagram
    participant F as Frontend
    participant B as Backend API
    participant M as Auth Middleware
    participant DB as Database
    participant S as Security Module
    participant E as Endpoint Handler

    F->>B: Request protected endpoint
    Note over F,B: Authorization: Bearer <token>

    B->>M: Intercept request
    M->>M: Extract Bearer token

    alt No token provided
        M-->>F: 403 Forbidden
    else Token provided
        M->>S: Decode JWT token

        alt Invalid/expired token
            S-->>M: Decode failed
            M-->>F: 401 Unauthorized
        else Valid token
            S-->>M: Token payload
            M->>M: Check token type = "access"

            alt Wrong token type
                M-->>F: 401 Unauthorized
                Note over M,F: Refresh token used
            else Correct type
                M->>M: Extract user ID
                M->>DB: Find user by ID

                alt User not found
                    DB-->>M: No user
                    M-->>F: 404 Not Found
                else User exists
                    DB-->>M: User record

                    alt User inactive
                        M-->>F: 403 Forbidden
                    else User active
                        M->>E: Pass request with user
                        E->>E: Process request
                        E-->>F: Success response
                    end
                end
            end
        end
    end
```

## Complete User Journey

```mermaid
flowchart TD
    Start([User Visits App]) --> CheckAuth{Has Valid<br/>Access Token?}

    CheckAuth -->|No| LoginPage[Show Login Page]
    CheckAuth -->|Yes| Dashboard[Show Dashboard]

    LoginPage --> LoginChoice{User Action}
    LoginChoice -->|Login| Login[Enter Credentials]
    LoginChoice -->|Register| Register[Enter Registration Info]

    Login --> ValidateLogin{Valid<br/>Credentials?}
    ValidateLogin -->|No| LoginError[Show Error]
    LoginError --> LoginPage
    ValidateLogin -->|Yes| GetTokens[Receive JWT Tokens]

    Register --> ValidateReg{Valid<br/>Registration?}
    ValidateReg -->|No| RegError[Show Error]
    RegError --> LoginPage
    ValidateReg -->|Yes| GetTokens

    GetTokens --> StoreTokens[Store Tokens<br/>in localStorage]
    StoreTokens --> Dashboard

    Dashboard --> MakeRequest[Make API Request]
    MakeRequest --> AddToken[Add Bearer Token<br/>to Header]
    AddToken --> SendRequest[Send Request]

    SendRequest --> CheckResponse{Response<br/>Status}
    CheckResponse -->|200 OK| ShowData[Display Data]
    CheckResponse -->|401 Unauthorized| RefreshFlow[Try Token Refresh]
    CheckResponse -->|Other Error| ShowError[Show Error]

    RefreshFlow --> RefreshValid{Refresh<br/>Successful?}
    RefreshValid -->|Yes| UpdateTokens[Update Tokens]
    UpdateTokens --> SendRequest
    RefreshValid -->|No| ClearTokens[Clear All Tokens]
    ClearTokens --> LoginPage

    ShowData --> Dashboard
    ShowError --> Dashboard

    Dashboard --> Logout{User<br/>Logout?}
    Logout -->|Yes| CallLogout[POST /api/auth/logout]
    CallLogout --> ClearTokens
    Logout -->|No| Dashboard
```

## Security Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Client[Web Browser]
        Storage[localStorage/sessionStorage]
    end

    subgraph "API Gateway Layer"
        CORS[CORS Middleware]
        RateLimit[Rate Limit Middleware<br/>100 req/min]
        GZip[GZip Compression]
    end

    subgraph "Authentication Layer"
        Bearer[Bearer Token Parser]
        JWTValidator[JWT Token Validator]
        UserLoader[User Loader]
    end

    subgraph "Security Module"
        BCrypt[BCrypt Password Hasher]
        JWTGen[JWT Token Generator]
        JWTDec[JWT Token Decoder]
    end

    subgraph "Business Logic"
        AuthService[Auth Service]
        Endpoints[API Endpoints]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL<br/>Users Table)]
    end

    Client -->|HTTPS Request| CORS
    CORS --> RateLimit
    RateLimit --> GZip
    GZip --> Bearer

    Bearer -->|Protected Routes| JWTValidator
    Bearer -->|Public Routes| Endpoints

    JWTValidator --> JWTDec
    JWTDec --> UserLoader
    UserLoader --> DB
    UserLoader --> Endpoints

    Endpoints --> AuthService
    AuthService --> BCrypt
    AuthService --> JWTGen
    AuthService --> DB

    JWTGen -.->|Store| Storage
    Client -.->|Retrieve| Storage

    style BCrypt fill:#f9f,stroke:#333
    style JWTGen fill:#f9f,stroke:#333
    style JWTDec fill:#f9f,stroke:#333
    style DB fill:#bbf,stroke:#333
    style RateLimit fill:#ffa,stroke:#333
```

## Token Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: User Login/Register

    Created --> Active: Token Generated

    state Active {
        [*] --> InUse
        InUse --> Validated: API Request
        Validated --> InUse: Valid Token
        Validated --> Expired: TTL Exceeded
    }

    Active --> Refreshed: Refresh Token Used
    Refreshed --> Active: New Tokens Generated

    Active --> Expired: Time Limit
    state Expired {
        [*] --> AccessExpired: 30 minutes
        [*] --> RefreshExpired: 30 days
    }

    AccessExpired --> Refreshed: Use Refresh Token
    RefreshExpired --> [*]: Must Re-Login

    Active --> Revoked: User Logout
    Revoked --> [*]

    Expired --> [*]: Token Discarded
```

## Password Security Flow

```mermaid
flowchart LR
    subgraph Registration
        A[Plain Password<br/>MyPass123!] --> B[Validate Strength]
        B --> C{Valid?}
        C -->|No| D[Reject]
        C -->|Yes| E[Truncate to 72 bytes]
        E --> F[bcrypt.hashpw]
        F --> G[Add Random Salt]
        G --> H[Hashed Password<br/>$2b$12$abc...]
        H --> I[(Store in DB)]
    end

    subgraph Login
        J[User Enters Password] --> K[Get Hashed from DB]
        K --> L[bcrypt.checkpw]
        L --> M{Match?}
        M -->|Yes| N[Generate JWT]
        M -->|No| O[Reject Login]
    end

    style F fill:#f96,stroke:#333
    style L fill:#f96,stroke:#333
    style I fill:#bbf,stroke:#333
```

## Error Handling Flow

```mermaid
flowchart TD
    Request[API Request] --> Validation{Request<br/>Validation}

    Validation -->|Invalid| ValidationError[422 Validation Error<br/>Field-level errors]
    Validation -->|Valid| Auth{Authentication<br/>Required?}

    Auth -->|No| Handler[Endpoint Handler]
    Auth -->|Yes| TokenCheck{Token<br/>Valid?}

    TokenCheck -->|No Token| NoAuth[403 Forbidden]
    TokenCheck -->|Invalid/Expired| AuthError[401 Unauthorized]
    TokenCheck -->|Valid| UserCheck{User<br/>Active?}

    UserCheck -->|Inactive| InactiveError[403 Forbidden<br/>Account inactive]
    UserCheck -->|Active| PermCheck{Has<br/>Permission?}

    PermCheck -->|No| PermError[403 Authorization Error]
    PermCheck -->|Yes| Handler

    Handler --> DBOp{Database<br/>Operation}

    DBOp -->|Unique Violation| Conflict[409 Conflict]
    DBOp -->|FK Violation| NotFound[404 Not Found]
    DBOp -->|Other Error| DBError[500 Database Error]
    DBOp -->|Success| Success[200/201 Success]

    ValidationError --> ErrorFormat[Standard Error Format]
    NoAuth --> ErrorFormat
    AuthError --> ErrorFormat
    InactiveError --> ErrorFormat
    PermError --> ErrorFormat
    Conflict --> ErrorFormat
    NotFound --> ErrorFormat
    DBError --> ErrorFormat

    ErrorFormat --> Response[JSON Response]
    Success --> Response

    style ValidationError fill:#faa,stroke:#333
    style AuthError fill:#faa,stroke:#333
    style InactiveError fill:#faa,stroke:#333
    style PermError fill:#faa,stroke:#333
    style Conflict fill:#faa,stroke:#333
    style NotFound fill:#faa,stroke:#333
    style DBError fill:#faa,stroke:#333
    style Success fill:#afa,stroke:#333
```
