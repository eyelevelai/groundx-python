import typing


def check_map(
    fty: str,
    sty: str,
    val: str,
    mp: typing.Dict[str, typing.Dict[str, str]],
    should_warn: bool = True,
) -> typing.Optional[str]:
    if sty not in mp:
        sty = ""
    if sty not in mp:
        return None

    vl = val.lower().strip()

    nmp = mp[sty]
    if vl not in nmp:
        if should_warn:
            print(f"[arcadia-v1] {fty} not found [{sty}] [{vl}]")
        return None

    return nmp[vl]


def check_valid(sty: str, val: str, valid: typing.Dict[str, typing.List[str]]) -> bool:
    vl = val.lower().strip()

    if sty not in valid:
        sty = ""

    return sty in valid and vl in valid[sty]
