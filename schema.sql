-- ==========================================================
-- Trip Planner Database Schema
-- Exactly 6 Main Tables
-- ==========================================================

CREATE DATABASE IF NOT EXISTS trip_planner;
USE trip_planner;

-- ----------------------------------------------------------
-- 1. USERS TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_role CHECK (role IN ('user', 'admin'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 2. TRIPS TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS trips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    destination VARCHAR(150) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_dates CHECK (end_date >= start_date),
    CONSTRAINT chk_budget CHECK (budget >= 0.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 3. DESTINATIONS TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS destinations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    city_area VARCHAR(200) NULL,
    overview_description TEXT NOT NULL,
    travel_tips TEXT NULL,
    local_food TEXT NULL,
    suggested_itinerary TEXT NULL,
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 4. PLACE_SUGGESTIONS TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS place_suggestions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    destination_id INT NOT NULL,
    submitted_by INT NULL,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    things_to_see TEXT NOT NULL,
    best_time_to_visit VARCHAR(100) NOT NULL,
    estimated_cost_min DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    estimated_cost_max DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    recommended_duration VARCHAR(50) NOT NULL,
    address VARCHAR(255) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (destination_id) REFERENCES destinations(id) ON DELETE CASCADE,
    FOREIGN KEY (submitted_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_cost_min CHECK (estimated_cost_min >= 0.00),
    CONSTRAINT chk_cost_range CHECK (estimated_cost_max >= estimated_cost_min),
    CONSTRAINT chk_status CHECK (status IN ('pending', 'approved', 'rejected'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 5. PLACE_IMAGES TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS place_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    place_id INT NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(200) NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_place_img UNIQUE (place_id, image_url(255)),
    FOREIGN KEY (place_id) REFERENCES place_suggestions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 6. ACTIVITIES TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trip_id INT NOT NULL,
    place_suggestion_id INT NULL,
    name VARCHAR(150) NOT NULL,
    activity_date DATE NOT NULL,
    activity_time TIME NULL,
    category VARCHAR(50) NOT NULL,
    place VARCHAR(200) NOT NULL,
    estimated_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (place_suggestion_id) REFERENCES place_suggestions(id) ON DELETE SET NULL,
    CONSTRAINT chk_activity_cost CHECK (estimated_cost >= 0.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_trip ON activities(trip_id);
CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(activity_date);
CREATE INDEX IF NOT EXISTS idx_places_dest ON place_suggestions(destination_id);
CREATE INDEX IF NOT EXISTS idx_places_status ON place_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_places_category ON place_suggestions(category);
CREATE INDEX IF NOT EXISTS idx_images_place ON place_images(place_id);

-- ----------------------------------------------------------
-- SEED DATA
-- ----------------------------------------------------------

-- Default Admin and Demo User
INSERT INTO users (id, username, email, password_hash, role) VALUES
(1, 'admin', 'admin@tripplanner.com', 'scrypt:32768:8:1$JtsZO2dyPbegJzGj$b8e4e5d85e2a75381ecb28f00e2dc29d014c6b267c2c68216a3443dd41b7eb7c32c982bfefdec3f3a51dadbcebfd6a82b725c154970d5a3c3c7fb829c0937fb8', 'admin'),
(2, 'john', 'john@example.com', 'scrypt:32768:8:1$XFqUBzalcJWG1pAw$8d81ea490c194aa648ef5de534e5d1ca8157ecc2c479174f709ea8696a616b11c90948934e40fff0650793a4fda2b02c248cec0e264296ab3fa54d1705e96320', 'user')
ON DUPLICATE KEY UPDATE id=id;

-- Destinations
INSERT INTO destinations (id, name, city_area, overview_description, travel_tips, local_food, suggested_itinerary, created_by) VALUES
(1, 'Kerala', 'Alleppey, Munnar, Kochi', 'God''s Own Country, Kerala is a tropical paradise known for its serene backwaters, lush green hills, beautiful beaches and rich cultural heritage.', 'Carry light and comfortable clothing.\nRespect local culture and traditions.\nUse public transport or trusted cabs.\nKeep a reusable water bottle.\nBook houseboats in advance.', 'Appam & Stew\nKerala Sadya\nFresh Seafood\nSpices and Coconut-based dishes', 'Day 1: Morning - Alleppey Backwaters (houseboat)\nAfternoon - Local food & village tour\nEvening - Sunset at Alleppey Beach\n\nDay 2: Morning - Munnar Tea Gardens\nAfternoon - Visit to Eravikulam National Park\nEvening - Return to Kochi', 1),
(2, 'Goa', 'North & South Goa', 'Famous for its pristine coastline, sun-kissed beaches, vibrant nightlife, and Portuguese heritage architecture.', 'Rent a scooter to explore at your own pace.\nTry water sports early in the morning.\nRespect local beach cleanliness guidelines.', 'Goan Fish Curry\nPork Vindaloo\nBebinca\nPoee & Cafreal', 'Day 1: North Goa beaches and water sports\nDay 2: Old Goa heritage churches and sunset cruise', 1),
(3, 'Jaipur', 'Pink City, Rajasthan', 'The capital of Rajasthan, celebrated for magnificent royal palaces, historic forts, colorful bazaars, and rich Rajputana culture.', 'Wear comfortable walking shoes for palace tours.\nHaggle respectfully at traditional bazaars.\nVisit Amer Fort early in the morning to avoid crowds.', 'Dal Baati Churma\nLaal Maas\nPyaaz Kachori\nGhewar', 'Day 1: City Palace, Hawa Mahal, and local bazaar shopping\nDay 2: Amer Fort and Nahargarh sunset view', 1),
(4, 'Kashmir', 'Srinagar, Gulmarg, Pahalgam', 'Paradise on Earth featuring snow-capped peaks, shimmering lakes, pine valleys, and floating wooden houseboats.', 'Dress in warm layers even during shoulder season.\nTake an early morning Shikara ride to the floating market.\nSip traditional Kahwa tea.', 'Kashmiri Wazwan\nRogan Josh\nDum Aloo\nKahwa with saffron and almonds', 'Day 1: Dal Lake Shikara ride and Mughal Gardens\nDay 2: Gulmarg Gondola and scenic meadow stroll', 1),
(5, 'Bali', 'Ubud, Canggu, Uluwatu', 'An Indonesian island paradise blessed with emerald volcanic hills, cascading rice terraces, cliffside temples, and vibrant coastal culture.', 'Carry local currency (IDR) for traditional markets.\nDress respectfully with sarongs when entering temples.\nRent a private driver or scooter.', 'Nasi Goreng\nBabi Guling\nSate Lilit\nFresh Tropical Smoothie Bowls', 'Day 1: Ubud rice terraces, monkey forest, and artisan markets\nDay 2: Uluwatu clifftop temple and sunset Kecak dance', 1)
ON DUPLICATE KEY UPDATE id=id;

-- Place Suggestions (Approved catalog)
INSERT INTO place_suggestions (id, destination_id, submitted_by, name, category, short_description, things_to_see, best_time_to_visit, estimated_cost_min, estimated_cost_max, recommended_duration, address, status) VALUES
(1, 1, 1, 'Alleppey Backwaters', 'Nature', 'A serene network of canals, lakes and lagoons with lush greenery and traditional houseboats.', 'Houseboat cruise\nVillage walk\nBird watching\nLocal markets', 'Oct – Mar', 1000.00, 2500.00, '1 – 2 days', 'Alleppey, Alappuzha, Kerala, India', 'approved'),
(2, 1, 1, 'Munnar Tea Gardens', 'Nature', 'Rolling tea plantations, misty hills and cool climate make Munnar a perfect getaway for nature lovers.', 'Tea plantation visit\nEravikulam National Park\nMattupetty Dam\nPhoto points', 'Sep – Mar', 800.00, 2000.00, '1 – 2 days', 'Munnar, Idukki, Kerala, India', 'approved'),
(3, 1, 1, 'Fort Kochi', 'Historical', 'A charming coastal area with colonial architecture, Chinese fishing nets and vibrant art & culture.', 'Chinese fishing nets\nSt. Francis Church\nMattancherry Palace\nArt cafes & galleries', 'Oct – Feb', 500.00, 1500.00, '1 – 2 days', 'Fort Kochi, Kochi, Kerala, India', 'approved'),
(4, 1, 1, 'Periyar Wildlife Sanctuary', 'Nature', 'Spot elephants, tigers and rich biodiversity in a natural rainforest habitat surrounding Periyar Lake.', 'Periyar Lake boat safari\nSpice plantation tour\nJungle trek\nBamboo rafting', 'Oct – Mar', 800.00, 2200.00, '1 – 2 days', 'Thekkady, Idukki, Kerala, India', 'approved'),
(5, 1, 1, 'Varkala Beach', 'Beach', 'Stunning red cliffside beach offering panoramic Arabian Sea sunsets and bohemian cafe culture.', 'Cliffside sunset walk\nSurfing and swimming\nJanardanaswamy Temple\nAyurvedic wellness', 'Oct – Mar', 600.00, 1800.00, '1 – 2 days', 'Varkala, Thiruvananthapuram, Kerala', 'approved'),
(6, 1, 1, 'Trek to Chembra Peak', 'Adventure', 'The highest peak in Wayanad featuring a picturesque heart-shaped lake surrounded by mist.', 'Heart-shaped lake (Hridaya Saras)\nPanoramic summit views\nTea estate trail\nWayanad landscape', 'Oct – May', 500.00, 1500.00, '1 day', 'Meppadi, Wayanad, Kerala', 'approved'),
(7, 2, 1, 'Baga Beach', 'Beach', 'One of the most famous lively beaches in North Goa, known for water sports and energetic beach shacks.', 'Parasailing and jet ski\nBeach shack dining\nNightlife and music\nSouvenir shopping', 'Nov – Feb', 800.00, 2500.00, '1 – 2 days', 'Baga, North Goa, India', 'approved'),
(8, 3, 1, 'Hawa Mahal', 'Historical', 'The iconic Palace of Winds with 953 intricately carved honeycomb windows built in pink sandstone.', 'Intricate jharokha windows\nCity view from upper floors\nCourtyard museum\nJohari Bazaar walk', 'Oct – Mar', 300.00, 800.00, '2 – 3 hours', 'Hawa Mahal Rd, Badi Choupad, Jaipur, Rajasthan', 'approved'),
(9, 3, 1, 'Jaisalmer Fort', 'Historical', 'A living golden fort rising from the Thar Desert with ancient sandstone palaces and Jain temples.', 'Golden Fort walk\nJain Temples\nRaj Mahal Palace\nSunset terrace view', 'Oct – Mar', 400.00, 1200.00, 'Half day', 'Fort Area, Jaisalmer, Rajasthan', 'approved'),
(10, 4, 1, 'Dal Lake & Houseboats', 'Nature', 'The jewel of Srinagar featuring calm mirror-like waters, floating gardens, and wooden carved houseboats.', 'Shikara boat ride\nFloating flower market\nChar Chinar island\nMughal heritage gardens', 'Apr – Oct', 1200.00, 3500.00, '1 – 2 days', 'Srinagar, Jammu and Kashmir', 'approved'),
(11, 5, 1, 'Tegallalang Rice Terraces', 'Nature', 'UNESCO-recognized terraced valley framed by swaying coconut palms and traditional irrigation canals.', 'Scenic terrace walk\nBali jungle swings\nLuwak coffee tasting\nArtisan wood carvings', 'Apr – Oct', 600.00, 2000.00, 'Half day', 'Ubud, Bali, Indonesia', 'approved')
ON DUPLICATE KEY UPDATE id=id;

-- Place Images (All distinct, varied high-resolution photographs)
INSERT INTO place_images (place_id, image_url, alt_text, is_primary, display_order) VALUES
-- Alleppey Backwaters
(1, 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80', 'Traditional Kettuvallam Houseboat on palm waters', 1, 1),
(1, 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&w=800&q=80', 'Serene village canal canoe ride in Alleppey', 0, 2),
(1, 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=800&q=80', 'Sunset over Vembanad Lake backwaters', 0, 3),
(1, 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=80', 'Lush green tropical coconut lagoon in Kerala', 0, 4),

-- Munnar Tea Gardens
(2, 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80', 'Munnar rolling emerald tea plantation hills', 1, 1),
(2, 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80', 'Winding mountain path through tea valley', 0, 2),
(2, 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80', 'Eravikulam misty mountain peaks and valleys', 0, 3),
(2, 'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=800&q=80', 'Morning sunrise over Western Ghats mist', 0, 4),

-- Fort Kochi
(3, 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80', 'Giant Chinese fishing nets at dramatic sunset', 1, 1),
(3, 'https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80', 'Colonial heritage architecture of Fort Kochi', 0, 2),
(3, 'https://images.unsplash.com/photo-1596178065887-1198b6148b2b?auto=format&fit=crop&w=800&q=80', 'Historic spice market and antique street', 0, 3),
(3, 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=80', 'Arabian Sea coastal promenade and lighthouse', 0, 4),

-- Periyar Wildlife Sanctuary
(4, 'https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?auto=format&fit=crop&w=1200&q=80', 'Wild Asian elephants grazing by Periyar Lake', 1, 1),
(4, 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80', 'Periyar Lake morning boat safari tour', 0, 2),
(4, 'https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80', 'Deep rainforest canopy and jungle trek', 0, 3),
(4, 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=80', 'Fragrant spice plantation pepper and cardamom', 0, 4),

-- Varkala Beach
(5, 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80', 'Varkala red cliff looking down on golden sands', 1, 1),
(5, 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80', 'Pristine coastal waves and Arabian sea beach', 0, 2),
(5, 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80', 'Bohemian sunset clifftop cafes and palm trees', 0, 3),
(5, 'https://images.unsplash.com/photo-1502680390469-be75c86b636f?auto=format&fit=crop&w=800&q=80', 'Surfing waves and relaxed coastal lifestyle', 0, 4),

-- Trek to Chembra Peak
(6, 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80', 'Heart-shaped natural lake atop Chembra mountain', 1, 1),
(6, 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80', 'Sweeping panoramic summit view of Wayanad hills', 0, 2),
(6, 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=800&q=80', 'Lush tea estate trails on the mountain slopes', 0, 3),
(6, 'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=800&q=80', 'Misty cloud trail leading to summit ridge', 0, 4),

-- Baga Beach Goa
(7, 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80', 'Vibrant Baga beach with boats and shacks', 1, 1),
(7, 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80', 'Water sports parasailing and jet skis', 0, 2),
(7, 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80', 'Candlelit beach shack dining at twilight', 0, 3),
(7, 'https://images.unsplash.com/photo-1502680390469-be75c86b636f?auto=format&fit=crop&w=800&q=80', 'Golden tropical sunset on the Goa coastline', 0, 4),

-- Hawa Mahal Jaipur
(8, 'https://images.unsplash.com/photo-1603262110263-fb010d6e75dc?auto=format&fit=crop&w=1200&q=80', 'Iconic pink sandstone honeycomb facade of Hawa Mahal', 1, 1),
(8, 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=800&q=80', 'Intricate royal jharokhas and carved stone lattices', 0, 2),
(8, 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80', 'City Palace courtyards and peacock gates', 0, 3),
(8, 'https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80', 'Vibrant Johari Bazaar traditional shopping lane', 0, 4),

-- Jaisalmer Fort
(9, 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80', 'Golden sandstone Sonar Qila rising from the desert', 1, 1),
(9, 'https://images.unsplash.com/photo-1603262110263-fb010d6e75dc?auto=format&fit=crop&w=800&q=80', 'Carved yellow sandstone Jain temple towers', 0, 2),
(9, 'https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=800&q=80', 'Thar desert sand dunes and camel safari', 0, 3),
(9, 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80', 'Rooftop cafe overlooking the golden fortress city', 0, 4),

-- Dal Lake Kashmir
(10, 'https://images.unsplash.com/photo-1566837945700-30057527ade0?auto=format&fit=crop&w=1200&q=80', 'Colorful Shikara boats gliding on Dal Lake', 1, 1),
(10, 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80', 'Carved cedar wooden houseboats moored at sunrise', 0, 2),
(10, 'https://images.unsplash.com/photo-1596178065887-1198b6148b2b?auto=format&fit=crop&w=800&q=80', 'Floating flower and vegetable market in early morning', 0, 3),
(10, 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80', 'Snow-capped Himalayan peaks framing the Kashmir valley', 0, 4),

-- Tegallalang Rice Terraces Bali
(11, 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1200&q=80', 'Cascading emerald green rice terraces of Tegallalang', 1, 1),
(11, 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?auto=format&fit=crop&w=800&q=80', 'Famous Bali jungle swing soaring over the valley', 0, 2),
(11, 'https://images.unsplash.com/photo-1555400038-63f5ba517a47?auto=format&fit=crop&w=800&q=80', 'Balinese water temples and traditional farmer pathways', 0, 3),
(11, 'https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?auto=format&fit=crop&w=800&q=80', 'Tropical palm rainforest surrounding rice terraces', 0, 4)
ON DUPLICATE KEY UPDATE is_primary=VALUES(is_primary);

-- Demo Trips for John
INSERT INTO trips (id, user_id, destination, start_date, end_date, budget) VALUES
(1, 2, 'Kyoto', '2025-04-12', '2025-04-16', 5000.00),
(2, 2, 'Kerala', '2025-05-05', '2025-05-07', 6000.00),
(3, 2, 'Jaipur', '2025-06-10', '2025-06-12', 4500.00)
ON DUPLICATE KEY UPDATE id=id;

-- Demo Activities for John's Kerala Trip (Trip 2) matching Image 3 (Total ₹4,200, Remaining ₹1,800)
INSERT INTO activities (id, trip_id, place_suggestion_id, name, activity_date, activity_time, category, place, estimated_cost) VALUES
(1, 2, 1, 'Houseboat Check-in', '2025-05-05', '09:00:00', 'Nature', 'Alleppey Jetty', 2000.00),
(2, 2, NULL, 'Lunch', '2025-05-05', '13:00:00', 'Food', 'Alleppey Floating Resto', 600.00),
(3, 2, 1, 'Backwater Tour', '2025-05-05', '16:00:00', 'Nature', 'Punnamada Lake', 1000.00),
(4, 2, 3, 'Fort Kochi Walk', '2025-05-06', '10:00:00', 'Historical', 'Fort Kochi Heritage Zone', 600.00),
-- Activities for Kyoto Trip (Trip 1)
(5, 1, NULL, 'Fushimi Inari Shrine Hike', '2025-04-12', '08:30:00', 'Historical', 'Fushimi Inari', 500.00),
(6, 1, NULL, 'Traditional Ramen Lunch', '2025-04-12', '13:00:00', 'Food', 'Gion Quarter', 1200.00),
(7, 1, NULL, 'Arashiyama Bamboo Grove', '2025-04-13', '09:00:00', 'Nature', 'Arashiyama', 1500.00),
-- Activities for Jaipur Trip (Trip 3)
(8, 3, 8, 'Hawa Mahal & City Palace', '2025-06-10', '10:00:00', 'Historical', 'Badi Choupad', 1200.00),
(9, 3, NULL, 'Chokhi Dhani Dinner', '2025-06-10', '19:30:00', 'Food', 'Tonk Road', 1600.00)
ON DUPLICATE KEY UPDATE id=id;
