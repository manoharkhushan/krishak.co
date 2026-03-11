from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timedelta
import os
import requests
from collections import defaultdict
import time
import random
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# Configuration
# Best Practice: Use Environment Variables, fall back to strings for local dev
app.secret_key = os.environ.get('SECRET_KEY', 'krishak_secret_key_2026_dev')
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'Khushan@2828')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'krishak_db')
app.config['OPENWEATHER_API_KEY'] = os.environ.get('OPENWEATHER_API_KEY', 'your_openweather_api_key_here')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Google OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', 'your_google_client_id')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', 'your_google_client_secret')

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

# Database Connection Helper
def get_db_connection():
    """Establishes a new database connection for the request."""
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
def home():
    """Home page after successful login/signup"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        location = data.get('location')
        password = data.get('password')
        
        if not all([name, email, password]):
            return jsonify({'success': False, 'message': 'Please fill all required fields'}), 400
        
        # Hash password using pbkdf2 for compatibility
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Check if email already exists
                cur.execute("SELECT email FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    return jsonify({'success': False, 'message': 'Email already registered'}), 400
                
                # Insert new user
                cur.execute("""
                    INSERT INTO users (name, email, phone, location, password_hash)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, email, phone, location, password_hash))
                
                conn.commit()
                user_id = cur.lastrowid
                
                # Auto-login after registration
                session['user_id'] = user_id
                session['user_name'] = name
                session['user_email'] = email
                
                return jsonify({'success': True, 'message': 'Registration successful! Redirecting to home...', 'redirect': '/home'})
        
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
        finally:
            if conn: conn.close()
    
    return render_template('signup.html', bg_image='login.jpeg')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'success': False, 'message': 'Please fill all fields'}), 400
        
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                return jsonify({'success': True, 'message': 'Login successful!', 'redirect': '/home'})
            else:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
        finally:
            if conn: conn.close()
    
    return render_template('login.html', bg_image='login.jpeg')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/auth/google')
