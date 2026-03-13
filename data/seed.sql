-- Kingsford University seed data (no embeddings — seed.py adds those for courses, knowledge_docs, scholarships)

-- ── Courses ───────────────────────────────────────────────────────────────────
INSERT INTO courses (code, name, faculty, level, study_mode, duration_years, atar_cutoff, annual_fee_aud, description, career_outcomes) VALUES

-- Engineering & Technology
('CS101', 'Bachelor of Computer Science', 'Engineering & Technology', 'Undergraduate', 'Full-time', 3.0, 85, 14500,
 'A rigorous three-year program covering algorithms, data structures, operating systems, AI, machine learning, and full-stack software engineering. Students choose a specialisation in Year 2 from Artificial Intelligence, Cybersecurity, or Cloud Systems. All students complete a capstone industry project in their final semester, working in teams on real briefs from partner companies such as Atlassian, Canva, and ANZ. The degree is accredited by the Australian Computer Society (ACS) at the Professional level. Average class size is 28 students, and first-year students receive a dedicated academic mentor.',
 'Graduates enter roles across software development, data engineering, AI research, and tech entrepreneurship. Median starting salary is $82,000. Common employers include Atlassian, Canva, ANZ, Deloitte, and Melbourne-based startups. With experience, graduates progress to senior engineer, engineering manager, or CTO roles. Several alumni have founded funded startups including two ASX-listed companies.'),

('CS201', 'Bachelor of Software Engineering (Hons)', 'Engineering & Technology', 'Undergraduate', 'Full-time', 4.0, 88, 14500,
 'An accredited four-year Honours program that combines computer science foundations with professional engineering practice. The curriculum spans software architecture, distributed systems, agile delivery, human-computer interaction, and project management. Year 3 includes a 12-week industry placement with one of 40+ partner companies. The Honours thesis in Year 4 allows students to pursue original research under a named supervisor. Accredited by Engineers Australia, making graduates eligible for Chartered Engineer status after two years of professional experience.',
 'Graduates work as software engineers, DevOps engineers, technical leads, and solutions architects. Median starting salary is $87,000 — among the highest for engineering graduates in Victoria. Top employers include ThoughtWorks, REA Group, AWS, and major banks. The Honours qualification opens doors to PhD programs at Melbourne, RMIT, and international universities.'),

('DS301', 'Master of Data Science', 'Engineering & Technology', 'Postgraduate', 'Full-time', 2.0, NULL, 18000,
 'A two-year postgraduate program for graduates with a quantitative bachelor degree (maths, statistics, computer science, or related). Core units cover statistical modelling, machine learning, deep learning, big-data engineering (Spark, Hadoop), natural language processing, and data ethics. Students complete a data science consulting project with an industry partner in Semester 3, and a 12,000-word research thesis in Semester 4. Entry requires a bachelor degree with a credit average or above. No ATAR is required — applicants are assessed on academic transcripts.',
 'Graduates enter roles as data scientists, ML engineers, AI researchers, and analytics managers across finance, healthcare, retail, and government. Median starting salary is $98,000. Top employers include CommBank, Seek, Telstra, and data consultancies. Many graduates go on to PhD programs or research roles at CSIRO and university labs.'),

('CY401', 'Bachelor of Cybersecurity', 'Engineering & Technology', 'Undergraduate', 'Full-time', 3.0, 80, 14500,
 'A hands-on three-year degree covering network security, ethical hacking, cryptography, digital forensics, incident response, and security governance. Students gain access to Kingsford''s dedicated Cyber Range — a simulated enterprise environment used for penetration testing labs and capture-the-flag competitions. The program prepares students for industry certifications including CompTIA Security+, CEH, and CISSP (foundation). In Year 3, students complete a 10-week internship with a security firm or government agency. Industry partners include ASD, KPMG, Telstra Security, and a number of Melbourne-based security consultancies.',
 'Graduates work as security analysts, penetration testers, incident responders, and SOC analysts. Median starting salary is $79,000. The program has a clear pathway to CISO roles with 8–10 years of experience. Government and defence employers are strong recruiters, and several graduates have joined the Australian Signals Directorate (ASD) and the Australian Cyber Security Centre (ACSC).'),

