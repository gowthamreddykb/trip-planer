"""
Places and Multi-Place Submission Tests for Trip Planner.
"""
from tests.conftest import login_client
import db

def test_multi_place_submission(client):
    import uuid
    dest_name = f"Himachal Pradesh {uuid.uuid4().hex[:4]}"
    # Submit 3 places for Himachal destination in a single submission
    response = client.post('/suggest-places', data={
        'csrf_token': 'test-csrf-token',
        'destination_name': dest_name,
        'city_area': 'Manali, Spiti, Dharamshala',
        'overview_description': 'Northern Indian state in the Himalayas known for trekking, snow, and scenic valleys.',
        'travel_tips': 'Pack heavy woolens in winter.\nBook rohtang pass permit in advance.',
        'local_food': 'Siddu\nThukpa\nDham',
        
        # Place 0
        'place_name_0': 'Solang Valley',
        'category_0': 'Adventure',
        'short_description_0': 'Famous for paragliding, zorbing and winter skiing.',
        'things_to_see_0': 'Paragliding\nZorbing\nCable car',
        'best_time_to_visit_0': 'Dec – Feb',
        'estimated_cost_min_0': '1500',
        'estimated_cost_max_0': '3500',
        'recommended_duration_0': '1 day',
        'address_0': 'Solang, Manali, Himachal Pradesh',
        'image_url_0': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb',

        # Place 1
        'place_name_1': 'Rohtang Pass',
        'category_1': 'Mountain',
        'short_description_1': 'High mountain pass connecting Kullu with Lahaul and Spiti.',
        'things_to_see_1': 'Snow point\nGlacier views',
        'best_time_to_visit_1': 'May – Oct',
        'estimated_cost_min_1': '2000',
        'estimated_cost_max_1': '4000',
        'recommended_duration_1': '1 day',
        'address_1': 'Rohtang Pass Highway',
        'image_url_1': 'https://images.unsplash.com/photo-1544735716-392fe2489ffa',

        # Place 2
        'place_name_2': 'Old Manali Cafes',
        'category_2': 'Culture',
        'short_description_2': 'Quiet village with bohemian cafes, live acoustic music and apple orchards.',
        'things_to_see_2': 'Cafe hopping\nApple orchard walks',
        'best_time_to_visit_2': 'Apr – Jun',
        'estimated_cost_min_2': '500',
        'estimated_cost_max_2': '1200',
        'recommended_duration_2': 'Half day',
        'address_2': 'Old Manali, Manali',
        'image_url_2': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"submitted for review" in response.data or b"successfully" in response.data

    # Verify destination was created
    dest = db.query_db("SELECT * FROM destinations WHERE name = %s", (dest_name,), one=True)
    assert dest is not None

    # Verify all 3 places were created separately and linked to this destination
    places = db.query_db("SELECT * FROM place_suggestions WHERE destination_id = %s", (dest['id'],))
    assert len(places) == 3
    names = {p['name'] for p in places}
    assert 'Solang Valley' in names
    assert 'Rohtang Pass' in names
    assert 'Old Manali Cafes' in names

    # Verify status is 'pending'
    for p in places:
        assert p['status'] == 'pending'

def test_explore_search_and_category_filters(client):
    # Test search for "Beach" with category "Beach" -> should find Baga Beach or Varkala Beach
    response = client.get('/explore?search=Beach&category=Beach')
    assert response.status_code == 200
    assert b"Beach" in response.data

    # Test search for "Fort" with category "Historical" -> should find Fort Kochi, Hawa Mahal, or Jaisalmer Fort
    response = client.get('/explore?search=Fort&category=Historical')
    assert response.status_code == 200
    assert b"Fort" in response.data

def test_pending_places_hidden_from_public_explore(client):
    import uuid
    p_name = f"Hidden Cave {uuid.uuid4().hex[:6]}"
    db.query_db(
        """
        INSERT INTO place_suggestions (destination_id, name, category, short_description, things_to_see, best_time_to_visit, recommended_duration, status)
        VALUES (1, %s, 'Nature', 'Secret unseen cave', 'Cave walk', 'All Year', '1 hr', 'pending')
        """,
        (p_name,),
        commit=True
    )
    # The place was created as 'pending', should not be on /explore
    response = client.get(f'/explore?search={p_name}')
    assert response.status_code == 200
    assert b"No Places Found" in response.data
    assert b"View Details" not in response.data

def test_admin_can_approve_suggestion(client):
    import uuid
    p_name = f"Pending Waterfall {uuid.uuid4().hex[:6]}"
    p_id = db.query_db(
        """
        INSERT INTO place_suggestions (destination_id, name, category, short_description, things_to_see, best_time_to_visit, recommended_duration, status)
        VALUES (1, %s, 'Nature', 'Misty waterfall', 'Water splash', 'All Year', '2 hrs', 'pending')
        """,
        (p_name,),
        commit=True
    )

    login_client(client, "admin", "admin123")

    response = client.post(f'/admin/place-suggestions/{p_id}/approve', data={
        'csrf_token': 'test-csrf-token'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Check DB status is now 'approved'
    updated = db.query_db("SELECT status FROM place_suggestions WHERE id = %s", (p_id,), one=True)
    assert updated['status'] == 'approved'

def test_normal_user_blocked_from_admin_review(client):
    login_client(client, "john", "password123")

    # John has role='user', should get 403 on admin route
    response = client.get('/admin/place-suggestions')
    assert response.status_code == 403
