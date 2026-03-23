"""
Fallback demo data — used only when no JSONL dataset files are found.
Contains 20 realistic software products so the app still works out of the box.
"""
import json
import numpy as np
from models import User, Product, Rating
from engine.trust_engine import TrustEngine

PRODUCTS_DATA = [
    {"asin": "B001SOFT01", "title": "Adobe Acrobat Pro DC 2024", "description": "Professional PDF creation and editing.", "category": "Productivity Software", "price": 299.99, "image_url": "https://picsum.photos/seed/adobe/300/200", "features": ["PDF editing", "E-signatures", "Cloud sync", "OCR"]},
    {"asin": "B001SOFT02", "title": "Microsoft Office 365 Personal", "description": "Complete Office suite: Word, Excel, PowerPoint.", "category": "Productivity Software", "price": 69.99, "image_url": "https://picsum.photos/seed/office/300/200", "features": ["Word processing", "Spreadsheets", "Presentations", "Email"]},
    {"asin": "B001SOFT03", "title": "Kaspersky Internet Security 2024", "description": "Comprehensive antivirus and internet security.", "category": "Security Software", "price": 39.99, "image_url": "https://picsum.photos/seed/kaspersky/300/200", "features": ["Real-time protection", "VPN", "Password manager"]},
    {"asin": "B001SOFT04", "title": "Quickbooks Pro 2024", "description": "Award-winning accounting software for small businesses.", "category": "Business Software", "price": 399.99, "image_url": "https://picsum.photos/seed/quickbooks/300/200", "features": ["Invoicing", "Expense tracking", "Tax reports", "Payroll"]},
    {"asin": "B001SOFT05", "title": "AutoCAD LT 2024", "description": "Professional 2D CAD software for drafting.", "category": "Design Software", "price": 549.00, "image_url": "https://picsum.photos/seed/autocad/300/200", "features": ["2D drafting", "DWG format", "Cloud storage"]},
    {"asin": "B001SOFT06", "title": "Malwarebytes Premium", "description": "Advanced malware protection.", "category": "Security Software", "price": 39.99, "image_url": "https://picsum.photos/seed/malware/300/200", "features": ["Malware removal", "Ransomware protection", "Browser guard"]},
    {"asin": "B001SOFT07", "title": "Norton 360 Deluxe", "description": "All-in-one security suite.", "category": "Security Software", "price": 49.99, "image_url": "https://picsum.photos/seed/norton/300/200", "features": ["Antivirus", "VPN", "Password manager", "Dark web monitoring"]},
    {"asin": "B001SOFT08", "title": "Photoshop Elements 2024", "description": "Easy photo editing powered by AI.", "category": "Design Software", "price": 99.99, "image_url": "https://picsum.photos/seed/photoshop/300/200", "features": ["AI photo editing", "One-click fixes", "Guided edits"]},
    {"asin": "B001SOFT09", "title": "TurboTax Premier 2023", "description": "Maximize your tax deductions.", "category": "Business Software", "price": 89.99, "image_url": "https://picsum.photos/seed/turbotax/300/200", "features": ["Investment income", "Rental properties", "Step-by-step guidance"]},
    {"asin": "B001SOFT10", "title": "Bitdefender Total Security", "description": "Multi-platform security suite.", "category": "Security Software", "price": 44.99, "image_url": "https://picsum.photos/seed/bitdefender/300/200", "features": ["Multi-device", "Webcam protection", "Anti-ransomware"]},
    {"asin": "B001SOFT11", "title": "VMware Workstation Pro 17", "description": "Run multiple operating systems as VMs.", "category": "Developer Tools", "price": 199.99, "image_url": "https://picsum.photos/seed/vmware/300/200", "features": ["Multiple VMs", "Snapshots", "Networking"]},
    {"asin": "B001SOFT12", "title": "Slack Pro Annual Plan", "description": "Messaging platform for teams.", "category": "Business Software", "price": 87.75, "image_url": "https://picsum.photos/seed/slack/300/200", "features": ["Channels", "Video calls", "File sharing"]},
    {"asin": "B001SOFT13", "title": "Premiere Elements 2024", "description": "Easy video editing for beginners.", "category": "Design Software", "price": 99.99, "image_url": "https://picsum.photos/seed/premiere/300/200", "features": ["AI editing", "Motion titles", "4K support"]},
    {"asin": "B001SOFT14", "title": "Acronis True Image 2024", "description": "Complete data protection and backup.", "category": "Security Software", "price": 49.99, "image_url": "https://picsum.photos/seed/acronis/300/200", "features": ["Full image backup", "Cloud storage", "Ransomware protection"]},
    {"asin": "B001SOFT15", "title": "Parallels Desktop 19 for Mac", "description": "Run Windows on Mac without rebooting.", "category": "Developer Tools", "price": 99.99, "image_url": "https://picsum.photos/seed/parallels/300/200", "features": ["Windows on Mac", "Coherence mode", "DirectX 11"]},
    {"asin": "B001SOFT16", "title": "ESET NOD32 Antivirus", "description": "Essential antivirus with machine learning.", "category": "Security Software", "price": 39.99, "image_url": "https://picsum.photos/seed/eset/300/200", "features": ["Machine learning", "Low system impact", "Exploit blocker"]},
    {"asin": "B001SOFT17", "title": "Lightroom Classic CC 2024", "description": "Desktop-based photo editing.", "category": "Design Software", "price": 119.88, "image_url": "https://picsum.photos/seed/lightroom/300/200", "features": ["RAW editing", "Cataloging", "Presets", "Cloud sync"]},
    {"asin": "B001SOFT18", "title": "Zoom Pro Annual Plan", "description": "Video conferencing with HD video.", "category": "Business Software", "price": 149.90, "image_url": "https://picsum.photos/seed/zoom/300/200", "features": ["HD video", "Recording", "Webinars", "Breakout rooms"]},
    {"asin": "B001SOFT19", "title": "Sage 50cloud Accounting", "description": "Desktop accounting with cloud connectivity.", "category": "Business Software", "price": 567.00, "image_url": "https://picsum.photos/seed/sage/300/200", "features": ["Invoicing", "Inventory", "Payroll", "Tax filing"]},
    {"asin": "B001SOFT20", "title": "Corel WordPerfect Office X9", "description": "Powerful office suite.", "category": "Productivity Software", "price": 249.99, "image_url": "https://picsum.photos/seed/corel/300/200", "features": ["Word processing", "Spreadsheets", "PDF editor"]},
]

