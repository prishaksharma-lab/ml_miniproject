import json, joblib, warnings, numpy as np, pandas as pd, matplotlib.pyplot as plt
warnings.filterwarnings("ignore")
from pathlib import Path
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, GridSearchCV
from sklearn.ensemble import IsolationForest, RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (f1_score, precision_recall_fscore_support, roc_auc_score,
                             average_precision_score, ConfusionMatrixDisplay)

def _resolve_processed_output_root():
    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        project_root / "data preprocessing" / "processed_output",
        project_root / "data preprocessing",
        Path.cwd() / "data preprocessing" / "processed_output",
        Path.cwd() / "data preprocessing",
    ]
    for candidate in candidates:
        if candidate.is_dir() and candidate.name == "processed_output":
            return candidate
        if candidate.is_dir() and (candidate / "processed_output").is_dir():
            return candidate / "processed_output"
    return candidates[0]

ROOT = _resolve_processed_output_root()
run_dirs = sorted(ROOT.glob("run_*"))
if not run_dirs:
    raise FileNotFoundError(f"No run_* folders found under '{ROOT}'.")
required_files = ["features.json", "turbofan_full.csv", "train_normal.csv", "test_all.csv"]
valid_runs = [run for run in run_dirs if all((run / name).exists() for name in required_files)]
if not valid_runs:
    raise FileNotFoundError(
        f"No complete training run found under '{ROOT}'. Expected files: {required_files}"
    )
RUN = valid_runs[-1]  # use the latest complete run
RES = RUN / "results"; RES.mkdir(exist_ok=True)

with open(RUN / "features.json", "r", encoding="utf-8") as fh:
    feats = json.load(fh)
full  = pd.read_csv(RUN / "turbofan_full.csv")
norm  = pd.read_csv(RUN / "train_normal.csv")      # healthy rows, train engines
test  = pd.read_csv(RUN / "test_all.csv")
train_lab = full[full.split == "train"].reset_index(drop=True)   # labelled train engines
yte = test["label"].values
Q_GRID = [(0.90, 0.99), (0.95, 0.99), (0.95, 0.999), (0.99, 0.999)]

def zones(s, t1, t2):
    return np.where(s <= t1, "normal", np.where(s <= t2, "near_anomaly", "anomaly"))

def cal_split(df, seed=42):          # healthy rows split by engine: fit part / calibration part
    a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed).split(df, groups=df["unit"]))
    return df.iloc[a][feats].values, df.iloc[b][feats].values

def metrics(name, y, pred, s_near=None):
    p, r, f, _ = precision_recall_fscore_support(y, pred, labels=["near_anomaly"], zero_division=0)
    d = dict(model=name, macroF1=f1_score(y, pred, average="macro"), near_P=p[0], near_R=r[0], near_F1=f[0],
             FAR=np.mean(pred[y == "normal"] != "normal"))
    if s_near is not None:
        m = y != "anomaly"; yb = y[m] == "near_anomaly"
        d["PR_AUC"] = average_precision_score(yb, s_near[m]); d["ROC_AUC"] = roc_auc_score(yb, s_near[m])
    return d

# ---------- models: each factory takes healthy X and returns a scoring function ----------
class Christoffel:
    def __init__(self, d=2, reg=1e-6): self.d, self.reg = d, reg
    def fit(self, X):
        self.pf = PolynomialFeatures(self.d).fit(X); M = 0
        for i in range(0, len(X), 5000):
            V = self.pf.transform(X[i:i+5000]); M = M + V.T @ V
        self.Minv = np.linalg.inv(M / len(X) + self.reg * np.eye(M.shape[0])); return self
    def score(self, X):
        out = []
        for i in range(0, len(X), 5000):
            V = self.pf.transform(X[i:i+5000]); out.append(((V @ self.Minv) * V).sum(1))
        return np.concatenate(out)

def sub(X, n=15000, seed=0):
    return X[np.random.RandomState(seed).choice(len(X), min(n, len(X)), replace=False)]

def f_canari(X, d=2, reg=1e-6): return Christoffel(d, reg).fit(X).score
def f_iforest(X, n=300):
    m = IsolationForest(n_estimators=n, random_state=42).fit(X); return lambda Z: -m.score_samples(Z)
def f_ocsvm(X, nu=0.05):
    m = OneClassSVM(gamma="scale", nu=nu).fit(sub(X)); return lambda Z: -m.decision_function(Z)
def f_lof(X, k=35):
    m = LocalOutlierFactor(n_neighbors=k, novelty=True).fit(sub(X)); return lambda Z: -m.score_samples(Z)
def f_autoenc(X, h=(8, 3, 8)):
    S = sub(X, 30000)
    m = MLPRegressor(hidden_layer_sizes=h, max_iter=60, early_stopping=True, random_state=42).fit(S, S)
    return lambda Z: ((Z - m.predict(Z)) ** 2).sum(1)
def f_oja(X, k=4, epochs=3, lr=1e-3):     # Hebbian: Sanger's rule
    X = sub(X, 20000); rng = np.random.RandomState(0); W = rng.normal(0, .1, (k, X.shape[1]))
    for _ in range(epochs):
        for x in X[rng.permutation(len(X))]:
            y = W @ x; W += lr * (np.outer(y, x) - np.tril(np.outer(y, y)) @ W)
    return lambda Z: ((Z - (Z @ W.T) @ W) ** 2).sum(1)

GRIDS = {
  "Mahalanobis (d=1)": (f_canari, [dict(d=1, reg=1e-6)]),
  "CANARI":            (f_canari, [dict(d=d, reg=r) for d in (2, 3) for r in (1e-6, 1e-3)]),
  "Isolation Forest":  (f_iforest, [dict(n=200), dict(n=400)]),
  "One-Class SVM":     (f_ocsvm, [dict(nu=0.02), dict(nu=0.05)]),
  "LOF":               (f_lof, [dict(k=20), dict(k=50)]),
  "Autoencoder":       (f_autoenc, [dict(h=(8, 3, 8)), dict(h=(10, 5, 10))]),
  "Hebbian (Sanger)":  (f_oja, [dict(k=3), dict(k=5)]),
}

def cv_tune(factory, grid, k=5):      # GroupKFold by engine on TRAIN engines only
    best = (-1, None, None)
    for params in grid:
        res = {q: [] for q in Q_GRID}
        for tr, va in GroupKFold(k).split(train_lab, groups=train_lab["unit"]):
            T, V = train_lab.iloc[tr], train_lab.iloc[va]
            Xf, Xc = cal_split(T[T.label == "normal"])
            fn = factory(Xf, **params); sc, sv = fn(Xc), fn(V[feats].values)
            for q in Q_GRID:
                t1, t2 = np.quantile(sc, q)
                res[q].append(f1_score(V.label, zones(sv, t1, t2), average="macro"))
        for q, v in res.items():
            if np.mean(v) > best[0]: best = (np.mean(v), params, q)
    return best