import pymysql
import os

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Khushan@2828',
    'database': 'krishak_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def setup_database():
    try:
        # Connect to MySQL server (without specifying database to create it if needed)
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS krishak_db")
            print("Database 'krishak_db' created or already exists.")

        connection.commit()
        connection.close()

        # Now connect to the specific database
        connection = pymysql.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            # Drop existing tables in correct order (child tables first)
            tables_to_drop = [
                'community_emoji_reactions',
                'community_likes',
                'community_comments',
                'community_posts',
                'community_categories',
                'user_documents',
                'user_profiles',
                'vaccinations',
                'milk_records',
                'estrus_cycles',
                'cattle',
                'government_schemes',
                'expenses',
                'expense_categories',
                'users'
            ]
            
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"Dropped table: {table}")
                except Exception as e:
                    print(f"Error dropping table {table}: {e}")

            connection.commit()
            
            # Read and execute the schema file
            with open('schema.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Remove comment lines
            lines = sql_content.split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('--') and line.strip()]
            sql_content = '\n'.join(filtered_lines)

            # Split the SQL file into individual statements
            statements = sql_content.split(';')

            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        print(f"Executed: {statement[:50]}...")
                    except Exception as e:
                        print(f"Error executing statement: {e}")
                        print(f"Statement: {statement}")

        # Alter password_hash column to TEXT if needed
        try:
            cursor.execute("ALTER TABLE users MODIFY password_hash TEXT")
            print("Altered password_hash column to TEXT.")
        except Exception as e:
            print(f"Alter table skipped or failed: {e}")

        # Ensure required_documents column exists in government_schemes
        try:
            cursor.execute("ALTER TABLE government_schemes ADD COLUMN required_documents TEXT AFTER eligibility")
            print("Added required_documents column to government_schemes.")
        except pymysql.Error as e:
            if e.args[0] == 1060:  # Duplicate column error
                print("Column required_documents already exists.")
            else:
                print(f"Error adding column: {e}")

        # Add type column to community_likes table
        try:
            cursor.execute("ALTER TABLE community_likes ADD COLUMN type ENUM('like', 'dislike') DEFAULT 'like'")
            print("Added type column to community_likes.")
        except pymysql.Error as e:
            if e.args[0] == 1060:  # Duplicate column error
                print("Column type already exists in community_likes.")
            else:
                print(f"Error adding type column: {e}")

        connection.commit()
        print("Database setup completed successfully!")

        # Remove the repeated scheme (Kisan Credit Card)
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM government_schemes WHERE scheme_name = 'Kisan Credit Card'")
            print("Removed repeated scheme: Kisan Credit Card")

        # Insert some sample government schemes
        with connection.cursor() as cursor:
            sample_schemes = [
                ("PM-KISAN", "Pradhan Mantri Kisan Samman Nidhi - Direct income support of Rs. 6000 per year", "All landholding farmer families", "Aadhar Card, Bank Account Details, Land Records", "https://pmkisan.gov.in/", True),
                ("Soil Health Card", "Provides soil health information to farmers - Free soil testing and health cards", "All farmers", "Aadhar Card, Land Records, Soil Sample (if applicable)", "https://soilhealth.dac.gov.in/", True),
                ("Pradhan Mantri Fasal Bima Yojana", "Crop insurance scheme - Financial support against crop loss", "All farmers growing notified crops", "Aadhar Card, Bank Account Details, Land Records, Crop Details", "https://pmfby.gov.in/", True)
            ]

            cursor.executemany("""
                INSERT IGNORE INTO government_schemes
                (scheme_name, description, eligibility, required_documents, link, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, sample_schemes)

        connection.commit()
        print("Sample government schemes inserted.")

    except Exception as e:
        print(f"Error setting up database: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    setup_database()
