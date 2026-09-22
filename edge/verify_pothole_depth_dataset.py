from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"D:\drone\POTHOLE_TRAINING_DATASET")
rows = []

for split in ["train", "val", "test"]:
    folder = ROOT / "depths" / split
    files = sorted(folder.glob("*.npy"))
    print(f"{split}: {len(files)} files")
    for i, p in enumerate(files, 1):
        try:
            d = np.load(p)
            finite = np.isfinite(d)
            positive = finite & (d > 0)
            vals = d[positive]
            rows.append({
                "split": split, "file": p.name,
                "shape": str(d.shape), "dtype": str(d.dtype),
                "min": float(np.nanmin(d)), "max": float(np.nanmax(d)),
                "mean_positive": float(vals.mean()) if vals.size else np.nan,
                "median_positive": float(np.median(vals)) if vals.size else np.nan,
                "p99_positive": float(np.percentile(vals, 99)) if vals.size else np.nan,
                "zero_fraction": float(np.mean(d == 0)),
                "finite_fraction": float(np.mean(finite)),
                "positive_fraction": float(np.mean(positive))
            })
        except Exception as e:
            rows.append({"split": split, "file": p.name, "shape": "ERROR", "dtype": "", "error": str(e)})
        if i % 100 == 0 or i == len(files):
            print(f"  checked {i}/{len(files)}")

df = pd.DataFrame(rows)
out = ROOT / "depth_verification.csv"
df.to_csv(out, index=False)

print("\n" + "="*60)
print("DEPTH DATASET VERIFICATION")
print("="*60)
print("Total:", len(df))
print("\nShapes:\n", df["shape"].value_counts())
print("\nDtypes:\n", df["dtype"].value_counts())
valid = df[df["shape"] != "ERROR"]
print("\nGlobal raw min:", valid["min"].min())
print("Global raw max:", valid["max"].max())
print("\nMax > 3000:", int((valid["max"] > 3000).sum()))
print("Max > 5000:", int((valid["max"] > 5000).sum()))
print("\nZero fraction mean:", valid["zero_fraction"].mean())
print("Zero fraction max:", valid["zero_fraction"].max())
print("\nSaved:", out)
print("\nRun this first. We will use the confirmed scale to generate physical dimension targets.")
