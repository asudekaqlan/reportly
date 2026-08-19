"""Self-serve procedures. Category steers; keywords confirm the issue."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    categories: tuple[str, ...]
    keywords: tuple[str, ...]
    reply: str
    usually_resolves: bool = True


RULES: tuple[Rule, ...] = (
    Rule(
        id="payment_not_posted",
        title="Payment not applied",
        categories=(
            "student loan",
            "credit card",
            "mortgage",
            "vehicle loan",
            "payday",
            "personal loan",
        ),
        keywords=(
            "paid on time",
            "payment never",
            "never applied",
            "payment not",
            "still late",
            "marked late",
            "payment was made",
            "i paid",
            "i have paid",
            "posted",
        ),
        reply=(
            "It sounds like a payment was sent but the account still shows late. "
            "Please reply with the payment date, amount, and confirmation/reference number. "
            "Servicers often take 3-5 business days to apply a payment. "
            "If you already have a confirmation and the late status remains after that window, "
            "I will open a specialist record so the payment can be traced and the late mark reviewed.\n\n"
            "If this does not resolve it, say so and I can file a complaint."
        ),
    ),
    Rule(
        id="credit_report_error",
        title="Credit report error",
        categories=("credit reporting", "credit repair", "consumer reports"),
        keywords=(
            "incorrect",
            "not mine",
            "error on",
            "mixed file",
            "wrong information",
            "does not belong",
            "inaccurate",
            "identity theft",
        ),
        reply=(
            "Credit report disputes go to the bureau that published the item and to the company "
            "that furnished it. Note the bureau, the account name, and what is wrong. "
            "File an official dispute and keep the confirmation. "
            "If this is identity theft, say so immediately — that is treated as urgent.\n\n"
            "If the item stays after a dispute, or you want this filed as a complaint, tell me."
        ),
    ),
    Rule(
        id="debt_not_mine",
        title="Debt not mine",
        categories=("debt collection",),
        keywords=(
            "not my debt",
            "never owed",
            "wrong person",
            "do not owe",
            "don't owe",
            "never had an account",
            "not mine",
        ),
        reply=(
            "If this is not your debt, do not promise a payment. "
            "Ask the collector in writing for a debt validation notice: creditor name, amount, "
            "and how they tied it to you. You generally have 30 days after first contact to dispute. "
            "Keep copies of everything.\n\n"
            "If they keep collecting after a written dispute, I can open a complaint for a specialist."
        ),
    ),
    Rule(
        id="harassing_calls",
        title="Harassing collection calls",
        categories=("debt collection", "mortgage"),
        keywords=(
            "harassing",
            "hang up",
            "robocall",
            "called me",
            "calling me",
            "phone call",
            "collection call",
            "at night",
            "repeatedly",
        ),
        reply=(
            "Repeated or odd-hour collection calls should be logged: date, time, number, and what was said. "
            "You can request that contact happen in writing only. "
            "Calls before 8am or after 9pm local time, or continuing after a written cease request, "
            "are stronger grounds for a specialist complaint.\n\n"
            "Say if the calls are still happening, or ask me to file a complaint."
        ),
    ),
    Rule(
        id="unauthorized_charge",
        title="Unauthorized charge or fraud",
        categories=(
            "credit card",
            "checking",
            "bank account",
            "money transfer",
            "money service",
            "prepaid",
        ),
        keywords=(
            "unauthorized",
            "fraud",
            "didn't make",
            "did not make",
            "didn't authorize",
            "did not authorize",
            "stolen card",
            "not my purchase",
            "i didn't buy",
        ),
        reply=(
            "Treat this as possible fraud. Freeze or replace the card/account if you still have access, "
            "and dispute the charge with the issuer as unauthorized. "
            "Write down the date, amount, merchant, and when you noticed it. "
            "I am also opening a high-priority record so a specialist can follow the dispute.\n\n"
            "Say so if this does not help and I can file a complaint."
        ),
        usually_resolves=False,
    ),
    Rule(
        id="overdraft_fee",
        title="Overdraft or unexpected account fee",
        categories=("checking", "savings", "prepaid", "bank account", "bank account or service"),
        keywords=(
            "overdraft",
            "overdraft fee",
            "nsf",
            "account closed",
            "unexpected fee",
            "monthly fee",
            "charged a fee",
            "deducted a fee",
            "deducted an unexpected",
            "fee from my account",
            "fee from my checking",
        ),
        reply=(
            "For an unexpected fee, ask the bank for the fee type, posting date, and the transaction "
            "that triggered it. First-time overdrafts are often reversed if you request a courtesy refund. "
            "If the account was closed, ask for the closing reason and any remaining balance in writing.\n\n"
            "If they refuse or the account stays closed, I can file this for a specialist."
        ),
    ),
    Rule(
        id="transfer_not_arrived",
        title="Transfer not arrived",
        categories=("money transfer", "money service", "virtual currency"),
        keywords=(
            "didn't arrive",
            "did not arrive",
            "still pending",
            "not received",
            "hasn't arrived",
            "has not arrived",
            "transfer missing",
            "never received",
        ),
        reply=(
            "Please send the transfer reference/confirmation number, send date, amount, and whether "
            "the recipient details were confirmed. Many transfers clear in 24-48 hours. "
            "If that window has already passed, I will open a record so the payment can be traced.\n\n"
            "Tell me if it still has not arrived, or say so and I can file a complaint."
        ),
    ),
    Rule(
        id="vehicle_dealer_vs_lender",
        title="Vehicle dealer vs lender",
        categories=("vehicle loan", "vehicle lease"),
        keywords=(
            "dealer",
            "dealership",
            "transmission",
            "lemon",
            "repair",
            "warranty",
            "condition of the car",
            "the car is",
        ),
        reply=(
            "Vehicle condition and repairs are usually the dealer’s responsibility; the loan itself "
            "is the lender’s. Keep paying the loan unless you have written legal advice not to — "
            "stopping payment can add a credit injury on top of the car problem. "
            "This kind of case almost always needs a specialist, so I am opening a record with that split noted.\n\n"
            "Say so if you want this filed as a complaint."
        ),
        usually_resolves=False,
    ),
)


def _category_match(category: str, rule: Rule) -> bool:
    cat = (category or "").lower()
    if not cat or cat == "unknown":
        return False
    return any(token in cat for token in rule.categories)


def _keyword_hits(text: str, rule: Rule) -> list[str]:
    lowered = (text or "").lower()
    return [kw for kw in rule.keywords if kw in lowered]


def match_rule(text: str, category: str, min_score: int = 2) -> dict | None:
    """Return the best matching rule, or None."""
    best = None
    best_score = 0
    best_hits: list[str] = []

    for rule in RULES:
        hits = _keyword_hits(text, rule)
        if not hits:
            continue
        score = len(hits)
        matched_category = _category_match(category, rule)
        if matched_category:
            score += 2
        if score > best_score:
            best_score = score
            best = rule
            best_hits = hits

    if best is None or best_score < min_score:
        return None

    return {
        "rule": best,
        "score": best_score,
        "keyword_hits": best_hits,
        "category_matched": _category_match(category, best),
    }
