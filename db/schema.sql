-- Job-Search Agent tracker schema (SQLite)
-- Create the database:  sqlite3 job_search.db < schema.sql
CREATE TABLE IF NOT EXISTS Job_Tracker (
    Job_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Date_Created TEXT DEFAULT (CURRENT_DATE),  -- date entry was added (YYYY-MM-DD)
    Source TEXT,             -- LinkedIn, Indeed, Company Site, ...
    Agent TEXT,              -- which agent/session created this entry
    App_URL TEXT,            -- primary application link (de-dupe key)
    Other_App_URL TEXT,      -- secondary link (e.g., the ATS posting actually read)
    Title TEXT NOT NULL,
    Company TEXT NOT NULL,
    Location TEXT,           -- Remote, Hybrid, City/State
    JD TEXT,                 -- 1-2 sentence summary of the job description
    Salary_Range TEXT,       -- verbatim from posting, or 'Unlisted'
    Employment_Type TEXT,    -- Full-time, Contract, ...
    Date_Posted TEXT,        -- ISO date
    HM_or_TA TEXT,           -- named hiring contact, or 'Not listed'
    Job_Track TEXT,          -- which rubric track scored this role
    Fitness_Score INTEGER,   -- 1-5 per the rubric (targeting lens: is this the kind of role I want?)
    Recruiter_Match INTEGER, -- 0-100 % (recruiter lens: would a screener shortlist this resume?)
    Key_Gaps TEXT,
    Anchor_Story TEXT,
    Notes TEXT,              -- PROVISIONAL flags, source URLs, scratchpad
    Status TEXT DEFAULT 'To Apply',
    Date_Updated TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_app_url ON Job_Tracker(App_URL);
