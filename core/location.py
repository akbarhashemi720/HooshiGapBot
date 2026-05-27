# HooshiGap Core - Location System
# Platform-independent location and geohash management

import math
import httpx
import pygeohash as geohash

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"

async def db_patch(table, params, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.patch(f"{SUPABASE_URL}/rest/v1/{table}?{params}", json=data, headers=headers)

def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def encode_location(lat, lon, precision=4):
    try:
        return geohash.encode(lat, lon, precision)
    except:
        return ""

def decode_location(geohash_str):
    try:
        return geohash.decode(geohash_str)
    except:
        return None, None

def get_nearby_geohashes(lat, lon, precision=4):
    try:
        center = geohash.encode(lat, lon, precision)
        neighbors = geohash.neighbors(center)
        return [center] + neighbors
    except:
        return []

def get_distance_bucket(dist_km):
    if dist_km < 1:
        return "کمتر از 1 کیلومتر"
    elif dist_km < 5:
        return "در محدوده 5 کیلومتر"
    elif dist_km < 10:
        return "در محدوده 10 کیلومتر"
    elif dist_km < 30:
        return "در محدوده 30 کیلومتر"
    else:
        return "در محدوده 60 کیلومتر"

async def update_user_location(telegram_id, lat, lon):
    gh = encode_location(lat, lon, precision=4)
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "latitude": round(lat, 2),
        "longitude": round(lon, 2),
        "geohash": gh if gh else ""
    })

def filter_nearby_users(users, my_lat, my_lon, max_km):
    nearby = []
    for user in users:
        if user.get("latitude") and user.get("longitude"):
            dist = distance_km(my_lat, my_lon, user["latitude"], user["longitude"])
            if dist <= max_km:
                user["distance"] = round(dist, 1)
                user["distance_bucket"] = get_distance_bucket(dist)
                nearby.append(user)
    nearby.sort(key=lambda x: x["distance"])
    return nearby

__all__ = [
    "distance_km",
    "encode_location",
    "decode_location",
    "get_nearby_geohashes",
    "get_distance_bucket",
    "update_user_location",
    "filter_nearby_users"
]
