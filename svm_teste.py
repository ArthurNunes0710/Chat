import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import random
import gc

from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import f1_score, accuracy_score, recall_score, confusion_matrix

from deap import base, creator, tools

warnings.filterwarnings("ignore")


# CONFIG

filepath = "dataset.csv"
date = "2024-01-02"
ticker_id = 2952

SEED = 7
random.seed(SEED)
np.random.seed(SEED)

HORIZONTE = 1

POP_SIZE = 15
NGEN = 1000
N_SPLITS = 5
CX_PB = 0.8


# CARREGA DATASET

df_final = pd.read_csv(filepath)
df_final["datetime"] = pd.to_datetime(df_final["datetime"])

def Filtrar(date, ticker_id):
    df_ticker = df_final[df_final["id_ticker"] == ticker_id].reset_index(drop=True)
    data = pd.to_datetime(date).date()

    df_day = df_ticker[df_ticker["datetime"].dt.date == data]

    if df_day.empty:
        print("Sem dados.")
        return None

    return df_ticker

df_modelo = Filtrar(date, ticker_id)
if df_modelo is None:
    raise SystemExit


# NORMALIZAÇÕES

for col in ["ADX", "ADXR", "CMO", "IMI"]:
    df_modelo[col] /= 100.0

df_modelo["MOM"] /= df_modelo["close"]
df_modelo["SAR"] /= df_modelo["close"]
df_modelo["ROC"] /= 100.0


# TARGET

y = df_modelo["trend"].shift(-HORIZONTE)

X = df_modelo.drop(
    columns=["id_ticker", "date", "time", "datetime", "trend"]
)

X = X.iloc[:-HORIZONTE]
y = y.iloc[:-HORIZONTE]


# SCALING

macd_cols = ["MACD", "MACD_SIGNAL", "MACD_HIST"]

macd_scaler = StandardScaler()
X[macd_cols] = macd_scaler.fit_transform(X[macd_cols])

cols_minmax = [
    "open","high","low","close","volume","average","amount_stock",
    "EMA_3","SMA_3","DEMA_3","TRIMA_3","WMA_3","TEMA_3",
    "EMA_5","SMA_5","DEMA_5","TRIMA_5","WMA_5","TEMA_5",
    "EMA_7","SMA_7","DEMA_7","TRIMA_7","WMA_7","TEMA_7",
    "EMA_9","SMA_9","DEMA_9","TRIMA_9","WMA_9","TEMA_9"
]

scaler = MinMaxScaler()
X[cols_minmax] = scaler.fit_transform(X[cols_minmax])


# FEATURES

best_features = [
'TRIMA_3','DEMA_3','SMA_3','EMA_3','WMA_3','TEMA_3',
'TRIMA_5','SMA_5','EMA_5','WMA_5','TEMA_5',
'TRIMA_7','SMA_7','WMA_7',
'TRIMA_9','SMA_9','WMA_9',
'SAR','MOM','ROC'
]

X_all = X[best_features].values.astype(np.float32)
y_all = y.values.astype(np.int32)


# SPLIT DEV / TEST

TEST_SIZE = 0.3
split_idx = int(len(X_all)*(1-TEST_SIZE))

X_dev = X_all[:split_idx]
y_dev = y_all[:split_idx]

X_test_final = X_all[split_idx:]
y_test_final = y_all[split_idx:]


# HISTÓRICO

history_best = []
history_mean = []


# DECODE INDIVÍDUO

def decode_individual(ind):

    C_exp = np.clip(ind[0], -3, 3)
    gamma_exp = np.clip(ind[1], -4, 1)

    C = 10 ** C_exp
    gamma = 10 ** gamma_exp

    kernel = "rbf"
    degree = 3

    return C, gamma, kernel, degree


# TRAIN FOLD

def train_fold(tr_idx, va_idx, C, gamma, kernel, degree):

    X_tr = X_dev[tr_idx]
    X_va = X_dev[va_idx]
    y_tr = y_dev[tr_idx]
    y_va = y_dev[va_idx]

    model = SVC(
        C=C,
        gamma=gamma,
        kernel=kernel,
        degree=degree,
        random_state=SEED
    )

    model.fit(X_tr, y_tr)

    # treino
    y_pred_tr = model.predict(X_tr)
    score_tr = f1_score(y_tr, y_pred_tr, average="macro")

    # validação
    y_pred_va = model.predict(X_va)
    score_va = f1_score(y_va, y_pred_va, average="macro")

    del model
    gc.collect()

    return score_tr, score_va


