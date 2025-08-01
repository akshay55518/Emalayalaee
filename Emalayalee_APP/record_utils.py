import os
from datetime import datetime


# CDN Base URL from environment (default: empty)
# cdn_base = os.getenv("CDN", "").rstrip("/")

# Static Bunny CDN URLs
base_featured_url = "https://ccdn.emalayalee.com/featured-image/"
base_image_url = "https://ccdn.emalayalee.com/images/"
base_pdf_url = "https://ccdn.emalayalee.com/pdf/"
base_charaman_home_url = "https://ccdn.emalayalee.com/charamam/home-image/"
base_charaman_images_url = "https://ccdn.emalayalee.com/charamam/charamam-images/"
cdn_base = "https://emalayalee.b-cdn.net"

def add_full_urls(record, table_name="news"):
    """Enhance a record with full URLs for images, PDF, etc. Supports newsmalayalam & charamam."""
    if not record or not isinstance(record, dict):
        return {}  # Prevents errors on None
    
    cdn = (record.get("cdn") or "").lower()
    id_ = record.get("id", "")

    # Handle language
    lang = record.get("language") or ""
    record["language"] = [l for l in lang.split("@,@")] if "@,@" in lang else []

    # Handle date formatting
    if "date" in record and isinstance(record["date"], datetime):
        record["date"] = record["date"].strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'

    # Handle paid flag
    if "paid" in record:
        record["paid"] = record["paid"] != 0
    
    if "paid" in record:
        record["need_subscription"] = bool(record["paid"])

    cdn_type = (record.get("cdn") or "").lower()
    id_ = record.get("id", "")

    # NEWS TABLE (newsmalayalam)
    if table_name == "newsmalayalam":
        if cdn_type == "bunny":
            record["images2"] = (
                f"{base_featured_url}{record['images2']}" if record.get("images2") else None
            )
            if record.get("images"):
                img_list = [img.strip() for img in record["images"].split("@*@") if img.strip()]
                record["images"] = [f"{base_image_url}{img}" for img in img_list]
            else:
                record["images"] = []
            # record["pdf_url"] = f"{base_pdf_url}{record['pdf']}" if record.get("pdf") else None
        else:
            record["images2"] = (
                f"{cdn_base}/photo/{record['images2']}" if record.get("images2") else None
            )
            if record.get("images"):
                img_list = [img.strip() for img in record["images"].split("@*@") if img.strip()]
                record["images"] = [f"{cdn_base}/photo/{img}" for img in img_list]
            else:
                record["images"] = []
            # record["pdf_url"] = f"{cdn_base}/pdf/{record['pdf']}" if record.get("pdf") else None

    # CHARAMAM TABLE
    elif table_name == "charamam":
        if cdn_type == "bunny":
            record["images2"] = (
                f"{base_charaman_home_url}{record['images2']}" if record.get("images2") else None
            )
            if record.get("images"):
                img_list = [img.strip() for img in record["images"].split("@*@") if img.strip()]
                record["images"] = [f"{base_charaman_images_url}{img}" for img in img_list]
            else:
                record["images"] = []
        else:
            record["images2"] = (
                f"{cdn_base}/photocharamam/{record['images2']}" if record.get("images2") else None
            )
            if record.get("images"):
                img_list = [img.strip() for img in record["images"].split("@*@") if img.strip()]
                # Retain ID-based path for non-Bunny CDN (from Section 1)
                record["images"] = [f"{cdn_base}/getNewsImages.php?photo={id_}_{img}" for img in img_list]
            else:
                record["images"] = []

    return record
