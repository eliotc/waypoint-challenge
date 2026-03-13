-- Kingsford University seed data (no embeddings — seed.py adds those for courses, knowledge_docs, scholarships)

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
 'Explore all five faculties, meet academics, tour labs and student spaces. Free parking on campus. Register online to receive your welcome pack in advance.',
 2000, 834),

('Engineering & Tech Info Session',
 'InfoSession',
 '2026-03-19 18:00+11', '2026-03-19 19:30+11',
 'Engineering Precinct, Room E201',
 'Deep dive into our CS, Software Engineering, Cybersecurity, and Cloud Computing programs. Q&A with current students and program directors.',
 80, 31),

('Postgrad Open Evening',
 'InfoSession',
 '2026-03-25 18:00+11', '2026-03-25 20:00+11',
 'Online (Zoom)',
 'Explore our Masters and Graduate Certificate programs. Hear from program directors and alumni about career outcomes and study pathways.',
 500, 211),

('Health Sciences Campus Tour',
 'CampusTour',
 '2026-03-22 10:00+11', '2026-03-22 11:30+11',
 'Health Sciences Building, 45 Wellbeing Way',
 'Guided tour of simulation labs, clinical skills rooms, and student common areas. Meet Nursing and OT students in person.',
 20, 9),

('Business & Commerce Info Night',
 'InfoSession',
 '2026-03-26 17:30+11', '2026-03-26 19:00+11',
 'Business School Atrium',
 'MBA, Finance, and BBA program overview. Scholarship information, entry requirement Q&A, and networking with alumni.',
 120, 54),

('Saturday Campus Tour',
 'CampusTour',
 '2026-03-15 10:00+11', '2026-03-15 11:30+11',
 'Main Campus Welcome Centre',
 'General campus tour covering library, student hub, accommodation, sports facilities, and key buildings. No registration required — just show up!',
 25, 12),

('Saturday Campus Tour',
 'CampusTour',
 '2026-03-22 10:00+11', '2026-03-22 11:30+11',
 'Main Campus Welcome Centre',
 'General campus tour covering library, student hub, accommodation, sports facilities, and key buildings. No registration required — just show up!',
 25, 18),

('Scholarship & Financial Aid Webinar',
 'Webinar',
 '2026-03-17 12:00+11', '2026-03-17 13:00+11',
 'Online (Zoom)',
 'Learn about merit scholarships, equity bursaries, and the application process for 2027 entry. Our Financial Aid team will walk through HECS-HELP eligibility, payment plans, and how to apply.',
 1000, 634),

('Arts & Humanities Open Studio',
 'InfoSession',
 '2026-03-28 14:00+11', '2026-03-28 16:00+11',
 'Creative Arts Building, Studio A3',
 'Explore Psychology, Digital Media, and Education programs. Live demonstrations in our film studio and UX design lab.',
 60, 27),

('International Students Welcome Session',
 'InfoSession',
 '2026-04-01 10:00+11', '2026-04-01 12:00+11',
 'International Centre, Ground Floor',
 'Dedicated session for prospective international students covering visa pathways, English language requirements, on-campus housing, and student support services.',
 150, 88);

-- ── Scholarships ───────────────────────────────────────────────────────────────
INSERT INTO scholarships (name, type, faculty, annual_value_aud, duration_years, eligibility, description, application_deadline) VALUES

('Kingsford Academic Excellence Scholarship',
 'Merit', NULL, 8000, 3,
 'ATAR 95 or above, commencing undergraduate domestic student.',
 'Our flagship merit scholarship rewards outstanding academic achievement. Valued at $8,000 per year for the duration of your degree. Recipients are also invited to the annual Excellence Dinner and mentoring program.',
 '2026-10-31'),

('Vice-Chancellor''s Future Leaders Award',
 'Merit', NULL, 5000, 4,
 'ATAR 90 or above, demonstrated leadership in school or community.',
 'Awarded to students who show exceptional leadership potential alongside academic achievement. Includes a $5,000 annual stipend and access to the Future Leaders development program.',
 '2026-10-31'),

('Kingsford Equity Bursary',
 'Equity', NULL, 3000, 1,
 'Domestic student experiencing financial hardship; household income below $50,000 p.a.',
 'A needs-based bursary of $3,000 to help cover living and study costs. Renewable annually subject to satisfactory academic progress and continued eligibility. Applications assessed on a rolling basis.',
 NULL),

('First-in-Family Scholarship',
 'Equity', NULL, 4000, 3,
 'First person in your immediate family to attend university; domestic student.',
 'Supporting students who are blazing a trail in higher education. Provides $4,000 per year plus access to peer mentoring, career workshops, and a dedicated First-in-Family support coordinator.',
 '2026-11-15'),

('Engineering & Technology Industry Scholarship',
 'Faculty', 'Engineering & Technology', 6000, 3,
 'Enrolling in an undergraduate Engineering & Technology degree; ATAR 85+.',
 'Co-funded by our industry partners including TechVic and Melbourne Digital Alliance. Includes $6,000 per year plus a guaranteed industry placement in Year 2. Strong preference for students with demonstrated interest in AI or cybersecurity.',
 '2026-10-15'),

('Health Sciences Clinical Excellence Award',
 'Faculty', 'Health Sciences', 4500, 3,
 'Enrolling in Nursing, Public Health, or Occupational Therapy; demonstrated commitment to community health.',
 'Supports future healthcare professionals with $4,500 per year. Recipients complete an additional 40-hour community health placement and are fast-tracked for clinical coordinator roles post-graduation.',
 '2026-11-01'),

('Kingsford International Student Scholarship',
 'International', NULL, 7000, 3,
 'International student (student visa); offer of admission to a Kingsford undergraduate degree.',
 'Reduces the cost of studying in Australia for high-achieving international students. Valued at $7,000 per year off tuition fees. Recipients must maintain a GPA of 3.0 or above.',
 '2026-09-30'),

('Women in STEM Scholarship',
 'Merit', 'Engineering & Technology', 5000, 3,
 'Female or non-binary student enrolling in CS, Software Engineering, Data Science, or Cybersecurity; ATAR 80+.',
 'Encouraging diversity in technology. Provides $5,000 per year plus a mentoring relationship with a senior woman in tech from our industry network. Open to domestic and international students.',
 '2026-10-31');