def google_login():
    """Initiate Google OAuth login"""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()

        # Extract user information
        google_id = user_info.get('id')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')

        if not email:
            return jsonify({'success': False, 'message': 'Email not provided by Google'}), 400

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Check if user exists
                cur.execute("SELECT user_id, name, email FROM users WHERE email = %s", (email,))
                user = cur.fetchone()

                if user:
                    # Update existing user with Google info if needed
                    if not user['name'] and name:
                        cur.execute("UPDATE users SET name = %s WHERE user_id = %s", (name, user['user_id']))
                        conn.commit()
                    user_id = user['user_id']
                else:
                    # Create new user
                    # Generate a random password for Google users (they won't use it)
                    temp_password = os.urandom(24).hex()
                    password_hash = generate_password_hash(temp_password, method='pbkdf2:sha256')

                    cur.execute("""
                        INSERT INTO users (name, email, phone, location, password_hash)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (name or 'Google User', email, '', 'Unknown', password_hash))
                    conn.commit()
                    user_id = cur.lastrowid

                    # Create profile with Google picture
                    if picture:
                        cur.execute("INSERT INTO user_profiles (user_id, profile_picture) VALUES (%s, %s)",
                                  (user_id, picture))
                        conn.commit()

                # Set session
                session['user_id'] = user_id
                session['user_name'] = name or user['name'] if user else 'Google User'
                session['user_email'] = email

                return redirect(url_for('home'))

        except Exception as e:
            app.logger.error(f"Google auth error: {str(e)}")
            return jsonify({'success': False, 'message': 'Authentication failed'}), 500
        finally:
            if conn: conn.close()

    except Exception as e:
        app.logger.error(f"Google OAuth error: {str(e)}")
        return redirect(url_for('login'))


@app.route('/api/expenses', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_expenses():
    user_id = session.get('user_id')
    conn = None
    
    try:
        conn = get_db_connection()
        
        if request.method == 'POST':
            data = request.get_json() if request.is_json else request.form
            
            expense_date = data.get('expense_date')
            category_id = data.get('category_id')
            amount = data.get('amount')
            remarks = data.get('remarks', '')
            
            if not all([expense_date, category_id, amount]):
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO expenses (user_id, category_id, expense_date, amount, remarks)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, category_id, expense_date, amount, remarks))
                conn.commit()
                expense_id = cur.lastrowid
                
            return jsonify({'success': True, 'message': 'Expense added successfully', 'expense_id': expense_id})
        
        elif request.method == 'DELETE':
            expense_id = request.args.get('expense_id')
            if not expense_id:
                # Try getting from JSON body if not in args
                data = request.get_json() if request.is_json else {}
                expense_id = data.get('expense_id')

            if not expense_id:
                return jsonify({'success': False, 'message': 'Expense ID required'}), 400
            
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM expenses 
                    WHERE expense_id = %s AND user_id = %s
                """, (expense_id, user_id))
                conn.commit()
                
            return jsonify({'success': True, 'message': 'Expense deleted successfully'})
        
        # GET method fallthrough
        return jsonify({'success': True, 'message': 'Use profile route for viewing expenses'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/analytics')
@login_required
def analytics():
    user_id = session.get('user_id')
    conn = None
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Monthly expense trend (last 6 months)
            cur.execute("""
                SELECT
                    CONCAT(YEAR(expense_date), '-', LPAD(MONTH(expense_date), 2, '0')) as month,
                    SUM(amount) as total_amount
                FROM expenses
                WHERE user_id = %s
                    AND expense_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY CONCAT(YEAR(expense_date), '-', LPAD(MONTH(expense_date), 2, '0'))
                ORDER BY month
            """, (user_id,))
            monthly_trend = cur.fetchall()
            
            # Category-wise breakdown
            cur.execute("""
                SELECT 
                    ec.category_name,
                    SUM(e.amount) as total_amount,
                    COUNT(e.expense_id) as count
                FROM expenses e
                JOIN expense_categories ec ON e.category_id = ec.category_id
                WHERE e.user_id = %s
                GROUP BY ec.category_id, ec.category_name
                ORDER BY total_amount DESC
            """, (user_id,))
            category_breakdown = cur.fetchall()
            
        return jsonify({
            'success': True,
            'monthly_trend': monthly_trend,
            'category_breakdown': category_breakdown
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/schemes')
def schemes():
    return render_template('schemes.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/community')
@login_required
def community():
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get categories
            cur.execute("SELECT * FROM community_categories ORDER BY category_name")
            categories = cur.fetchall()

            # Build query for posts
            query = """
                SELECT
                    p.post_id,
                    p.title,
                    p.content,
                    p.created_at,
                    p.updated_at,
                    c.category_name,
                    p.category_id,
                    u.name as author_name,
                    up.profile_picture,
                    COALESCE(like_counts.like_count, 0) as like_count,
                    COALESCE(dislike_counts.dislike_count, 0) as dislike_count,
                    COALESCE(comment_counts.comment_count, 0) as comment_count
                FROM community_posts p
                JOIN community_categories c ON p.category_id = c.category_id
                JOIN users u ON p.user_id = u.user_id
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                LEFT JOIN (
                    SELECT post_id, COUNT(*) as like_count
                    FROM community_likes
                    WHERE type = 'like'
                    GROUP BY post_id
                ) like_counts ON p.post_id = like_counts.post_id
                LEFT JOIN (
                    SELECT post_id, COUNT(*) as dislike_count
                    FROM community_likes
                    WHERE type = 'dislike'
                    GROUP BY post_id
                ) dislike_counts ON p.post_id = dislike_counts.post_id
                LEFT JOIN (
                    SELECT post_id, COUNT(*) as comment_count
                    FROM community_comments
                    GROUP BY post_id
                ) comment_counts ON p.post_id = comment_counts.post_id
            """
            params = []

            if category_filter:
                query += " WHERE p.category_id = %s"
                params.append(category_filter)

            query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
            params.extend([per_page, offset])

            cur.execute(query, params)
            posts = cur.fetchall()

            # Get comments for each post
            for post in posts:
                cur.execute("""
                    SELECT
                        c.content,
                        c.created_at,
                        u.name as author_name,
                        up.profile_picture
                    FROM community_comments c
                    JOIN users u ON c.user_id = u.user_id
                    LEFT JOIN user_profiles up ON u.user_id = up.user_id
                    WHERE c.post_id = %s
                    ORDER BY c.created_at ASC
                """, (post['post_id'],))
                post['comments'] = cur.fetchall()

            # Get total posts for pagination
            count_query = "SELECT COUNT(*) as total FROM community_posts"
            count_params = []
            if category_filter:
                count_query += " WHERE category_id = %s"
                count_params.append(category_filter)

            cur.execute(count_query, count_params)
            total_posts = cur.fetchone()['total']
            total_pages = int((total_posts + per_page - 1) // per_page)

            # Calculate page numbers for pagination
            page_numbers = list(range(max(1, page - 2), min(total_pages + 1, page + 3)))

        return render_template('community.html',
                             posts=posts,
                             categories=categories,
                             page=page,
                             total_pages=total_pages,
                             page_numbers=page_numbers,
                             category_filter=category_filter,
                             current_user={'name': session.get('user_name'), 'id': session.get('user_id')})

    except Exception as e:
        return f"Error loading community: {str(e)}", 500
    finally:
        if conn: conn.close()

@app.route('/api/community/posts', methods=['POST'])
@login_required
def create_post():
    user_id = session.get('user_id')
    data = request.get_json() if request.is_json else request.form

    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')

    if not all([title, content, category_id]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO community_posts (user_id, category_id, title, content)
                VALUES (%s, %s, %s, %s)
            """, (user_id, category_id, title, content))
            conn.commit()

        return jsonify({'success': True, 'message': 'Post created successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/community/posts/<int:post_id>', methods=['PUT'])
@login_required
def edit_post(post_id):
    user_id = session.get('user_id')

    # Get JSON data from request
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400

    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')

    if not all([title, content, category_id]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if post belongs to user
            cur.execute("SELECT user_id FROM community_posts WHERE post_id = %s", (post_id,))
            post = cur.fetchone()

            if not post or post['user_id'] != user_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403

            cur.execute("""
                UPDATE community_posts
                SET title = %s, content = %s, category_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE post_id = %s
            """, (title, content, category_id, post_id))
            conn.commit()

        return jsonify({'success': True, 'message': 'Post updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/community/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    user_id = session.get('user_id')

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if user already has a reaction on this post
            cur.execute("SELECT like_id, type FROM community_likes WHERE post_id = %s AND user_id = %s", (post_id, user_id))
            existing_reaction = cur.fetchone()

            if existing_reaction:
                if existing_reaction['type'] == 'like':
                    # Remove like
                    cur.execute("DELETE FROM community_likes WHERE like_id = %s", (existing_reaction['like_id'],))
                else:
                    # Change dislike to like
                    cur.execute("UPDATE community_likes SET type = 'like' WHERE like_id = %s", (existing_reaction['like_id'],))
            else:
                # Add like
                cur.execute("INSERT INTO community_likes (post_id, user_id, type) VALUES (%s, %s, 'like')", (post_id, user_id))

            # Get updated counts
            cur.execute("SELECT COUNT(*) as count FROM community_likes WHERE post_id = %s AND type = 'like'", (post_id,))
            like_result = cur.fetchone()
            like_count = like_result['count']

            cur.execute("SELECT COUNT(*) as count FROM community_likes WHERE post_id = %s AND type = 'dislike'", (post_id,))
            dislike_result = cur.fetchone()
            dislike_count = dislike_result['count']

            conn.commit()

        return jsonify({'success': True, 'like_count': like_count, 'dislike_count': dislike_count})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/community/posts/<int:post_id>/dislike', methods=['POST'])
@login_required
def dislike_post(post_id):
    user_id = session.get('user_id')

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if user already has a reaction on this post
            cur.execute("SELECT like_id, type FROM community_likes WHERE post_id = %s AND user_id = %s", (post_id, user_id))
            existing_like = cur.fetchone()

            if existing_like:
                if existing_like['type'] == 'dislike':
                    # Undislike: remove the dislike
                    cur.execute("""
                        DELETE FROM community_likes
                        WHERE post_id = %s AND user_id = %s
                    """, (post_id, user_id))
                else:
                    # Change like to dislike
                    cur.execute("""
                        UPDATE community_likes
                        SET type = 'dislike'
                        WHERE post_id = %s AND user_id = %s
                    """, (post_id, user_id))
            else:
                # Add new dislike
                cur.execute("""
                    INSERT INTO community_likes (post_id, user_id, type)
                    VALUES (%s, %s, 'dislike')
                """, (post_id, user_id))

            conn.commit()

            # Get updated counts
            cur.execute("""
                SELECT COUNT(*) as like_count
                FROM community_likes
                WHERE post_id = %s AND type = 'like'
            """, (post_id,))
            like_count = cur.fetchone()['like_count']

            cur.execute("""
                SELECT COUNT(*) as dislike_count
                FROM community_likes
                WHERE post_id = %s AND type = 'dislike'
            """, (post_id,))
            dislike_count = cur.fetchone()['dislike_count']

        return jsonify({'success': True, 'like_count': like_count, 'dislike_count': dislike_count})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/community/posts/<int:post_id>/react', methods=['POST'])
@login_required
def react_to_post(post_id):
    user_id = session.get('user_id')
    data = request.get_json()
    emoji = data.get('emoji')

    if not emoji:
        return jsonify({'success': False, 'message': 'Emoji is required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if user already reacted with this emoji
            cur.execute("""
                SELECT reaction_id FROM community_emoji_reactions
                WHERE post_id = %s AND user_id = %s AND emoji = %s
            """, (post_id, user_id, emoji))
            existing_reaction = cur.fetchone()

            if existing_reaction:
                # Remove the reaction
                cur.execute("""
                    DELETE FROM community_emoji_reactions
                    WHERE reaction_id = %s
                """, (existing_reaction['reaction_id'],))
            else:
                # Add new reaction
                cur.execute("""
                    INSERT INTO community_emoji_reactions (post_id, user_id, emoji)
                    VALUES (%s, %s, %s)
                """, (post_id, user_id, emoji))

            conn.commit()

        return jsonify({'success': True, 'message': 'Reaction updated'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/community/comments/<int:comment_id>/react', methods=['POST'])
@login_required
def react_to_comment(comment_id):
    user_id = session.get('user_id')
    data = request.get_json()
    emoji = data.get('emoji')

    if not emoji:
        return jsonify({'success': False, 'message': 'Emoji is required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if user already reacted with this emoji
            cur.execute("""
                SELECT reaction_id FROM community_emoji_reactions
                WHERE comment_id = %s AND user_id = %s AND emoji = %s
            """, (comment_id, user_id, emoji))
            existing_reaction = cur.fetchone()

            if existing_reaction:
                # Remove the reaction
                cur.execute("""
                    DELETE FROM community_emoji_reactions
                    WHERE reaction_id = %s
                """, (existing_reaction['reaction_id'],))
            else:
                # Add new reaction
                cur.execute("""
                    INSERT INTO community_emoji_reactions (comment_id, user_id, emoji)
                    VALUES (%s, %s, %s)
                """, (comment_id, user_id, emoji))

            conn.commit()

        return jsonify({'success': True, 'message': 'Reaction updated'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/community/comments', methods=['POST'])
@login_required
def create_comment():
    user_id = session.get('user_id')
    data = request.get_json() if request.is_json else request.form

    post_id = data.get('post_id')
    content = data.get('content')

    if not all([post_id, content]):
        return jsonify({'success': False, 'message': 'Post ID and content are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO community_comments (post_id, user_id, content)
                VALUES (%s, %s, %s)
            """, (post_id, user_id, content))
            conn.commit()

        return jsonify({'success': True, 'message': 'Comment added successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/community/comments/<int:comment_id>', methods=['PUT'])
@login_required
def edit_comment(comment_id):
    user_id = session.get('user_id')
    data = request.get_json()

    content = data.get('content')

    if not content:
        return jsonify({'success': False, 'message': 'Content is required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if comment belongs to user
            cur.execute("SELECT user_id FROM community_comments WHERE comment_id = %s", (comment_id,))
            comment = cur.fetchone()

            if not comment or comment['user_id'] != user_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403

            cur.execute("UPDATE community_comments SET content = %s, updated_at = CURRENT_TIMESTAMP WHERE comment_id = %s", (content, comment_id))
            conn.commit()

        return jsonify({'success': True, 'message': 'Comment updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/livestock')
@login_required
def livestock():
    user_id = session.get('user_id')
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get cattle
            cur.execute("SELECT * FROM cattle WHERE user_id = %s ORDER BY name", (user_id,))
            cattle = cur.fetchall()

            # Get vaccinations
            cur.execute("""
                SELECT v.*, c.name as cattle_name
                FROM vaccinations v
                JOIN cattle c ON v.cattle_id = c.cattle_id
                WHERE c.user_id = %s
                ORDER BY v.date_administered DESC
            """, (user_id,))
            vaccinations = cur.fetchall()

            # Get milk records
            cur.execute("""
                SELECT m.*, c.name as cattle_name
                FROM milk_records m
                JOIN cattle c ON m.cattle_id = c.cattle_id
                WHERE c.user_id = %s
                ORDER BY m.record_date DESC
            """, (user_id,))
            milk_records = cur.fetchall()

            # Get estrus cycles
            cur.execute("""
                SELECT e.*, c.name as cattle_name
                FROM estrus_cycles e
                JOIN cattle c ON e.cattle_id = c.cattle_id
                WHERE c.user_id = %s
                ORDER BY e.start_date DESC
            """, (user_id,))
            estrus_cycles = cur.fetchall()

        return render_template('livestock.html', cattle=cattle, vaccinations=vaccinations, milk_records=milk_records, estrus_cycles=estrus_cycles)

    except Exception as e:
        return f"Error loading livestock: {str(e)}", 500
    finally:
        if conn: conn.close()

@app.route('/api/cattle', methods=['POST'])
@login_required
def add_cattle():
    user_id = session.get('user_id')
    data = request.get_json() if request.is_json else request.form

    name = data.get('name')
    breed = data.get('breed')
    date_of_birth = data.get('date_of_birth')
    gender = data.get('gender')
    purchase_date = data.get('purchase_date')
    purchase_price = data.get('purchase_price')
    notes = data.get('notes')

    if not all([name, gender]):
        return jsonify({'success': False, 'message': 'Name and gender are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO cattle (user_id, name, breed, date_of_birth, gender, purchase_date, purchase_price, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, name, breed, date_of_birth, gender, purchase_date, purchase_price, notes))
            conn.commit()

        if request.is_json:
            return jsonify({'success': True, 'message': 'Cattle added successfully'})
        else:
            return redirect(url_for('livestock'))

    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
        else:
            return f"Error: {str(e)}", 500
    finally:
        if conn: conn.close()

@app.route('/api/vaccinations', methods=['POST'])
@login_required
def add_vaccination():
    user_id = session.get('user_id')
    data = request.get_json() if request.is_json else request.form

    cattle_id = data.get('cattle_id')
    vaccine_name = data.get('vaccine_name')
    date_administered = data.get('date_administered')
    next_due_date = data.get('next_due_date')
    administered_by = data.get('administered_by')
    notes = data.get('notes')

    if not all([cattle_id, vaccine_name, date_administered]):
        return jsonify({'success': False, 'message': 'Cattle, vaccine name, and date are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if cattle belongs to user
            cur.execute("SELECT cattle_id FROM cattle WHERE cattle_id = %s AND user_id = %s", (cattle_id, user_id))
            if not cur.fetchone():
                return jsonify({'success': False, 'message': 'Invalid cattle'}), 400

            cur.execute("""
                INSERT INTO vaccinations (cattle_id, vaccine_name, date_administered, next_due_date, administered_by, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (cattle_id, vaccine_name, date_administered, next_due_date, administered_by, notes))
            conn.commit()

        return jsonify({'success': True, 'message': 'Vaccination added successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/milk_records', methods=['POST'])
@login_required
def add_milk_record():
    user_id = session.get('user_id')
    data = request.get_json() if request.is_json else request.form

    cattle_id = data.get('cattle_id')
    record_date = data.get('record_date')
    liters = data.get('liters')
    notes = data.get('notes')

    if not all([cattle_id, record_date, liters]):
        return jsonify({'success': False, 'message': 'Cattle, record date, and liters are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if cattle belongs to user
            cur.execute("SELECT cattle_id FROM cattle WHERE cattle_id = %s AND user_id = %s", (cattle_id, user_id))
            if not cur.fetchone():
                return jsonify({'success': False, 'message': 'Invalid cattle'}), 400

            cur.execute("""
                INSERT INTO milk_records (cattle_id, record_date, liters, notes)
                VALUES (%s, %s, %s, %s)
            """, (cattle_id, record_date, liters, notes))
            conn.commit()

        return jsonify({'success': True, 'message': 'Milk record added successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/estrus_cycles', methods=['POST'])
@login_required
def add_estrus_cycle():
    user_id = session.get('user_id')
    data = request.get_json() if request.is_json else request.form

    cattle_id = data.get('cattle_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    notes = data.get('notes')

    if not all([cattle_id, start_date]):
        return jsonify({'success': False, 'message': 'Cattle and start date are required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if cattle belongs to user
            cur.execute("SELECT cattle_id FROM cattle WHERE cattle_id = %s AND user_id = %s", (cattle_id, user_id))
            if not cur.fetchone():
                return jsonify({'success': False, 'message': 'Invalid cattle'}), 400

            cur.execute("""
                INSERT INTO estrus_cycles (cattle_id, start_date, end_date, notes)
                VALUES (%s, %s, %s, %s)
            """, (cattle_id, start_date, end_date, notes))
            conn.commit()

        return jsonify({'success': True, 'message': 'Estrus cycle added successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn: conn.close()

@app.route('/crop-requirements')
@login_required
def crop_requirements():
    return render_template('crop_requirements.html')

@app.route('/farming-calendar')
@login_required
def farming_calendar():
    return render_template('farming_calendar.html')

@app.route('/mandi-prices')
@login_required
def mandi_prices():
    # Get location from query parameter or user's profile
    location = request.args.get('location', None)
    user_id = session.get('user_id')

    if not location:
        # Get user's location from profile or default
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT location FROM users WHERE user_id = %s", (user_id,))
                user = cur.fetchone()
                if user and user['location']:
                    location = user['location']
                else:
                    location = 'Delhi'  # Default location
        except Exception as e:
            app.logger.warning(f"Could not fetch user location: {str(e)}")
            location = 'Delhi'
        finally:
            if conn: conn.close()

    # Fetch Mandi prices
    prices = get_mandi_prices(location)

    return render_template('mandi_prices.html', prices=prices, location=location)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session.get('user_id')

    if request.method == 'POST':
        # Handle profile updates and document uploads
        if 'bio' in request.form or 'profile_picture' in request.files or 'banner' in request.files:
            # Update profile
            bio = request.form.get('bio', '')
            profile_picture = request.files.get('profile_picture')
            banner = request.files.get('banner')

            # Ensure upload folder exists
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Handle profile picture upload
            profile_picture_path = None
            if profile_picture and profile_picture.filename:
                filename = secure_filename(f"{user_id}_pfp_{profile_picture.filename}")
                profile_picture_path = os.path.join(upload_folder, filename)
                profile_picture.save(profile_picture_path)
                profile_picture_path = f"static/uploads/{filename}"

            # Handle banner upload
            banner_path = None
            if banner and banner.filename:
                filename = secure_filename(f"{user_id}_banner_{banner.filename}")
                banner_path = os.path.join(upload_folder, filename)
                banner.save(banner_path)
                banner_path = f"static/uploads/{filename}"

            conn = None
            try:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    # Check if profile exists
                    cur.execute("SELECT profile_id FROM user_profiles WHERE user_id = %s", (user_id,))
                    profile = cur.fetchone()

                    if profile:
                        # Update existing profile
                        update_fields = []
                        update_values = []
                        if bio:
                            update_fields.append("bio = %s")
                            update_values.append(bio)
                        if profile_picture_path:
                            update_fields.append("profile_picture = %s")
                            update_values.append(profile_picture_path)
                        if banner_path:
                            update_fields.append("banner = %s")
                            update_values.append(banner_path)

                        if update_fields:
                            update_values.append(user_id)
                            cur.execute(f"UPDATE user_profiles SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s", update_values)
                    else:
                        # Create new profile
                        cur.execute("""
                            INSERT INTO user_profiles (user_id, profile_picture, banner, bio)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, profile_picture_path, banner_path, bio))

                    conn.commit()
                return jsonify({'success': True, 'message': 'Profile updated successfully'})
            except Exception as e:
                app.logger.error(f"Profile update error: {str(e)}")
                return jsonify({'success': False, 'message': 'Failed to update profile'})
            finally:
                if conn: conn.close()

        elif 'document_name' in request.form and 'document' in request.files:
            # Handle document upload
            document_name = request.form.get('document_name')
            document_type = request.form.get('document_type', 'other')
            document = request.files.get('document')

            if not document_name or not document:
                return jsonify({'success': False, 'message': 'Document name and file are required'})

            # Ensure upload folder exists
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            filename = secure_filename(f"{user_id}_{document_type}_{document.filename}")
            file_path = os.path.join(upload_folder, filename)
            document.save(file_path)
            file_path = f"static/uploads/{filename}"

            conn = None
            try:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_documents (user_id, document_name, document_type, file_path)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, document_name, document_type, file_path))
                    conn.commit()
                return jsonify({'success': True, 'message': 'Document uploaded successfully'})
            except Exception as e:
                app.logger.error(f"Document upload error: {str(e)}")
                return jsonify({'success': False, 'message': 'Failed to upload document'})
            finally:
                if conn: conn.close()

    # GET request: display profile
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get user profile
            cur.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
            profile = cur.fetchone() or {}

            # Get user documents
            cur.execute("SELECT * FROM user_documents WHERE user_id = %s ORDER BY uploaded_at DESC", (user_id,))
            documents = cur.fetchall()

        return render_template('profile.html', profile=profile, documents=documents)
    except Exception as e:
        app.logger.error(f"Profile display error: {str(e)}")
        return "Error loading profile", 500
    finally:
        if conn: conn.close()

@app.route('/api/weather')
@login_required
def weather():
    # Get location from query parameter, default to Delhi
    location = request.args.get('city', 'Delhi')

    api_key = app.config['OPENWEATHER_API_KEY']
    if api_key == 'your_openweather_api_key_here':
        # Return mock weather data for demo purposes, varying by city
        mock_weather_data = {
            'Delhi': {'temperature': 28, 'description': 'Clear sky', 'humidity': 65, 'wind_speed': 3.5},
            'Mumbai': {'temperature': 30, 'description': 'Partly cloudy', 'humidity': 75, 'wind_speed': 4.2},
            'Bangalore': {'temperature': 25, 'description': 'Light rain', 'humidity': 80, 'wind_speed': 2.8},
            'Chennai': {'temperature': 32, 'description': 'Sunny', 'humidity': 70, 'wind_speed': 5.1},
            'Kolkata': {'temperature': 29, 'description': 'Overcast', 'humidity': 85, 'wind_speed': 3.9},
            'Pune': {'temperature': 27, 'description': 'Clear sky', 'humidity': 60, 'wind_speed': 3.0},
            'Hyderabad': {'temperature': 31, 'description': 'Hot and humid', 'humidity': 78, 'wind_speed': 4.5},
            'Ahmedabad': {'temperature': 33, 'description': 'Sunny', 'humidity': 55, 'wind_speed': 2.5}
        }

        # Mock forecast data
        mock_forecast = [
            {'date': '2023-07-01', 'temp_min': 25, 'temp_max': 32, 'description': 'Sunny'},
            {'date': '2023-07-02', 'temp_min': 26, 'temp_max': 31, 'description': 'Partly cloudy'},
            {'date': '2023-07-03', 'temp_min': 24, 'temp_max': 30, 'description': 'Light rain'},
            {'date': '2023-07-04', 'temp_min': 27, 'temp_max': 33, 'description': 'Clear sky'},
            {'date': '2023-07-05', 'temp_min': 25, 'temp_max': 32, 'description': 'Sunny'}
        ]

        # Default to Delhi if city not in mock data
        city_data = mock_weather_data.get(location.title(), mock_weather_data['Delhi'])

        weather_info = {
            'location': location,
            'temperature': city_data['temperature'],
            'description': city_data['description'],
            'humidity': city_data['humidity'],
            'wind_speed': city_data['wind_speed']
        }
        return jsonify({'success': True, 'weather': weather_info, 'forecast': mock_forecast})

    try:
        # Fetch current weather
        current_url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric'
        current_response = requests.get(current_url)
        current_response.raise_for_status()
        current_data = current_response.json()

        weather_info = {
            'location': current_data['name'],
            'temperature': round(current_data['main']['temp']),
            'description': current_data['weather'][0]['description'].capitalize(),
            'humidity': current_data['main']['humidity'],
            'wind_speed': current_data['wind']['speed']
        }

        # Fetch 5-day forecast
        forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric'
        forecast_response = requests.get(forecast_url)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Process forecast data into daily summaries
        from collections import defaultdict
        daily_forecasts = defaultdict(list)

        for item in forecast_data['list']:
            date = item['dt_txt'].split(' ')[0]  # Get date part
            temp = item['main']['temp']
            desc = item['weather'][0]['description']
            daily_forecasts[date].append({'temp': temp, 'description': desc})

        # Summarize each day
        forecast_list = []
        for date, entries in list(daily_forecasts.items())[:5]:  # Take first 5 days
            temps = [e['temp'] for e in entries]
            descriptions = [e['description'] for e in entries]
            forecast_list.append({
                'date': date,
                'temp_min': round(min(temps)),
                'temp_max': round(max(temps)),
                'description': max(set(descriptions), key=descriptions.count).capitalize()  # Most common description
            })

        return jsonify({'success': True, 'weather': weather_info, 'forecast': forecast_list})

    except requests.RequestException as e:
        return jsonify({'success': False, 'message': f'Weather API error: {str(e)}'})
    except KeyError:
        return jsonify({'success': False, 'message': 'Invalid weather data received'})

def get_mandi_prices(location):
    """
    Fetch real-time Mandi prices from data.gov.in API or fallback to mock data.
    """
    try:
        # Try to fetch from data.gov.in API
        # Note: This is a placeholder - actual API endpoint and key would be needed
        api_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {
            'api-key': 'your_data_gov_in_api_key',  # Replace with actual API key
            'format': 'json',
            'limit': 100,
            'filters[state]': 'Delhi' if location.lower() == 'delhi' else 'Maharashtra'  # Map location to state
        }

        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Process API data
        prices = []
        if 'records' in data:
            for record in data['records'][:10]:  # Limit to 10 records
                prices.append({
                    'commodity': record.get('commodity', 'Unknown'),
                    'variety': record.get('variety', 'N/A'),
                    'market': record.get('market', 'Unknown Market'),
                    'price': float(record.get('modal_price', 0)),
                    'date': record.get('arrival_date', 'N/A')
                })

        if prices:
            return prices

    except Exception as e:
        app.logger.warning(f"Failed to fetch Mandi prices from API: {str(e)}")

    # Fallback to mock data
    return get_mock_mandi_prices(location)

def get_mock_mandi_prices(location):
    """
    Return mock Mandi prices for demonstration purposes.
    """
    # Base prices for different crops
    base_prices = {
        'Wheat': {'min': 1800, 'max': 2200},
        'Rice': {'min': 2500, 'max': 3500},
        'Cotton': {'min': 4500, 'max': 5500},
        'Sugarcane': {'min': 280, 'max': 320},
        'Maize': {'min': 1600, 'max': 2000},
        'Soybean': {'min': 3200, 'max': 3800},
        'Turmeric': {'min': 8000, 'max': 12000},
        'Chilli': {'min': 1500, 'max': 2500}
    }

    # Location-based price variations
    location_multipliers = {
        'delhi': 1.0,
        'mumbai': 1.05,
        'pune': 1.02,
        'bangalore': 0.98,
        'chennai': 0.95,
        'kolkata': 1.03,
        'hyderabad': 0.97,
        'ahmedabad': 1.01
    }

    multiplier = location_multipliers.get(location.lower(), 1.0)

    # Generate mock prices
    prices = []
    markets = [
        f"{location.title()} APMC",
        f"{location.title()} Krishi Mandi",
        f"{location.title()} Grain Market",
        f"{location.title()} Agricultural Market"
    ]

    for crop, price_range in base_prices.items():
        # Add some randomness
        base_price = random.uniform(price_range['min'], price_range['max']) * multiplier
        variation = random.uniform(0.95, 1.05)
        final_price = round(base_price * variation, 2)

        prices.append({
            'commodity': crop,
            'variety': 'Common',
            'market': random.choice(markets),
            'price': final_price,
            'date': datetime.now().strftime('%Y-%m-%d')
        })

    return prices

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
