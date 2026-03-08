-- Kingsford University seed data (no embeddings — seed.py adds those)

-- ── Courses ───────────────────────────────────────────────────────────────────
INSERT INTO courses (code, name, faculty, level, study_mode, duration_years, atar_cutoff, annual_fee_aud, description, career_outcomes) VALUES

-- Engineering & Technology
('CS101',  'Bachelor of Computer Science',              'Engineering & Technology', 'Undergraduate', 'Full-time', 3.0, 85, 14500, 'A rigorous program covering algorithms, systems, AI, and software engineering. Strong industry placement record.', 'Software engineer, data scientist, systems architect, startup founder.'),
('CS201',  'Bachelor of Software Engineering (Hons)',   'Engineering & Technology', 'Undergraduate', 'Full-time', 4.0, 88, 14500, 'Combines computer science fundamentals with professional engineering practice. Accredited by Engineers Australia.', 'Software engineer, DevOps engineer, technical lead, solutions architect.'),
('DS301',  'Master of Data Science',                   'Engineering & Technology', 'Postgraduate',  'Full-time', 2.0, NULL, 18000, 'Advanced machine learning, statistical modelling, and big-data engineering for graduates with a quantitative background.', 'Data scientist, ML engineer, AI researcher, analytics manager.'),
('CY401',  'Bachelor of Cybersecurity',                'Engineering & Technology', 'Undergraduate', 'Full-time', 3.0, 80, 14500, 'Hands-on coverage of network security, ethical hacking, cryptography, and digital forensics. Includes industry certifications.', 'Security analyst, penetration tester, incident responder, CISO pathway.'),
('IT501',  'Graduate Certificate in Cloud Computing',  'Engineering & Technology', 'Postgraduate',  'Online',    0.5, NULL, 8000,  'Practical cloud architecture on AWS, GCP, and Azure. Ideal for working professionals upskilling quickly.', 'Cloud architect, DevOps engineer, infrastructure lead.'),

-- Business & Commerce
('BA101',  'Bachelor of Business Administration',      'Business & Commerce', 'Undergraduate', 'Full-time', 3.0, 75, 13000, 'Broad business degree covering management, marketing, finance, and entrepreneurship with a Melbourne focus.', 'Manager, entrepreneur, consultant, marketing specialist.'),
('FN201',  'Bachelor of Finance',                      'Business & Commerce', 'Undergraduate', 'Full-time', 3.0, 78, 13000, 'Deep dive into financial markets, corporate finance, investment analysis, and risk management.', 'Financial analyst, investment banker, fund manager, CFO pathway.'),
('MB301',  'Master of Business Administration',        'Business & Commerce', 'Postgraduate',  'Part-time', 2.0, NULL, 22000, 'Executive MBA designed for professionals with 3+ years experience. Blended delivery — weekend intensives plus online.', 'Senior manager, C-suite executive, consultant, entrepreneur.'),
('MK401',  'Bachelor of Marketing & Communications',  'Business & Commerce', 'Undergraduate', 'Full-time', 3.0, 72, 13000, 'Strategic marketing, digital advertising, brand management, and content creation in the age of AI.', 'Marketing manager, brand strategist, digital marketer, PR specialist.'),

-- Arts & Humanities
('PS101',  'Bachelor of Psychology',                   'Arts & Humanities', 'Undergraduate', 'Full-time', 3.0, 78, 12500, 'Accredited psychology degree with placements in clinical, organisational, and community settings.', 'Psychologist (with further study), counsellor, HR specialist, researcher.'),
('DM201',  'Bachelor of Digital Media',               'Arts & Humanities', 'Undergraduate', 'Full-time', 3.0, 70, 12500, 'Creative program combining film, animation, UX design, and social media. State-of-the-art studio facilities.', 'UX designer, content creator, film producer, art director.'),
('EN301',  'Master of Education',                      'Arts & Humanities', 'Postgraduate',  'Part-time', 2.0, NULL, 14000, 'For practising teachers seeking to specialise in leadership, curriculum design, or inclusive education.', 'School principal, curriculum coordinator, education consultant.'),

-- Health Sciences
('NU101',  'Bachelor of Nursing',                      'Health Sciences', 'Undergraduate', 'Full-time', 3.0, 72, 13500, 'AHPRA-accredited nursing degree with 800+ hours of clinical placement across Melbourne hospitals.', 'Registered nurse, clinical coordinator, nurse practitioner pathway.'),
('PH201',  'Bachelor of Public Health',               'Health Sciences', 'Undergraduate', 'Full-time', 3.0, 68, 13000, 'Population health, epidemiology, health policy, and global health. Strong research component.', 'Public health officer, health policy analyst, epidemiologist, NGO roles.'),
('OT301',  'Master of Occupational Therapy',          'Health Sciences', 'Postgraduate',  'Full-time', 2.0, NULL, 19000, 'AHPRA-accredited graduate-entry OT for students with a relevant bachelor degree.', 'Occupational therapist in hospitals, aged care, disability, and community settings.');

-- ── Events ────────────────────────────────────────────────────────────────────
INSERT INTO events (title, event_type, start_at, end_at, location, description, max_capacity, spots_left) VALUES

('Kingsford Open Day 2026',
 'OpenDay',
 '2026-03-21 09:00+11', '2026-03-21 16:00+11',
 'Main Campus, Kingsford Blvd, Melbourne',
 'Explore faculties, meet academics, tour labs and student spaces. Free parking on campus.',
 2000, 834),

('Engineering & Tech Info Session',
 'InfoSession',
 '2026-03-14 11:00+11', '2026-03-14 12:30+11',
 'Engineering Precinct, Room E201',
 'Deep dive into our CS, Software Engineering, and Cybersecurity programs. Q&A with current students.',
 80, 23),

('Postgrad Open Evening',
 'InfoSession',
 '2026-03-18 18:00+11', '2026-03-18 20:00+11',
 'Online (Zoom)',
 'Explore our Masters and Graduate Certificate programs. Hear from program directors and alumni.',
 500, 211),

('Health Sciences Campus Tour',
 'CampusTour',
 '2026-03-12 10:00+11', '2026-03-12 11:30+11',
 'Health Sciences Building, 45 Wellbeing Way',
 'Guided tour of simulation labs, clinical skills rooms, and student common areas.',
 20, 7),

('Business & Commerce Info Night',
 'InfoSession',
 '2026-03-19 17:30+11', '2026-03-19 19:00+11',
 'Business School Atrium',
 'MBA, Finance, and BBA program overview. Scholarship information and entry requirement Q&A.',
 120, 54),

('Saturday Campus Tour',
 'CampusTour',
 '2026-03-15 10:00+11', '2026-03-15 11:30+11',
 'Main Campus Welcome Centre',
 'General campus tour covering library, student hub, accommodation, and key facilities.',
 25, 12),

('Scholarship Webinar',
 'Webinar',
 '2026-03-11 12:00+11', '2026-03-11 13:00+11',
 'Online (Zoom)',
 'Learn about merit scholarships, equity bursaries, and the application process for 2027 entry.',
 1000, 678);
