"""
Seed the DB with realistic Amazon Software-category products, users, ratings,
and pre-compute trust scores exactly as the pipeline does.
"""
import json
import numpy as np
from extensions import db
from models import User, Product, Rating
from engine.trust_engine import TrustEngine

PRODUCTS_DATA = [
    {
        "asin": "B001SOFT01", "title": "Adobe Acrobat Pro DC 2024",
        "description": "Professional PDF creation and editing. Convert, edit, sign and share PDFs.",
        "category": "Productivity Software", "price": 299.99,
        "image_url": "https://picsum.photos/seed/adobe/300/200",
        "features": ["PDF editing", "E-signatures", "Cloud sync", "OCR", "Form creation"]
    },
    {
        "asin": "B001SOFT02", "title": "Microsoft Office 365 Personal",
        "description": "Complete Office suite: Word, Excel, PowerPoint, Outlook, and more.",
        "category": "Productivity Software", "price": 69.99,
        "image_url": "https://picsum.photos/seed/office/300/200",
        "features": ["Word processing", "Spreadsheets", "Presentations", "Email", "Cloud storage"]
    },
    {
        "asin": "B001SOFT03", "title": "Kaspersky Internet Security 2024",
        "description": "Comprehensive antivirus and internet security for all devices.",
        "category": "Security Software", "price": 39.99,
        "image_url": "https://picsum.photos/seed/kaspersky/300/200",
        "features": ["Real-time protection", "VPN", "Password manager", "Parental controls"]
    },
    {
        "asin": "B001SOFT04", "title": "Quickbooks Pro 2024",
        "description": "Award-winning accounting software for small businesses.",
        "category": "Business Software", "price": 399.99,
        "image_url": "https://picsum.photos/seed/quickbooks/300/200",
        "features": ["Invoicing", "Expense tracking", "Tax reports", "Payroll", "Bank sync"]
    },
    {
        "asin": "B001SOFT05", "title": "AutoCAD LT 2024",
        "description": "Professional 2D CAD software for drafting and documentation.",
        "category": "Design Software", "price": 549.00,
        "image_url": "https://picsum.photos/seed/autocad/300/200",
        "features": ["2D drafting", "DWG format", "Cloud storage", "Collaboration"]
    },
    {
        "asin": "B001SOFT06", "title": "Malwarebytes Premium",
        "description": "Advanced malware protection detecting threats that antivirus misses.",
        "category": "Security Software", "price": 39.99,
        "image_url": "https://picsum.photos/seed/malware/300/200",
        "features": ["Malware removal", "Ransomware protection", "Browser guard", "Real-time scanning"]
    },
    {
        "asin": "B001SOFT07", "title": "Corel WordPerfect Office X9",
        "description": "Powerful office suite with enhanced PDF features and compatibility.",
        "category": "Productivity Software", "price": 249.99,
        "image_url": "https://picsum.photos/seed/corel/300/200",
        "features": ["Word processing", "Spreadsheets", "PDF editor", "Macro support"]
    },
    {
        "asin": "B001SOFT08", "title": "Norton 360 Deluxe",
        "description": "All-in-one security: antivirus, VPN, password manager, and dark web monitoring.",
        "category": "Security Software", "price": 49.99,
        "image_url": "https://picsum.photos/seed/norton/300/200",
        "features": ["Antivirus", "VPN", "Password manager", "Dark web monitoring", "Cloud backup"]
    },
    {
        "asin": "B001SOFT09", "title": "Photoshop Elements 2024",
        "description": "Easy photo editing powered by Adobe Sensei AI.",
        "category": "Design Software", "price": 99.99,
        "image_url": "https://picsum.photos/seed/photoshop/300/200",
        "features": ["AI photo editing", "One-click fixes", "Guided edits", "Organizer", "Slideshow"]
    },
    {
        "asin": "B001SOFT10", "title": "TurboTax Premier 2023",
        "description": "Maximize your tax deductions for investments and rental properties.",
        "category": "Business Software", "price": 89.99,
        "image_url": "https://picsum.photos/seed/turbotax/300/200",
        "features": ["Investment income", "Rental properties", "Step-by-step guidance", "Audit support"]
    },
    {
        "asin": "B001SOFT11", "title": "Bitdefender Total Security",
        "description": "Multi-platform security for Windows, Mac, Android and iOS.",
        "category": "Security Software", "price": 44.99,
        "image_url": "https://picsum.photos/seed/bitdefender/300/200",
        "features": ["Multi-device", "Webcam protection", "Safe banking", "Anti-ransomware"]
    },
    {
        "asin": "B001SOFT12", "title": "VMware Workstation Pro 17",
        "description": "Run multiple operating systems as virtual machines on one PC.",
        "category": "Developer Tools", "price": 199.99,
        "image_url": "https://picsum.photos/seed/vmware/300/200",
        "features": ["Multiple VMs", "Snapshots", "Networking", "Cross-platform", "DirectX support"]
    },
    {
        "asin": "B001SOFT13", "title": "Slack Pro Annual Plan",
        "description": "Messaging platform for teams with channels, calls, and integrations.",
        "category": "Business Software", "price": 87.75,
        "image_url": "https://picsum.photos/seed/slack/300/200",
        "features": ["Channels", "Video calls", "File sharing", "App integrations", "Searchable history"]
    },
    {
        "asin": "B001SOFT14", "title": "Premiere Elements 2024",
        "description": "Easy-to-use video editing for beginners and hobbyists.",
        "category": "Design Software", "price": 99.99,
        "image_url": "https://picsum.photos/seed/premiere/300/200",
        "features": ["AI editing", "Motion titles", "Guided edits", "4K support", "Social sharing"]
    },
    {
        "asin": "B001SOFT15", "title": "Acronis True Image 2024",
        "description": "Complete data protection: backup, recovery, and cyber security.",
        "category": "Security Software", "price": 49.99,
        "image_url": "https://picsum.photos/seed/acronis/300/200",
        "features": ["Full image backup", "Cloud storage", "Ransomware protection", "Mobile backup"]
    },
    {
        "asin": "B001SOFT16", "title": "Sage 50cloud Accounting",
        "description": "Desktop accounting with cloud connectivity for growing businesses.",
        "category": "Business Software", "price": 567.00,
        "image_url": "https://picsum.photos/seed/sage/300/200",
        "features": ["Invoicing", "Inventory", "Payroll", "Tax filing", "Bank reconciliation"]
    },
    {
        "asin": "B001SOFT17", "title": "Parallels Desktop 19 for Mac",
        "description": "Run Windows on Mac without rebooting — seamlessly.",
        "category": "Developer Tools", "price": 99.99,
        "image_url": "https://picsum.photos/seed/parallels/300/200",
        "features": ["Windows on Mac", "Coherence mode", "Touch Bar support", "DirectX 11"]
    },
    {
        "asin": "B001SOFT18", "title": "ESET NOD32 Antivirus",
        "description": "Essential antivirus with machine learning protection.",
        "category": "Security Software", "price": 39.99,
        "image_url": "https://picsum.photos/seed/eset/300/200",
        "features": ["Machine learning", "Low system impact", "Exploit blocker", "UEFI scanner"]
    },
    {
        "asin": "B001SOFT19", "title": "Lightroom Classic CC 2024",
        "description": "Desktop-based photo editing and organization for photographers.",
        "category": "Design Software", "price": 119.88,
        "image_url": "https://picsum.photos/seed/lightroom/300/200",
        "features": ["RAW editing", "Cataloging", "Presets", "Cloud sync", "Print module"]
    },
    {
        "asin": "B001SOFT20", "title": "Zoom Pro Annual Plan",
        "description": "Video conferencing with HD video, recording and webinar features.",
        "category": "Business Software", "price": 149.90,
        "image_url": "https://picsum.photos/seed/zoom/300/200",
        "features": ["HD video", "Recording", "Webinars", "Breakout rooms", "Whiteboard"]
    },
]

