def format_iq_money(amount: int) -> str:
    if amount < 1000:
        return f"{amount} دينار عراقي"
    return f"{amount:,} دينار عراقي"
