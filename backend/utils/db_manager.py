
import mysql.connector
import os
import re
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.db = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'Test@123'),
            database=os.getenv('DB_DATABASE', 'missing_database')
        )
        self.cursor = self.db.cursor(dictionary=True)
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Create tables with consistent column types
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS missing_children (
                id INT AUTO_INCREMENT PRIMARY KEY,
                child_name VARCHAR(255) NOT NULL,
                case_id VARCHAR(36) NOT NULL,
                parent_phone VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_case_id (case_id)
            )
            """)
            self.db.commit()

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS missing_child_photos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                case_id VARCHAR(36) NOT NULL,
                photo LONGBLOB NOT NULL,
                FOREIGN KEY (case_id) REFERENCES missing_children(case_id) ON DELETE CASCADE
            )
            """)
            self.db.commit()

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reported_children (
                id INT AUTO_INCREMENT PRIMARY KEY,
                child_name VARCHAR(255),
                location VARCHAR(255) NOT NULL,
                reporter_name VARCHAR(255) NOT NULL,
                reporter_phone VARCHAR(20) NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            self.db.commit()
            
            # Create table for mole data
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mole_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                case_id VARCHAR(36) NOT NULL,
                description TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES missing_children(case_id) ON DELETE CASCADE
            )
            """)
            self.db.commit()
            
            # Check if parent_phone column exists, add it if it doesn't
            try:
                self.cursor.execute("SELECT parent_phone FROM missing_children LIMIT 1")
                # Consume the result to avoid unread result errors
                self.cursor.fetchall()
            except mysql.connector.Error as err:
                if err.errno == 1054:  # Unknown column error
                    print("Adding missing parent_phone column to missing_children table")
                    self.cursor.execute("ALTER TABLE missing_children ADD COLUMN parent_phone VARCHAR(20)")
                    self.db.commit()
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            self._reset_connection()
            raise

    def _reset_connection(self):
        """Reset the database connection if needed"""
        try:
            self.cursor.close()
            self.db.close()
        except:
            pass
        
        self.db = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_DATABASE', 'missing_database')
        )
        self.cursor = self.db.cursor(dictionary=True)

    def insert_missing_child(self, child_name, case_id, files, parent_phone=None, distinguishing_features=None):
        """Insert a missing child record with multiple photos and mole data"""
        try:
            # Insert child record
            sql = "INSERT INTO missing_children (child_name, case_id, parent_phone) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (child_name, case_id, parent_phone))

            # Insert each photo
            for photo in files:
                photo_data = photo.read()
                sql = "INSERT INTO missing_child_photos (case_id, photo) VALUES (%s, %s)"
                self.cursor.execute(sql, (case_id, photo_data))
            
            # Store mole data if provided
            if distinguishing_features and len(distinguishing_features.strip()) > 0:
                sql = "INSERT INTO mole_data (case_id, description) VALUES (%s, %s)"
                self.cursor.execute(sql, (case_id, distinguishing_features))

            self.db.commit()
            return True
        except Exception as e:
            print(f"Error inserting missing child: {e}")
            self.db.rollback()
            self._reset_connection()
            raise

    def store_reported_child(self, child_name, location, reporter_name, reporter_phone, details=""):
        """Store information about a reported (found) child"""
        try:
            sql = """
            INSERT INTO reported_children 
            (child_name, location, reporter_name, reporter_phone, details) 
            VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (child_name, location, reporter_name, reporter_phone, details))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error storing reported child: {e}")
            self.db.rollback()
            self._reset_connection()
            raise

    def get_last_seen_locations(self, child_name):
        """Get locations where a child was last seen, ordered by most recent first"""
        try:
            sql = """
            SELECT location, created_at 
            FROM reported_children 
            WHERE child_name = %s 
            ORDER BY created_at DESC
            """
            self.cursor.execute(sql, (child_name,))
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error getting last seen locations: {e}")
            self._reset_connection()
            raise

    def get_parent_phone(self, child_name):
        """Get parent phone number for a missing child by name"""
        try:
            sql = """
            SELECT parent_phone 
            FROM missing_children 
            WHERE child_name = %s
            """
            self.cursor.execute(sql, (child_name,))
            result = self.cursor.fetchone()
            return result['parent_phone'] if result and 'parent_phone' in result else None
        except Exception as e:
            print(f"Error getting parent phone: {e}")
            self._reset_connection()
            raise

    def retrieve_child_photos(self, output_dir="./training_data"):
        """Retrieve all photos grouped by child name for model training"""
        try:
            sql = """
            SELECT mc.child_name, mcp.photo 
            FROM missing_children mc 
            JOIN missing_child_photos mcp ON mc.case_id = mcp.case_id
            """
            self.cursor.execute(sql)
            results = self.cursor.fetchall()

            if not results:
                return None

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Group photos by child name
            for result in results:
                child_name = result['child_name']
                photo_data = result['photo']
                
                # Create child-specific directory
                child_dir = os.path.join(output_dir, self._sanitize_filename(child_name))
                os.makedirs(child_dir, exist_ok=True)

                # Save photo with unique filename
                photo_path = os.path.join(child_dir, f"photo_{hash(str(photo_data))}.jpg")
                with open(photo_path, "wb") as f:
                    f.write(photo_data)

            return output_dir
        except Exception as e:
            print(f"Error retrieving photos: {e}")
            self._reset_connection()
            raise

    def get_child_details(self, child_name):
        """Get details of a missing child by name"""
        try:
            sql = """
            SELECT mc.* 
            FROM missing_children mc
            WHERE mc.child_name = %s
            """
            self.cursor.execute(sql, (child_name,))
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            print(f"Error getting child details: {e}")
            self._reset_connection()
            raise
    
    def get_all_mole_data(self):
        """Get all mole descriptions with associated child names"""
        try:
            sql = """
            SELECT md.id, md.description, mc.child_name, mc.case_id
            FROM mole_data md
            JOIN missing_children mc ON md.case_id = mc.case_id
            """
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error getting mole data: {e}")
            self._reset_connection()
            raise
    
    def get_mole_data_for_child(self, child_name):
        """Get mole descriptions for a specific child"""
        try:
            sql = """
            SELECT md.description
            FROM mole_data md
            JOIN missing_children mc ON md.case_id = mc.case_id
            WHERE mc.child_name = %s
            """
            self.cursor.execute(sql, (child_name,))
            result = self.cursor.fetchone()
            return result['description'] if result else None
        except Exception as e:
            print(f"Error getting mole data for child: {e}")
            self._reset_connection()
            raise

    def _sanitize_filename(self, name):
        """Remove invalid characters from filename"""
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def close(self):
        """Close database connection"""
        try:
            self.cursor.close()
            self.db.close()
        except:
            pass