USERS_DATA = [
    {"username": "alice_dev", "email": "alice@example.com", "password": "password123"},
    {"username": "bob_tech", "email": "bob@example.com", "password": "password123"},
    {"username": "carol_pm", "email": "carol@example.com", "password": "password123"},
    {"username": "dave_design", "email": "dave@example.com", "password": "password123"},
    {"username": "eve_security", "email": "eve@example.com", "password": "password123"},
    {"username": "frank_biz", "email": "frank@example.com", "password": "password123"},
    {"username": "grace_analyst", "email": "grace@example.com", "password": "password123"},
    {"username": "henry_admin", "email": "henry@example.com", "password": "password123"},
]

RATINGS_DATA = [
    # (username, asin, rating, review_text, verified, helpful_votes)
    ("alice_dev",    "B001SOFT01", 5.0, "Absolutely essential for my PDF workflow. The OCR feature alone is worth the price. Highly recommended for professionals.", True, 12),
    ("alice_dev",    "B001SOFT02", 4.0, "Microsoft Office is the industry standard. Works flawlessly with all my documents. OneDrive integration is a big plus.", True, 8),
    ("alice_dev",    "B001SOFT12", 5.0, "VMware is rock solid. I run multiple dev environments without any issues. Snapshot feature is a lifesaver.", True, 15),
    ("alice_dev",    "B001SOFT17", 4.0, "Parallels makes Windows on Mac feel native. Boot Camp is gone but Parallels fills the gap perfectly.", True, 7),
    ("bob_tech",     "B001SOFT03", 3.0, "Kaspersky works but it feels heavy on system resources. Slows down my older laptop noticeably.", True, 4),
    ("bob_tech",     "B001SOFT06", 5.0, "Malwarebytes caught threats that my old antivirus missed completely. The ransomware protection gives real peace of mind.", True, 20),
    ("bob_tech",     "B001SOFT08", 4.0, "Norton 360 is comprehensive. VPN is decent and the dark web monitoring caught my email in a breach.", True, 11),
    ("bob_tech",     "B001SOFT12", 5.0, "Best virtualization software for developers. Networking features are very advanced and configurable.", True, 9),
    ("bob_tech",     "B001SOFT18", 4.0, "ESET is incredibly lightweight. My system runs just as fast with it enabled. Good detection rates.", True, 6),
    ("carol_pm",     "B001SOFT02", 5.0, "Office 365 has become indispensable for our team. Real-time collaboration in Word and Excel is seamless.", True, 14),
    ("carol_pm",     "B001SOFT04", 4.0, "QuickBooks is a solid accounting package. Took a few weeks to learn but now it saves me hours every month.", True, 8),
    ("carol_pm",     "B001SOFT13", 5.0, "Slack transformed how our distributed team communicates. The integrations with other tools are brilliant.", True, 18),
    ("carol_pm",     "B001SOFT20", 5.0, "Zoom Pro is flawless for client calls. The recording feature is very useful for review sessions.", True, 13),
    ("dave_design",  "B001SOFT05", 5.0, "AutoCAD LT is incredibly powerful for 2D drafting. The DWG compatibility with clients is perfect.", True, 16),
    ("dave_design",  "B001SOFT09", 4.0, "Photoshop Elements is perfect for my hobby photography. The AI features make complex edits very easy.", True, 7),
    ("dave_design",  "B001SOFT14", 5.0, "Premiere Elements is great for family videos. The guided edits mean I always get professional results.", True, 10),
    ("dave_design",  "B001SOFT19", 5.0, "Lightroom Classic is the best photo organizer I have used. The preset system is incredibly powerful.", True, 22),
    ("eve_security", "B001SOFT03", 4.0, "Kaspersky has strong detection rates. The VPN is a nice bonus for travel. Interface could be cleaner.", False, 3),
    ("eve_security", "B001SOFT06", 5.0, "Malwarebytes is an excellent second-layer defense. I run it alongside my main AV and it catches extra threats.", True, 17),
    ("eve_security", "B001SOFT08", 5.0, "Norton 360 Deluxe is the most complete security package I have tried. No performance impact at all.", True, 19),
    ("eve_security", "B001SOFT11", 4.0, "Bitdefender Total Security is very comprehensive and extremely lightweight. Safe banking mode is great.", True, 12),
    ("eve_security", "B001SOFT15", 5.0, "Acronis True Image is the best backup solution available. Saved my data once already after a drive failure.", True, 24),
    ("frank_biz",    "B001SOFT04", 5.0, "QuickBooks Pro has streamlined our entire accounting process. The bank sync feature alone saves hours per week.", True, 21),
    ("frank_biz",    "B001SOFT10", 4.0, "TurboTax Premier made filing investment taxes much less painful. Step-by-step guidance is very clear.", True, 9),
    ("frank_biz",    "B001SOFT13", 4.0, "Slack is good but can become noisy. The channel structure helps but requires discipline from the whole team.", True, 6),
    ("frank_biz",    "B001SOFT16", 3.0, "Sage 50cloud is powerful but has a steep learning curve. Customer support was not very helpful either.", False, 2),
    ("grace_analyst","B001SOFT02", 5.0, "Excel alone makes Office 365 worth every penny. Power Query and Power Pivot are game changers for data work.", True, 25),
    ("grace_analyst","B001SOFT04", 4.0, "QuickBooks handles our small business finances well. Reports are detailed and export to Excel easily.", True, 11),
    ("grace_analyst","B001SOFT10", 5.0, "TurboTax Premier is brilliant for complex tax situations. Imported all my brokerage data automatically.", True, 15),
    ("grace_analyst","B001SOFT20", 4.0, "Zoom is reliable for large team meetings. Occasional audio quality issues but generally very solid.", True, 8),
    ("henry_admin",  "B001SOFT01", 4.0, "Adobe Acrobat Pro is great but quite expensive. The feature set is unmatched though for serious PDF work.", True, 10),
    ("henry_admin",  "B001SOFT07", 3.0, "WordPerfect is decent but feels dated compared to modern alternatives. Some compatibility issues too.", False, 1),
    ("henry_admin",  "B001SOFT11", 5.0, "Bitdefender is phenomenal. Zero performance hit and blocked every test threat I threw at it perfectly.", True, 20),
    ("henry_admin",  "B001SOFT17", 5.0, "Parallels Desktop is brilliant for running legacy Windows apps on my M2 Mac. Fast and very stable.", True, 14),
    ("henry_admin",  "B001SOFT18", 4.0, "ESET NOD32 is the most efficient antivirus I have used. Barely noticeable when running in the background.", True, 9),
]


