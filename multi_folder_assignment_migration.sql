-- Migration script to support multiple folder assignments

-- Step 1: Create the new junction table
CREATE TABLE user_folder_assignments (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    folder_number INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, folder_number)
);

-- Step 2: Migrate existing single folder assignments
INSERT INTO user_folder_assignments (user_id, folder_number)
SELECT u.id, u.assigned_folder
FROM users u
WHERE u.assigned_folder IS NOT NULL;

-- Step 3: Add indexes for better performance
CREATE INDEX idx_user_folder_assignments_user_id ON user_folder_assignments(user_id);
CREATE INDEX idx_user_folder_assignments_folder_number ON user_folder_assignments(folder_number);

-- Step 4: (Optional) Drop the old column after migration is confirmed
-- ALTER TABLE users DROP COLUMN assigned_folder;

-- Useful queries after migration:

-- Get all folders for a specific user
SELECT uf.folder_number
FROM user_folder_assignments uf
JOIN users u ON u.id = uf.user_id
WHERE u.email = 'user@example.com'
ORDER BY uf.folder_number;

-- Get all users assigned to a specific folder
SELECT u.email, u.id
FROM users u
JOIN user_folder_assignments uf ON u.id = uf.user_id
WHERE uf.folder_number = 10;

-- Get users with multiple folder assignments
SELECT u.email, COUNT(uf.folder_number) as folder_count, 
       ARRAY_AGG(uf.folder_number ORDER BY uf.folder_number) as folders
FROM users u
JOIN user_folder_assignments uf ON u.id = uf.user_id
GROUP BY u.id, u.email
HAVING COUNT(uf.folder_number) > 1;

-- Add multiple folders to a user
-- Replace 'user-uuid-here' with actual user ID
INSERT INTO user_folder_assignments (user_id, folder_number) VALUES
('user-uuid-here', 25),
('user-uuid-here', 30),
('user-uuid-here', 45)
ON CONFLICT (user_id, folder_number) DO NOTHING; -- Ignore if already exists