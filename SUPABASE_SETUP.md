# Supabase Auth Setup Guide

## Overview
Supabase provides authentication, database, and real-time features for Code Archaeologist.

## Step 1: Create Supabase Project

1. Go to https://supabase.com and sign up/login
2. Click "New Project"
3. Choose organization, name it "code-archaeologist"
4. Select region closest to your users
5. Wait for project to be created (~2 minutes)

## Step 2: Get API Keys

In your Supabase dashboard:

1. Go to **Project Settings** → **API**
2. Copy these values:
   - `Project URL` → Set as `SUPABASE_URL`
   - `anon public` → Set as `SUPABASE_KEY`
   - `service_role secret` → Set as `SUPABASE_SERVICE_KEY` (keep this secret!)

## Step 3: Configure Environment

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...
```

## Step 4: Create Database Tables

In Supabase Dashboard, go to **SQL Editor** → **New Query**, run:

```sql
-- Users profile table (extends Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company TEXT,
    plan TEXT DEFAULT 'free', -- free, pro, team, enterprise
    analyses_used INTEGER DEFAULT 0,
    analyses_limit INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    trace_data JSONB,
    graph_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analysis history
CREATE TABLE IF NOT EXISTS public.analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    project_id UUID REFERENCES public.projects(id),
    file_name TEXT NOT NULL,
    language TEXT NOT NULL,
    query_type TEXT,
    query_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Allow insert on signup" 
    ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- RLS Policies for projects
CREATE POLICY "Users can view own projects" 
    ON public.projects FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own projects" 
    ON public.projects FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects" 
    ON public.projects FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects" 
    ON public.projects FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for analyses
CREATE POLICY "Users can view own analyses" 
    ON public.analyses FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own analyses" 
    ON public.analyses FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Function to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, plan, analyses_used, analyses_limit)
    VALUES (
        NEW.id, 
        NEW.email, 
        NEW.raw_user_meta_data->>'full_name',
        'free',
        0,
        5
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
```

Click **Run** to execute.

## Step 5: Configure Auth Settings

In Supabase Dashboard:

1. Go to **Authentication** → **Settings**
2. Under **Site URL**, set: `http://localhost:8501` (for local dev)
3. Under **Redirect URLs**, add:
   - `http://localhost:8501`
   - `https://your-production-domain.com`

## Step 6: Enable Providers (Optional)

In **Authentication** → **Providers**:

Enable social logins:
- Google (requires Google OAuth setup)
- GitHub (requires GitHub OAuth app)
- Or keep email/password only

## Step 7: Test Authentication

Start the backend:
```bash
uvicorn backend.main:app --reload
```

Test endpoints with curl:

```bash
# 1. Sign up
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "full_name": "Test User"}'

# 2. Login (use the email/password from signup)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Response: {"access_token": "...", "token_type": "bearer", ...}

# 3. Access protected endpoint
curl -X POST http://localhost:8000/trace \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source_path": "tests/sample_code.py"}'

# 4. Get profile
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## API Endpoints

### Auth Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/signup` | Create new account | No |
| POST | `/auth/login` | Login and get token | No |
| POST | `/auth/logout` | Logout | Yes |
| GET | `/auth/me` | Get current user profile | Yes |
| PUT | `/auth/me` | Update profile | Yes |
| POST | `/auth/reset-password` | Request password reset | No |
| POST | `/auth/refresh` | Refresh access token | No |
| DELETE | `/auth/account` | Delete account | Yes |

### Protected Analysis Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/trace` | Trace source file | Yes + check limit |
| POST | `/graph` | Build graph | Yes |
| POST | `/query` | Run graph query | Yes |

### Public Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/openapi.json` | OpenAPI spec |

## Usage Limits

| Plan | Analyses/Month | Features |
|------|----------------|----------|
| Free | 5 | Basic tracing, Python only |
| Pro | 50 | All languages, PDF export |
| Team | 500 | Team sharing, batch analysis |
| Enterprise | Unlimited | On-premise, SLA |

Limits are enforced via `check_analysis_limit` dependency on `/trace` endpoint.

## Troubleshooting

### "Supabase credentials not configured"
- Check `.env` file exists and has correct values
- Restart the server after editing `.env`

### "Failed to create user"
- Check Supabase Auth settings allow email/password signup
- Verify email format is valid

### "Authentication required" (401)
- Include `Authorization: Bearer <token>` header
- Token may have expired, get a new one via `/auth/login`

### "Analysis limit reached" (403)
- User has used all their monthly analyses
- Upgrade plan or wait for next billing cycle

### Row Level Security errors
- Ensure SQL setup was run completely
- Check user is authenticated before accessing tables