def seed_data(db_instance):
    """Seed all data and compute trust scores."""
    # Skip if already seeded
    if User.query.count() > 0:
        return

    print("[SEED] Seeding database...")
    trust_engine = TrustEngine()

    # Create users
    user_map = {}
    for ud in USERS_DATA:
        u = User(username=ud['username'], email=ud['email'])
        u.set_password(ud['password'])
        db_instance.session.add(u)
        db_instance.session.flush()
        user_map[ud['username']] = u

    # Create products
    product_map = {}
    for pd_data in PRODUCTS_DATA:
        p = Product(
            asin=pd_data['asin'],
            title=pd_data['title'],
            description=pd_data['description'],
            category=pd_data['category'],
            price=pd_data['price'],
            image_url=pd_data['image_url'],
            features=json.dumps(pd_data['features'])
        )
        db_instance.session.add(p)
        db_instance.session.flush()
        product_map[pd_data['asin']] = p

    # Create ratings
    for uname, asin, rating, text, verified, helpful in RATINGS_DATA:
        u = user_map[uname]
        p = product_map[asin]
        r = Rating(
            user_id=u.id, product_id=p.id,
            rating=rating, review_text=text,
            verified_purchase=verified, helpful_votes=helpful
        )
        db_instance.session.add(r)
    db_instance.session.commit()

    # Compute per-product trust scores using TrustEngine
    mean_price = float(np.mean([p['price'] for p in PRODUCTS_DATA]))

    for asin, prod_obj in product_map.items():
        ratings_qs = Rating.query.filter_by(product_id=prod_obj.id).all()
        if not ratings_qs:
            continue

        # Update avg_rating / rating_count
        raw = [r.rating for r in ratings_qs]
        prod_obj.avg_rating = float(np.mean(raw))
        prod_obj.rating_count = len(raw)

        # Product trust details
        p_details = trust_engine.product_trust_score(prod_obj, ratings_qs, mean_price)

        # Seller trust: all products in same category
        same_cat = [pm for a, pm in product_map.items() if pm.category == prod_obj.category and a != asin]
        seller_pairs = []
        for sp in same_cat:
            sp_ratings = Rating.query.filter_by(product_id=sp.id).all()
            if sp_ratings:
                seller_pairs.append((sp, sp_ratings))
        s_trust = trust_engine.seller_trust_score(seller_pairs, mean_price)

        # User trust: average across all reviewers
        user_trusts = []
        for r in ratings_qs:
            u_ratings = Rating.query.filter_by(user_id=r.user_id).all()
            user_trusts.append(trust_engine.user_trust_score(u_ratings))
        u_trust = float(np.mean(user_trusts)) if user_trusts else 0.5

        final = 0.55 * p_details['product_trust'] + 0.35 * u_trust + 0.10 * s_trust

        prod_obj.product_trust    = round(p_details['product_trust'], 3)
        prod_obj.seller_trust     = round(s_trust, 3)
        prod_obj.final_trust_score = round(final, 3)
        prod_obj.avg_rating_norm  = round(p_details['avg_rating_norm'], 3)
        prod_obj.verified_ratio   = round(p_details['verified_ratio'], 3)
        prod_obj.review_confidence = round(p_details['review_confidence'], 3)
        prod_obj.text_quality     = round(p_details['text_quality'], 3)
        prod_obj.price_factor     = round(p_details['price_factor'], 3)
        prod_obj.title_similarity = round(p_details['title_similarity'], 3)

    db_instance.session.commit()
    print(f"[SEED] Done. {len(PRODUCTS_DATA)} products, {len(USERS_DATA)} users, {len(RATINGS_DATA)} ratings.")