RATINGS_DATA = [
    ("alice_dev", "B001SOFT01", 5.0, "Absolutely essential for my PDF workflow.", True, 12),
    ("alice_dev", "B001SOFT02", 4.0, "Microsoft Office is the industry standard.", True, 8),
    ("alice_dev", "B001SOFT11", 5.0, "VMware is rock solid for dev environments.", True, 15),
    ("bob_tech",  "B001SOFT03", 3.0, "Kaspersky works but feels heavy on resources.", True, 4),
    ("bob_tech",  "B001SOFT06", 5.0, "Malwarebytes caught threats my AV missed.", True, 20),
    ("bob_tech",  "B001SOFT07", 4.0, "Norton 360 is comprehensive with no impact.", True, 11),
    ("carol_pm",  "B001SOFT02", 5.0, "Real-time collaboration in Office is seamless.", True, 14),
    ("carol_pm",  "B001SOFT04", 4.0, "QuickBooks saves me hours every month.", True, 8),
    ("carol_pm",  "B001SOFT12", 5.0, "Slack transformed how our team communicates.", True, 18),
    ("dave_design","B001SOFT05", 5.0, "AutoCAD is incredibly powerful for drafting.", True, 16),
    ("dave_design","B001SOFT08", 4.0, "Photoshop Elements makes complex edits easy.", True, 7),
    ("dave_design","B001SOFT17", 5.0, "Lightroom is the best photo organizer ever.", True, 22),
]

DEMO_USERS = [
    {"username": "alice_dev",   "email": "alice@example.com",  "password": "password123"},
    {"username": "bob_tech",    "email": "bob@example.com",    "password": "password123"},
    {"username": "carol_pm",    "email": "carol@example.com",  "password": "password123"},
    {"username": "dave_design", "email": "dave@example.com",   "password": "password123"},
]


def seed_demo_data(db_instance):
    trust_engine = TrustEngine()
    user_map = {}
    for ud in DEMO_USERS:
        u = User(username=ud['username'], email=ud['email'])
        u.set_password(ud['password'])
        db_instance.session.add(u)
        db_instance.session.flush()
        user_map[ud['username']] = u

    product_map = {}
    for pd_data in PRODUCTS_DATA:
        p = Product(
            asin=pd_data['asin'], title=pd_data['title'],
            description=pd_data['description'], category=pd_data['category'],
            price=pd_data['price'], image_url=pd_data['image_url'],
            features=json.dumps(pd_data['features'])
        )
        db_instance.session.add(p)
        db_instance.session.flush()
        product_map[pd_data['asin']] = p

    for uname, asin, rating, text, verified, helpful in RATINGS_DATA:
        u = user_map[uname]
        p = product_map[asin]
        r = Rating(user_id=u.id, product_id=p.id, rating=rating,
                   review_text=text, verified_purchase=verified, helpful_votes=helpful)
        db_instance.session.add(r)
    db_instance.session.commit()

    mean_price = float(np.mean([p['price'] for p in PRODUCTS_DATA]))
    for asin, prod_obj in product_map.items():
        ratings_qs = Rating.query.filter_by(product_id=prod_obj.id).all()
        if not ratings_qs:
            continue
        raw = [r.rating for r in ratings_qs]
        prod_obj.avg_rating = float(np.mean(raw))
        prod_obj.rating_count = len(raw)
        p_det = trust_engine.product_trust_score(prod_obj, ratings_qs, mean_price)
        user_trusts = [trust_engine.user_trust_score(Rating.query.filter_by(user_id=r.user_id).all()) for r in ratings_qs]
        u_trust = float(np.mean(user_trusts))
        final = 0.55 * p_det['product_trust'] + 0.35 * u_trust + 0.10 * 0.5
        prod_obj.product_trust = round(p_det['product_trust'], 3)
        prod_obj.seller_trust = 0.5
        prod_obj.final_trust_score = round(final, 3)
        prod_obj.avg_rating_norm = round(p_det['avg_rating_norm'], 3)
        prod_obj.verified_ratio = round(p_det['verified_ratio'], 3)
        prod_obj.review_confidence = round(p_det['review_confidence'], 3)
        prod_obj.text_quality = round(p_det['text_quality'], 3)
        prod_obj.price_factor = round(p_det['price_factor'], 3)
        prod_obj.title_similarity = round(p_det['title_similarity'], 3)
    db_instance.session.commit()
    print(f"[SEED] Demo fallback complete: {len(PRODUCTS_DATA)} products.")