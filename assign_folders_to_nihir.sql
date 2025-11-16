-- SQL commands to assign multiple folders to nihir.shah5@gmail.com

-- Method 1: If using the junction table approach (user_folder_assignments)
-- First, get the user ID for nihir.shah5@gmail.com
-- Then insert all folder assignments

-- Step 1: Find the user ID (run this first to get the user's UUID)
SELECT id, email FROM users WHERE email = 'nihir.shah5@gmail.com';

-- Step 2: Insert multiple folder assignments
-- Replace 'USER_ID_FROM_STEP_1' with the actual UUID from step 1
INSERT INTO user_folder_assignments (user_id, folder_number) VALUES
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 1),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 9),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 17),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 21),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 23),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 33),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 37),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 40),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 45),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 46),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 47),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 48),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 49),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 50),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 55),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 57),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 60),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 63),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 65),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 66),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 68),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 69),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 71),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 73),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 74),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 75),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 78),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 79),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 81),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 83),
((SELECT id FROM users WHERE email = 'nihir.shah5@gmail.com'), 84)
ON CONFLICT (user_id, folder_number) DO NOTHING; -- Prevents duplicates if some already exist

-- Method 2A: If you want to keep using the existing 'assigned_folder' column (singular)
-- First, modify the existing column type to handle larger data
ALTER TABLE users ALTER COLUMN assigned_folder TYPE JSONB USING assigned_folder::text::jsonb;

-- If the above fails because of existing data format, use this alternative:
-- ALTER TABLE users ALTER COLUMN assigned_folder TYPE TEXT;
-- Then update the specific user:
UPDATE users 
SET assigned_folder = '[1,9,17,21,23,33,37,40,45,46,47,48,49,50,55,57,60,63,65,66,68,69,71,73,74,75,78,79,81,83,84]'::jsonb
WHERE email = 'nihir.shah5@gmail.com';

-- Method 2B: If you want to create a NEW 'assigned_folders' column (plural) and keep the old one
ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_folders JSONB DEFAULT '[]'::jsonb;

UPDATE users 
SET assigned_folders = '[1,9,17,21,23,33,37,40,45,46,47,48,49,50,55,57,60,63,65,66,68,69,71,73,74,75,78,79,81,83,84]'::jsonb
WHERE email = 'nihir.shah5@gmail.com';

-- Method 3: If using comma-separated string in users table
-- First, add the assigned_folders column if it doesn't exist (as TEXT for comma-separated)
ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_folders TEXT DEFAULT '';

-- Then update the user's assigned_folders column with comma-separated string
UPDATE users 
SET assigned_folders = '1,9,17,21,23,33,37,40,45,46,47,48,49,50,55,57,60,63,65,66,68,69,71,73,74,75,78,79,81,83,84'
WHERE email = 'nihir.shah5@gmail.com';

-- Verification queries:

-- If using junction table approach:
SELECT u.email, uf.folder_number
FROM users u
JOIN user_folder_assignments uf ON u.id = uf.user_id
WHERE u.email = 'nihir.shah5@gmail.com'
ORDER BY uf.folder_number;

-- If using JSON array approach with existing 'assigned_folder' column:
SELECT email, assigned_folder
FROM users
WHERE email = 'nihir.shah5@gmail.com';

-- If using JSON array approach with new 'assigned_folders' column:
SELECT email, assigned_folders
FROM users
WHERE email = 'nihir.shah5@gmail.com';

-- Count total folders assigned:
SELECT u.email, COUNT(uf.folder_number) as total_folders
FROM users u
JOIN user_folder_assignments uf ON u.id = uf.user_id
WHERE u.email = 'nihir.shah5@gmail.com'
GROUP BY u.email;