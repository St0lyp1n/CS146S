from client import mcp, make_user_card_request

BILIBILI_API_BASE = "https://api.bilibili.com/x/"


@mcp.tool()
async def get_user_card(mid: int) -> str:
    """获取哔哩哔哩用户名片信息。

    Args:
        mid: 用户 UID
    """
    url = f"{BILIBILI_API_BASE}web-interface/card"
    data = await make_user_card_request(url, mid=mid, photo=True)
    if not data:
        return "Unable to fetch user card information."
    card = data.get("card")
    if not card:
        return "User card information not found."

    vip = card.get("vip") or {}
    vip_status = "是" if vip.get("vipStatus") or vip.get("status") else "否"

    return (
        f"UID: {card.get('mid', mid)}\n"
        f"名称 Name: {card.get('name', 'Unknown')}\n"
        f"等级 Level: {card.get('level_info', {}).get('current_level', '?')}\n"
        f"性别 Gender: {card.get('sex', 'Unknown')}\n"
        f"用户状态 User_Status: {card.get('spacesta', '?')}\n"
        f"头像链接 Avatar_URL: {card.get('face', '')}\n"
        f"粉丝数 Followers: {data.get('follower', card.get('fans', '?'))}\n"
        f"关注数 Followings: {card.get('attention', '?')}\n"
        f"稿件数 Archives: {data.get('archive_count', '?')}\n"
        f"获赞数 Likes: {data.get('like_num', '?')}\n"
        f"签名 Signature: {card.get('sign', '')}\n"
        f"大会员 VIP: {vip_status}\n"
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
