from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
from sqlalchemy.exc import IntegrityError

def create_admin_user():
    db = SessionLocal()
    
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("✅ Admin user already exists!")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")
            print(f"   Role: {existing_admin.role}")
            return
        
        admin_user = User(
            email="admin@mcq.com",
            username="admin",
            full_name="Administrator",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            email_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("🎉 Admin user created successfully!")
        print(f"   Username: {admin_user.username}")
        print(f"   Password: admin123")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role}")
        print("\n⚠️  Please change the password after first login!")
        
    except IntegrityError as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        print("Admin user might already exist with different details.")
    except Exception as e:
        db.rollback()
        print(f"❌ Unexpected error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Creating Admin User for MCQ Platform")
    print("=" * 50)
    create_admin_user()
    print("=" * 50)
    print("Admin User Creation Process Completed")