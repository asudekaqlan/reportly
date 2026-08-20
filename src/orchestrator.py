"""ITSM turn: classify, suggest KB solution, fill fields, open ticket, or queue report."""

from dataclasses import dataclass, field

from intents import detect_intents, looks_confirm, looks_decline
from reports import looks_report_command, queue_report_job
from rules import force_ticket
from sentiment import analyze_sentiment, looks_positive_resolution
from slots import apply_answer, extract_slots, merge_slots, missing_fields, next_prompt
from solutions import find_solutions, format_solution
from summaries import build_manager_copy, llm_enabled
from taxonomy import classify_request, path_line
from tickets import append_followup, create_ticket, update_status


@dataclass
class TurnResult:
    reply: str
    phase: str
    last_rule_id: str | None
    ticket: dict | None = None
    debug: dict = field(default_factory=dict)
    slots: dict = field(default_factory=dict)
    classification: dict | None = None


def _urgency(sentiment: str, high_risk: bool, impact: str = "") -> str:
    if high_risk or "tüm ofis" in (impact or ""):
        return "high"
    if sentiment == "angry":
        return "high"
    return "medium"


def _primary_ask(history: list[dict], text: str) -> str:
    for message in history:
        if message.get("role") == "user":
            ask = str(message.get("content") or "").strip()
            if ask:
                return ask
    return (text or "").strip()


def _merge_class(previous: dict | None, incoming: dict) -> dict:
    if incoming and not incoming.get("unclear"):
        return incoming
    if previous and not previous.get("unclear"):
        return previous
    return incoming or previous or classify_request("")


def _debug(classification: dict, sentiment: dict, action: str, extra: dict | None = None) -> dict:
    source = classification.get("source") or "none"
    if source == "model":
        confidence = float(classification.get("model_confidence") or 0.0)
    else:
        confidence = min(1.0, (classification.get("score") or 0) / 4)
    payload = {
        "category": classification.get("path_label") or "unclear",
        "confidence": confidence,
        "nlu_source": source,
        "sentiment": sentiment["label"],
        "high_risk": sentiment["high_risk"],
        "talep_turu": classification.get("talep_turu_label") or "—",
        "birim": classification.get("birim_label") or "—",
        "modul": classification.get("modul_label") or "—",
        "surec": classification.get("surec_label") or "—",
        "rule_id": classification.get("surec") or None,
        "action": action,
    }
    if extra:
        payload.update(extra)
    return payload


def _with_llm_reply(result: TurnResult, customer_text: str) -> TurnResult:
    if not llm_enabled():
        return result
    if len((customer_text or "").strip()) < 12:
        return result
    from llm_analyze import rewrite_customer_reply

    rewritten = rewrite_customer_reply(canned_reply=result.reply)
    if rewritten:
        result.reply = rewritten
    return result


def _open_itsm_ticket(
    *,
    classification: dict,
    sentiment: dict,
    text: str,
    history: list[dict],
    slots: dict,
    why: str,
    customer_email: str,
    solution_ids: list[str],
) -> dict:
    ask = _primary_ask(history, text)
    copy = build_manager_copy(
        classification=classification,
        sentiment=sentiment["label"],
        customer_ask=ask,
        why_unresolved=why,
        high_risk=sentiment["high_risk"],
        history=history,
        latest_user=text,
        slots=slots,
        solution_ids=solution_ids,
    )
    return create_ticket(
        urgency=_urgency(sentiment["label"], sentiment["high_risk"], slots.get("impact", "")),
        customer_ask=ask,
        why_unresolved=why,
        summary_bullets=copy["summary_bullets"],
        recommended_next_step=copy["recommended_next_step"],
        handoff_notes=copy["handoff_notes"],
        sentiment=sentiment["label"],
        customer_email=customer_email,
        talep_turu=str(classification.get("talep_turu") or ""),
        talep_turu_label=str(classification.get("talep_turu_label") or ""),
        birim=str(classification.get("birim") or ""),
        birim_label=str(classification.get("birim_label") or ""),
        modul=str(classification.get("modul") or ""),
        modul_label=str(classification.get("modul_label") or ""),
        surec=str(classification.get("surec") or ""),
        surec_label=str(classification.get("surec_label") or ""),
        asset=str(slots.get("asset") or ""),
        location=str(slots.get("location") or ""),
        impact=str(slots.get("impact") or ""),
        solution_ids=solution_ids,
    )


def _ticket_reply(ticket: dict) -> str:
    path = ticket.get("path_label") or "sınıflandırma"
    return (
        f"Talebin kaydedildi: {ticket['id']}.\n"
        f"Sınıf: {path}.\n"
        f"Varlık: {ticket.get('asset') or '—'} · konum: {ticket.get('location') or '—'} · "
        f"etki: {ticket.get('impact') or '—'}.\n"
        f"{ticket.get('birim_label') or 'İlgili birim'} kuyruğuna düştü."
    )


