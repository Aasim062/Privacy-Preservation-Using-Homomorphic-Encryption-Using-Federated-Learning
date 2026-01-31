import os
import argparse
import numpy as np
import pandas as pd

try:
    from pyfhel import Pyfhel, PyCtxt
except Exception as e:
    raise SystemExit(
        "Pyfhel is required. Install with:\n  pip install pyfhel\n\n"
        f"Import error details:\n{e}"
    )

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_H1 = os.path.normpath(os.path.join(HERE, "..", "LocalModels", "Hospital1", "hospital1_weights.csv"))
DEFAULT_H2 = os.path.normpath(os.path.join(HERE, "..", "LocalModels", "Hospital2", "hospital2_weights.csv"))

KEY_DIR    = os.path.join(HERE, "keys")
CT_DIR     = os.path.join(HERE, "ciphertexts")
GLOBAL_DIR = os.path.join(HERE, "global")

def _find_coef_column(df: pd.DataFrame) -> str:
    for cand in ("Coefficient", "coefficient", "coef", "Coef"):
        if cand in df.columns:
            return cand
    raise ValueError(f"Coefficient column not found. Available columns: {list(df.columns)}")

def weights_csv_to_vector(csv_path: str) -> np.ndarray:
    """
    Build vector [coef_0, ..., coef_(n-1), intercept] from a weights CSV.
    Accepts either an explicit 'Intercept' row in 'Feature', or treats last row as intercept.
    """
    df = pd.read_csv(csv_path)
    coef_col = _find_coef_column(df)

    if "Feature" in df.columns:
        mask_int = df["Feature"].astype(str).str.lower().eq("intercept")
        if mask_int.any():
            intercept = float(df.loc[mask_int, coef_col].values[0])
            coefs = df.loc[~mask_int, coef_col].astype(float).values
        else:
            intercept = float(df[coef_col].values[-1])
            coefs = df[coef_col].values[:-1].astype(float)
    else:
        intercept = float(df[coef_col].values[-1])
        coefs = df[coef_col].values[:-1].astype(float)

    vec = np.concatenate([coefs, [intercept]]).astype(float)
    return vec

def weights_csv_feature_names(csv_path: str) -> list:
    """
    Return feature names in the same order as coefficients in weights_csv_to_vector (excluding intercept).
    If no 'Feature' column, synthesize names like f0,f1,... and 'Intercept'.
    """
    df = pd.read_csv(csv_path)
    coef_col = _find_coef_column(df)

    if "Feature" in df.columns:
        mask_int = df["Feature"].astype(str).str.lower().eq("intercept")
        if mask_int.any():
            features = df.loc[~mask_int, "Feature"].astype(str).tolist()
        else:
            features = df["Feature"].astype(str).tolist()[:-1]
    else:
        n = len(df[coef_col].values) - 1
        features = [f"f{i}" for i in range(n)]

    return features + ["Intercept"]

def ensure_dirs():
    os.makedirs(KEY_DIR, exist_ok=True)
    os.makedirs(CT_DIR, exist_ok=True)
    os.makedirs(GLOBAL_DIR, exist_ok=True)

def keygen_if_missing(poly_degree=2**15, scale_bits=40, sec_bits=128) -> Pyfhel:
    """
    Create or load CKKS context & keys. RNS optimization is used internally by Pyfhel for CKKS.
    """
    ctx_path = os.path.join(KEY_DIR, "ckks_context.bin")
    pub_path = os.path.join(KEY_DIR, "ckks_public.key")
    sec_path = os.path.join(KEY_DIR, "ckks_secret.key")

    HE = Pyfhel()
    if os.path.exists(ctx_path) and os.path.exists(pub_path) and os.path.exists(sec_path):
        HE.contextLoad(ctx_path)
        HE.restorepublicKey(pub_path)
        HE.restoresecretKey(sec_path)
        return HE

    HE.contextGen(
        scheme="CKKS",
        n=poly_degree,         
        scale=2**scale_bits,   
        sec=sec_bits
    )
    HE.keyGen()
    HE.contextSave(ctx_path)
    HE.savepublicKey(pub_path)
    HE.savesecretKey(sec_path)
    print(f"✅ Keys generated in {KEY_DIR}")
    return HE

def load_for_server() -> Pyfhel:
    """
    Load context + public key (no secret key). Use on aggregator/server side.
    """
    HE = Pyfhel()
    HE.contextLoad(os.path.join(KEY_DIR, "ckks_context.bin"))
    HE.restorepublicKey(os.path.join(KEY_DIR, "ckks_public.key"))
    return HE

