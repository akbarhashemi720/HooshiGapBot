# HooshiGap Utils
# Helper functions - platform independent

import math
import pygeohash as geohash

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

def get_user_link(user):
    username = user.get("username")
    tid = user.get("telegram_id")
    if username:
        return f'<a href="https://t.me/{username}">پروفایل تلگرام</a>'
    else:
        return f'<a href="tg://user?id={tid}">پروفایل تلگرام</a>'

__all__ = [
    "distance_km",
    "encode_location",
    "decode_location",
    "get_nearby_geohashes",
    "get_distance_bucket",
    "get_user_link"
]
