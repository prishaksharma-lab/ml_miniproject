from common import *
from math import comb
from sklearn.decomposition import PCA

class CanariPaper:
    """Billet et al. DX 2026: eCF growth ratio G = eCF_n2 / eCF_n1, Chebyshev threshold.
    PCA stands in for the paper's CLOE autoencoder."""
    def __init__(self, dim=8, n1=1, n2=4, reg=1e-6):
        self.dim, self.n1, self.n2, self.reg = dim, n1, n2, reg
    def fit(self, X):
        self.pca = PCA(self.dim, random_state=42).fit(X)
        Z = self.pca.transform(X)
        self.c1 = Christoffel(self.n1, self.reg).fit(Z)
        self.c2 = Christoffel(self.n2, self.reg).fit(Z)
        return self
    def _eCF(self, X):
        Z = self.pca.transform(X); return self.c1.score(Z), self.c2.score(Z)
    def score(self, X):
        e1, e2 = self._eCF(X); return e2 / e1
    def calibrate(self, Xval, k=1.5, q_anom=1.0):
        e1, e2 = self._eCF(Xval)
        self.tau_na = comb(self.dim + self.n2, self.n2) / e1.min() + k * (e2 / e1).std()   # paper eq. 23
        self.tau_an = np.quantile(e2, q_anom)       # anomaly = eCF above healthy max
        return self
    def predict(self, X):
        e1, e2 = self._eCF(X)
        return np.where(e2 > self.tau_an, "anomaly", np.where(e2 / e1 > self.tau_na, "near_anomaly", "normal"))

def f_growth(X, dim=8):                       # growth-ratio score, used with quantile thresholds
    return CanariPaper(dim=dim).fit(X).score

def cv_paper(dims=(6, 8, 10), ks=(2**.5, 1.5, 2), nfold=5):
    res = {(d, k): [] for d in dims for k in ks}
    for tr, va in GroupKFold(nfold).split(train_lab, groups=train_lab["unit"]):
        T, V = train_lab.iloc[tr], train_lab.iloc[va]
        Xf, Xc = cal_split(T[T.label == "normal"])
        for d in dims:
            m = CanariPaper(dim=d).fit(Xf)
            for k in ks:
                m.calibrate(Xc, k=k)
                res[(d, k)].append(f1_score(V.label, m.predict(V[feats].values), average="macro"))
    out = {key: np.mean(v) for key, v in res.items()}
    return max(out, key=out.get), out