('IT501', 'Graduate Certificate in Cloud Computing', 'Engineering & Technology', 'Postgraduate', 'Online', 0.5, NULL, 8000,
 'A six-month online program designed for working IT professionals who want to move into cloud architecture or DevOps. Units cover cloud fundamentals (AWS, GCP, Azure), infrastructure-as-code with Terraform, container orchestration with Kubernetes, site reliability engineering (SRE), and cloud security. All assessments are practical — students deploy real infrastructure to cloud accounts provided by the program. Delivery is 100% asynchronous, making it suitable for full-time professionals. Completion grants credit toward the Master of Information Technology if students choose to continue.',
 'Graduates move into cloud architect, DevOps engineer, and infrastructure lead roles, typically with an immediate salary uplift of $15,000–$25,000. Employers actively recruiting graduates include AWS partner firms, Deloitte Cloud, Accenture, and state government digital units.'),

-- Business & Commerce
('BA101', 'Bachelor of Business Administration', 'Business & Commerce', 'Undergraduate', 'Full-time', 3.0, 75, 13000,
 'A three-year broad-based business degree structured around four pillars: management and leadership, marketing and communications, finance and accounting, and entrepreneurship and innovation. In Year 2, students choose a major from: Management, Entrepreneurship, or International Business. All students complete a 120-hour professional placement and a live consulting project for a Melbourne business in their final year. The program includes a Study Tour elective to Southeast Asia or Europe. Class sizes are capped at 35, and students are assigned a business mentor from the Kingsford Alumni Network.',
 'Graduates take on roles as business analysts, marketing coordinators, operations managers, and startup founders. Median starting salary is $68,000. Employers include Deloitte, PwC, local government, and fast-growth startups. Entrepreneurship major graduates have collectively founded 14 businesses in the past five years, three of which have received venture capital funding.'),

('FN201', 'Bachelor of Finance', 'Business & Commerce', 'Undergraduate', 'Full-time', 3.0, 78, 13000,
 'A rigorous three-year degree covering financial markets, corporate finance, investment analysis, derivatives, risk management, and financial modelling. Students use Bloomberg terminals from Year 1 and complete a semester-long simulated portfolio management exercise. In Year 3, students choose a specialisation in either Investment Banking or Financial Risk. The program is CFA Institute-affiliated, meaning students are well-prepared for the CFA Level 1 exam upon graduation. An industry internship in Year 2 or 3 is strongly encouraged and supported by the Careers team.',
 'Graduates work as financial analysts, investment bankers, risk managers, and fund managers. Median starting salary is $78,000, rising significantly in investment banking and funds management. Top employers include Macquarie Group, NAB, Westpac Institutional Bank, and boutique asset managers. The CFA pathway opens international opportunities in London, Singapore, and New York.'),

('MB301', 'Master of Business Administration', 'Business & Commerce', 'Postgraduate', 'Part-time', 2.0, NULL, 22000,
 'An executive MBA designed for professionals with a minimum of three years work experience. Delivered in a blended format — intensive weekend workshops once per month plus online learning between sessions — so students can continue working full-time. The curriculum covers strategic management, financial decision-making, leadership and organisational behaviour, marketing strategy, and digital transformation. A signature feature is the Global Business Immersion: a week-long trip to a major business hub (Singapore, Tokyo, or London) in Semester 3. Students complete a strategic consulting project for a real organisation as their capstone.',
 'MBA graduates move into senior management, C-suite, and consulting roles. Median post-MBA salary uplift is 28% within two years of graduation. Employers include the Big 4 consulting firms, ASX-listed corporates, and government agencies. Many graduates launch their own businesses, backed by the Kingsford Startup Studio alumni network.'),

