
# pip install phonecodes
import re
import numpy as np
from copy import deepcopy

from phonecodes import phonecodes

from spanpygui import Audio, Text

def convert_alphabet(text:Text, orig='arpabet', targ='ipa') -> Text:
    text = deepcopy(text)
    for t in text:
        t.label = phonecodes.convert(t.label, orig, targ)
    return text

PHONEME_CLASSES = {
    # Broad categories
    "vowels": set("i y ɨ ʉ ɪ ʏ e ø ə ɘ ɵ ɛ œ æ a ɶ ɜ ɝ ɞ ʌ ɔ ɒ ɑ ʊ u o ɯ ɚ".split()),
    "consonants": set("p b t d k g m n ŋ f v θ ð s z ʃ ʒ ʧ ʤ h ʔ l ɹ ɻ r ɾ ʎ ʟ w j".split()),
    "diphthongs": set("aɪ aʊ ɔɪ eɪ oʊ".split()),
    "semivowels": set("w j ɥ ʍ".split()),
    "rhotic_vowels": set("ɝ ɚ".split()),

    # Vowels by placement
    "front_vowels": set("ɪ i y e ø ɛ œ æ a".split()),
    "central_vowels": set("ɨ ʉ ə ɘ ɵ ɜ ɝ ɞ ɐ".split()),
    "back_vowels": set("u ɯ o ɤ ɔ ʊ ʌ ɑ ɒ".split()),
    
    # Vowels by height
    "high_vowels": set("i y ɨ ʉ ɪ ʏ ʊ u ɯ".split()),
    "mid_vowels": set("e ø ə ɘ ɵ ɛ œ ɜ ɝ ɞ ʌ o ɔ".split()),
    "low_vowels": set("æ a ɶ ɒ ɑ".split()),

    # Consonants by manner of articulation
    "nasals": set("m n ŋ".split()),
    "fricatives_affricates": set("f v θ ð s z ʃ ʒ ʧ ʤ h".split()),
    "stops": set("p b t d k g ʔ".split()),
    "laterals_taps_others": set("l ɹ ɻ r ɾ ʎ ʟ".split()),

    # Consonants by place of articulation
    "labial": set("p b m f v w ʍ".split()),  # Includes bilabial, labiodental
    "coronal": set("t d n θ ð s z ʃ ʒ ʧ ʤ l ɹ r ɾ".split()),  # Includes dental, alveolar, postalveolar
    "dorsal_laryngeal": set("k g ŋ ʔ h j ɥ".split()),  # Includes velar, uvular, glottal
}

def PER(pred:Text|list[Text], ref:Text|list[Text], weight={}, pclasses=PHONEME_CLASSES, sanitize_markers=True, count_insertion=True, return_ops=False):
    if not isinstance(pred, list):
        return _PER(pred, ref, weight=weight, pclasses=pclasses, sanitize_markers=sanitize_markers, count_insertion=count_insertion, return_ops=return_ops)
    assert len(pred) == len(ref)
    pers, operations = [], []
    for p, r in pred, ref:
        per, ops, _ = _PER(p, r, weight=weight, pclasses=pclasses, sanitize_markers=sanitize_markers, count_insertion=count_insertion, return_ops=True)
        pers.append(per)
        ops.append(ops)
    total = {}
    sum = 0
    for cls in pers[0]:
        total[cls] = 0
        for per in pers:
            if cls == 'length':
                sum += per[cls]
                continue
            total[cls] += per['length'] * per[cls]
    for cls in total: total[cls] /= sum
    return ((total, operations) if return_ops else total)

