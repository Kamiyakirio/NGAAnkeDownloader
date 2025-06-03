import re


class UBBRand:
    """
    These codes are copied from js files from nga forum and re-coded into python by GPT.
    """

    def __init__(self, authorId=None, tId=None, pId=None, seedOffset=0):
        if authorId is not None and tId is not None and pId is not None:
            if tId > 10246184 or pId > 200188932:
                seed = authorId + tId + pId + seedOffset
            else:
                seed = authorId + tId + pId
        else:
            import random

            seed = random.randint(0, 10000)
        self.seed = seed

    def rnd(self):
        self.seed = (self.seed * 9301 + 49297) % 233280
        return self.seed / 233280.0

    def randint(self, low, high):
        return int(self.rnd() * (high - low + 1)) + low


def replace_dice_tags(text, authorId=None, tId=None, pId=None, seedOffset=0):
    rng = UBBRand(authorId, tId, pId, seedOffset)

    def dice_replacer(match):
        expr = match.group(1)  # 例如 '3+d6'
        rr = expr
        total = 0
        expr = "+" + expr  # 保证每个项前都有 +

        def roll_term(m):
            nonlocal total
            sign, num, d, sides = m.groups()
            num = int(num) if num else (1 if d else 0)
            sides = int(sides) if sides else None

            if not d:
                total += num
                return f"+{num}"

            if num > 10 or sides > 100000:
                return "+OUT OF LIMIT"

            rolls = []
            for _ in range(num):
                rand = rng.randint(1, sides)
                rolls.append(rand)
                total += rand
            return "".join([f"+d{sides}({r})" for r in rolls])

        rolled_expr = re.sub(
            r"(\+)(\d{0,10})(?:(d)(\d{1,10}))?", roll_term, expr, flags=re.IGNORECASE
        )

        return f"ROLL : {rr}={rolled_expr[1:]}={total}"

    return re.sub(
        r"\[dice\]([\dd+\s]+?)\[/dice\]", dice_replacer, text, flags=re.IGNORECASE
    )