('MK401', 'Bachelor of Marketing & Communications', 'Business & Commerce', 'Undergraduate', 'Full-time', 3.0, 72, 13000,
 'A creative and strategic three-year degree covering brand management, digital marketing, content creation, advertising, public relations, and consumer behaviour. Students work on live campaigns for real brands through the Kingsford Marketing Studio — a learning agency that serves local and national clients. The program integrates emerging technology including AI-powered marketing tools, data analytics, and social media management platforms. Students can choose a major in Digital Marketing, Brand Strategy, or Public Relations. A 150-hour industry placement is embedded in Year 3.',
 'Graduates work as marketing managers, brand strategists, digital marketers, content creators, and PR specialists. Median starting salary is $64,000. Employers include McCann, Ogilvy, major retailers, media agencies, and in-house marketing teams at ASX companies. Digital marketing majors are in particularly high demand, with graduates often receiving multiple offers.'),

-- Arts & Humanities
('PS101', 'Bachelor of Psychology', 'Arts & Humanities', 'Undergraduate', 'Full-time', 3.0, 78, 12500,
 'An APAC-accredited three-year psychology degree that provides the foundational sequence required for postgraduate clinical or organisational psychology study. Core units include developmental psychology, social psychology, cognitive neuroscience, research methods, and statistics. Students complete supervised placements in clinical, community, and organisational settings totalling 120 hours across Years 2 and 3. The program has dedicated research labs equipped for eye-tracking, EEG, and behavioural experiments. Students wishing to become registered psychologists must complete a fourth-year Honours program followed by a two-year masters — the full sequence is available at Kingsford.',
 'With the full sequence (Honours + Masters), graduates register as psychologists and work in clinical, counselling, forensic, or organisational settings. Median salary for registered psychologists is $95,000. Without further study, a three-year psychology degree supports careers in HR, market research, community services, mental health support, and education. Graduates are employed by hospitals, schools, corporates, and NGOs.'),

('DM201', 'Bachelor of Digital Media', 'Arts & Humanities', 'Undergraduate', 'Full-time', 3.0, 70, 12500,
 'A creative three-year program combining film production, animation, UX/UI design, game design, and social media strategy. Students have access to state-of-the-art facilities including a film studio with professional lighting and sound, a motion-capture lab, and Adobe Creative Cloud on all campus workstations. Majors are available in Film & Television, UX Design, or Game Development. Industry guests and working professionals run masterclasses each semester. All students build a professional portfolio across their three years, culminating in a public graduate showcase attended by industry recruiters.',
 'Graduates work as UX designers, content creators, film producers, game designers, animators, and social media strategists. Median starting salary is $62,000. Employers include game studios, advertising agencies, production companies, streaming platforms, and in-house creative teams. UX design graduates are particularly sought after in Melbourne''s growing tech sector, with some receiving graduate offers above $75,000.'),

('EN301', 'Master of Education', 'Arts & Humanities', 'Postgraduate', 'Part-time', 2.0, NULL, 14000,
 'A two-year part-time postgraduate program for practising teachers who want to deepen their expertise or move into leadership roles. Specialisations are available in Educational Leadership, Curriculum Design, and Inclusive Education. The program is delivered online with monthly on-campus intensive weekends, making it manageable alongside a full teaching load. Units are co-designed with principals and system leaders from the Victorian Department of Education. A professional learning project — completed in your own school — forms the capstone assessment, ensuring immediate real-world impact.',
 'Graduates move into school leadership, curriculum coordination, and education consulting roles. Principals with a Master of Education earn a median salary of $130,000 in Victoria. Curriculum coordinators earn $95,000–$110,000. The specialisation in Inclusive Education qualifies graduates for leading NDIS and student support programs. Several graduates have moved into policy roles with the Victorian Department of Education and ACARA.'),

-- Health Sciences
('NU101', 'Bachelor of Nursing', 'Health Sciences', 'Undergraduate', 'Full-time', 3.0, 72, 13500,
 'An AHPRA-accredited three-year nursing degree that qualifies graduates for registration as a Registered Nurse (RN) in Australia. Students complete over 800 hours of clinical placement across Melbourne''s leading hospitals and community health services, including Royal Melbourne Hospital, Alfred Health, and Peninsula Health. Core units cover anatomy and physiology, pharmacology, medical-surgical nursing, mental health nursing, paediatric nursing, and aged care. Simulation labs replicate ICU, emergency, and maternity ward environments. Kingsford has a 98% clinical placement success rate and an employment rate of 96% within three months of graduation.',
 'Graduates register as Registered Nurses and work across acute hospitals, primary health care, aged care, disability services, and mental health services. Graduate nurse salary in Victoria is $72,000–$78,000, rising to $95,000+ for clinical nurse specialists and $120,000+ for nurse practitioners. Many graduates pursue postgraduate specialisation in ICU, emergency, midwifery, or mental health. Several Kingsford nursing alumni have progressed to Director of Nursing roles in major metropolitan hospitals.'),