def _PER(pred:Text, ref:Text, weight={}, pclasses=PHONEME_CLASSES, sanitize_markers=True, count_insertion=True, return_ops=False):
    def split_tokens(txt:Text):
        out = []
        for t in txt:
            for p in t.label:
                if sanitize_markers and p in r"[ˈːˌˑ‿ʰ̃˥˩̪̥̬̟̠ʷʲˠˤ˞̤̰]": continue
                elif p: out.append(p)
        return out
    ref_list = split_tokens(ref)
    pred_list = split_tokens(pred)
    
    m, n = len(ref_list), len(pred_list)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    ops = [[None] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m+1):
        dp[i][0] = dp[i - 1][0] + weight.get((' ', ref_list[i - 1]), 1)  # Deletion cost
        ops[i][0] = 'delete'
    for j in range(1, n+1):
        dp[0][j] = dp[0][j - 1] + weight.get((pred_list[j - 1], ' '), 1)  # Insertion cost
        ops[0][j] = 'insert'
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            sub_cost = weight.get((pred_list[j - 1], ref_list[i - 1]), 1)  # Substitution cost
            del_cost = weight.get((' ', ref_list[i - 1]), 1)             # Deletion cost
            ins_cost = weight.get((pred_list[j - 1], ' '), 1)             # Insertion cost

            sub_cost = dp[i - 1][j - 1] + (0 if ref_list[i - 1] == pred_list[j - 1] else sub_cost)
            del_cost += dp[i-1][j]
            ins_cost += dp[i][j-1]
            
            if sub_cost < del_cost and sub_cost < ins_cost:
                dp[i][j] = sub_cost
                ops[i][j] = 'match' if ref_list[i - 1] == pred_list[j - 1] else 'replace'
            elif del_cost < sub_cost and del_cost < ins_cost:
                dp[i][j] = del_cost
                ops[i][j] = 'delete'
            else:
                dp[i][j] = ins_cost
                ops[i][j] = 'insert'
    i, j = m, n
    operations = []
    while i > 0 or j > 0:
        match ops[i][j]:
            case 'match':
                operations.append(("match", ref_list[i - 1], pred_list[j - 1]))
                i, j = i - 1, j - 1
            case 'replace':
                operations.append(("replace", ref_list[i - 1], pred_list[j - 1]))
                i, j = i - 1, j - 1
            case 'delete':
                operations.append(("delete", ref_list[i - 1], ' '))
                i -= 1
            case 'insert':
                operations.append(("insert", ' ', pred_list[j - 1]))
                j -= 1
            case _:
                print('error', ops[i][j])
    operations.reverse()

    pers = {'total': dp[m][n] / len(ref_list)}
    if pclasses:
        for cls in pclasses: pers[cls] = 0
        get_phoneme_classes = lambda x: [k for k, v in pclasses.items() if x in v]
        for op, i, j in operations:
            if op in ["replace", "delete"]:
                for cls in get_phoneme_classes(i): pers[cls] += 1
            elif count_insertion:
                for cls in get_phoneme_classes(j): pers[cls] += 1
        totals = {cls: 0 for cls in pclasses}
        for phoneme in ref_list:
            ref_classes = get_phoneme_classes(phoneme)
            for cls in ref_classes:
                totals[cls] += 1
        for cls in pclasses:
            if cls == 'total': continue
            if totals[cls] > 0:
                pers[cls] /= totals[cls]
            else:
                pers[cls] = 0
    return ((pers, operations, ref_list) if return_ops else pers)

def PMILD(preds:list[Text], refs:list[Text], ret_per=False):
    pmi = {}
    min_per = np.inf
    while True:
        joint = {}
        marg = {}
        total_joint = 0
        total_marg = 0

        def count(p, r):
            nonlocal total_joint, total_marg
            key = tuple(sorted((p,r)))
            if p not in marg: marg[p] = 0
            if r not in marg: marg[r] = 0
            if tuple(key) not in joint: joint[key] = 0
            marg[p] += 1
            marg[r] += 1
            joint[key] += 1
            total_marg += 2
            total_joint += 1

        total = 0
        pmild = 0
        for pred, ref in zip(preds, refs):
            per, ops, ref_list = PER(pred, ref, weight=pmi, return_ops=True)
            total += len(ref_list)
            pmild += per['total'] * len(ref_list)
            for op in ops:
                match op[0]:
                    case 'replace':
                        count(op[2], op[1])
                    case 'delete':
                        count(' ', op[1])
                    case 'insert':
                        count(op[2], ' ')
                    case _:
                        pass
        pmild /= total
        if pmild >= min_per:
            break
        if ret_per: return pmild
        min_per = pmild

        min_pmi = np.inf
        max_pmi = -np.inf
        for p, r in joint:
            pmi[(p,r)] = -np.log2((joint[(p,r)]/total_joint) / (marg[p]*marg[r]/(total_marg**2)))
            min_pmi = min(min_pmi, pmi[(p,r)])
            max_pmi = max(max_pmi, pmi[(p,r)])
        for p, r in joint:
            pmi[(p,r)] = (pmi[(p,r)] - min_pmi) / (max_pmi - min_pmi)
        #print(pmild, pmi)

    return min_per