"""
Supabase client configuration and initialization
"""

import os
from functools import lru_cache
from supabase import create_client, Client

# Load from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # anon key for client
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # service role key for admin


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client (anon key) for user operations
    Cached to avoid creating multiple clients
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Supabase credentials not configured. "
            "Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@lru_cache()
def get_supabase_admin() -> Client:
    """
    Get Supabase admin client (service role key) for admin operations
    Use with caution - bypasses RLS policies
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError(
            "Supabase admin credentials not configured. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
        )
    
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def init_supabase_tables():
    """
    Initialize required tables in Supabase if they don't exist
    Run this once during setup
    """
    admin = get_supabase_admin()
    
    # Note: In production, use Supabase migrations or dashboard to create tables
    # This is a reference for the schema:
    
    TABLES_SQL = """
    -- Users table (managed by Supabase Auth, but we can add metadata)
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
        source_code TEXT, -- stored temporarily during analysis
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
    
    -- Teams (for team plan)
    CREATE TABLE IF NOT EXISTS public.teams (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        name TEXT NOT NULL,
        owner_id UUID REFERENCES auth.users(id) NOT NULL,
        plan TEXT DEFAULT 'team',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Team members
    CREATE TABLE IF NOT EXISTS public.team_members (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        team_id UUID REFERENCES public.teams(id) NOT NULL,
        user_id UUID REFERENCES auth.users(id) NOT NULL,
        role TEXT DEFAULT 'member', -- owner, admin, member
        joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(team_id, user_id)
    );
    
    -- Enable RLS
    ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;
    
    -- RLS Policies
    CREATE POLICY "Users can view own profile" 
        ON public.profiles FOR SELECT USING (auth.uid() = id);
    
    CREATE POLICY "Users can update own profile" 
        ON public.profiles FOR UPDATE USING (auth.uid() = id);
    
    CREATE POLICY "Users can view own projects" 
        ON public.projects FOR SELECT USING (auth.uid() = user_id);
    
    CREATE POLICY "Users can create own projects" 
        ON public.projects FOR INSERT WITH CHECK (auth.uid() = user_id);
    
    CREATE POLICY "Users can update own projects" 
        ON public.projects FOR UPDATE USING (auth.uid() = user_id);
    
    CREATE POLICY "Users can delete own projects" 
        ON public.projects FOR DELETE USING (auth.uid() = user_id);
    """
    
    # In practice, execute this SQL in Supabase dashboard
    print("Table schema defined. Execute in Supabase SQL Editor:")
    print(TABLES_SQL)