def load_for_decrypt() -> Pyfhel:
    """
    Load context + public + secret key (client/hospital side).
    """
    HE = Pyfhel()
    HE.contextLoad(os.path.join(KEY_DIR, "ckks_context.bin"))
    HE.restorepublicKey(os.path.join(KEY_DIR, "ckks_public.key"))
    HE.restoresecretKey(os.path.join(KEY_DIR, "ckks_secret.key"))
    return HE

def encrypt_weights_csv(weights_csv: str, out_name: str, verify: bool = False) -> str:
    HE = keygen_if_missing()
    vec = weights_csv_to_vector(weights_csv)

    ptxt = HE.encodeVec(vec)      
    ctxt = HE.encryptPtxt(ptxt)   

    out_path = os.path.join(CT_DIR, out_name)
    ctxt.save(out_path)
    print(f"🔐 Encrypted {os.path.basename(weights_csv)} → {out_path} (len={len(vec)})")

    if verify:
        try:
            dec = HE.decryptFrac(ctxt)
            k = min(5, len(vec))
            print("   Verify (first few entries):")
            for i in range(k):
                print(f"     orig={vec[i]: .6f}   dec={dec[i]: .6f}")
        except Exception as e:
            print(f"   (Verification skipped: {e})")

    return out_path

def aggregate_ciphertexts(ct_paths, average=True) -> str:
    HE = load_for_server()
    agg = PyCtxt(pyfhel=HE, serialized=True, fileName=ct_paths[0])
    for p in ct_paths[1:]:
        c = PyCtxt(pyfhel=HE, serialized=True, fileName=p)
        agg += c
    if average:
        agg *= (1.0 / len(ct_paths))
    out_path = os.path.join(GLOBAL_DIR, "global_avg.ct" if average else "global_sum.ct")
    agg.save(out_path)
    print(f"🧮 Saved homomorphic {'average' if average else 'sum'} → {out_path}")
    return out_path

def decrypt_ciphertext_to_csv(ct_path: str, canonical_features: list) -> tuple[str, str]:
    HE = load_for_decrypt()
    ctxt = PyCtxt(pyfhel=HE, serialized=True, fileName=ct_path)
    vec = HE.decryptFrac(ctxt)

    out_csv_idx = os.path.join(GLOBAL_DIR, "global_weights.csv")
    pd.DataFrame({"Index": np.arange(len(vec)), "Value": vec}).to_csv(out_csv_idx, index=False)

    if len(canonical_features) != len(vec):
        raise ValueError(
            f"Length mismatch: features({len(canonical_features)}) vs values({len(vec)}). "
            "Ensure both hospitals used identical feature order + intercept."
        )
    out_csv_named = os.path.join(GLOBAL_DIR, "global_weights_named.csv")
    pd.DataFrame({"Feature": canonical_features, "Coefficient": vec}).to_csv(out_csv_named, index=False)

    print(f"🔓 Decrypted {ct_path} →")
    print(f"   - {out_csv_idx} (Index/Value)")
    print(f"   - {out_csv_named} (Feature/Coefficient)")
    return out_csv_idx, out_csv_named

def main():
    ensure_dirs()
    ap = argparse.ArgumentParser(description="CKKS-RNS Homomorphic Encryption for Federated LR Weights")
    ap.add_argument("--h1", default=DEFAULT_H1, help="Hospital-1 weights CSV path")
    ap.add_argument("--h2", default=DEFAULT_H2, help="Hospital-2 weights CSV path")
    ap.add_argument("--sum", dest="do_sum", action="store_true", help="Use sum (default is average)")
    ap.add_argument("--verify", action="store_true", help="Print small decrypt check after encrypt")
    args = ap.parse_args()

    if not os.path.exists(args.h1):
        raise FileNotFoundError(f"Hospital-1 weights not found: {args.h1}")
    if not os.path.exists(args.h2):
        raise FileNotFoundError(f"Hospital-2 weights not found: {args.h2}")

    ct1 = encrypt_weights_csv(args.h1, "hospital1.ct", verify=args.verify)
    ct2 = encrypt_weights_csv(args.h2, "hospital2.ct", verify=args.verify)

    len1 = len(weights_csv_to_vector(args.h1))
    len2 = len(weights_csv_to_vector(args.h2))
    if len1 != len2:
        raise ValueError(f"Weight vector length mismatch: H1={len1}, H2={len2}. Align features & intercept.")

    global_ct = aggregate_ciphertexts([ct1, ct2], average=(not args.do_sum))

    canonical_feats = weights_csv_feature_names(args.h1)
    decrypt_ciphertext_to_csv(global_ct, canonical_feats)

    print("\n✅ Done. Keys in 'keys/'. Ciphertexts in 'ciphertexts/'. Global outputs in 'global/'.")
    print("   Keep 'ckks_secret.key' private. Share only context + public key + ciphertexts with server.")

if __name__ == "__main__":
    main()
