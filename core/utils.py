def format_iq_money(amount: int) -> str:

    # أقل من 1000
    if amount < 1000:
        return f"{amount} دينار عراقي"

    # 1000 أو أكثر
    return f"{amount:,} دينار عراقي"