('PH201', 'Bachelor of Public Health', 'Health Sciences', 'Undergraduate', 'Full-time', 3.0, 68, 13000,
 'A three-year degree examining the social, environmental, and systemic determinants of population health. Core units include epidemiology, biostatistics, health promotion, environmental health, global health, and health policy. Students complete a research project in partnership with a public health agency — past partners include the Victorian Department of Health, WHO collaborating centres, and Médecins Sans Frontières Australia. Fieldwork opportunities exist in Southeast Asia and the Pacific through elective units in Years 2 and 3. The degree provides direct pathways to the Master of Public Health (MPH) for students wishing to specialise further.',
 'Graduates work as public health officers, health policy analysts, epidemiologists, health promotion officers, and NGO program managers. Median starting salary is $65,000 in government and $70,000 in private health or NGO roles. International health organisations including WHO, UNICEF, and the World Bank recruit from this program. With a Master of Public Health, graduates can move into senior policy, research director, or global health advisor roles.'),

('OT301', 'Master of Occupational Therapy', 'Health Sciences', 'Postgraduate', 'Full-time', 2.0, NULL, 19000,
 'An AHPRA-accredited two-year graduate-entry program for students with a relevant bachelor degree in health sciences, psychology, or biomedicine. Students develop skills in functional assessment, occupational performance analysis, assistive technology, neurological rehabilitation, paediatric OT, and mental health OT. Over 1,000 hours of supervised clinical placement are integrated across the two years in settings including acute hospitals, paediatric services, aged care, disability (NDIS), and community health. Kingsford''s OT program is consistently ranked in the top 5 in Australia. Entry is competitive — applicants are assessed on academic results, a personal statement, and an interview.',
 'Graduates register with AHPRA and work across hospitals, aged care, NDIS providers, schools, disability services, and private practice. Graduate OT salary is $75,000–$82,000, rising to $100,000+ for senior and specialist roles. NDIS growth has created strong demand — the program has a 100% employment rate within 6 months of graduation. Private practice OTs can earn $110,000–$130,000. Some graduates pursue research PhDs or clinical specialist roles in neurological or paediatric rehabilitation.'),

-- Arts & Humanities (continued)
('CA101', 'Bachelor of Creative Arts', 'Arts & Humanities', 'Undergraduate', 'Full-time', 3.0, 65, 12000,
 'A three-year studio-based degree integrating fine art, painting, sculpture, printmaking, drawing, and emerging digital art practices. Students develop a personal creative voice across multiple disciplines before choosing a specialisation in Year 2: Fine Art, Illustration, or Contemporary Craft. The program is structured around studio critiques, visiting artist lectures, and collaborative projects with cultural institutions including the National Gallery of Victoria and Melbourne''s Heide Museum of Modern Art. A dedicated gallery space on campus — the Kingsford Studio Gallery — hosts an annual graduate exhibition open to the public and attended by commercial galleries, collectors, and arts funding bodies. Students also complete a professional practice unit covering grant writing, artist statements, exhibition proposals, and self-employment in the arts.',
 'Graduates work as practising artists, illustrators, art educators, gallery assistants, community arts facilitators, and arts administrators. Many establish independent studio practices supported by Australia Council for the Arts grants and state arts funding. Median starting salary in arts-adjacent roles is $58,000, with experienced working artists earning $70,000–$90,000 through commissions, exhibitions, and residencies. Several Kingsford alumni have been selected for the Archibald Prize and the Venice Biennale Australia Pavilion. The degree also provides direct entry into the Master of Fine Arts (MFA) for students wishing to pursue research-led studio practice.');

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