def _suggest_reply(classification: dict, hits: list[dict]) -> str:
    path = path_line(classification)
    blocks = [f"Talebini şöyle sınıflandırdım: {path}."]
    if hits:
        blocks.append("Benzer çözüm kayıtlarından öneri:")
        blocks.extend(format_solution(row) for row in hits)
        blocks.append(
            "Bu adımlar işe yaradıysa yaz. Yetmezse veya kayıt açmamı istersen "
            "“talep aç” demen yeterli; eksik alanları tamamlarım."
        )
    else:
        blocks.append(
            "Bu sınıfta hazır çözüm kaydı bulamadım. Ticket açmamı ister misin?"
        )
    return "\n\n".join(blocks)


def _collect_or_open(
    *,
    text: str,
    history: list[dict],
    classification: dict,
    sentiment: dict,
    slots: dict,
    customer_email: str,
    solution_ids: list[str],
    why: str,
    intro: str = "",
) -> TurnResult:
    merged = merge_slots(slots, extract_slots(text))
    prompt = next_prompt(merged)
    if prompt:
        debug = _debug(classification, sentiment, "collect_fields")
        lead = intro.strip() + "\n\n" if intro.strip() else ""
        return TurnResult(
            reply=f"{lead}{path_line(classification)}.\n{prompt}",
            phase="collect_fields",
            last_rule_id=classification.get("surec") or (solution_ids[0] if solution_ids else None),
            debug=debug,
            slots=merged,
            classification=classification,
        )
    ticket = _open_itsm_ticket(
        classification=classification,
        sentiment=sentiment,
        text=text,
        history=history,
        slots=merged,
        why=why,
        customer_email=customer_email,
        solution_ids=solution_ids,
    )
    debug = _debug(classification, sentiment, "ticket_open", {"ticket_id": ticket["id"]})
    return TurnResult(
        reply=_ticket_reply(ticket),
        phase="ticket_open",
        last_rule_id=classification.get("surec"),
        ticket=ticket,
        debug=debug,
        slots=merged,
        classification=classification,
    )