# FITNESS

eval_cache = {}

def evaluate(individual):

    key = tuple(individual)

    if key in eval_cache:
        return (eval_cache[key],)

    C, gamma, kernel, degree = decode_individual(individual)

    tscv = TimeSeriesSplit(n_splits=N_SPLITS)

    scores_tr = []
    scores_va = []

    for tr_idx, va_idx in tscv.split(X_dev):
        s_tr, s_va = train_fold(tr_idx, va_idx, C, gamma, kernel, degree)
        scores_tr.append(s_tr)
        scores_va.append(s_va)

    mean_tr = float(np.mean(scores_tr))
    mean_va = float(np.mean(scores_va))
    

    
    C_penalty = 0.001 * max(0, np.log10(C) - 10)
    gamma_penalty = 0.001 * max(0, np.log10(gamma) + 2)

    fitness = (0.4 * mean_tr + 0.6 * mean_va  - C_penalty - gamma_penalty)

    eval_cache[key] = fitness

    return (fitness,)


# GA — DEAP

if "FitnessMax" in creator.__dict__:
    del creator.FitnessMax
if "Individual" in creator.__dict__:
    del creator.Individual

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()


toolbox.register("C", random.uniform, -5, 15)
toolbox.register("gamma", random.uniform, -15, 3)

toolbox.register(
    "individual",
    tools.initCycle,
    creator.Individual,
    (
        toolbox.C,
        toolbox.gamma,
    ),
    n=1
)

toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", evaluate)
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.5, indpb=0.1)
toolbox.register("select", tools.selTournament, tournsize=3)


# LOOP GA

population = toolbox.population(n=POP_SIZE)
hof = tools.HallOfFame(1)

for ind in population:
    ind.fitness.values = toolbox.evaluate(ind)

hof.update(population)

for gen in range(1, NGEN+1):

    offspring = toolbox.select(population, len(population))
    offspring = list(map(toolbox.clone, offspring))

    for c1, c2 in zip(offspring[::2], offspring[1::2]):
        if random.random() < CX_PB:
            toolbox.mate(c1, c2)
            del c1.fitness.values
            del c2.fitness.values

    for mut in offspring:
        if random.random() < 0.5:
            toolbox.mutate(mut)
            del mut.fitness.values

    invalid = [ind for ind in offspring if not ind.fitness.valid]

    for ind in invalid:
        ind.fitness.values = toolbox.evaluate(ind)

    best_prev = tools.selBest(population,1)[0]
    offspring[-1] = toolbox.clone(best_prev)
    offspring[-1].fitness.values = best_prev.fitness.values

    population[:] = offspring
    hof.update(population)

    fits = [ind.fitness.values[0] for ind in population]

    history_best.append(hof[0].fitness.values[0])
    history_mean.append(np.mean(fits))

    print(
        f"Geração {gen:03d} | "
        f"mean={np.mean(fits):.4f} | "
        f"best={hof[0].fitness.values[0]:.4f}"
    )


# RESULTADO FINAL

best_ind = hof[0]

C, gamma, kernel, degree = decode_individual(best_ind)

print("\n MELHOR INDIVÍDUO ")
print("C:", C)
print("gamma:", gamma)
print("kernel:", kernel)
print("degree:", degree)

svm_final = SVC(
    C=C,
    gamma=gamma,
    kernel=kernel,
    degree=degree,
    random_state=SEED
)

svm_final.fit(X_dev, y_dev)

y_pred_final = svm_final.predict(X_test_final)

print("\n TESTE FINAL")

print("Accuracy:", accuracy_score(y_test_final, y_pred_final))
print("F1 macro:", f1_score(y_test_final, y_pred_final, average="macro"))
print("Recall  :", recall_score(y_test_final, y_pred_final, average="macro"))

print("\nMatriz Confusão:")
print(confusion_matrix(y_test_final, y_pred_final))


# GRÁFICO

plt.figure(figsize=(10,6))
plt.plot(history_best, label="Best")
plt.plot(history_mean, label="Mean")
plt.legend()
plt.grid(True)
plt.show()