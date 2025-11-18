from corrector.text_utils import Correction, apply_token_corrections, detokenize, tokenize


def test_tokenize_and_apply_replacement():
    text = "La baca del coche es roja.\nEl hombre va a ojear el libro."
    toks = tokenize(text)
    # Find positions of target words
    words = [t.text for t in toks]
    idx_baca = words.index("baca")
    idx_ojear = words.index("ojear")

    corrs = [
        Correction(token_id=idx_baca, replacement="vaca", reason="Confusión baca/vaca", original="baca"),
        Correction(token_id=idx_ojear, replacement="hojear", reason="Confusión ojear/hojear", original="ojear"),
    ]
    new_tokens = apply_token_corrections(toks, corrs)
    out = detokenize(new_tokens)
    assert "vaca del coche" in out
    assert "a hojear el libro" in out

