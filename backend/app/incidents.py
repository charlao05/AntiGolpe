from .schema import UserState


def incident_protocol(state: UserState, text: str) -> list[str] | None:
    if state not in {UserState.JA_FUI_VITIMA, UserState.JA_AGI}:
        return None

    lower = text.lower()
    fraud_markers = (
        "golpe",
        "fraude",
        "suspeito",
        "não reconheço",
        "nao reconheco",
        "fui enganado",
        "fui enganada",
        "não fui eu",
        "nao fui eu",
        "cai no golpe",
    )
    likely_fraud = any(marker in lower for marker in fraud_markers)

    steps = [
        "interrompa novas interações com o possível fraudador",
        "preserve comprovantes, mensagens e demais evidências",
    ]

    if "pix" in lower and likely_fraud:
        steps += [
            "contate seu banco imediatamente e solicite o MED quando aplicável",
            "registre ocorrência",
        ]
    elif "cartão" in lower or "cartao" in lower:
        steps += [
            "bloqueie o cartão pelo canal oficial",
            "conteste transações quando aplicável",
        ]
    elif "senha" in lower or "código" in lower or "codigo" in lower:
        steps += [
            "troque a credencial pelo canal oficial e não forneça novos códigos",
        ]
    else:
        steps += [
            "contate a instituição envolvida por canal oficial independente",
        ]
    return steps
