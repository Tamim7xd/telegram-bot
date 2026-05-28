def need_xp(level):
    return level * 200


def level_up(level, xp, titles):
    while xp >= need_xp(level):
        xp -= need_xp(level)
        level += 1

    title = titles[min(level - 1, len(titles) - 1)]

    return level, xp, title