def handle_turn(
    text: str,
    *,
    history: list[dict],
    phase: str,
    last_rule_id: str | None,
    last_ticket_id: str | None = None,
    customer_email: str = "",
    slots: dict | None = None,
    classification: dict | None = None,
) -> TurnResult:
    text = (text or "").strip()
    owner = (customer_email or "").strip().lower()
    sentiment = analyze_sentiment(text)
    if force_ticket(text):
        sentiment["high_risk"] = True
    intents = detect_intents(text)
    prior = " ".join(
        str(message.get("content") or "")
        for message in history
        if message.get("role") == "user"
    )
    incoming = classify_request(" ".join(part for part in (prior, text) if part))
    classed = _merge_class(classification, incoming)
    current_slots = merge_slots(slots, None)
    solution_ids = [last_rule_id] if last_rule_id and str(last_rule_id).startswith("S-") else []

    if looks_report_command(text):
        job = queue_report_job(
            command=text,
            birim=str(classed.get("birim") or ""),
            requested_by=owner,
        )
        debug = _debug(classed, sentiment, "report_queued", {"job_id": job["id"]})
        return _with_llm_reply(
            TurnResult(
                reply=(
                    f"Rapor komutun kuyruğa alındı: {job['id']}. "
                    "Günlük JOB (`python src\\daily_jobs.py`) çalışınca özet ilgili birime işlenir."
                ),
                phase=phase if phase != "open" else "open",
                last_rule_id=last_rule_id,
                debug=debug,
                slots=current_slots,
                classification=classed,
            ),
            text,
        )

    if phase == "ticket_open" and looks_positive_resolution(text) and not intents["still_unresolved"]:
        if last_ticket_id:
            update_status(last_ticket_id, "resolved")
        debug = _debug(classed, sentiment, "resolved")
        return _with_llm_reply(
            TurnResult(
                reply="Kaydı kapattım. Yeni bir ITSM talebi olursa yazman yeterli.",
                phase="open",
                last_rule_id=None,
                debug=debug,
                slots=merge_slots(None, None),
                classification=None,
            ),
            text,
        )

    if phase == "ticket_open":
        ticket = append_followup(last_ticket_id or "", text)
        debug = _debug(classed, sentiment, "ticket_followup")
        tid = last_ticket_id or (ticket or {}).get("id") or ""
        extra = " İkinci kayıt açmadım; bunu aynı talebe işledim." if intents["open_ticket"] else ""
        return _with_llm_reply(
            TurnResult(
                reply=f"Açık kaydın var ({tid}). Bu ayrıntıyı nota ekledim.{extra}",
                phase="ticket_open",
                last_rule_id=last_rule_id,
                ticket=ticket,
                debug=debug,
                slots=current_slots,
                classification=classed,
            ),
            text,
        )

    if phase == "suggest_solution":
        if looks_positive_resolution(text) and not intents["still_unresolved"] and not intents["open_ticket"]:
            debug = _debug(classed, sentiment, "self_resolved")
            return _with_llm_reply(
                TurnResult(
                    reply="Güzel, kayıt açmadım. Tekrar olursa yaz.",
                    phase="open",
                    last_rule_id=None,
                    debug=debug,
                    slots=merge_slots(None, None),
                    classification=None,
                ),
                text,
            )
        if looks_decline(text) and not intents["open_ticket"]:
            debug = _debug(classed, sentiment, "solution_declined")
            return _with_llm_reply(
                TurnResult(
                    reply="Tamam, ticket açmadım. İstersen başka bir taleple devam edebiliriz.",
                    phase="open",
                    last_rule_id=None,
                    debug=debug,
                    slots=merge_slots(None, None),
                    classification=None,
                ),
                text,
            )
        if intents["open_ticket"] or intents["still_unresolved"] or looks_confirm(text):
            result = _collect_or_open(
                text=text,
                history=history,
                classification=classed,
                sentiment=sentiment,
                slots=current_slots,
                customer_email=owner,
                solution_ids=solution_ids,
                why="Kullanıcı çözüm kaydından sonra ticket istedi veya sorun devam etti.",
            )
            return _with_llm_reply(result, text)
        debug = _debug(classed, sentiment, "suggest_wait")
        return _with_llm_reply(
            TurnResult(
                reply="İşe yaradıysa yaz. Ticket için “talep aç” demen yeterli.",
                phase="suggest_solution",
                last_rule_id=last_rule_id,
                debug=debug,
                slots=current_slots,
                classification=classed,
            ),
            text,
        )

    if phase == "collect_fields":
        missing = missing_fields(current_slots)
        field = missing[0] if missing else "asset"
        current_slots = apply_answer(current_slots, field, text)
        result = _collect_or_open(
            text=text,
            history=history,
            classification=classed,
            sentiment=sentiment,
            slots=current_slots,
            customer_email=owner,
            solution_ids=solution_ids,
            why="Zorunlu alanlar tamamlandı; ticket oluşturuldu.",
        )
        return _with_llm_reply(result, text)

    if phase == "clarify":
        if incoming.get("unclear") and not intents["open_ticket"]:
            debug = _debug(classed, sentiment, "clarify")
            return _with_llm_reply(
                TurnResult(
                    reply=(
                        "Hâlâ net değil. "
                        + str(classed.get("clarify_hint") or "Kısaca cihaz, ağ, yazılım veya erişim de.")
                    ),
                    phase="clarify",
                    last_rule_id=None,
                    debug=debug,
                    slots=merge_slots(current_slots, extract_slots(text)),
                    classification=classed,
                ),
                text,
            )
        classed = _merge_class(classed, incoming)

    # New / clarified request
    current_slots = merge_slots(current_slots, extract_slots(text))
    if classed.get("unclear") and not intents["open_ticket"]:
        debug = _debug(classed, sentiment, "clarify")
        return _with_llm_reply(
            TurnResult(
                reply=(
                    "Talebini anlamak için biraz netleştireyim. "
                    + str(classed.get("clarify_hint") or "")
                ),
                phase="clarify",
                last_rule_id=None,
                debug=debug,
                slots=current_slots,
                classification=classed,
            ),
            text,
        )

    hits = []
    if not sentiment["high_risk"]:
        hits = find_solutions(text, birim=str(classed.get("birim") or ""))
    solution_ids = [str(h.get("id")) for h in hits if h.get("id")]
    want_ticket = intents["open_ticket"] or sentiment["high_risk"]
    if hits and not want_ticket:
        sid = solution_ids[0]
        debug = _debug(classed, sentiment, "suggest_solution", {"solution_id": sid})
        return _with_llm_reply(
            TurnResult(
                reply=_suggest_reply(classed, hits),
                phase="suggest_solution",
                last_rule_id=sid,
                debug=debug,
                slots=current_slots,
                classification=classed,
            ),
            text,
        )

    intro = ""
    if hits:
        intro = _suggest_reply(classed, hits)
    why = (
        "Yüksek risk; self-servis atlandı."
        if sentiment["high_risk"]
        else "Hazır çözüm yok veya kullanıcı doğrudan kayıt istedi."
    )
    result = _collect_or_open(
        text=text,
        history=history,
        classification=classed,
        sentiment=sentiment,
        slots=current_slots,
        customer_email=owner,
        solution_ids=solution_ids,
        why=why,
        intro=intro,
    )
    return _with_llm_reply(result, text)
