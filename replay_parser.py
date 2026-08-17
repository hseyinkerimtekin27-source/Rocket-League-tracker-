"""
replay_parser.py
-----------------
Rocket League .replay dosyalarının HEADER kısmını (sıkıştırılmamış, belgelenmiş
binary format) saf Python ile okuyup maç istatistiklerini çıkarır.

Not: Replay dosyasının "network stream" kısmı (top pozisyonu, boost alma anları vb.)
sıkıştırılmış ve çok daha karmaşıktır; onu parse etmiyoruz çünkü ihtiyacımız yok.
Header kısmı zaten skor, gol/asist/kurtarış, oyuncu isimleri, harita, playlist gibi
maç sonu istatistiklerinin tamamını düz metin/property olarak içeriyor.

Format kaynak: Psyonix'in resmi olmayan ama yıllardır topluluk tarafından
tersine mühendislikle çözülmüş ve doğrulanmış replay header yapısı
(bkz. rattletrap, boxcars, RocketLeagueReplayParser projeleri).
"""

import struct
import io


class ReplayParseError(Exception):
    pass


def _read_u32(f):
    return struct.unpack("<I", f.read(4))[0]


def _read_i32(f):
    return struct.unpack("<i", f.read(4))[0]


def _read_u64(f):
    return struct.unpack("<Q", f.read(8))[0]


def _read_float(f):
    return struct.unpack("<f", f.read(4))[0]


def _read_string(f):
    """RL strings: int32 length (negative => UTF-16LE), null terminated."""
    length = _read_i32(f)
    if length == 0:
        return ""
    if length < 0:
        # UTF-16, length is negative char count (including null terminator)
        n = -length
        raw = f.read(n * 2)
        return raw.decode("utf-16-le", errors="replace").rstrip("\x00")
    else:
        raw = f.read(length)
        return raw.decode("ascii", errors="replace").rstrip("\x00")


def _read_property_value(f, prop_type):
    if prop_type == "BoolProperty":
        return struct.unpack("<B", f.read(1))[0] != 0
    if prop_type in ("ByteProperty",):
        k = _read_string(f)
        v = _read_string(f)
        return {"key": k, "value": v}
    if prop_type == "IntProperty":
        return _read_i32(f)
    if prop_type == "FloatProperty":
        return _read_float(f)
    if prop_type == "QWordProperty":
        return _read_u64(f)
    if prop_type == "StrProperty":
        return _read_string(f)
    if prop_type == "NameProperty":
        return _read_string(f)
    if prop_type == "ArrayProperty":
        count = _read_i32(f)
        arr = []
        for _ in range(count):
            arr.append(_read_property_dict(f))
        return arr
    raise ReplayParseError(f"Bilinmeyen property tipi: {prop_type}")


def _read_property_dict(f):
    """Reads properties until 'None' key is hit. Returns a dict."""
    result = {}
    while True:
        key = _read_string(f)
        if key == "None" or key == "":
            break
        type_name = _read_string(f)
        # 8 bytes: value size (u64) - not needed since we parse structurally,
        # but some property types omit it depending on version; length-prefixed
        # values in RL replays include this 8-byte size field before the value.
        _size = _read_u64(f)
        value = _read_property_value(f, type_name)
        result[key] = value
    return result


def parse_replay_header(filepath):
    """
    Verilen .replay dosyasının header'ını parse eder ve maç istatistiklerini
    içeren bir dict döndürür.
    """
    with open(filepath, "rb") as f:
        header_size = _read_u32(f)
        _header_crc = _read_u32(f)

        header_bytes = f.read(header_size)

    hf = io.BytesIO(header_bytes)

    engine_version = _read_u32(hf)
    licensee_version = _read_u32(hf)

    net_version = 0
    # Net version field exists from licensee version >= 18 onward (documented behavior)
    if licensee_version >= 18:
        net_version = _read_u32(hf)

    replay_class = _read_string(hf)

    props = _read_property_dict(hf)

    return _extract_stats(props)


def _extract_stats(props):
    """Ham property dict'ini bizim işimize yarayan sade bir yapıya indirger."""
    team0 = props.get("Team0Score", 0)
    team1 = props.get("Team1Score", 0)
    match_type = props.get("MatchType", "Unknown")
    map_name = props.get("MapName", "Unknown")
    date = props.get("Date", "")
    team_size = props.get("TeamSize", None)
    playlist = props.get("MatchType", "Unknown")

    player_stats_raw = props.get("PlayerStats", [])
    players = []
    for p in player_stats_raw:
        players.append({
            "name": p.get("Name", "?"),
            "team": p.get("Team", 0),
            "score": p.get("Score", 0),
            "goals": p.get("Goals", 0),
            "assists": p.get("Assists", 0),
            "saves": p.get("Saves", 0),
            "shots": p.get("Shots", 0),
            "is_bot": bool(p.get("bBot", False)),
            "platform": (p.get("Platform") or {}).get("value", "Unknown"),
        })

    mvp_name = None
    if players:
        mvp_name = max(players, key=lambda pl: pl["score"])["name"]

    return {
        "team0_score": team0,
        "team1_score": team1,
        "match_type": match_type,
        "map_name": map_name,
        "date": date,
        "team_size": team_size,
        "playlist": playlist,
        "players": players,
        "mvp_name_guess": mvp_name,
    }


def find_user_result(stats, player_name):
    """
    Verilen oyuncu adına göre bu maçta kazanıp kaybetmediğini ve
    kişisel istatistiklerini çıkarır.
    """
    me = None
    for p in stats["players"]:
        if p["name"].strip().lower() == player_name.strip().lower():
            me = p
            break
    if me is None:
        return None

    my_team_score = stats["team0_score"] if me["team"] == 0 else stats["team1_score"]
    opp_team_score = stats["team1_score"] if me["team"] == 0 else stats["team0_score"]
    result = "win" if my_team_score > opp_team_score else "loss"

    return {
        "result": result,
        "goals": me["goals"],
        "assists": me["assists"],
        "saves": me["saves"],
        "shots": me["shots"],
        "score": me["score"],
        "mvp": stats["mvp_name_guess"] == me["name"],
        "map": stats["map_name"],
        "playlist": stats["playlist"],
        "date": stats["date"],
        "team_score": my_team_score,
        "opp_team_score": opp_team_score,
    }
